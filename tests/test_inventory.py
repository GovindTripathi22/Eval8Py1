import unittest

from inventory import find_reagent, parse_hazards, parse_quantity


class ParseQuantityTests(unittest.TestCase):
    def test_can_read_a_number(self):
        self.assertEqual(parse_quantity("25"), 25)

    def test_lots_is_unknown(self):
        self.assertIsNone(parse_quantity("lots"))


class ParseHazardsTests(unittest.TestCase):
    def test_comma_string_is_split(self):
        self.assertEqual(parse_hazards("Flammable, Corrosive"),
                         ["flammable", "corrosive"])


class FindReagentTests(unittest.TestCase):
    def test_find_reagent_ignores_case(self):
        items = [{"name": "Ethanol", "quantity_ml": 40}]
        result = find_reagent(items, "ethanol")
        self.assertEqual(result, items[0])

    def test_missing_reagent_returns_none(self):
        items = [{"name": "Salt"}]
        self.assertIsNone(find_reagent(items, "NaOH"))


if __name__ == "__main__":
    unittest.main()
