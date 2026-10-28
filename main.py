"""Command-line entry point for the reagent inventory report."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from inventory import normalize_storage, parse_hazards
from report import build_report, summary_line, write_report
from safety import find_unsafe

REQUIRED_KEYS = (
    "name",
    "formula",
    "category",
    "quantity_ml",
    "expiry",
    "storage",
)


def format_set(values: set[str]) -> str:
    """Format a set in deterministic sorted order."""
    contents = ", ".join(repr(value) for value in sorted(values))
    return "{" + contents + "}"


def _parse_quantity(value: object) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            number = float(value)
        except ValueError:
            return None
        return int(number) if number.is_integer() else number
    return None


def _load_records(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        raw_records = json.load(handle)

    if not isinstance(raw_records, list):
        raise ValueError("data must be a JSON list")

    records: list[dict[str, Any]] = []
    skipped: list[str] = []
    for raw in raw_records:
        if not isinstance(raw, dict):
            skipped.append("<unknown>: record is not an object")
            continue

        missing = [key for key in REQUIRED_KEYS if key not in raw]
        if missing:
            name = raw.get("name", "<unknown>")
            skipped.append(f"{name}: missing {', '.join(missing)}")
            continue

        quantity = _parse_quantity(raw["quantity_ml"])
        if quantity is None:
            skipped.append(
                f"{raw['name']}: quantity_ml {raw['quantity_ml']!r} is not a number"
            )
            continue

        records.append(
            {
                "name": str(raw["name"]),
                "formula": str(raw["formula"]),
                "category": str(raw["category"]),
                "quantity_ml": quantity,
                "expiry": str(raw["expiry"]),
                "storage": normalize_storage(raw["storage"]),
                "hazards": parse_hazards(raw.get("hazards")),
            }
        )
    return records, skipped


def _expiring_count(records: list[dict[str, Any]], reference: date) -> int:
    count = 0
    for record in records:
        try:
            expiry = date.fromisoformat(record["expiry"])
        except ValueError:
            continue
        if expiry < reference:
            count += 1
    return count


def main(
    argv: list[str] | None = None,
    data_path: Path = Path("reagents.json"),
    out_path: Path = Path("report.json"),
) -> int:
    """Build and save an inventory report, returning a process exit code."""
    args = sys.argv[1:] if argv is None else argv
    reference_text = args[0] if args else date.today().isoformat()

    try:
        reference = date.fromisoformat(reference_text)
    except (TypeError, ValueError):
        print("error: reference date must be YYYY-MM-DD")
        return 1

    threshold = 50.0
    if len(args) > 1:
        try:
            threshold = float(args[1])
        except (TypeError, ValueError):
            print("error: low-stock threshold must be a number")
            return 1

    if len(args) > 2:
        print("usage: python main.py [REFERENCE_DATE] [LOW_STOCK]")
        return 1

    try:
        records, skipped = _load_records(Path(data_path))
    except FileNotFoundError:
        print(f"error: data file not found: {data_path}")
        return 1
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"error: could not load data file: {error}")
        return 1

    for message in skipped:
        print(f"Skipped {message}")

    report = build_report(records, find_unsafe(records), threshold)
    expiring = _expiring_count(records, reference)
    write_report(report, Path(out_path))
    print(summary_line(report, expiring))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
