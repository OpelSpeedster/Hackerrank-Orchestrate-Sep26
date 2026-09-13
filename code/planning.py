from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from forecasting import FinancialForecaster
from models import Dataset, PaymentOption, Profile, Request, amount_text


@dataclass(frozen=True)
class SpendingChange:
    event_id: str
    action: str
    category: str
    new_amount: Optional[Decimal] = None

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
    candidates: list[SpendingChange] = []
    seen_categories: set[str] = set()
    for event in reversed(dataset.events_by_user.get(request.user_id, [])):
        if event.event_date >= request.request_date or event.status != "settled" or event.amount is None:
            continue
        if event.category in seen_categories or event.category in profile.protected_categories:
            continue
        if event.flexibility in {"stoppable", "reducible_or_stoppable"} and event.category in profile.stop_categories:
            candidates.append(SpendingChange(event.event_id, "stop", event.category))
            seen_categories.add(event.category)
        elif event.flexibility in {"reducible", "reducible_or_stoppable"} and event.category in profile.reduce_categories:
            if event.minimum_allowed_amount is not None and event.minimum_allowed_amount < event.amount:
                candidates.append(
                    SpendingChange(
                        event.event_id,
                        "reduce",
                        event.category,
                        event.minimum_allowed_amount,
                    )
                )
                seen_categories.add(event.category)
        if len(candidates) >= 3:
            break
    return candidates


def _candidate_changes(changes: list[SpendingChange], limit: int = 3) -> list[list[SpendingChange]]:
    output: list[list[SpendingChange]] = [[]]
    for change in changes[:limit]:
        output.append([change])
    # A compact pair search covers the common cases without combinatorial growth.
    for index, first in enumerate(changes[:limit]):
        for second in changes[index + 1 : limit]:
            output.append([first, second])
    return output


def _suppressed(changes: list[SpendingChange]) -> set[str]:
    return {change.category for change in changes}


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
) -> Optional[Candidate]:
    if not _accepted(forecaster.profile, "full_payment"):
        return None
    result = forecaster.simulate([(request.request_date, request.requested_amount)], _suppressed(changes))
    if not result.safe:
        return None
    return Candidate(
        method="full_payment",
        status="affordable_now",
        payments=[(request.request_date, request.requested_amount)],
        earliest_full=request.request_date,
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
    earliest = forecaster.earliest_full_payment_date(request.requested_amount, _suppressed(changes))
    if earliest is None or earliest > request.desired_completion_date:
        return None
    remainder = request.requested_amount - safe_today
    payments = [(request.request_date, safe_today), (earliest, remainder)]
    if not forecaster.simulate(payments, _suppressed(changes)).safe:
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
        if not forecaster.simulate(schedule, _suppressed(changes)).safe:
            continue
        output.append(
            Candidate(
                method="installments",
                status="affordable_with_plan",
                payments=schedule,
                earliest_full=forecaster.earliest_full_payment_date(request.requested_amount),
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
    if not _accepted(profile, "full_payment") or baseline_earliest is None:
        return None
    if baseline_earliest > request.desired_completion_date:
        return None
    payments = [(baseline_earliest, request.requested_amount)]
    if not forecaster.simulate(payments, _suppressed(changes)).safe:
        return None
    return Candidate(
        method="wait",
        status="affordable_later",
        payments=payments,
        earliest_full=baseline_earliest,
        changes=changes,
        total_cost=request.requested_amount,
        explanation=f"Wait until {baseline_earliest}, when the full payment passes the safety check.",
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
        full = _full_candidate(forecaster, request, changes)
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
