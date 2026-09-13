from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from forecasting import convert_to_home
from loaders import load_dataset
from models import Dataset, Event, Profile

REQUIRED_CSV_FILES = (
    "financial_profiles.csv",
    "financial_events.csv",
    "exchange_rates.csv",
    "requests.csv",
    "sample_requests.csv",
    "request_payment_options.csv",
    "messages.csv",
    "images.csv",
    "output.csv",
)


@dataclass(frozen=True)
class IngestedData:
    dataset: Dataset
    csv_row_counts: dict[str, int]
    image_count: int


def _row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return max(0, sum(1 for _ in csv.DictReader(handle)))


def load_all(dataset_dir: str | Path) -> IngestedData:
    """Load every participant-facing file and keep its inventory observable."""
    root = Path(dataset_dir)
    missing = [name for name in REQUIRED_CSV_FILES if not (root / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing dataset files: {', '.join(missing)}")
    dataset = load_dataset(root)
    image_count = sum(1 for _ in (root / "media" / "images").glob("*.png"))
    return IngestedData(
        dataset=dataset,
        csv_row_counts={name: _row_count(root / name) for name in REQUIRED_CSV_FILES},
        image_count=image_count,
    )


def normalize_event(event: Event, profile: Profile, dataset: Dataset) -> dict:
    """Return a home-currency evidence view without changing the source event."""
    if event.amount is None:
        normalized = None
        conversion_status = "missing_amount"
    elif event.currency == profile.home_currency:
        normalized = event.amount
        conversion_status = "home_currency"
    else:
        settlement_date = event.settlement_date or event.event_date
        rate = dataset.rates.get((settlement_date, event.currency, profile.home_currency))
        if rate is None:
            normalized = None
            conversion_status = "missing_exchange_rate"
        else:
            normalized = event.amount * rate
            conversion_status = "converted"
    return {
        "event_id": event.event_id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "description": event.description,
        "category": event.category,
        "direction": event.direction,
        "amount": str(event.amount) if event.amount is not None else None,
        "currency": event.currency,
        "normalized_amount": str(normalized) if normalized is not None else None,
        "home_currency": profile.home_currency,
        "conversion_status": conversion_status,
        "event_date": event.event_date,
        "settlement_date": event.settlement_date,
        "status": event.status,
        "linked_event_id": event.linked_event_id,
        "flexibility": event.flexibility,
    }
