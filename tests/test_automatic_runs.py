from __future__ import annotations

import unittest
from typing import Any

from src.ui.engine.runs.automatic_batch import (
    build_run_summary_table,
    format_automatic_run_name,
    format_automatic_run_notes,
    run_automatic_live_batch,
)


def make_run(run_name: str, target_injections: int, max_flags: int) -> dict[str, Any]:
    return {
        "run_id": run_name,
        "name": run_name,
        "parameters": {
            "target_injections": target_injections,
            "max_flags": max_flags,
        },
        "summary": {
            "processed_mails": 3,
            "actual_injections": target_injections,
            "flagged_count": 1,
            "flag_rate": 33.33,
            "success": True,
        },
    }


class AutomaticRunsTests(unittest.TestCase):
    def test_format_automatic_run_name_uses_default_prefix_when_empty(self) -> None:
        self.assertEqual(
            format_automatic_run_name(prefix=" ", target_injections=2, max_flags=5, repetition=1),
            "auto-live-t2-f5-r1",
        )

    def test_format_automatic_run_notes_appends_traceable_metadata(self) -> None:
        notes = format_automatic_run_notes(
            notes="baseline",
            target_injections=4,
            max_flags=7,
            repetition=2,
            runs_per_combination=3,
        )

        self.assertIn("baseline", notes)
        self.assertIn("auto.target_injections=4", notes)
        self.assertIn("auto.max_flags=7", notes)
        self.assertIn("auto.repetition=2/3", notes)

    def test_execute_batch_saves_successes_and_continues_after_failure(self) -> None:
        saved: list[dict[str, Any]] = []
        progress_events: list[tuple[int, int, str]] = []
        attempted: list[str] = []

        def run_live(**kwargs: Any) -> dict[str, Any]:
            run_name = kwargs["run_name"]
            attempted.append(run_name)
            if run_name == "batch-t2-f5-r1":
                raise RuntimeError("model failed")
            return make_run(
                run_name=run_name,
                target_injections=kwargs["target_injections"],
                max_flags=kwargs["max_flags"],
            )

        with self.assertLogs("src.ui.engine.runs.automatic_batch", level="INFO") as logs:
            result = run_automatic_live_batch(
                run_name_prefix="batch",
                combinations=[(2, 3), (2, 5)],
                runs_per_combination=1,
                dataset_path="data/mails.json",
                keyword="boredom",
                model_name="test-model",
                api_key="secret",
                surveillance_config={"check_fields": ["recipient"], "phrases": ["alpha"]},
                system_prompt_template="Use {keyword} {target_injections} {max_flags}",
                max_emails=3,
                notes="test",
                run_live=run_live,
                save_run=saved.append,
                progress_callback=lambda done, total, name: progress_events.append((done, total, name)),
            )

        self.assertEqual(attempted, ["batch-t2-f3-r1", "batch-t2-f5-r1"])
        self.assertEqual([run["name"] for run in saved], ["batch-t2-f3-r1"])
        self.assertEqual([run["name"] for run in result.created], ["batch-t2-f3-r1"])
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.failure_rows[0]["run_name"], "batch-t2-f5-r1")
        self.assertEqual(result.failure_rows[0]["error"], "model failed")
        self.assertEqual(progress_events[0], (0, 2, "batch-t2-f3-r1"))
        self.assertEqual(progress_events[-1], (2, 2, "batch-t2-f5-r1"))
        self.assertTrue(any("automatic_batch_started" in message for message in logs.output))
        self.assertTrue(any("automatic_run_failed" in message for message in logs.output))
        self.assertTrue(any("automatic_batch_finished" in message for message in logs.output))

    def test_execute_batch_rejects_missing_api_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "API key is required"):
            run_automatic_live_batch(
                run_name_prefix="batch",
                combinations=[(1, 2)],
                runs_per_combination=1,
                dataset_path="data/mails.json",
                keyword="boredom",
                model_name="test-model",
                api_key="",
                surveillance_config={},
                system_prompt_template="",
                max_emails=None,
                notes="",
                run_live=lambda **_: {},
                save_run=lambda _: None,
            )

    def test_build_run_summary_table_extracts_summary_fields(self) -> None:
        overview = build_run_summary_table([make_run("run-1", 2, 4)])

        self.assertEqual(
            overview,
            [
                {
                    "run_id": "run-1",
                    "name": "run-1",
                    "target_injections": 2,
                    "max_flags": 4,
                    "processed": 3,
                    "injections": 2,
                    "flags": 1,
                    "flag_rate": 33.33,
                    "success": True,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
