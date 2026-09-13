from __future__ import annotations

import csv
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
ROOT = CODE_DIR.parent
sys.path.insert(0, str(CODE_DIR))

from loaders import load_dataset  # noqa: E402
from validation import OUTPUT_COLUMNS, validate_row  # noqa: E402


def main() -> int:
    output_path = ROOT / "output.csv"
    if not output_path.exists():
        print("output.csv is missing; run python3 code/main.py first.")
        return 1
    dataset = load_dataset(ROOT / "dataset")
    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(dataset.requests):
        print(f"row count mismatch: {len(rows)} != {len(dataset.requests)}")
        return 1
    if not rows or list(rows[0]) != OUTPUT_COLUMNS:
        print("header mismatch")
        return 1
    errors = {}
    for request, row in zip(dataset.requests, rows):
        row_errors = validate_row(dataset, request, row)
        if row_errors:
            errors[request.request_id] = row_errors
    if errors:
        print(f"invalid rows: {len(errors)}")
        for request_id, row_errors in list(errors.items())[:10]:
            print(request_id, row_errors)
        return 1
    print(f"Validated {len(rows)} output rows successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
from __future__ import annotations

import csv
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
ROOT = CODE_DIR.parent
sys.path.insert(0, str(CODE_DIR))

from loaders import load_dataset  # noqa: E402
from validation import OUTPUT_COLUMNS, validate_row  # noqa: E402


def main() -> int:
    output_path = ROOT / "output.csv"
    if not output_path.exists():
        print("output.csv is missing; run python3 code/main.py first.")
        return 1
    dataset = load_dataset(ROOT / "dataset")
    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(dataset.requests):
        print(f"row count mismatch: {len(rows)} != {len(dataset.requests)}")
        return 1
    if not rows or list(rows[0]) != OUTPUT_COLUMNS:
        print("header mismatch")
        return 1
    errors = {}
    for request, row in zip(dataset.requests, rows):
        row_errors = validate_row(dataset, request, row)
        if row_errors:
            errors[request.request_id] = row_errors
    if errors:
        print(f"invalid rows: {len(errors)}")
        for request_id, row_errors in list(errors.items())[:10]:
            print(request_id, row_errors)
        return 1
    print(f"Validated {len(rows)} output rows successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
from __future__ import annotations

import csv
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
ROOT = CODE_DIR.parent
sys.path.insert(0, str(CODE_DIR))

from loaders import load_dataset  # noqa: E402
from validation import OUTPUT_COLUMNS, validate_row  # noqa: E402


def main() -> int:
    output_path = ROOT / "output.csv"
    if not output_path.exists():
        print("output.csv is missing; run python3 code/main.py first.")
        return 1
    dataset = load_dataset(ROOT / "dataset")
    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(dataset.requests):
        print(f"row count mismatch: {len(rows)} != {len(dataset.requests)}")
        return 1
    if not rows or list(rows[0]) != OUTPUT_COLUMNS:
        print("header mismatch")
        return 1
    errors = {}
    for request, row in zip(dataset.requests, rows):
        row_errors = validate_row(dataset, request, row)
        if row_errors:
            errors[request.request_id] = row_errors
    if errors:
        print(f"invalid rows: {len(errors)}")
        for request_id, row_errors in list(errors.items())[:10]:
            print(request_id, row_errors)
        return 1
    print(f"Validated {len(rows)} output rows successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
from __future__ import annotations

import csv
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
ROOT = CODE_DIR.parent
sys.path.insert(0, str(CODE_DIR))

from loaders import load_dataset  # noqa: E402
from validation import OUTPUT_COLUMNS, validate_row  # noqa: E402


def main() -> int:
    output_path = ROOT / "output.csv"
    if not output_path.exists():
        print("output.csv is missing; run python3 code/main.py first.")
        return 1
    dataset = load_dataset(ROOT / "dataset")
    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(dataset.requests):
        print(f"row count mismatch: {len(rows)} != {len(dataset.requests)}")
        return 1
    if not rows or list(rows[0]) != OUTPUT_COLUMNS:
        print("header mismatch")
        return 1
    errors = {}
    for request, row in zip(dataset.requests, rows):
        row_errors = validate_row(dataset, request, row)
        if row_errors:
            errors[request.request_id] = row_errors
    if errors:
        print(f"invalid rows: {len(errors)}")
        for request_id, row_errors in list(errors.items())[:10]:
            print(request_id, row_errors)
        return 1
    print(f"Validated {len(rows)} output rows successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
