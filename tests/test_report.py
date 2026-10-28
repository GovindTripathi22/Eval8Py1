import json
import tempfile
import unittest
from pathlib import Path

from report import build_reorder, build_report, read_report, summary_line, write_report


class ReorderTests(unittest.TestCase):
    def test_low_stock_items_are_sorted(self):
        data = [
            {"name": "Salt", "quantity_ml": 25},
            {"name": "Acid", "quantity_ml": 10},
            {"name": "Full", "quantity_ml": 500},
        ]

        result = build_reorder(data, low_stock=50)

        self.assertEqual([item["name"] for item in result],
                         ["Acid", "Salt"])
        self.assertEqual([item["priority"] for item in result], [1, 2])

    def test_original_records_are_not_changed(self):
        data = [{"name": "Salt", "quantity_ml": 25}]
        build_reorder(data)
        self.assertNotIn("priority", data[0])


class ReportTests(unittest.TestCase):
    def test_report_has_reorder_and_unsafe(self):
        data = [{"name": "Salt", "quantity_ml": 25}]
        unsafe = [{"name": "Acid", "reason": "bad storage"}]

        result = build_report(data, unsafe)

        self.assertEqual(result["unsafe"], unsafe)
        self.assertEqual(result["reorder"][0]["name"], "Salt")

    def test_save_and_read_report(self):
        report = {"reorder": [], "unsafe": []}

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            write_report(report, path)
            loaded = read_report(path)

        self.assertEqual(loaded, report)

    def test_summary_line(self):
        report = {"reorder": [1, 2], "unsafe": [3]}
        self.assertEqual(summary_line(report, 4),
                         "2 to reorder, 1 unsafe, 4 expiring")


if __name__ == "__main__":
    unittest.main()
