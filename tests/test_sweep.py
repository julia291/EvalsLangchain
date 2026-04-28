from __future__ import annotations

import unittest

from src.ui.engine.sweep import build_sweep_plan, parse_int_spec


class TestParseIntSpec(unittest.TestCase):
    def test_single_values(self):
        self.assertEqual(parse_int_spec("6,9,12", minimum=0, label="X"), [6, 9, 12])

    def test_range(self):
        self.assertEqual(parse_int_spec("4-7", minimum=0, label="X"), [4, 5, 6, 7])

    def test_range_with_step(self):
        self.assertEqual(parse_int_spec("4-10:2", minimum=0, label="X"), [4, 6, 8, 10])

    def test_mixed_spec(self):
        self.assertEqual(parse_int_spec("3,5-7,10", minimum=0, label="X"), [3, 5, 6, 7, 10])

    def test_deduplicates_values(self):
        self.assertEqual(parse_int_spec("3,3,3", minimum=0, label="X"), [3])

    def test_raises_on_empty(self):
        with self.assertRaises(ValueError):
            parse_int_spec("", minimum=0, label="X")

    def test_raises_on_below_minimum(self):
        with self.assertRaises(ValueError):
            parse_int_spec("0", minimum=1, label="Flags")

    def test_raises_on_invalid_token(self):
        with self.assertRaises(ValueError):
            parse_int_spec("abc", minimum=0, label="X")

    def test_raises_on_inverted_range(self):
        with self.assertRaises(ValueError):
            parse_int_spec("10-5", minimum=0, label="X")

    def test_raises_on_zero_step(self):
        with self.assertRaises(ValueError):
            parse_int_spec("1-10:0", minimum=0, label="X")

    def test_ignores_extra_commas(self):
        self.assertEqual(parse_int_spec("5,,7", minimum=0, label="X"), [5, 7])


class TestBuildSweepPlan(unittest.TestCase):
    def test_cartesian_product(self):
        combos, total, rows = build_sweep_plan([6, 9], [3, 5], runs_per_combination=2)
        self.assertEqual(len(combos), 4)
        self.assertEqual(total, 8)
        self.assertIn((6, 3), combos)
        self.assertIn((9, 5), combos)

    def test_preview_rows_count_matches_combinations(self):
        _, _, rows = build_sweep_plan([1, 2], [3], runs_per_combination=1)
        self.assertEqual(len(rows), 2)

    def test_preview_row_fields(self):
        _, _, rows = build_sweep_plan([5], [10], runs_per_combination=3)
        row = rows[0]
        self.assertEqual(row["target_injections"], 5)
        self.assertEqual(row["max_flags"], 10)
        self.assertEqual(row["runs_per_combination"], 3)

    def test_single_combination(self):
        combos, total, _ = build_sweep_plan([6], [6], runs_per_combination=1)
        self.assertEqual(combos, [(6, 6)])
        self.assertEqual(total, 1)


if __name__ == "__main__":
    unittest.main()
