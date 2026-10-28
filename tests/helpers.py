"""Test helpers for inventory safety tests."""


def make(name: str, storage: str = "shelf", hazards: list[str] | None = None) -> dict:
    """Build the minimum inventory record needed by safety tests."""
    return {
        "name": name,
        "storage": storage,
        "hazards": hazards or [],
    }
