import json
from pathlib import Path
from typing import Any


def build_reorder(
    records: list[dict[str, Any]], low_stock: float = 50
) -> list[dict[str, Any]]:
    """Return low-stock records ordered by quantity and name."""
    low = [record for record in records if record["quantity_ml"] <= low_stock]
    ordered = sorted(low, key=lambda record: (record["quantity_ml"], record["name"]))

    return [
        {"priority": priority, **record}
        for priority, record in enumerate(ordered, start=1)
    ]


def build_report(
    records: list[dict[str, Any]], unsafe: list[Any], low_stock: float = 50
) -> dict[str, list[Any]]:
    """Combine reorder and unsafe inventory findings into a report."""
    return {
        "reorder": build_reorder(records, low_stock),
        "unsafe": unsafe,
    }


def write_report(report: dict[str, list[Any]], path: Path) -> None:
    """Save an inventory report as formatted JSON."""
    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)


def read_report(path: Path) -> dict[str, list[Any]]:
    """Load an inventory report previously saved by write_report."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def summary_line(report: dict[str, list[Any]], expiring: int) -> str:
    """Summarize reorder, unsafe, and expiring item counts."""
    return (
        f"{len(report['reorder'])} to reorder, "
        f"{len(report['unsafe'])} unsafe, "
        f"{expiring} expiring"
    )
