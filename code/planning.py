from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import combinations
from typing import Optional

from forecasting import FinancialForecaster, convert_to_home, recurring_stream_key
from models import Dataset, Event, PaymentOption, Profile, Request, amount_text


@dataclass(frozen=True)
class SpendingChange:
    event_id: str
    action: str
    category: str
    new_amount: Optional[Decimal] = None
    stream_key: str = ""

    @property
    def output(self) -> str:
        if self.action == "stop":
            return f"stop:{self.event_id}"
        return f"reduce_to:{self.event_id}:{amount_text(self.new_amount or Decimal('0'))}"


@dataclass
class Candidate:
    method: str
    status: str
    payments: list[tuple[str, Decimal]]
    earliest_full: Optional[str]
    changes: list[SpendingChange]
    total_cost: Decimal
    option_id: str = ""
    explanation: str = ""

    @property
    def first_date(self) -> str:
        return self.payments[0][0] if self.payments else "9999-12-31"

    @property
    def completes_by_deadline(self) -> bool:
        return bool(self.payments) and self.payments[-1][0] <= self._deadline

    _deadline: str = "9999-12-31"


def _accepted(profile: Profile, method: str) -> bool:
    return method in profile.accepted_methods


def _months(option: PaymentOption) -> float:
    if option.number_of_payments <= 1 or not option.payment_frequency_days:
        return 0.0
    return ((option.number_of_payments - 1) * option.payment_frequency_days) / 30.4375


def _changes(dataset: Dataset, profile: Profile, request: Request) -> list[SpendingChange]:
    """Build actions from the latest eligible event in every recurring stream."""
    request_date = date.fromisoformat(request.request_date)
    latest_by_stream: dict[str, Event] = {}
    for event in dataset.events_by_user.get(request.user_id, []):
        event_date = event.settlement_date or event.event_date
        if not event_date or date.fromisoformat(event_date) >= request_date:
            continue
        if event.status != "settled" or event.amount is None:
            continue
        if not event.is_recurring_candidate or event.category in profile.protected_categories:
            continue
        stream_key = recurring_stream_key(event)
        current = latest_by_stream.get(stream_key)
        if current is None or date.fromisoformat(event_date) > date.fromisoformat(current.settlement_date or current.event_date):
            latest_by_stream[stream_key] = event

    candidates: list[SpendingChange] = []
    for stream_key, event in sorted(
        latest_by_stream.items(),
        key=lambda item: (item[1].settlement_date or item[1].event_date, item[0]),
        reverse=True,
    ):
        event_date = event.settlement_date or event.event_date
        flexible = event.flexibility
        if flexible in {"stoppable", "reducible_or_stoppable"} and event.category in profile.stop_categories:
            candidates.append(
                SpendingChange(event.event_id, "stop", event.category, stream_key=stream_key)
            )
        if flexible in {"reducible", "reducible_or_stoppable"} and event.category in profile.reduce_categories:
            if event.minimum_allowed_amount is None or event.minimum_allowed_amount >= event.amount:
                continue
            new_amount = convert_to_home(
                dataset,
                event.minimum_allowed_amount,
                event.currency,
                profile.home_currency,
                event_date,
            )
            if new_amount is not None:
                candidates.append(
                    SpendingChange(
                        event.event_id,
                        "reduce",
                        event.category,
                        new_amount,
                        stream_key,
                    )
                )
    return candidates


def _candidate_changes(changes: list[SpendingChange]) -> list[list[SpendingChange]]:
    output: list[list[SpendingChange]] = [[]]
    for size in (1, 2, 3):
        for combination in combinations(changes, size):
            stream_keys = [change.stream_key or change.event_id for change in combination]
            if len(set(stream_keys)) == len(stream_keys):
                output.append(list(combination))
    return output


def _change_map(changes: list[SpendingChange]) -> dict[str, Optional[Decimal]]:
    output: dict[str, Optional[Decimal]] = {}
    for change in changes:
        replacement = None if change.action == "stop" else change.new_amount
        output[change.event_id] = replacement
        if change.stream_key:
            output[change.stream_key] = replacement
    return output


def _candidate_key(candidate: Candidate) -> tuple:
    return (
        not candidate.completes_by_deadline,
        len(candidate.changes),
        candidate.total_cost,
        candidate.first_date,
        len(candidate.payments),
        candidate.option_id,
    )


def _full_candidate(
    forecaster: FinancialForecaster,
    request: Request,
    changes: list[SpendingChange],
    baseline_earliest: Optional[str],
) -> Optional[Candidate]:
    if not _accepted(forecaster.profile, "full_payment"):
        return None
    change_map = _change_map(changes)
    result = forecaster.simulate(
        [(request.request_date, request.requested_amount)],
        change_map,
    )
    if not result.safe:
        return None
    return Candidate(
        method="full_payment",
        status="affordable_now" if not changes else "affordable_with_plan",
        payments=[(request.request_date, request.requested_amount)],
        earliest_full=request.request_date if not changes else baseline_earliest,
        changes=changes,
        total_cost=request.requested_amount,
        explanation="The full payment passes the 90-day minimum-balance safety check.",
        _deadline=request.desired_completion_date,
    )


def _partial_candidate(
    forecaster: FinancialForecaster,
    request: Request,
    safe_today: Decimal,
    changes: list[SpendingChange],
) -> Optional[Candidate]:
    if not request.allows_partial_payment or not _accepted(forecaster.profile, "partial_payment"):
        return None
    if safe_today <= 0 or safe_today >= request.requested_amount:
        return None
    change_map = _change_map(changes)
    earliest = forecaster.earliest_full_payment_date(
        request.requested_amount,
        change_map,
        request.desired_completion_date,
    )
    if earliest is None or earliest > request.desired_completion_date:
        return None
    remainder = request.requested_amount - safe_today
    payments = [(request.request_date, safe_today), (earliest, remainder)]
    if not forecaster.simulate(payments, change_map).safe:
        return None
    return Candidate(
        method="partial_payment",
        status="affordable_with_plan",
        payments=payments,
        earliest_full=earliest,
        changes=changes,
        total_cost=request.requested_amount,
        explanation="Pay the safe amount today and the remaining balance on the earliest safe date.",
        _deadline=request.desired_completion_date,
    )


def _installment_candidates(
    forecaster: FinancialForecaster,
    profile: Profile,
    request: Request,
    options: list[PaymentOption],
    changes: list[SpendingChange],
) -> list[Candidate]:
    if not _accepted(profile, "installments"):
        return []
    output: list[Candidate] = []
    for option in options:
        if option.payment_method != "installments":
            continue
        if profile.max_installment_months is None or _months(option) > profile.max_installment_months:
            continue
        schedule = option.schedule()
        if not schedule or schedule[0][0] < request.request_date or schedule[-1][0] > request.desired_completion_date:
            continue
        change_map = _change_map(changes)
        if not forecaster.simulate(schedule, change_map).safe:
            continue
        output.append(
            Candidate(
                method="installments",
                status="affordable_with_plan",
                payments=schedule,
                earliest_full=forecaster.earliest_full_payment_date(
                    request.requested_amount,
                    change_map,
                ),
                changes=changes,
                total_cost=option.total_payable_amount,
                option_id=option.payment_option_id,
                explanation=f"Use supplied installment option {option.payment_option_id}; every payment stays above the minimum balance.",
                _deadline=request.desired_completion_date,
            )
        )
    return output


def _wait_candidate(
    forecaster: FinancialForecaster,
    profile: Profile,
    request: Request,
    changes: list[SpendingChange],
    baseline_earliest: Optional[str],
) -> Optional[Candidate]:
    if not _accepted(profile, "full_payment"):
        return None
    change_map = _change_map(changes)
    earliest = forecaster.earliest_full_payment_date(
        request.requested_amount,
        change_map,
        request.desired_completion_date,
    )
    if earliest is None or earliest > request.desired_completion_date:
        return None
    payments = [(earliest, request.requested_amount)]
    if not forecaster.simulate(payments, change_map).safe:
        return None
    return Candidate(
        method="wait",
        status="affordable_later",
        payments=payments,
        earliest_full=earliest,
        changes=changes,
        total_cost=request.requested_amount,
        explanation=f"Wait until {earliest}, when the full payment passes the safety check.",
        _deadline=request.desired_completion_date,
    )


def plan_request(dataset: Dataset, request: Request) -> tuple[dict, dict]:
    profile = dataset.profiles[request.user_id]
    forecaster = FinancialForecaster(dataset, profile, request)
    safe_today = forecaster.amount_safe_today(request.requested_amount)
    baseline_earliest = forecaster.earliest_full_payment_date(request.requested_amount)
    available_changes = _changes(dataset, profile, request)

    candidates: list[Candidate] = []
    for changes in _candidate_changes(available_changes):
        full = _full_candidate(forecaster, request, changes, baseline_earliest)
        if full:
            candidates.append(full)
        partial = _partial_candidate(forecaster, request, safe_today, changes)
        if partial:
            candidates.append(partial)
        candidates.extend(
            _installment_candidates(
                forecaster,
                profile,
                request,
                dataset.options_by_request.get(request.request_id, []),
                changes,
            )
        )
        waiting = _wait_candidate(forecaster, profile, request, changes, baseline_earliest)
        if waiting:
            candidates.append(waiting)

    if candidates:
        best = sorted(candidates, key=_candidate_key)[0]
    else:
        status = "affordable_later" if baseline_earliest else "not_affordable"
        best = Candidate(
            method="not_recommended",
            status=status,
            payments=[],
            earliest_full=baseline_earliest,
            changes=[],
            total_cost=Decimal("0"),
            explanation="No user-approved payment plan passes the 90-day safety check.",
            _deadline=request.desired_completion_date,
        )

    return {
        "request_id": request.request_id,
        "amount_safe_to_pay": amount_text(safe_today),
        "affordability_status": best.status,
        "recommended_payment_method": best.method,
        "payment_plan": "|".join(f"{date_value}:{amount_text(amount)}" for date_value, amount in best.payments) or "none",
        "earliest_date_for_full_payment": best.earliest_full or "",
        "spending_changes_needed": "|".join(change.output for change in best.changes) or "none",
        "decision_explanation": best.explanation,
    }, {
        "safe_today": safe_today,
        "earliest_full": baseline_earliest,
        "profile": profile,
        "forecaster": forecaster,
        "candidate": best,
    }
