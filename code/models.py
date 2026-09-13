from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

ZERO = Decimal("0")
CENT = Decimal("0.01")


def decimal(value: Any, default: Optional[Decimal] = None) -> Optional[Decimal]:
    if value is None or str(value).strip() == "":
        return default
    try:
        return Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return default


def amount_text(value: Decimal) -> str:
    value = value.quantize(CENT) if value != value.to_integral() else value
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


@dataclass(frozen=True)
class Profile:
    user_id: str
    home_currency: str
    current_available_balance: Decimal
    minimum_balance_to_keep: Decimal
    financial_priorities: frozenset[str]
    protected_categories: frozenset[str]
    reduce_categories: frozenset[str]
    stop_categories: frozenset[str]
    accepted_methods: frozenset[str]
    max_installment_months: Optional[int]


@dataclass
class Event:
    event_id: str
    user_id: str
    event_type: str
    description: str
    category: str
    direction: str
    amount: Optional[Decimal]
    currency: str
    event_date: str
    settlement_date: str
    status: str
    linked_event_id: str
    flexibility: str
    minimum_allowed_amount: Optional[Decimal]
    source: str = "csv"

    @property
    def is_debit(self) -> bool:
        return self.direction == "debit"

    @property
    def is_credit(self) -> bool:
        return self.direction == "credit"

    @property
    def is_recurring_candidate(self) -> bool:
        return self.event_type in {"expense", "subscription", "income", "debt_payment"}


@dataclass(frozen=True)
class Request:
    request_id: str
    user_id: str
    request_date: str
    request_type: str
    requested_amount: Decimal
    desired_completion_date: str
    allows_partial_payment: bool
    request_text: str


@dataclass(frozen=True)
class PaymentOption:
    payment_option_id: str
    request_id: str
    payment_method: str
    payment_amount: Decimal
    number_of_payments: int
    first_payment_date: str
    payment_frequency_days: Optional[int]
    financing_fee: Decimal
    total_payable_amount: Decimal

    def schedule(self) -> list[tuple[str, Decimal]]:
        from datetime import date, timedelta

        start = date.fromisoformat(self.first_payment_date)
        frequency = self.payment_frequency_days or 0
        return [
            ((start + timedelta(days=frequency * index)).isoformat(), self.payment_amount)
            for index in range(self.number_of_payments)
        ]


@dataclass(frozen=True)
class Message:
    message_id: str
    user_id: str
    request_id: str
    related_event_id: str
    sent_at: str
    source_type: str
    message_text: str


@dataclass(frozen=True)
class ImageRef:
    image_id: str
    user_id: str
    request_id: str
    related_event_id: str


@dataclass
class Usage:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: Decimal = ZERO
    extraction_calls: int = 0
    reasoning_calls: int = 0

    def add_response(self, response: Any, kind: str, input_rate: Decimal = ZERO, output_rate: Decimal = ZERO) -> None:
        self.calls += 1
        if kind == "extraction":
            self.extraction_calls += 1
        else:
            self.reasoning_calls += 1
        details = getattr(response, "usage", None)
        if details is not None:
            prompt = int(getattr(details, "prompt_tokens", 0) or 0)
            completion = int(getattr(details, "completion_tokens", 0) or 0)
            self.input_tokens += prompt
            self.output_tokens += completion
            self.estimated_cost_usd += (
                Decimal(prompt) / Decimal(1_000_000) * input_rate
                + Decimal(completion) / Decimal(1_000_000) * output_rate
            )


@dataclass
class Dataset:
    profiles: dict[str, Profile]
    events_by_user: dict[str, list[Event]]
    requests: list[Request]
    options_by_request: dict[str, list[PaymentOption]]
    messages_by_user: dict[str, list[Message]]
    messages_by_request: dict[str, list[Message]]
    messages_by_event: dict[str, list[Message]]
    images_by_event: dict[str, list[ImageRef]]
    images_by_request: dict[str, list[ImageRef]]
    rates: dict[tuple[str, str, str], Decimal]
