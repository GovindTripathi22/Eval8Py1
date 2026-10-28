import json
from datetime import date
from pathlib import Path

STORAGE_PLACES = (
    "shelf",
    "fridge",
    "cabinet",
    "flammables cabinet",
    "flammables_cabinet",
)
REQUIRED_KEYS = ("name", "formula", "category", "quantity_ml", "expiry", "storage")


def parse_hazards(raw: object) -> list[str]:
    """Normalize hazard data from messy inputs into a clean list."""
    if raw is None:
        return []

    if isinstance(raw, list):
        return [str(item).strip().lower() for item in raw if str(item).strip()]

    if isinstance(raw, str):
        return [item.strip().lower() for item in raw.split(",") if item.strip()]

    return [str(raw).strip().lower()]


def normalize_storage(value: object) -> str:
    """Normalize storage names to a consistent format."""
    if not isinstance(value, str):
        return "unknown"

    cleaned = value.strip().lower().replace("_", " ")
    if cleaned == "flammables cabinet":
        return "flammables cabinet"
    if cleaned == "flammables_cabinet":
        return "flammables cabinet"
    return cleaned


def parse_quantity(raw: object) -> int | None:
    """Convert a quantity value to an integer when possible."""
    if raw is None:
        return None

    if isinstance(raw, int):
        return raw

    if isinstance(raw, str):
        cleaned = raw.strip()
        if not cleaned:
            return None
        if cleaned.lower() == "lots":
            return None
        try:
            return int(cleaned)
        except ValueError:
            try:
                return int(float(cleaned))
            except ValueError:
                return None

    return None


def load_inventory(path: str | Path) -> list[dict]:
    """Load inventory data from a JSON file and normalize it."""
    inventory_path = Path(path)
    with inventory_path.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    cleaned: list[dict] = []

    for item in raw_data:
        if not isinstance(item, dict):
            continue

        missing_keys = [key for key in REQUIRED_KEYS if key not in item]
        if missing_keys:
            continue

        normalized = {
            "name": str(item["name"]).strip(),
            "formula": str(item["formula"]).strip(),
            "category": str(item["category"]).strip().lower(),
            "quantity_ml": parse_quantity(item["quantity_ml"]),
            "expiry": str(item["expiry"]).strip(),
            "storage": normalize_storage(item["storage"]),
            "hazards": parse_hazards(item.get("hazards")),
        }

        if normalized["quantity_ml"] is None:
            normalized["quantity_ml"] = 0

        if normalized["storage"] not in STORAGE_PLACES and normalized["storage"] != "unknown":
            normalized["storage"] = "unknown"

        if normalized["expiry"]:
            try:
                date.fromisoformat(normalized["expiry"])
            except ValueError:
                normalized["expiry"] = "unknown"

        cleaned.append(normalized)

    return cleaned


def find_reagent(inventory: list[dict], name: str) -> dict | None:
    for reagent in inventory:
        if reagent["name"].lower() == name.lower():
            return reagent
    return None


def list_expired(inventory: list[dict]) -> list[str]:
    expired: list[str] = []
    today = date.today()

    for reagent in inventory:
        expiry = reagent.get("expiry")
        if expiry in (None, "unknown"):
            continue

        try:
            expiry_date = date.fromisoformat(expiry)
        except ValueError:
            continue

        if expiry_date < today:
            expired.append(reagent["name"])

    return expired


def print_inventory(inventory: list[dict]) -> None:
    print("Reagent Inventory")
    print("=" * 60)

    for reagent in inventory:
        print(
            f"- {reagent['name']} | Formula: {reagent['formula']} | "
            f"Category: {reagent['category']} | Qty: {reagent['quantity_ml']} mL | "
            f"Storage: {reagent['storage']} | Hazards: {', '.join(reagent['hazards']) or 'None'}"
        )

    expired = list_expired(inventory)
    print("\nExpired reagents:")
    if expired:
        for name in expired:
            print(f"  - {name}")
    else:
        print("  None")


def main() -> None:
    inventory = load_inventory("reagents.json")
    print_inventory(inventory)


if __name__ == "__main__":
    main()
