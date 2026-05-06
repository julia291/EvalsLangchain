from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from src.ui.store import repository


def make_run(name: str, model_name: str, target_injections: int = 2) -> dict[str, Any]:
    return {
        "run_id": name,
        "created_at": f"2026-05-0{target_injections}T12:00:00+00:00",
        "name": name,
        "parameters": {
            "model_name": model_name,
            "target_injections": target_injections,
            "max_flags": 5,
            "surveillance": {"check_fields": ["recipient"], "phrase_count": 3},
        },
        "summary": {"processed_mails": 1},
        "results": [],
    }


class RepositoryTests(unittest.TestCase):
    def test_save_runs_groups_live_runs_by_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs_path = Path(tmp) / "ui_runs.json"
            runs = [
                make_run("run-1", "gemini-2.5-flash", 1),
                make_run("run-2", "gemini-2.5-flash", 2),
                make_run("run-3", "gpt-5.4", 3),
            ]

            with patch.object(repository, "RUNS_PATH", runs_path):
                repository.save_runs(runs)
                loaded = repository.load_runs()

            payload = json.loads(runs_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 2)
            self.assertEqual(set(payload["models"]), {"gemini-2.5-flash", "gpt-5.4"})
            self.assertEqual(len(payload["models"]["gemini-2.5-flash"]["runs"]), 2)
            self.assertEqual([run["run_id"] for run in loaded], ["run-1", "run-2", "run-3"])

    def test_append_run_flattens_hyperparameters_for_visualization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs_path = Path(tmp) / "ui_runs.json"

            with patch.object(repository, "RUNS_PATH", runs_path):
                repository.append_run(make_run("run-1", "gemini-2.5-flash"))
                run = repository.load_runs()[0]

            self.assertEqual(run["hyperparameters"]["model_name"], "gemini-2.5-flash")
            self.assertEqual(run["hyperparameters"]["target_injections"], 2)
            self.assertEqual(run["hyperparameters"]["surveillance.check_fields"], ["recipient"])
            self.assertEqual(run["hyperparameters"]["surveillance.phrase_count"], 3)

    def test_load_runs_ignores_old_flat_list_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs_path = Path(tmp) / "ui_runs.json"
            runs_path.write_text(json.dumps([make_run("old", "gemini-2.5-flash")]), encoding="utf-8")

            with patch.object(repository, "RUNS_PATH", runs_path):
                self.assertEqual(repository.load_runs(), [])

    def test_save_runs_requires_model_name(self) -> None:
        run = make_run("run-1", " ")

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(repository, "RUNS_PATH", Path(tmp) / "ui_runs.json"):
                with self.assertRaisesRegex(ValueError, "model_name"):
                    repository.save_runs([run])


if __name__ == "__main__":
    unittest.main()
