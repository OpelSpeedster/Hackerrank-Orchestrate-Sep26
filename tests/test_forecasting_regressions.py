from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from forecasting import FinancialForecaster
from models import Dataset, Event, Message, Profile, Request
from planning import _candidate_changes, _change_map, _changes, plan_request


HOME = "USD"


def profile(balance: str = "1000", minimum: str = "100") -> Profile:
    return Profile(
        user_id="user",
        home_currency=HOME,
        current_available_balance=Decimal(balance),
        minimum_balance_to_keep=Decimal(minimum),
        financial_priorities=frozenset(),
        protected_categories=frozenset(),
        reduce_categories=frozenset({"shopping"}),
        stop_categories=frozenset({"streaming"}),
        accepted_methods=frozenset({"full_payment", "partial_payment", "installments"}),
        max_installment_months=24,
    )


def request(request_date: str = "2026-01-01") -> Request:
    return Request(
        request_id="request",
        user_id="user",
        request_date=request_date,
        request_type="purchase",
        requested_amount=Decimal("100"),
        desired_completion_date="2026-02-01",
        allows_partial_payment=True,
        request_text="test",
    )


def event(
    event_id: str,
    *,
    amount: str | None,
    event_date: str = "2026-01-02",
    settlement_date: str = "2026-01-02",
    status: str = "settled",
    direction: str = "debit",
    currency: str = HOME,
    category: str = "shopping",
    flexibility: str = "fixed",
    event_type: str = "expense",
) -> Event:
    return Event(
        event_id=event_id,
        user_id="user",
        event_type=event_type,
        description=event_id,
        category=category,
        direction=direction,
        amount=Decimal(amount) if amount is not None else None,
        currency=currency,
        event_date=event_date,
        settlement_date=settlement_date,
        status=status,
        linked_event_id="",
        flexibility=flexibility,
        minimum_allowed_amount=Decimal("10") if flexibility != "fixed" else None,
    )


def dataset(events: list[Event], rates: dict[tuple[str, str, str], Decimal] | None = None) -> Dataset:
    return Dataset(
        profiles={"user": profile()},
        events_by_user={"user": events},
        requests=[request()],
        options_by_request={},
        messages_by_user={},
        messages_by_request={},
        messages_by_event={},
        images_by_event={},
        images_by_request={},
        rates=rates or {},
    )


class ForecastingRegressionTests(unittest.TestCase):
    def test_same_day_same_amount_events_are_not_deduplicated(self) -> None:
        events = [
            event("debit_a", amount="300"),
            event("debit_b", amount="300"),
        ]
        result = FinancialForecaster(dataset(events), profile(), request()).simulate()
        self.assertEqual(result.balances["2026-01-02"], Decimal("400"))

    def test_cash_states_follow_problem_rules(self) -> None:
        events = [
            event("pending_debit", amount="200", status="pending"),
            event("pending_credit", amount="500", status="pending", direction="credit"),
            event("cancelled", amount="400", status="cancelled"),
            event("unrealized", amount="700", status="unrealized", direction="credit"),
            event("scheduled_salary", amount="300", status="scheduled", direction="credit", category="salary", event_type="income"),
        ]
        result = FinancialForecaster(dataset(events), profile(), request()).simulate()
        self.assertEqual(result.balances["2026-01-02"], Decimal("1100"))
        self.assertTrue(result.safe)

    def test_missing_dated_rate_is_conservative(self) -> None:
        events = [event("foreign_debit", amount="10", currency="EUR")]
        forecaster = FinancialForecaster(dataset(events), profile(), request())
        result = forecaster.simulate()
        self.assertFalse(result.safe)
        self.assertEqual(forecaster.amount_safe_today(Decimal("100")), Decimal("0.00"))
        self.assertTrue(any("unknown_cash_event:foreign_debit" in item for item in result.violations))

    def test_amount_safe_today_accounts_for_future_obligations(self) -> None:
        future_expense = event(
            "future_expense",
            amount="850",
            event_date="2026-01-02",
            settlement_date="2026-01-02",
            category="one_time",
            flexibility="fixed",
        )
        forecaster = FinancialForecaster(dataset([future_expense]), profile(), request())
        self.assertEqual(forecaster.amount_safe_today(Decimal("100")), Decimal("50.00"))

    def test_amount_safe_today_ignores_optional_spending_changes(self) -> None:
        future_expense = event(
            "future_expense",
            amount="850",
            event_date="2026-01-02",
            settlement_date="2026-01-02",
            category="one_time",
            flexibility="reducible",
        )
        forecaster = FinancialForecaster(dataset([future_expense]), profile(), request())
        self.assertEqual(
            forecaster.amount_safe_today(Decimal("100"), {"future_expense": None}),
            Decimal("50.00"),
        )

    def test_recurrence_uses_settlement_dates(self) -> None:
        events = [
            event("subscription_1", amount="50", event_date="2025-11-01", settlement_date="2025-11-05", category="streaming", flexibility="stoppable", event_type="subscription"),
            event("subscription_2", amount="50", event_date="2025-12-01", settlement_date="2025-12-05", category="streaming", flexibility="stoppable", event_type="subscription"),
            event("subscription_3", amount="50", event_date="2026-01-01", settlement_date="2026-01-05", category="streaming", flexibility="stoppable", event_type="subscription"),
        ]
        for item in events:
            item.description = "Streaming plan"
        sample_dataset = dataset(events)
        sample_request = request("2026-01-10")
        sample_dataset.requests = [sample_request]
        forecaster = FinancialForecaster(sample_dataset, profile(), sample_request)
        recurring_dates = [when.isoformat() for when, source, amount in forecaster.recurring]
        self.assertIn("2026-02-05", recurring_dates)
        self.assertNotIn("2026-02-04", recurring_dates)
        self.assertNotIn("2026-01-31", recurring_dates)

    def test_monthly_recurrence_handles_month_end_without_drift(self) -> None:
        events = [
            event("subscription_1", amount="50", event_date="2025-11-30", settlement_date="2025-11-30", category="streaming", flexibility="stoppable", event_type="subscription"),
            event("subscription_2", amount="50", event_date="2025-12-31", settlement_date="2025-12-31", category="streaming", flexibility="stoppable", event_type="subscription"),
            event("subscription_3", amount="50", event_date="2026-01-31", settlement_date="2026-01-31", category="streaming", flexibility="stoppable", event_type="subscription"),
        ]
        for item in events:
            item.description = "Month-end streaming plan"
        sample_dataset = dataset(events)
        sample_request = request("2026-02-01")
        sample_dataset.requests = [sample_request]
        forecaster = FinancialForecaster(sample_dataset, profile(), sample_request)
        recurring_dates = [when.isoformat() for when, source, amount in forecaster.recurring]
        self.assertEqual(recurring_dates, ["2026-02-28", "2026-03-31", "2026-04-30"])

    def test_non_monthly_recurrence_keeps_interval_generation(self) -> None:
        events = [
            event("expense_1", amount="50", event_date="2025-12-01", settlement_date="2025-12-01", category="shopping"),
            event("expense_2", amount="50", event_date="2025-12-15", settlement_date="2025-12-15", category="shopping"),
            event("expense_3", amount="50", event_date="2025-12-29", settlement_date="2025-12-29", category="shopping"),
        ]
        sample_dataset = dataset(events)
        sample_request = request("2026-01-01")
        sample_dataset.requests = [sample_request]
        forecaster = FinancialForecaster(sample_dataset, profile(), sample_request)
        recurring_dates = [when.isoformat() for when, source, amount in forecaster.recurring]
        self.assertEqual(
            recurring_dates,
            [
                "2026-01-12",
                "2026-01-26",
                "2026-02-09",
                "2026-02-23",
                "2026-03-09",
                "2026-03-23",
            ],
        )

    def test_message_salary_amendment_updates_recurring_income(self) -> None:
        events = [
            event("salary_1", amount="100", event_date="2025-10-15", settlement_date="2025-10-15", direction="credit", category="salary", event_type="income"),
            event("salary_2", amount="100", event_date="2025-11-15", settlement_date="2025-11-15", direction="credit", category="salary", event_type="income"),
            event("salary_3", amount="100", event_date="2025-12-15", settlement_date="2025-12-15", direction="credit", category="salary", event_type="income"),
        ]
        for item in events:
            item.description = "Payroll credit"
        sample_dataset = dataset(events)
        sample_dataset.messages_by_user = {
            "user": [Message("message", "user", "", "", "2025-12-28T09:30:00Z", "employer", "Your next salary is USD 250.00.")]
        }
        sample_request = request("2026-01-01")
        sample_dataset.requests = [sample_request]
        forecaster = FinancialForecaster(sample_dataset, profile(), sample_request)
        self.assertTrue(forecaster.recurring)
        self.assertEqual(forecaster.recurring[0][2], Decimal("250"))

    def test_unapproved_commission_is_not_forecast(self) -> None:
        events = [
            event("salary_1", amount="100", event_date="2025-10-15", settlement_date="2025-10-15", direction="credit", category="salary", event_type="income",),
            event("salary_2", amount="100", event_date="2025-11-15", settlement_date="2025-11-15", direction="credit", category="salary", event_type="income",),
            event("salary_3", amount="100", event_date="2025-12-15", settlement_date="2025-12-15", direction="credit", category="salary", event_type="income",),
            event("commission_1", amount="500", event_date="2025-10-20", settlement_date="2025-10-20", direction="credit", category="salary", event_type="income"),
            event("commission_2", amount="500", event_date="2025-11-20", settlement_date="2025-11-20", direction="credit", category="salary", event_type="income"),
            event("commission_3", amount="500", event_date="2025-12-20", settlement_date="2025-12-20", direction="credit", category="salary", event_type="income"),
        ]
        for item in events[:3]:
            item.description = "Base salary"
        for item in events[3:]:
            item.description = "Performance commission"
        sample_dataset = dataset(events)
        sample_dataset.messages_by_user = {
            "user": [Message("message", "user", "", "", "2025-12-28T09:30:00Z", "employer", "Commission is not approved and is not payable.")]
        }
        sample_request = request("2026-01-01")
        sample_dataset.requests = [sample_request]
        forecaster = FinancialForecaster(sample_dataset, profile(), sample_request)
        self.assertTrue(all(source.description != "Performance commission" for _, source, _ in forecaster.recurring))

    def test_spending_change_targets_one_event_not_category(self) -> None:
        events = [
            event("shopping_a", amount="200", category="shopping", flexibility="reducible"),
            event("shopping_b", amount="200", category="shopping", flexibility="reducible"),
        ]
        forecaster = FinancialForecaster(dataset(events), profile(), request())
        result = forecaster.simulate(changes={"shopping_a": None})
        self.assertEqual(result.balances["2026-01-02"], Decimal("800"))

    def test_spending_changes_include_all_eligible_streams(self) -> None:
        events = []
        categories = {f"shopping_{index}" for index in range(9)}
        for index in range(9):
            item = event(
                f"shopping_{index}",
                amount="20",
                event_date=f"2025-12-{index + 1:02d}",
                settlement_date=f"2025-12-{index + 1:02d}",
                category=f"shopping_{index}",
                flexibility="reducible",
            )
            events.append(item)
        sample_dataset = dataset(events)
        sample_dataset.profiles["user"] = replace(
            sample_dataset.profiles["user"],
            reduce_categories=frozenset(categories),
        )
        sample_request = request("2026-01-01")
        sample_dataset.requests = [sample_request]
        changes = _changes(sample_dataset, sample_dataset.profiles["user"], sample_request)
        self.assertEqual(len(changes), 9)
        self.assertEqual({change.event_id for change in changes}, {f"shopping_{i}" for i in range(9)})

    def test_spending_changes_support_stop_and_reduce_without_conflicting_combinations(self) -> None:
        item = event(
            "flexible_shopping",
            amount="20",
            event_date="2025-12-02",
            settlement_date="2025-12-02",
            category="shopping",
            flexibility="reducible_or_stoppable",
        )
        sample_dataset = dataset([item])
        sample_dataset.profiles["user"] = Profile(
            user_id="user",
            home_currency=HOME,
            current_available_balance=Decimal("1000"),
            minimum_balance_to_keep=Decimal("100"),
            financial_priorities=frozenset(),
            protected_categories=frozenset(),
            reduce_categories=frozenset({"shopping"}),
            stop_categories=frozenset({"shopping"}),
            accepted_methods=frozenset({"full_payment", "partial_payment", "installments"}),
            max_installment_months=24,
        )
        sample_request = request()
        sample_dataset.requests = [sample_request]
        changes = _changes(sample_dataset, sample_dataset.profiles["user"], sample_request)
        self.assertEqual({change.action for change in changes}, {"stop", "reduce"})
        combinations = _candidate_changes(changes)
        self.assertTrue(all(len({change.stream_key for change in item}) == len(item) for item in combinations))
        self.assertFalse(any(len(item) == 2 for item in combinations))

    def test_spending_change_applies_to_matching_future_stream_only(self) -> None:
        history = []
        for index, day in enumerate(("2025-10-05", "2025-11-05", "2025-12-05"), start=1):
            item = event(
                f"streaming_{index}",
                amount="20",
                event_date=day,
                settlement_date=day,
                category="streaming",
                flexibility="stoppable",
                event_type="subscription",
            )
            item.description = "Streaming plan"
            history.append(item)
        matching_future = event(
            "matching_future",
            amount="20",
            event_date="2026-01-05",
            settlement_date="2026-01-05",
            category="streaming",
            flexibility="stoppable",
            event_type="subscription",
        )
        matching_future.description = "Streaming plan"
        unrelated_future = event(
            "unrelated_future",
            amount="30",
            event_date="2026-01-06",
            settlement_date="2026-01-06",
            category="streaming",
            flexibility="fixed",
            event_type="subscription",
        )
        unrelated_future.description = "Different streaming plan"
        sample_dataset = dataset(history + [matching_future, unrelated_future])
        sample_request = request("2026-01-01")
        sample_dataset.requests = [sample_request]
        changes = _changes(sample_dataset, sample_dataset.profiles["user"], sample_request)
        self.assertEqual(len(changes), 1)
        change_map = _change_map(changes)
        forecaster = FinancialForecaster(sample_dataset, sample_dataset.profiles["user"], sample_request)
        scenario = forecaster._scenario_events(change_map)
        scenario_by_id = {event_id: signed for _, event_id, signed, _, _ in scenario}
        self.assertNotIn("matching_future", scenario_by_id)
        self.assertEqual(scenario_by_id["unrelated_future"], Decimal("-30"))

    def test_plan_must_remain_safe_after_completion_deadline(self) -> None:
        future_expense = event(
            "future_expense",
            amount="950",
            event_date="2026-01-20",
            settlement_date="2026-01-20",
            category="one_time",
            flexibility="fixed",
        )
        sample_dataset = dataset([future_expense])
        sample_request = request("2026-01-01")
        sample_dataset.requests = [sample_request]
        row, _ = plan_request(sample_dataset, sample_request)
        self.assertNotEqual(row["recommended_payment_method"], "full_payment")
        self.assertNotEqual(row["affordability_status"], "affordable_now")


if __name__ == "__main__":
    unittest.main()
