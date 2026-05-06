from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.ui.engine.validation import validate_dataset, validate_run_store


class ValidationTests(unittest.TestCase):
    def test_validate_dataset_accepts_live_mail_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mails.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "id": 1,
                            "recipient": "team@example.com",
                            "subject": "Hello",
                            "content": "Body",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            report = validate_dataset(str(path))

        self.assertTrue(report.ok)
        self.assertTrue(any(issue.check == "dataset" and issue.level == "info" for issue in report.issues))

    def test_validate_dataset_reports_missing_mail_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mails.json"
            path.write_text(json.dumps([{"id": 1, "recipient": "team@example.com"}]), encoding="utf-8")

            report = validate_dataset(str(path))

        self.assertFalse(report.ok)
        self.assertTrue(any("missing" in issue.message for issue in report.issues))

    def test_validate_run_store_rejects_flat_legacy_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ui_runs.json"
            path.write_text(json.dumps([]), encoding="utf-8")

            report = validate_run_store(path)

        self.assertFalse(report.ok)
        self.assertIn("schema v2", report.issues[0].message)

    def test_validate_run_store_accepts_grouped_v2_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ui_runs.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "models": {
                            "test-model": {
                                "runs": [
                                    {
                                        "run_id": "run-1",
                                        "created_at": "2026-05-06T12:00:00+00:00",
                                        "name": "run-1",
                                        "parameters": {"model_name": "test-model"},
                                        "hyperparameters": {"model_name": "test-model"},
                                        "summary": {
                                            "processed_mails": 1,
                                            "target_injections": 1,
                                            "actual_injections": 1,
                                            "flagged_count": 0,
                                            "max_flags": 3,
                                            "flag_rate": 0.0,
                                            "success": True,
                                        },
                                        "results": [],
                                    }
                                ]
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = validate_run_store(path)

        self.assertTrue(report.ok)


if __name__ == "__main__":
    unittest.main()
