"""End-to-end tests for the inventory command-line entry point."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from main import format_set, main


SAMPLE = [
    {
        "name": "Ethanol",
        "formula": "C2H5OH",
        "category": "solvent",
        "quantity_ml": 40,
        "expiry": "2027-03-01",
        "storage": "fridge",
        "hazards": ["flammable"],
    },
    {
        "name": "NaOH",
        "formula": "NaOH",
        "category": "base",
        "quantity_ml": 30,
        "expiry": "2026-09-30",
        "storage": "shelf",
        "hazards": ["corrosive"],
    },
    {
        "name": "Salt",
        "formula": "NaCl",
        "category": "salt",
        "quantity_ml": 900,
        "expiry": "2026-10-01",
        "storage": "shelf",
        "hazards": [],
    },
    {
        "name": "Broken",
        "formula": "?",
        "category": "x",
        "quantity_ml": "lots",
        "expiry": "2027-01-01",
        "storage": "shelf",
        "hazards": [],
    },
]


class MainTests(unittest.TestCase):
    def run_main(self, argv: list, data: object = SAMPLE) -> tuple:
        """Run main() in a temporary folder and return its output and report."""
        with tempfile.TemporaryDirectory() as folder:
            data_path = Path(folder) / "reagents.json"
            out_path = Path(folder) / "out.json"
            data_path.write_text(json.dumps(data), encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = main(argv, data_path, out_path)

            saved = (
                json.loads(out_path.read_text(encoding="utf-8"))
                if out_path.exists()
                else None
            )
            return code, buffer.getvalue(), saved

    def test_summary_counts_match_the_data(self):
        code, output, saved = self.run_main(["2026-11-02"])

        self.assertEqual(code, 0)
        self.assertEqual(
            output.strip().splitlines()[-1],
            "2 to reorder, 1 unsafe, 2 expiring",
        )
        self.assertEqual(
            [record["name"] for record in saved["reorder"]],
            ["NaOH", "Ethanol"],
        )

    def test_threshold_argument_changes_reorder(self):
        _, output, _ = self.run_main(["2026-11-02", "35"])
        self.assertTrue(
            output.strip().endswith("1 to reorder, 1 unsafe, 2 expiring")
        )

    def test_skipped_record_is_reported(self):
        _, output, _ = self.run_main(["2026-11-02"])
        self.assertIn("Broken: quantity_ml 'lots' is not a number", output)

    def test_bad_date_returns_error_code(self):
        code, output, saved = self.run_main(["2026-13-01"])

        self.assertEqual(code, 1)
        self.assertIn("reference date must be YYYY-MM-DD", output)
        self.assertIsNone(saved)

    def test_bad_threshold_returns_error_code(self):
        code, output, _ = self.run_main(["2026-11-02", "fifty"])

        self.assertEqual(code, 1)
        self.assertIn("must be a number", output)

    def test_missing_data_file(self):
        buffer = io.StringIO()

        with tempfile.TemporaryDirectory() as folder:
            with redirect_stdout(buffer):
                code = main(
                    [],
                    Path(folder) / "nope.json",
                    Path(folder) / "out.json",
                )

        self.assertEqual(code, 1)
        self.assertIn("not found", buffer.getvalue())

    def test_windows_file_with_bom_and_crlf_still_loads(self):
        with tempfile.TemporaryDirectory() as folder:
            data_path = Path(folder) / "reagents.json"
            text = json.dumps(SAMPLE, indent=2).replace("\n", "\r\n")
            data_path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = main(
                    ["2026-11-02"],
                    data_path,
                    Path(folder) / "out.json",
                )

            self.assertEqual(code, 0)
            self.assertIn("2 to reorder", buffer.getvalue())

    def test_format_set_is_sorted(self):
        self.assertEqual(
            format_set({"salt", "acid", "base"}),
            "{'acid', 'base', 'salt'}",
        )
 

if __name__ == "__main__":
    unittest.main()
  