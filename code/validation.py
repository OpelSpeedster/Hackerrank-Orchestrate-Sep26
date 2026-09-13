from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from models import Dataset, Request, amount_text, decimal

OUTPUT_COLUMNS = [
    "request_id",
    "amount_safe_to_pay",
    "affordability_status",
    "recommended_payment_method",
    "payment_plan",
    "earliest_date_for_full_payment",
    "spending_changes_needed",
    "decision_explanation",
]

STATUSES = {"affordable_now", "affordable_with_plan", "affordable_later", "not_affordable"}
METHODS = {"full_payment", "partial_payment", "installments", "wait", "not_recommended"}


def parse_plan(value: str) -> list[tuple[str, Decimal]]:
    if not value or value == "none":
        return []
    result = []
    for item in value.split("|"):
        date_value, amount_value = item.split(":", 1)
        date.fromisoformat(date_value)
        result.append((date_value, decimal(amount_value)))
    return result


def validate_row(dataset: Dataset, request: Request, row: dict[str, str]) -> list[str]:
    errors: list[str] = []
    profile = dataset.profiles.get(request.user_id)
    if profile is None:
        return ["missing_profile"]
    if row.get("request_id") != request.request_id:
        errors.append("request_id_mismatch")
    try:
        safe = decimal(row.get("amount_safe_to_pay"))
        if safe is None or safe < 0 or safe > request.requested_amount:
            errors.append("amount_safe_to_pay_out_of_bounds")
    except Exception:
        errors.append("invalid_amount_safe_to_pay")
        safe = Decimal("0")
    if row.get("affordability_status") not in STATUSES:
        errors.append("invalid_affordability_status")
    method = row.get("recommended_payment_method")
    if method not in METHODS:
        errors.append("invalid_payment_method")
    try:
        plan = parse_plan(row.get("payment_plan", "none"))
    except Exception:
        errors.append("invalid_payment_plan_format")
        plan = []
    if any(plan[index][0] > plan[index + 1][0] for index in range(len(plan) - 1)):
        errors.append("payment_plan_not_chronological")
    earliest = row.get("earliest_date_for_full_payment", "")
    if earliest:
        try:
            date.fromisoformat(earliest)
        except ValueError:
            errors.append("invalid_earliest_date")
    if row.get("affordability_status") == "affordable_now" and earliest != request.request_date:
        errors.append("affordable_now_requires_request_date")

    if method == "full_payment":
        if not plan or len(plan) != 1 or plan[0] != (request.request_date, request.requested_amount):
            errors.append("invalid_full_payment_plan")
    elif method == "partial_payment":
        if len(plan) != 2:
            errors.append("partial_payment_requires_two_payments")
        else:
            if plan[0][0] != request.request_date or plan[0][1] != safe:
                errors.append("partial_payment_first_payment_mismatch")
            if plan[0][1] + plan[1][1] != request.requested_amount:
                errors.append("partial_payment_sum_mismatch")
            if not request.allows_partial_payment:
                errors.append("partial_payment_not_allowed")
    elif method == "installments":
        matching = False
        for option in dataset.options_by_request.get(request.request_id, []):
            if option.payment_method != "installments":
                continue
            if option.schedule() == plan:
                matching = True
                break
        if not matching:
            errors.append("installment_plan_not_supplied")
    elif method == "wait":
        if not plan or plan[-1][1] != request.requested_amount:
            errors.append("wait_plan_must_pay_full_amount")
    elif method == "not_recommended" and plan:
        errors.append("not_recommended_must_have_no_plan")

    if method in {"full_payment", "partial_payment", "installments"} and method not in profile.accepted_methods:
        errors.append("method_not_accepted_by_profile")
    if method == "wait" and "full_payment" not in profile.accepted_methods:
        errors.append("wait_requires_full_payment_preference")

    event_by_id = {event.event_id: event for event in dataset.events_by_user.get(request.user_id, [])}
    changes = row.get("spending_changes_needed", "none")
    if changes != "none":
        seen: set[str] = set()
        actions = changes.split("|")
        if len(actions) > 3:
            errors.append("too_many_spending_changes")
        for action in actions:
            parts = action.split(":")
            event_id = parts[1] if len(parts) > 1 else ""
            if event_id in seen:
                errors.append("duplicate_spending_change")
            seen.add(event_id)
            event = event_by_id.get(event_id)
            if event is None:
                errors.append("spending_change_event_not_found")
                continue
            if event.flexibility == "fixed" or event.status != "settled":
                errors.append("spending_change_not_flexible_settled_event")
            if event.category in profile.protected_categories:
                errors.append("spending_change_targets_protected_category")
            if parts[0] == "stop":
                if event.category not in profile.stop_categories or "stoppable" not in event.flexibility and event.flexibility != "reducible_or_stoppable":
                    errors.append("invalid_stop_category_or_flexibility")
            elif parts[0] == "reduce_to":
                if len(parts) != 3 or event.category not in profile.reduce_categories or "reducible" not in event.flexibility and event.flexibility != "reducible_or_stoppable":
                    errors.append("invalid_reduce_category_or_flexibility")
                else:
                    new_amount = decimal(parts[2])
                    if new_amount is None or new_amount < 0 or new_amount > event.amount:
                        errors.append("invalid_reduce_amount")
            else:
                errors.append("invalid_spending_change_action")
    return errors


def write_output(path: str | Path, rows: Iterable[dict[str, str]]) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in OUTPUT_COLUMNS})
