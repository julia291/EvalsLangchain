from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.ui.engine.validation import (
    validate_dataset,
    validate_imports,
    validate_run_store,
)


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

    def test_validate_dataset_reports_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mails.json"
            path.write_text(json.dumps([]), encoding="utf-8")
            report = validate_dataset(str(path))
        self.assertFalse(report.ok)
        self.assertTrue(any("no mails" in issue.message for issue in report.issues))

    def test_validate_dataset_rejects_empty_recipient(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mails.json"
            path.write_text(
                json.dumps(
                    [{"id": 1, "recipient": "  ", "subject": "s", "content": "c"}]
                ),
                encoding="utf-8",
            )
            report = validate_dataset(str(path))
        self.assertFalse(report.ok)
        self.assertTrue(
            any("empty or non-string recipient" in issue.message for issue in report.issues)
        )

    def test_validate_dataset_rejects_null_recipient(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mails.json"
            path.write_text(
                json.dumps(
                    [{"id": 1, "recipient": None, "subject": "s", "content": "c"}]
                ),
                encoding="utf-8",
            )
            report = validate_dataset(str(path))
        self.assertFalse(report.ok)

    def test_validate_dataset_warns_on_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mails.json"
            path.write_text(
                json.dumps(
                    [
                        {"id": 1, "recipient": "a@x.com", "subject": "s", "content": "c"},
                        {"id": 1, "recipient": "b@x.com", "subject": "s", "content": "c"},
                    ]
                ),
                encoding="utf-8",
            )
            report = validate_dataset(str(path))
        self.assertTrue(report.ok)  # Duplicates are warnings, not errors.
        self.assertTrue(
            any(issue.level == "warning" and "Duplicate" in issue.message for issue in report.issues)
        )

    def test_validate_dataset_reports_missing_file(self) -> None:
        report = validate_dataset("/does/not/exist/mails.json")
        self.assertFalse(report.ok)
        self.assertTrue(any("does not exist" in issue.message for issue in report.issues))

    def test_validate_dataset_reports_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mails.json"
            path.write_text("{not valid", encoding="utf-8")
            report = validate_dataset(str(path))
        self.assertFalse(report.ok)
        self.assertTrue(any("Invalid JSON" in issue.message for issue in report.issues))

    def test_validate_imports_succeeds_for_core_modules(self) -> None:
        report = validate_imports()
        self.assertTrue(report.ok, msg=str(report.as_rows()))
        self.assertTrue(any(issue.check == "imports" and issue.level == "info" for issue in report.issues))

    def test_validate_imports_reports_failing_module(self) -> None:
        report = validate_imports(module_names=["definitely.not.a.real.module.x"])
        self.assertFalse(report.ok)
        self.assertTrue(any(issue.level == "error" for issue in report.issues))

    def test_validate_run_store_returns_info_when_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_store(Path(tmp) / "missing.json")
        self.assertTrue(report.ok)
        self.assertTrue(any("No saved live runs" in issue.message for issue in report.issues))

    def test_validate_run_store_detects_model_name_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ui_runs.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "models": {
                            "expected-model": {
                                "runs": [
                                    {
                                        "run_id": "r1",
                                        "created_at": "2026-05-06T12:00:00+00:00",
                                        "name": "r1",
                                        "parameters": {"model_name": "wrong-model"},
                                        "hyperparameters": {"model_name": "wrong-model"},
                                        "summary": {
                                            "processed_mails": 0,
                                            "target_injections": 0,
                                            "actual_injections": 0,
                                            "flagged_count": 0,
                                            "max_flags": 1,
                                            "flag_rate": 0.0,
                                            "success": False,
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
        self.assertFalse(report.ok)
        self.assertTrue(any("parameters.model_name" in issue.message for issue in report.issues))

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
