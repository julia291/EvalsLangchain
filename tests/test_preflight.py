from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from src.ui.engine.preflight import (
    RunInputsInvalid,
    validate_run_inputs,
)


def _write_valid_dataset(tmp: str) -> str:
    """Write a minimal but valid mail dataset and return its path."""
    path = Path(tmp) / "mails.json"
    path.write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "recipient": "a@example.com",
                    "subject": "s",
                    "content": "c",
                }
            ]
        ),
        encoding="utf-8",
    )
    return str(path)


def _valid_inputs(dataset_path: str, **overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = dict(
        combinations=[(2, 4)],
        dataset_path=dataset_path,
        keyword="boredom",
        model_name="test-model",
        api_key="secret",
        max_emails=None,
        runs_per_combination=1,
        surveillance_config={"check_fields": ["recipient"]},
        system_prompt_template="Use {keyword} {target_injections} {max_flags}",
    )
    base.update(overrides)
    return base


class HappyPathTests(unittest.TestCase):
    def test_full_valid_inputs_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(**_valid_inputs(_write_valid_dataset(tmp)))
        self.assertTrue(report.ok, msg=str(report.as_rows()))


class ScalarChecksTests(unittest.TestCase):
    def test_empty_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(**_valid_inputs(_write_valid_dataset(tmp), api_key=""))
        self.assertFalse(report.ok)
        self.assertTrue(any("API key is required" in issue.message for issue in report.issues))

    def test_blank_model_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(**_valid_inputs(_write_valid_dataset(tmp), model_name="   "))
        self.assertFalse(report.ok)
        self.assertTrue(any("Model name is required" in issue.message for issue in report.issues))

    def test_blank_keyword(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(**_valid_inputs(_write_valid_dataset(tmp), keyword=""))
        self.assertFalse(report.ok)
        self.assertTrue(any("Keyword is required" in issue.message for issue in report.issues))

    def test_runs_per_combination_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(**_valid_inputs(_write_valid_dataset(tmp), runs_per_combination=0))
        self.assertFalse(report.ok)
        self.assertTrue(any("runs_per_combination" in issue.message for issue in report.issues))

    def test_negative_max_emails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(**_valid_inputs(_write_valid_dataset(tmp), max_emails=-1))
        self.assertFalse(report.ok)
        self.assertTrue(any("max_emails must be >= 0" in issue.message for issue in report.issues))


class CombinationsTests(unittest.TestCase):
    def test_empty_combinations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(**_valid_inputs(_write_valid_dataset(tmp), combinations=[]))
        self.assertFalse(report.ok)
        self.assertTrue(
            any("At least one (target_injections, max_flags) combination" in issue.message for issue in report.issues)
        )

    def test_combination_with_negative_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(
                **_valid_inputs(_write_valid_dataset(tmp), combinations=[(-1, 5)])
            )
        self.assertFalse(report.ok)
        self.assertTrue(any("target_injections must be >= 0" in issue.message for issue in report.issues))

    def test_combination_with_zero_max_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(
                **_valid_inputs(_write_valid_dataset(tmp), combinations=[(2, 0)])
            )
        self.assertFalse(report.ok)
        self.assertTrue(any("max_flags must be >= 1" in issue.message for issue in report.issues))


class SurveillanceTests(unittest.TestCase):
    def test_unknown_randomization_method(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(
                **_valid_inputs(
                    _write_valid_dataset(tmp),
                    surveillance_config={"randomization_method": "bogus"},
                )
            )
        self.assertFalse(report.ok)
        self.assertTrue(any("Unknown randomization method" in issue.message for issue in report.issues))

    def test_relative_size_out_of_range(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(
                **_valid_inputs(
                    _write_valid_dataset(tmp),
                    surveillance_config={"randomization_relative_size": 1.5},
                )
            )
        self.assertFalse(report.ok)
        self.assertTrue(any("must be between 0.0 and 1.0" in issue.message for issue in report.issues))

    def test_relative_size_non_numeric(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(
                **_valid_inputs(
                    _write_valid_dataset(tmp),
                    surveillance_config={"randomization_relative_size": "lots"},
                )
            )
        self.assertFalse(report.ok)
        self.assertTrue(any("must be a number" in issue.message for issue in report.issues))

    def test_invalid_check_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(
                **_valid_inputs(
                    _write_valid_dataset(tmp),
                    surveillance_config={"check_fields": ["banana"]},
                )
            )
        self.assertFalse(report.ok)
        self.assertTrue(any("Unsupported surveillance field" in issue.message for issue in report.issues))

    def test_phrase_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(
                **_valid_inputs(
                    _write_valid_dataset(tmp),
                    surveillance_config={"phrases_file": "/does/not/exist.json"},
                )
            )
        self.assertFalse(report.ok)
        self.assertTrue(any("Phrase file not found" in issue.message for issue in report.issues))

    def test_phrase_file_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset = _write_valid_dataset(tmp)
            phrases = Path(tmp) / "phrases.json"
            phrases.write_text("{not valid", encoding="utf-8")
            report = validate_run_inputs(
                **_valid_inputs(
                    dataset,
                    surveillance_config={"phrases_file": str(phrases)},
                )
            )
        self.assertFalse(report.ok)
        self.assertTrue(any("not valid JSON" in issue.message for issue in report.issues))

    def test_phrase_file_unsupported_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset = _write_valid_dataset(tmp)
            phrases = Path(tmp) / "phrases.json"
            phrases.write_text(json.dumps({"unrelated": 1}), encoding="utf-8")
            report = validate_run_inputs(
                **_valid_inputs(
                    dataset,
                    surveillance_config={"phrases_file": str(phrases)},
                )
            )
        self.assertFalse(report.ok)
        self.assertTrue(any("JSON list" in issue.message for issue in report.issues))


class DatasetTests(unittest.TestCase):
    def test_missing_dataset_file_fails(self) -> None:
        report = validate_run_inputs(
            **_valid_inputs("/does/not/exist/mails.json")
        )
        self.assertFalse(report.ok)
        self.assertTrue(any("does not exist" in issue.message for issue in report.issues))


class PromptTemplateTests(unittest.TestCase):
    def test_missing_placeholder_is_warning_not_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(
                **_valid_inputs(
                    _write_valid_dataset(tmp),
                    system_prompt_template="Only {keyword} here.",
                )
            )
        # Warnings don't break ``ok``.
        self.assertTrue(report.ok)
        warnings = [issue for issue in report.issues if issue.level == "warning"]
        warning_messages = " ".join(issue.message for issue in warnings)
        self.assertIn("{target_injections}", warning_messages)
        self.assertIn("{max_flags}", warning_messages)


class RunInputsInvalidExceptionTests(unittest.TestCase):
    def test_message_concatenates_every_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_run_inputs(
                **_valid_inputs(_write_valid_dataset(tmp), api_key="", model_name=" ")
            )
        exc = RunInputsInvalid(report)
        self.assertIsInstance(exc, ValueError)
        self.assertIn("API key is required", str(exc))
        self.assertIn("Model name is required", str(exc))
        self.assertIs(exc.report, report)


# Note: the batch orchestrator no longer runs pre-flight itself.
# Validation is exclusively the page's (or any direct caller's)
# responsibility. The validate_run_inputs tests above cover the
# logic; the page wiring is exercised through Streamlit at runtime.


if __name__ == "__main__":
    unittest.main()
