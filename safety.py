"""Safety checks for reagent storage."""

from typing import Any


def _has_hazard(record: dict[str, Any], hazard: str) -> bool:
    return hazard in record.get("hazards", [])


def find_unsafe(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return copies of unsafe records with a human-readable reason."""
    shelf_flammables = [
        record
        for record in records
        if record.get("storage", "shelf") == "shelf"
        and _has_hazard(record, "flammable")
    ]
    unsafe: list[dict[str, Any]] = []

    for record in records:
        reasons: list[str] = []
        storage = record.get("storage", "shelf")

        if _has_hazard(record, "flammable") and storage not in {
            "flammables_cabinet",
            "flammables cabinet",
        }:
            reasons.append(
                f"flammable stored in {storage}, not flammables_cabinet"
            )

        if (
            _has_hazard(record, "corrosive")
            and storage == "shelf"
            and any(neighbour is not record for neighbour in shelf_flammables)
        ):
            reasons.append("corrosive on shelf next to a flammable")

        if reasons:
            unsafe.append({**record, "reason": "; ".join(reasons)})

    return unsafe
