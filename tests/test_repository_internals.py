from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ui.store import repository
from src.ui.store.repository import _flatten, _ungroup


class FlattenTests(unittest.TestCase):
    def test_flattens_nested_dicts_with_dot_paths(self) -> None:
        flat = _flatten({"a": 1, "b": {"c": 2, "d": {"e": 3}}})
        self.assertEqual(flat, {"a": 1, "b.c": 2, "b.d.e": 3})

    def test_lists_remain_as_leaves(self) -> None:
        flat = _flatten({"surveillance": {"check_fields": ["recipient", "subject"]}})
        self.assertEqual(flat, {"surveillance.check_fields": ["recipient", "subject"]})

    def test_top_level_non_dict_returns_empty_or_singleton(self) -> None:
        self.assertEqual(_flatten("scalar"), {})  # No prefix, no key.
        self.assertEqual(_flatten("scalar", prefix="root"), {"root": "scalar"})


class UngroupTests(unittest.TestCase):
    def test_returns_empty_for_wrong_schema_version(self) -> None:
        self.assertEqual(_ungroup({"schema_version": 1, "models": {}}), [])

    def test_returns_empty_for_missing_models_key(self) -> None:
        self.assertEqual(_ungroup({"schema_version": 2}), [])

    def test_filters_garbage_run_entries(self) -> None:
        store = {
            "schema_version": 2,
            "models": {
                "m1": {"runs": [{"ok": 1}, "junk", None, {"ok": 2}]},
                "m2": "not-a-dict",
                "m3": {"runs": "not-a-list"},
            },
        }
        runs = _ungroup(store)
        self.assertEqual(runs, [{"ok": 1}, {"ok": 2}])


class LoadRunsRobustnessTests(unittest.TestCase):
    def test_corrupt_json_returns_empty_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs_path = Path(tmp) / "ui_runs.json"
            runs_path.write_text("{not valid json", encoding="utf-8")

            with patch.object(repository, "RUNS_PATH", runs_path):
                with self.assertLogs("src.ui.store.repository", level="WARNING") as logs:
                    self.assertEqual(repository.load_runs(), [])

            self.assertTrue(any("not valid JSON" in line for line in logs.output))

    def test_non_dict_root_returns_empty_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs_path = Path(tmp) / "ui_runs.json"
            runs_path.write_text(json.dumps(["unexpected"]), encoding="utf-8")

            with patch.object(repository, "RUNS_PATH", runs_path):
                with self.assertLogs("src.ui.store.repository", level="WARNING") as logs:
                    self.assertEqual(repository.load_runs(), [])

            self.assertTrue(any("top-level shape" in line for line in logs.output))


class SaveRunsAtomicityTests(unittest.TestCase):
    def test_existing_file_is_preserved_when_serialization_fails(self) -> None:
        # A run with a non-JSON-serializable value (a set) makes json.dump
        # raise mid-write. The existing file must survive intact.
        with tempfile.TemporaryDirectory() as tmp:
            runs_path = Path(tmp) / "ui_runs.json"
            runs_path.write_text(
                json.dumps({"schema_version": 2, "models": {}}), encoding="utf-8"
            )
            original = runs_path.read_text(encoding="utf-8")

            bad_run = {
                "run_id": "x",
                "name": "x",
                "parameters": {"model_name": "m", "bad": {1, 2}},  # set isn't JSON.
                "summary": {},
                "results": [],
            }

            with patch.object(repository, "RUNS_PATH", runs_path):
                with self.assertRaises(TypeError):
                    repository.save_runs([bad_run])

            # File contents unchanged.
            self.assertEqual(runs_path.read_text(encoding="utf-8"), original)
            # No leftover temp files in the directory.
            siblings = [p.name for p in runs_path.parent.iterdir()]
            self.assertEqual(siblings, [runs_path.name])


if __name__ == "__main__":
    unittest.main()
