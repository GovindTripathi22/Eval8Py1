"""Tests for flammable storage and corrosive proximity rules."""

import unittest

from safety import find_unsafe
from tests.helpers import make


def names(flagged: list) -> list:
    """Return just the names of flagged records, in order."""
    return [item["name"] for item in flagged]


class FlammableStorageTests(unittest.TestCase):
    def test_flammable_in_cabinet_is_safe(self):
        records = [
            make(
                "Hexane",
                storage="flammables_cabinet",
                hazards=["flammable"],
            )
        ]
        self.assertEqual(find_unsafe(records), [])

    def test_flammable_in_fridge_is_flagged(self):
        flagged = find_unsafe(
            [make("Ethanol", storage="fridge", hazards=["flammable"])]
        )
        self.assertEqual(names(flagged), ["Ethanol"])
        self.assertEqual(
            flagged[0]["reason"],
            "flammable stored in fridge, not flammables_cabinet",
        )

    def test_flammable_on_shelf_is_flagged(self):
        flagged = find_unsafe(
            [make("Acetone", hazards=["irritant", "flammable"])]
        )
        self.assertEqual(names(flagged), ["Acetone"])
        self.assertEqual(
            flagged[0]["reason"],
            "flammable stored in shelf, not flammables_cabinet",
        )

    def test_non_flammable_anywhere_is_safe(self):
        records = [
            make("Salt"),
            make("Cold", storage="fridge", hazards=["toxic"]),
        ]
        self.assertEqual(find_unsafe(records), [])


class CorrosiveNeighbourTests(unittest.TestCase):
    def test_corrosive_on_shelf_with_flammable_on_shelf(self):
        records = [
            make("HCl", hazards=["corrosive"]),
            make("Acetone", hazards=["flammable"]),
        ]
        flagged = find_unsafe(records)
        self.assertEqual(names(flagged), ["HCl", "Acetone"])
        self.assertEqual(
            flagged[0]["reason"],
            "corrosive on shelf next to a flammable",
        )

    def test_corrosive_on_shelf_flammable_in_cabinet_is_safe(self):
        records = [
            make("HCl", hazards=["corrosive"]),
            make(
                "Hexane",
                storage="flammables_cabinet",
                hazards=["flammable"],
            ),
        ]
        self.assertEqual(find_unsafe(records), [])

    def test_corrosive_in_fridge_next_to_nothing_on_shelf(self):
        records = [
            make("AgNO3", storage="fridge", hazards=["corrosive"]),
            make("Acetone", hazards=["flammable"]),
        ]
        self.assertEqual(names(find_unsafe(records)), ["Acetone"])

    def test_flammable_corrosive_alone_is_not_its_own_neighbour(self):
        flagged = find_unsafe([make("Acetic", hazards=["flammable", "corrosive"])])
        self.assertEqual(
            flagged[0]["reason"],
            "flammable stored in shelf, not flammables_cabinet",
        )

    def test_both_reasons_joined_when_another_flammable_is_near(self):
        records = [
            make("Acetic", hazards=["flammable", "corrosive"]),
            make("Acetone", hazards=["flammable"]),
        ]
        reason = find_unsafe(records)[0]["reason"]
        self.assertEqual(
            reason,
            "flammable stored in shelf, not flammables_cabinet; "
            "corrosive on shelf next to a flammable",
        )

    def test_records_are_not_modified(self):
        records = [
            make("HCl", hazards=["corrosive"]),
            make("Acetone", hazards=["flammable"]),
        ]
        before = [dict(record) for record in records]
        find_unsafe(records)
        self.assertEqual(records, before)


if __name__ == "__main__":
    unittest.main()
