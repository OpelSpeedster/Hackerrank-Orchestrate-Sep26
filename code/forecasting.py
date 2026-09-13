from __future__ import annotations

import calendar
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN
import re
from statistics import median
from typing import Iterable, Mapping, Optional

from models import CENT, Dataset, Event, Profile, Request, decimal

IGNORED_STATUSES = {"failed", "cancelled", "unrealized"}


def d(value: str) -> date:
    return date.fromisoformat(value)


def convert_to_home(
    dataset: Dataset,
    amount: Decimal,
    currency: str,
    home: str,
    settlement_date: str,
) -> Optional[Decimal]:
    """Use only the fixed rate for this event's settlement date.

    Reusing an older rate invents a financial fact. Missing or invalid rates
    are represented as ``None`` and make the affected forecast conservative.
    """
    if currency == home:
        return amount
    rate = dataset.rates.get((settlement_date, currency, home))
    if rate is None or rate == 0:
        return None
    return amount * rate


def _effective_date(event: Event) -> str:
    return event.settlement_date or event.event_date


def _is_cash_event(event: Event) -> bool:
    return event.direction in {"debit", "credit"} and event.status not in IGNORED_STATUSES


def _should_count(event: Event) -> bool:
    if not _is_cash_event(event) or event.amount is None:
        return False
    if event.status == "pending" and event.is_credit:
        return False
    return True


def _message_rules(dataset: Dataset, request: Request, profile: Profile) -> dict[str, object]:
    """Extract only explicit, structured amendments from relevant messages."""
    messages = []
    seen: set[str] = set()
    for message in dataset.messages_by_user.get(request.user_id, []):
        if message.message_id in seen:
            continue
        sent_date = message.sent_at[:10] if message.sent_at else ""
        if sent_date and sent_date <= request.request_date:
            messages.append(message.message_text)
            seen.add(message.message_id)
    for message in dataset.messages_by_request.get(request.request_id, []):
        if message.message_id in seen:
            continue
        sent_date = message.sent_at[:10] if message.sent_at else ""
        if sent_date and sent_date <= request.request_date:
            messages.append(message.message_text)
            seen.add(message.message_id)

    salary_amount: Optional[Decimal] = None
    salary_currency = profile.home_currency
    commission_not_confirmed = False
    rent_multiplier = Decimal("1")
    currency_amount = re.compile(r"\b(IDR|INR|ZAR|USD|EUR)\s*([0-9][0-9,]*(?:\.[0-9]+)?)\b", re.IGNORECASE)
    percent_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*%")
    for text in messages:
        lowered = text.lower()
        matches = list(currency_amount.finditer(text))
        salary_message = any(token in lowered for token in ("salary", "payroll", "gaji"))
        if salary_message and matches:
            currency = matches[-1].group(1).upper()
            value = Decimal(matches[-1].group(2).replace(",", ""))
            converted = convert_to_home(dataset, value, currency, profile.home_currency, request.request_date)
            if converted is not None:
                salary_amount = converted
                salary_currency = currency
        if "commission" in lowered or "komisi" in lowered:
            if any(token in lowered for token in ("not approved", "not earned", "not payable", "not paid", "belum disetujui", "belum diperoleh")):
                commission_not_confirmed = True
        if "rent" in lowered and "increase" in lowered:
            percent = percent_pattern.search(text)
            if percent:
                rent_multiplier = Decimal("1") + Decimal(percent.group(1)) / Decimal("100")
    return {
        "salary_amount": salary_amount,
        "salary_currency": salary_currency,
        "commission_not_confirmed": commission_not_confirmed,
        "rent_multiplier": rent_multiplier,
    }


def _is_commission(event: Event) -> bool:
    text = f"{event.description} {event.category}".lower()
    return "commission" in text or "komisi" in text or "sales" in text


def recurring_stream_key(event: Event) -> str:
    """Return a deterministic identity for one recurring financial stream."""
    description = ""
    if event.category == "salary" or event.event_type in {"subscription", "income", "debt_payment"}:
        description = " ".join(event.description.lower().split()) if event.description else ""
    return "|".join((event.event_type, event.category, event.direction, event.currency, description))


def _intervals(values: list[date]) -> list[int]:
    values = sorted(set(values))
    return [(later - earlier).days for earlier, later in zip(values, values[1:])]


def _month_number(value: date) -> int:
    return value.year * 12 + value.month - 1


def _add_months(value: date, months: int, preferred_day: int) -> date:
    """Advance by calendar months, clamping invalid days to month end."""
    month_number = _month_number(value) + months
    year, month_index = divmod(month_number, 12)
    month = month_index + 1
    day = min(preferred_day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _is_monthly_cadence(dates: list[date], typical: float, intervals: list[int]) -> bool:
    """Recognize monthly streams without mistaking arbitrary 30-day intervals."""
    if not (27 <= typical <= 35):
        return False
    month_steps = [
        _month_number(later) - _month_number(earlier)
        for earlier, later in zip(dates, dates[1:])
    ]
    supported_steps = sum(step == 1 for step in month_steps)
    return supported_steps >= len(intervals) * 0.7


def _recurring_events(
    dataset: Dataset,
    profile: Profile,
    request: Request,
    rules: dict[str, object] | None = None,
) -> list[tuple[date, Event, Decimal]]:
    """Infer only strong recurring patterns from settled history before the request."""
    rules = rules or {}
    grouped: dict[str, list[Event]] = defaultdict(list)
    request_date = d(request.request_date)
    for event in dataset.events_by_user.get(request.user_id, []):
        if not event.is_recurring_candidate or event.status != "settled":
            continue
        if rules.get("commission_not_confirmed") and _is_commission(event):
            continue
        effective_date = _effective_date(event)
        if event.amount is None or not effective_date or d(effective_date) >= request_date:
            continue
        grouped[recurring_stream_key(event)].append(event)

    generated: list[tuple[date, Event, Decimal]] = []
    for _, history in grouped.items():
        history = sorted(history, key=lambda event: _effective_date(event))
        if len(history) < 3:
            continue
        dates = [d(_effective_date(event)) for event in history]
        intervals = _intervals(dates)
        if len(intervals) < 2:
            continue
        typical = median(intervals)
        if not (5 <= typical <= 35):
            continue
        tolerance = max(2, int(typical * 0.20))
        if (
            history[-1].category == "salary"
            and rules.get("salary_amount") is None
            and (request_date - dates[-1]).days > typical + tolerance
        ):
            # A stale salary series is not enough evidence for a new credit;
            # expenses may still be forecast from their own supported history.
            continue
        if sum(abs(interval - typical) <= tolerance for interval in intervals) < len(intervals) * 0.7:
            continue
        last = history[-1]
        normalized_amounts: list[Decimal] = []
        for event in history[-3:]:
            if event.amount is None:
                continue
            normalized = convert_to_home(
                dataset,
                event.amount,
                event.currency,
                profile.home_currency,
                _effective_date(event),
            )
            if event.category == "salary" and not _is_commission(event) and rules.get("salary_amount") is not None:
                normalized = rules["salary_amount"]
            if event.category == "rent" and rules.get("rent_multiplier", Decimal("1")) != Decimal("1"):
                normalized = normalized * rules["rent_multiplier"] if normalized is not None else None
            if normalized is None:
                normalized_amounts = []
                break
            normalized_amounts.append(normalized)
        if not normalized_amounts:
            continue
        if last.is_debit:
            # Conservative for variable essentials; median for fixed subscriptions.
            typical_amount = max(normalized_amounts) if last.category in {"groceries", "utilities", "transport"} else median(normalized_amounts)
        else:
            typical_amount = median(normalized_amounts)

        last_date = d(_effective_date(last))
        monthly = _is_monthly_cadence(dates, typical, intervals)
        preferred_day = int(median([item.day for item in dates])) if monthly else None
        end = request_date + timedelta(days=90)
        occurrence_index = 1
        while True:
            if monthly:
                next_date = _add_months(last_date, occurrence_index, preferred_day or last_date.day)
            else:
                next_date = last_date + timedelta(days=int(typical) * occurrence_index)
            if next_date > end:
                break
            generated.append((next_date, last, typical_amount))
            occurrence_index += 1
    return generated


@dataclass
class ForecastResult:
    safe: bool
    minimum_balance: Decimal
    minimum_date: str
    balances: dict[str, Decimal]
    violations: list[str]


class FinancialForecaster:
    def __init__(self, dataset: Dataset, profile: Profile, request: Request):
        self.dataset = dataset
        self.profile = profile
        self.request = request
        self.request_date = d(request.request_date)
        self.end_date = self.request_date + timedelta(days=90)
        self.known_events = dataset.events_by_user.get(request.user_id, [])
        self.message_rules = _message_rules(dataset, request, profile)
        self.recurring = _recurring_events(dataset, profile, request, self.message_rules)
        self._unknown_events: list[tuple[date, str]] = []
        self._base_events = self._build_scenario_events()

    def _build_scenario_events(self) -> list[tuple[date, str, Decimal, str, Event | None]]:
        output: list[tuple[date, str, Decimal, str, Event | None]] = []
        seen_event_ids: set[str] = set()
        known_occurrences: set[tuple[date, str, str]] = set()
        seen_recurring: set[tuple[str, str, str]] = set()
        for event in self.known_events:
            event_date = _effective_date(event)
            if not event_date:
                continue
            when = d(event_date)
            if when < self.request_date or when > self.end_date:
                continue
            if not _is_cash_event(event) or (event.status == "pending" and event.is_credit):
                continue
            if event.event_id in seen_event_ids:
                continue
            seen_event_ids.add(event.event_id)
            if event.amount is None:
                self._unknown_events.append((when, event.event_id))
                continue
            if not _should_count(event):
                continue
            amount = convert_to_home(
                self.dataset, event.amount, event.currency, self.profile.home_currency, event_date
            )
            if event.category == "salary" and not _is_commission(event) and self.message_rules.get("salary_amount") is not None:
                amount = self.message_rules["salary_amount"]
            if event.category == "rent" and self.message_rules.get("rent_multiplier", Decimal("1")) != Decimal("1") and amount is not None:
                amount *= self.message_rules["rent_multiplier"]
            if amount is None and event.category == "rent" and self.message_rules.get("rent_multiplier", Decimal("1")) != Decimal("1"):
                prior_rent = [
                    candidate for candidate in self.known_events
                    if candidate.category == "rent"
                    and candidate.direction == event.direction
                    and candidate.amount is not None
                    and (candidate.settlement_date or candidate.event_date) < event_date
                ]
                if prior_rent:
                    prior = max(prior_rent, key=lambda candidate: _effective_date(candidate))
                    prior_amount = convert_to_home(
                        self.dataset,
                        prior.amount,
                        prior.currency,
                        self.profile.home_currency,
                        _effective_date(prior),
                    )
                    if prior_amount is not None:
                        amount = prior_amount * self.message_rules["rent_multiplier"]
            if amount is None:
                self._unknown_events.append((when, event.event_id))
                continue
            signed = -amount if event.is_debit else amount
            known_occurrences.add((when, event.category, event.direction))
            output.append((when, event.event_id, signed, "known", event))

        for when, source, amount in self.recurring:
            occurrence = (when, source.category, source.direction)
            if occurrence in known_occurrences:
                continue
            key = (source.event_id, when.isoformat(), str(amount))
            if key in seen_recurring:
                continue
            seen_recurring.add(key)
            signed = -amount if source.is_debit else amount
            output.append((when, source.event_id, signed, "recurring", source))
        return sorted(output, key=lambda item: (item[0], item[1]))

    def _scenario_events(
        self,
        changes: Mapping[str, Optional[Decimal]] | None = None,
    ) -> list[tuple[date, str, Decimal, str, Event | None]]:
        changes = changes or {}
        if not changes:
            return self._base_events
        output: list[tuple[date, str, Decimal, str, Event | None]] = []
        for when, event_id, signed, source, event in self._base_events:
            stream_key = recurring_stream_key(event) if event is not None else ""
            change_key = event_id if event_id in changes else stream_key
            if change_key not in changes:
                output.append((when, event_id, signed, source, event))
                continue
            replacement = changes[change_key]
            if replacement is None:
                continue
            output.append((when, event_id, -replacement if signed < 0 else replacement, source, event))
        return output

    def simulate(
        self,
        payments: Iterable[tuple[str, Decimal]] = (),
        changes: Mapping[str, Optional[Decimal]] | None = None,
    ) -> ForecastResult:
        payments_by_date: dict[date, list[Decimal]] = defaultdict(list)
        for payment_date, amount in payments:
            when = d(payment_date)
            if self.request_date <= when <= self.end_date:
                payments_by_date[when].append(amount)

        events_by_date: dict[date, list[tuple[str, Decimal, Event | None]]] = defaultdict(list)
        for when, event_id, signed, _, event in self._scenario_events(changes):
            events_by_date[when].append((event_id, signed, event))

        balance = self.profile.current_available_balance
        minimum = balance
        minimum_date = self.request_date.isoformat()
        balances: dict[str, Decimal] = {}
        violations: list[str] = [
            f"{when.isoformat()}:unknown_cash_event:{event_id}"
            for when, event_id in self._unknown_events
            if self.request_date <= when <= self.end_date
        ]
        dates = {self.request_date, self.end_date}
        dates.update(events_by_date)
        dates.update(payments_by_date)
        for current in sorted(when for when in dates if self.request_date <= when <= self.end_date):
            for event_id, signed, _ in events_by_date.get(current, []):
                balance += signed
                if balance < self.profile.minimum_balance_to_keep:
                    violations.append(f"{current.isoformat()}:event:{event_id}")
            for index, amount in enumerate(payments_by_date.get(current, []), start=1):
                balance -= amount
                if balance < self.profile.minimum_balance_to_keep:
                    violations.append(f"{current.isoformat()}:payment:{index}")
            if balance < minimum:
                minimum = balance
                minimum_date = current.isoformat()
            balances[current.isoformat()] = balance
        return ForecastResult(
            safe=not violations,
            minimum_balance=minimum,
            minimum_date=minimum_date,
            balances=balances,
            violations=violations,
        )

    def simulate_until(
        self,
        payments: Iterable[tuple[str, Decimal]],
        end_date: str,
        changes: Mapping[str, Optional[Decimal]] | None = None,
    ) -> ForecastResult:
        """Simulate a candidate only through its advertised completion date."""
        original_end = self.end_date
        self.end_date = min(original_end, d(end_date))
        try:
            return self.simulate(payments, changes)
        finally:
            self.end_date = original_end

    def amount_safe_today(
        self,
        requested_amount: Decimal,
        changes: Mapping[str, Optional[Decimal]] | None = None,
    ) -> Decimal:
        """Return the largest request-date payment safe over the full forecast.

        ``amount_safe_to_pay`` is calculated without optional spending changes:
        it describes the amount safe on the request date under the user's
        existing financial position.  Candidate plans may separately test
        permitted spending changes, but those changes must not inflate this
        field.

        Payment safety is monotonic in the payment amount: increasing a
        request-date debit can only lower the balance on that date and on all
        later dates.  We therefore search integer cents with a binary search
        against the same full-horizon simulation used for plan validation.
        """
        del changes  # Optional plan changes must not affect this output field.

        immediate_headroom = max(
            Decimal("0"),
            self.profile.current_available_balance - self.profile.minimum_balance_to_keep,
        )
        upper = min(requested_amount, immediate_headroom)
        upper_cents = int((upper / CENT).to_integral_value(rounding=ROUND_DOWN))
        if upper_cents <= 0:
            return Decimal("0.00")

        def safe_at(cents: int) -> bool:
            amount = Decimal(cents) * CENT
            return self.simulate([(self.request.request_date, amount)]).safe

        low = 0
        high = upper_cents
        while low < high:
            middle = (low + high + 1) // 2
            if safe_at(middle):
                low = middle
            else:
                high = middle - 1
        return (Decimal(low) * CENT).quantize(CENT)

    def earliest_full_payment_date(
        self,
        requested_amount: Decimal,
        changes: Mapping[str, Optional[Decimal]] | None = None,
        horizon: Optional[str] = None,
    ) -> Optional[str]:
        current = self.request_date
        final_date = min(self.end_date, d(horizon)) if horizon else self.end_date
        while current <= final_date:
            # The candidate date may be bounded by the request deadline, but
            # safety must still hold for the complete 90-day forecast. The
            # optional horizon limits only which dates are searched.
            result = self.simulate([(current.isoformat(), requested_amount)], changes)
            if result.safe:
                return current.isoformat()
            current += timedelta(days=1)
        return None
