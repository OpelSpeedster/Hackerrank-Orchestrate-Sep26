from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN
from statistics import median
from typing import Iterable, Optional

from models import CENT, Dataset, Event, Profile, Request, decimal

IGNORED_STATUSES = {"failed", "cancelled", "unrealized"}


def d(value: str) -> date:
    return date.fromisoformat(value)


def convert_to_home(dataset: Dataset, amount: Decimal, currency: str, home: str, settlement_date: str) -> Decimal:
    if currency == home:
        return amount
    rate = dataset.rates.get((settlement_date, currency, home))
    if rate is None:
        candidates = [
            (rate_date, value)
            for (rate_date, from_currency, to_currency), value in dataset.rates.items()
            if from_currency == currency and to_currency == home and rate_date <= settlement_date
        ]
        if candidates:
            rate = sorted(candidates)[-1][1]
    if rate is None or rate == 0:
        return amount
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


def _intervals(values: list[date]) -> list[int]:
    values = sorted(set(values))
    return [(later - earlier).days for earlier, later in zip(values, values[1:])]


def _recurring_events(dataset: Dataset, profile: Profile, request: Request) -> list[tuple[date, Event, Decimal]]:
    """Infer only strong recurring patterns from settled history before the request."""
    grouped: dict[tuple[str, str, str], list[Event]] = defaultdict(list)
    request_date = d(request.request_date)
    for event in dataset.events_by_user.get(request.user_id, []):
        if not event.is_recurring_candidate or event.status != "settled":
            continue
        if event.amount is None or not event.event_date or d(event.event_date) >= request_date:
            continue
        if event.currency != profile.home_currency:
            # Cross-currency recurrence is too easy to misinterpret without a dated rate.
            continue
        grouped[(event.event_type, event.category, event.direction)].append(event)

    generated: list[tuple[date, Event, Decimal]] = []
    for _, history in grouped.items():
        history = sorted(history, key=lambda event: event.event_date)
        if len(history) < 3:
            continue
        dates = [d(event.event_date) for event in history]
        intervals = _intervals(dates)
        if len(intervals) < 2:
            continue
        typical = median(intervals)
        if not (5 <= typical <= 35):
            continue
        tolerance = max(2, int(typical * 0.20))
        if sum(abs(interval - typical) <= tolerance for interval in intervals) < len(intervals) * 0.7:
            continue
        last = history[-1]
        amounts = [event.amount for event in history[-3:] if event.amount is not None]
        if not amounts:
            continue
        if last.is_debit:
            # Conservative for variable essentials; median for fixed subscriptions.
            typical_amount = max(amounts) if last.category in {"groceries", "utilities", "transport"} else median(amounts)
        else:
            typical_amount = median(amounts)
        next_date = d(last.event_date) + timedelta(days=int(typical))
        end = request_date + timedelta(days=90)
        while next_date <= end:
            generated.append((next_date, last, typical_amount))
            next_date += timedelta(days=int(typical))
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
        self.recurring = _recurring_events(dataset, profile, request)
        self._base_events = self._build_scenario_events()

    def _build_scenario_events(self) -> list[tuple[date, str, Decimal, str, Event | None]]:
        output: list[tuple[date, str, Decimal, str, Event | None]] = []
        seen: set[tuple[str, str, str, str]] = set()
        for event in self.known_events:
            event_date = _effective_date(event)
            if not event_date or event.amount is None:
                continue
            when = d(event_date)
            if when < self.request_date or when > self.end_date or not _should_count(event):
                continue
            amount = convert_to_home(
                self.dataset, event.amount, event.currency, self.profile.home_currency, event_date
            )
            signed = -amount if event.is_debit else amount
            key = (event.category, event.direction, event_date, str(amount))
            if key in seen:
                continue
            seen.add(key)
            output.append((when, event.event_id, signed, "known", event))

        for when, source, amount in self.recurring:
            key = (source.category, source.direction, when.isoformat(), str(amount))
            if key in seen:
                continue
            seen.add(key)
            signed = -amount if source.is_debit else amount
            output.append((when, source.event_id, signed, "recurring", source))
        return sorted(output, key=lambda item: (item[0], item[1]))

    def _scenario_events(self, suppressed_categories: set[str] | None = None) -> list[tuple[date, str, Decimal, str, Event | None]]:
        suppressed_categories = suppressed_categories or set()
        if not suppressed_categories:
            return self._base_events
        return [
            item for item in self._base_events
            if not (item[4] is not None and item[4].category in suppressed_categories and item[4].flexibility != "fixed")
        ]

    def simulate(
        self,
        payments: Iterable[tuple[str, Decimal]] = (),
        suppressed_categories: set[str] | None = None,
    ) -> ForecastResult:
        payments_by_date: dict[date, list[Decimal]] = defaultdict(list)
        for payment_date, amount in payments:
            when = d(payment_date)
            if self.request_date <= when <= self.end_date:
                payments_by_date[when].append(amount)

        events_by_date: dict[date, list[tuple[str, Decimal, Event | None]]] = defaultdict(list)
        for when, event_id, signed, _, event in self._scenario_events(suppressed_categories):
            events_by_date[when].append((event_id, signed, event))

        balance = self.profile.current_available_balance
        minimum = balance
        minimum_date = self.request_date.isoformat()
        balances: dict[str, Decimal] = {}
        violations: list[str] = []
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

    def amount_safe_today(self, requested_amount: Decimal, suppressed_categories: set[str] | None = None) -> Decimal:
        baseline = self.simulate((), suppressed_categories)
        upper = min(
            requested_amount,
            max(Decimal("0"), baseline.minimum_balance - self.profile.minimum_balance_to_keep),
        )
        return upper.quantize(CENT, rounding=ROUND_DOWN)

    def earliest_full_payment_date(self, requested_amount: Decimal, suppressed_categories: set[str] | None = None) -> Optional[str]:
        current = self.request_date
        while current <= self.end_date:
            result = self.simulate([(current.isoformat(), requested_amount)], suppressed_categories)
            if result.safe:
                return current.isoformat()
            current += timedelta(days=1)
        return None
