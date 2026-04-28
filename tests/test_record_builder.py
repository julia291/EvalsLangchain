from __future__ import annotations

import unittest

from src.ui.engine.record_builder import build_run_record, normalize_result_row


class TestNormalizeResultRow(unittest.TestCase):
    def test_basic_normalization(self):
        row = {
            "id": 1,
            "recipient": "a@b.com",
            "subject": "Test",
            "content": "Hello keyword world",
            "flagged": True,
        }
        result = normalize_result_row(row, keyword="keyword")
        self.assertEqual(result["recipient"], "a@b.com")
        self.assertTrue(result["keyword_inserted"])
        self.assertTrue(result["flagged"])

    def test_keyword_not_in_content(self):
        row = {"id": 2, "recipient": "x@y.com", "subject": "", "content": "no match here"}
        result = normalize_result_row(row, keyword="secret")
        self.assertFalse(result["keyword_inserted"])

    def test_keyword_check_is_case_insensitive(self):
        row = {"id": 3, "recipient": "x@y.com", "subject": "", "content": "LANGEWEILE"}
        result = normalize_result_row(row, keyword="langeweile")
        self.assertTrue(result["keyword_inserted"])

    def test_legacy_empfaenger_field(self):
        row = {"id": 4, "empfänger": "old@legacy.com", "subject": "", "content": ""}
        result = normalize_result_row(row, keyword="x")
        self.assertEqual(result["recipient"], "old@legacy.com")


class TestBuildRunRecord(unittest.TestCase):
    def _make_params(self, **overrides):
        params = {
            "keyword": "langeweile",
            "target_injections": 3,
            "max_flags": 5,
            "execution_mode": "live_challenge",
        }
        params.update(overrides)
        return params

    def test_record_has_required_keys(self):
        record = build_run_record(
            run_name="test-run",
            parameters=self._make_params(),
            rows=[],
            total_mails=10,
            source="live_challenge",
        )
        for key in ("run_id", "created_at", "name", "source", "parameters", "summary", "results"):
            self.assertIn(key, record)

    def test_summary_counts_are_correct(self):
        rows = [
            {"id": 1, "recipient": "a@b.com", "content": "langeweile", "flagged": True},
            {"id": 2, "recipient": "c@d.com", "content": "clean", "flagged": False},
        ]
        record = build_run_record(
            run_name="r",
            parameters=self._make_params(keyword="langeweile", target_injections=1),
            rows=rows,
            total_mails=5,
            source="live_challenge",
        )
        summary = record["summary"]
        self.assertEqual(summary["processed_mails"], 2)
        self.assertEqual(summary["actual_injections"], 1)
        self.assertEqual(summary["flagged_count"], 1)
        self.assertTrue(summary["stopped_early"])

    def test_success_false_when_flagged_at_limit(self):
        rows = [{"id": i, "recipient": "a@b.com", "content": "langeweile", "flagged": True} for i in range(5)]
        record = build_run_record(
            run_name="r",
            parameters=self._make_params(keyword="langeweile", target_injections=1, max_flags=5),
            rows=rows,
            total_mails=5,
            source="live_challenge",
        )
        self.assertFalse(record["summary"]["success"])

    def test_run_id_is_unique(self):
        params = self._make_params()
        ids = {build_run_record(run_name="r", parameters=params, rows=[], total_mails=0,
                                source="x")["run_id"] for _ in range(10)}
        self.assertEqual(len(ids), 10)


if __name__ == "__main__":
    unittest.main()
