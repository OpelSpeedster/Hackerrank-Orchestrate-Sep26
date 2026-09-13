from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from ingestion import normalize_event
from loaders import load_dataset
from models import Dataset, Request, amount_text, decimal
from planning import plan_request
from validation import validate_row

from gateway import GroqGateway
from modal_client import ModalClient
from retrieval import EvidenceIndex


class FinancialTools:
    """Allowlisted tools exposed to the agent orchestrator."""

    def __init__(
        self,
        dataset_root: Path,
        dataset: Dataset,
        index: EvidenceIndex,
        gateway: GroqGateway,
        modal: ModalClient,
    ):
        self.dataset_root = dataset_root
        self.dataset = dataset
        self.index = index
        self.gateway = gateway
        self.modal = modal

    def retrieve_financial_data(self, request: Request) -> dict[str, Any]:
        profile = self.dataset.profiles[request.user_id]
        message_event_ids = {
            message.related_event_id
            for message in self.dataset.messages_by_request.get(request.request_id, [])
            if message.related_event_id
        }
        linked_image_event_ids = {
            image.related_event_id
            for event_list in self.dataset.images_by_event.values()
            for image in event_list
            if image.related_event_id
        }
        events = [
            normalize_event(event, profile, self.dataset)
            for event in self.dataset.events_by_user.get(request.user_id, [])
            if event.event_date >= request.request_date
            or event.status in {"pending", "scheduled"}
            or event.event_id in message_event_ids
            or (event.amount is None and event.event_id in linked_image_event_ids)
        ]
        messages = []
        seen_messages: set[str] = set()
        for message in self.dataset.messages_by_request.get(request.request_id, []):
            if message.message_id not in seen_messages:
                messages.append(
                    {
                        "message_id": message.message_id,
                        "related_event_id": message.related_event_id,
                        "source_type": message.source_type,
                        "sent_at": message.sent_at,
                        "message_text": message.message_text[:1500],
                    }
                )
                seen_messages.add(message.message_id)
        for event in events:
            for message in self.dataset.messages_by_event.get(event["event_id"], []):
                if message.message_id not in seen_messages:
                    messages.append(
                        {
                            "message_id": message.message_id,
                            "related_event_id": message.related_event_id,
                            "source_type": message.source_type,
                            "sent_at": message.sent_at,
                            "message_text": message.message_text[:1500],
                        }
                    )
                    seen_messages.add(message.message_id)
        options = [
            {
                "payment_option_id": option.payment_option_id,
                "payment_method": option.payment_method,
                "payment_amount": amount_text(option.payment_amount),
                "number_of_payments": option.number_of_payments,
                "first_payment_date": option.first_payment_date,
                "payment_frequency_days": option.payment_frequency_days,
                "financing_fee": amount_text(option.financing_fee),
                "total_payable_amount": amount_text(option.total_payable_amount),
            }
            for option in self.dataset.options_by_request.get(request.request_id, [])
        ]
        images = [
            {
                "image_id": image.image_id,
                "related_event_id": image.related_event_id,
                "request_id": image.request_id,
            }
            for image in self.dataset.images_by_request.get(request.request_id, [])
        ]
        images.extend(
            {
                "image_id": image.image_id,
                "related_event_id": image.related_event_id,
                "request_id": image.request_id,
            }
            for event in events
            for image in self.dataset.images_by_event.get(event["event_id"], [])
            if image.request_id != request.request_id
        )
        return {
            "request": {
                "request_id": request.request_id,
                "user_id": request.user_id,
                "request_date": request.request_date,
                "request_type": request.request_type,
                "requested_amount": amount_text(request.requested_amount),
                "desired_completion_date": request.desired_completion_date,
                "allows_partial_payment": request.allows_partial_payment,
                "request_text": request.request_text[:2000],
            },
            "profile": {
                "home_currency": profile.home_currency,
                "current_available_balance": amount_text(profile.current_available_balance),
                "minimum_balance_to_keep": amount_text(profile.minimum_balance_to_keep),
                "protected_categories": sorted(profile.protected_categories),
                "reduce_categories": sorted(profile.reduce_categories),
                "stop_categories": sorted(profile.stop_categories),
                "accepted_methods": sorted(profile.accepted_methods),
                "max_installment_months": profile.max_installment_months,
            },
            "events": events[:160],
            "messages": messages[:40],
            "payment_options": options,
            "images": images,
        }

    async def search_faiss(self, request: Request, context: dict[str, Any]) -> list[dict]:
        event_ids = [str(event["event_id"]) for event in context.get("events", [])]
        query = f"{request.request_text} {request.request_type} {' '.join(event_ids)}"
        return await self.index.search_async(
            query=query,
            user_id=request.user_id,
            request_id=request.request_id,
            event_ids=event_ids,
            limit=8,
            embedder=self.modal,
        )

    async def extract_document(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        refs = []
        seen: set[str] = set()
        for item in context.get("images", []):
            image_id = str(item.get("image_id", ""))
            if image_id and image_id not in seen:
                refs.append(item)
                seen.add(image_id)
        missing_event_ids = {
            event["event_id"] for event in context.get("events", []) if event.get("amount") is None
        }
        refs = [ref for ref in refs if not ref.get("related_event_id") or ref.get("related_event_id") in missing_event_ids]
        if not refs:
            return []

        async def one(ref: dict[str, Any]) -> dict[str, Any] | None:
            image_id = str(ref["image_id"])
            related_event_id = str(ref.get("related_event_id", ""))
            image_path = self.dataset_root / "media" / "images" / f"{image_id}.png"
            result = await self.gateway.extract_image(image_id, related_event_id, image_path)
            if result is not None:
                return result
            if self.modal.enabled and image_path.exists():
                return await self.modal.extract_document(image_path, image_id, related_event_id)
            return None

        results = await __import__("asyncio").gather(*(one(ref) for ref in refs), return_exceptions=True)
        return [result for result in results if isinstance(result, dict)]

    def apply_extracted_evidence(self, evidence: list[dict[str, Any]]) -> int:
        events = {
            event.event_id: event
            for user_events in self.dataset.events_by_user.values()
            for event in user_events
        }
        applied = 0
        for item in evidence:
            event_id = str(item.get("related_event_id") or "")
            event = events.get(event_id)
            confidence = str(item.get("confidence", "")).lower()
            amount = decimal(item.get("amount"))
            if event is None or event.amount is not None or amount is None or amount < 0:
                continue
            if confidence not in {"high", "medium"}:
                continue
            event.amount = amount
            if item.get("currency"):
                event.currency = str(item["currency"])
            event.source = f"document:{item.get('source_id', 'unknown')}"
            applied += 1
        return applied

    def forecast_balance(self, request: Request) -> tuple[dict, dict]:
        return plan_request(self.dataset, request)

    def evaluate_payment_options(self, planned_row: dict, details: dict) -> dict:
        candidate = details.get("candidate")
        return {
            "row": planned_row,
            "candidate_method": getattr(candidate, "method", "not_recommended"),
            "payment_count": len(getattr(candidate, "payments", [])),
            "total_cost": amount_text(getattr(candidate, "total_cost", Decimal("0"))),
        }

    def validate_decision(self, request: Request, row: dict[str, str]) -> list[str]:
        return validate_row(self.dataset, request, row)
