from __future__ import annotations

import asyncio
import time
from typing import Any

from models import Request

from metrics import PipelineMetrics, RequestMetric
from tools import FinancialTools


class ElasticRouter:
    """Bounded agent loop whose tools are deterministic and allowlisted."""

    def __init__(self, tools: FinancialTools, metrics: PipelineMetrics):
        self.tools = tools
        self.metrics = metrics
        self.max_steps = max(1, int(__import__("os").getenv("AGENT_MAX_STEPS", "8")))
        self.request_semaphore = asyncio.Semaphore(
            max(1, int(__import__("os").getenv("MAX_CONCURRENCY", "4")))
        )
        self.evidence_lock = asyncio.Lock()

    @staticmethod
    def _fallback_row(request: Request, row: dict[str, str]) -> dict[str, str]:
        return {
            "request_id": request.request_id,
            "amount_safe_to_pay": row.get("amount_safe_to_pay", "0"),
            "affordability_status": "not_affordable",
            "recommended_payment_method": "not_recommended",
            "payment_plan": "none",
            "earliest_date_for_full_payment": row.get("earliest_date_for_full_payment", ""),
            "spending_changes_needed": "none",
            "decision_explanation": "No contract-valid recommendation could be produced safely.",
        }

    async def process(self, request: Request) -> dict[str, Any]:
        async with self.request_semaphore:
            started = time.perf_counter()
            trace: list[str] = []
            errors: list[str] = []
            guard_result: dict[str, Any] | None = None
            fallback_used = False
            context: dict[str, Any] = {}
            row: dict[str, str] = {}
            try:
                trace.append("retrieve_financial_data")
                context = await asyncio.to_thread(self.tools.retrieve_financial_data, request)
                model_context = {
                    "request": context.get("request", {}),
                    "messages": context.get("messages", []),
                    "evidence_summary": [
                        {
                            "event_id": event.get("event_id"),
                            "category": event.get("category"),
                            "amount": event.get("amount"),
                            "currency": event.get("currency"),
                            "status": event.get("status"),
                        }
                        for event in context.get("events", [])[:40]
                    ],
                }

                # The two configured Groq models run concurrently for this transaction.
                trace.extend(["guard_and_route", "extract_document"])
                guard_task = self.tools.gateway.guard_and_route(model_context)
                document_task = self.tools.extract_document(context)
                guard_result, extracted = await asyncio.gather(
                    guard_task,
                    document_task,
                    return_exceptions=True,
                )
                if isinstance(guard_result, Exception):
                    errors.append("guard_exception")
                    guard_result = {
                        "status": "failed",
                        "flagged": False,
                        "requested_tools": [],
                    }
                if isinstance(extracted, Exception):
                    errors.append("document_exception")
                    extracted = []

                if guard_result:
                    requested_tools = guard_result.get("requested_tools", [])
                else:
                    requested_tools = []
                if requested_tools or context.get("messages") or context.get("request", {}).get("request_text"):
                    trace.append("search_faiss")
                    context["semantic_evidence"] = await self.tools.search_faiss(request, context)
                else:
                    context["semantic_evidence"] = []

                if extracted:
                    async with self.evidence_lock:
                        applied = self.tools.apply_extracted_evidence(extracted)
                    context["extracted_evidence"] = extracted
                    context["applied_evidence_count"] = applied
                else:
                    context["extracted_evidence"] = []
                    context["applied_evidence_count"] = 0

                if len(trace) >= self.max_steps:
                    errors.append("agent_step_limit")

                trace.append("forecast_balance")
                row, details = await asyncio.to_thread(self.tools.forecast_balance, request)
                trace.append("evaluate_payment_options")
                _ = self.tools.evaluate_payment_options(row, details)
                trace.append("validate_decision")
                validation_errors = await asyncio.to_thread(self.tools.validate_decision, request, row)
                if validation_errors:
                    errors.extend(validation_errors)
                    fallback_used = True
                    row = self._fallback_row(request, row)
                    fallback_errors = await asyncio.to_thread(
                        self.tools.validate_decision, request, row
                    )
                    if fallback_errors:
                        raise RuntimeError(f"invalid fallback: {fallback_errors}")
            except Exception as exc:
                errors.append(type(exc).__name__)
                fallback_used = True
                if not row:
                    row = {
                        "request_id": request.request_id,
                        "amount_safe_to_pay": "0",
                        "affordability_status": "not_affordable",
                        "recommended_payment_method": "not_recommended",
                        "payment_plan": "none",
                        "earliest_date_for_full_payment": "",
                        "spending_changes_needed": "none",
                        "decision_explanation": "The request could not be evaluated safely.",
                    }
            latency_ms = (time.perf_counter() - started) * 1000
            guard_status = (
                str(guard_result.get("status", "failed"))
                if guard_result and self.tools.gateway.orchestrator_enabled
                else "disabled"
            )
            guard_flagged = guard_status == "completed" and bool(
                guard_result and guard_result.get("flagged")
            )
            image_ids = {
                str(item.get("image_id"))
                for item in context.get("images", [])
                if item.get("image_id")
            }
            image_statuses = [
                self.tools.gateway.extraction_status.get(image_id, "skipped")
                for image_id in image_ids
            ]
            if not image_statuses:
                qwen_status = "skipped"
            elif not self.tools.gateway.extraction_enabled:
                qwen_status = "disabled"
            elif "completed" in image_statuses:
                qwen_status = "completed"
            elif "timeout" in image_statuses:
                qwen_status = "timeout"
            elif "invalid_response" in image_statuses:
                qwen_status = "invalid_response"
            else:
                qwen_status = "failed"
            for status, prefix in ((guard_status, "guard"), (qwen_status, "qwen")):
                if status in {"failed", "timeout", "invalid_response"}:
                    errors.append(f"{prefix}_{status}")
            attempted_tools = len(trace)
            if not self.tools.gateway.orchestrator_enabled:
                attempted_tools -= 1
            if not self.tools.gateway.extraction_enabled or not image_ids:
                attempted_tools -= 1
            successful_tools = max(0, attempted_tools - sum(
                error.startswith(("guard_", "qwen_", "document_")) for error in errors
            ))
            model_calls = (1 if guard_status != "disabled" else 0) + sum(
                status not in {"disabled", "missing_file", "skipped"}
                for status in image_statuses
            )
            self.metrics.record_request(
                RequestMetric(
                    request_id=request.request_id,
                    latency_ms=latency_ms,
                    valid=not fallback_used,
                    fallback_used=fallback_used,
                    planned_steps=len(trace),
                    attempted_tools=attempted_tools,
                    successful_tools=successful_tools,
                    model_calls=model_calls,
                    guard_flagged=guard_flagged,
                    guard_status=("flagged" if guard_flagged else guard_status),
                    qwen_status=qwen_status,
                    errors=errors[:8],
                )
            )
            return {
                "request_id": request.request_id,
                "row": row,
                "trace": trace,
                "guard": guard_result,
                "errors": errors,
            }
