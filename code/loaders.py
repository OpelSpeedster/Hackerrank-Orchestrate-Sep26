from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from models import (
    Dataset,
    Event,
    ImageRef,
    Message,
    PaymentOption,
    Profile,
    Request,
    decimal,
)


def rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


def split_pipe(value: str) -> frozenset[str]:
    return frozenset(part.strip() for part in value.split("|") if part.strip())


def load_dataset(dataset_dir: str | Path = "dataset") -> Dataset:
    root = Path(dataset_dir)

    profiles: dict[str, Profile] = {}
    for row in rows(root / "financial_profiles.csv"):
        raw_max = row.get("max_installment_months", "").strip()
        profiles[row["user_id"]] = Profile(
            user_id=row["user_id"],
            home_currency=row["home_currency"],
            current_available_balance=decimal(row["current_available_balance"]),
            minimum_balance_to_keep=decimal(row["minimum_balance_to_keep"]),
            financial_priorities=split_pipe(row.get("financial_priorities", "")),
            protected_categories=split_pipe(row.get("expense_categories_to_protect", "")),
            reduce_categories=split_pipe(row.get("expense_categories_user_is_willing_to_reduce", "")),
            stop_categories=split_pipe(row.get("expense_categories_user_is_willing_to_stop", "")),
            accepted_methods=split_pipe(row.get("payment_methods_user_will_consider", "")),
            max_installment_months=int(raw_max) if raw_max else None,
        )

    events_by_user: dict[str, list[Event]] = defaultdict(list)
    for row in rows(root / "financial_events.csv"):
        event = Event(
            event_id=row["event_id"],
            user_id=row["user_id"],
            event_type=row["event_type"],
            description=row["description"],
            category=row["category"],
            direction=row["direction"],
            amount=decimal(row.get("amount")),
            currency=row["currency"],
            event_date=row["event_date"],
            settlement_date=row["settlement_date"],
            status=row["status"],
            linked_event_id=row.get("linked_event_id", ""),
            flexibility=row.get("flexibility", "fixed"),
            minimum_allowed_amount=decimal(row.get("minimum_allowed_amount")),
        )
        events_by_user[event.user_id].append(event)

    requests = [
        Request(
            request_id=row["request_id"],
            user_id=row["user_id"],
            request_date=row["request_date"],
            request_type=row["request_type"],
            requested_amount=decimal(row["requested_amount"]),
            desired_completion_date=row["desired_completion_date"],
            allows_partial_payment=row["allows_partial_payment"].strip().lower() == "true",
            request_text=row["request_text"],
        )
        for row in rows(root / "requests.csv")
    ]

    options_by_request: dict[str, list[PaymentOption]] = defaultdict(list)
    for row in rows(root / "request_payment_options.csv"):
        options_by_request[row["request_id"]].append(
            PaymentOption(
                payment_option_id=row["payment_option_id"],
                request_id=row["request_id"],
                payment_method=row["payment_method"],
                payment_amount=decimal(row["payment_amount"]),
                number_of_payments=int(row["number_of_payments"]),
                first_payment_date=row["first_payment_date"],
                payment_frequency_days=(
                    int(row["payment_frequency_days"])
                    if row.get("payment_frequency_days", "").strip()
                    else None
                ),
                financing_fee=decimal(row["financing_fee"], default=decimal("0")),
                total_payable_amount=decimal(row["total_payable_amount"]),
            )
        )

    messages_by_user: dict[str, list[Message]] = defaultdict(list)
    messages_by_request: dict[str, list[Message]] = defaultdict(list)
    messages_by_event: dict[str, list[Message]] = defaultdict(list)
    for row in rows(root / "messages.csv"):
        message = Message(
            message_id=row["message_id"],
            user_id=row["user_id"],
            request_id=row.get("request_id", ""),
            related_event_id=row.get("related_event_id", ""),
            sent_at=row["sent_at"],
            source_type=row["source_type"],
            message_text=row["message_text"],
        )
        messages_by_user[message.user_id].append(message)
        if message.request_id:
            messages_by_request[message.request_id].append(message)
        if message.related_event_id:
            messages_by_event[message.related_event_id].append(message)

    images_by_event: dict[str, list[ImageRef]] = defaultdict(list)
    images_by_request: dict[str, list[ImageRef]] = defaultdict(list)
    for row in rows(root / "images.csv"):
        image = ImageRef(
            image_id=row["image_id"],
            user_id=row["user_id"],
            request_id=row.get("request_id", ""),
            related_event_id=row.get("related_event_id", ""),
        )
        if image.related_event_id:
            images_by_event[image.related_event_id].append(image)
        if image.request_id:
            images_by_request[image.request_id].append(image)

    rates: dict[tuple[str, str, str], object] = {}
    for row in rows(root / "exchange_rates.csv"):
        rates[(row["rate_date"], row["from_currency"], row["to_currency"])] = decimal(row["rate"])

    return Dataset(
        profiles=profiles,
        events_by_user=dict(events_by_user),
        requests=requests,
        options_by_request=dict(options_by_request),
        messages_by_user=dict(messages_by_user),
        messages_by_request=dict(messages_by_request),
        messages_by_event=dict(messages_by_event),
        images_by_event=dict(images_by_event),
        images_by_request=dict(images_by_request),
        rates=rates,
    )
