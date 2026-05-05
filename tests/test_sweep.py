from __future__ import annotations

import unittest

from src.ui.engine.runs.parameter_sweep import build_parameter_sweep_plan, parse_integer_sweep_values


class SweepTests(unittest.TestCase):
    def test_parse_integer_sweep_values_accepts_values_ranges_steps_and_deduplicates(self) -> None:
        values = parse_integer_sweep_values("3, 5-7, 7, 10-14:2", minimum=0, label="Target")

        self.assertEqual(values, [3, 5, 6, 7, 10, 12, 14])

    def test_parse_integer_sweep_values_rejects_invalid_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "range start must be <= end"):
            parse_integer_sweep_values("8-4", minimum=0, label="Target")

    def test_parse_integer_sweep_values_rejects_values_below_minimum(self) -> None:
        with self.assertRaisesRegex(ValueError, "below minimum"):
            parse_integer_sweep_values("0,1", minimum=1, label="Max flags")

    def test_build_parameter_sweep_plan_returns_cartesian_preview(self) -> None:
        combinations, total_runs, preview_rows = build_parameter_sweep_plan(
            target_values=[2, 4],
            max_flag_values=[3, 5],
            runs_per_combination=2,
        )

        self.assertEqual(combinations, [(2, 3), (2, 5), (4, 3), (4, 5)])
        self.assertEqual(total_runs, 8)
        self.assertEqual(
            preview_rows[0],
            {
                "target_injections": 2,
                "max_flags": 3,
                "runs_per_combination": 2,
                "total_planned_runs": 8,
            },
        )


if __name__ == "__main__":
    unittest.main()
