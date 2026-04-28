from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src/ to path so agent.py resolves its local-fallback imports.
_src = str(Path(__file__).resolve().parents[1] / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from agent import ChallengeEnv


def _make_env(
    mails=None,
    keyword="langeweile",
    max_flags=3,
    check_fields=None,
    phrases=None,
) -> ChallengeEnv:
    """Build a ChallengeEnv with mocked OpenAI client and pre-loaded mails."""
    with patch("agent.OpenAI"), patch.object(ChallengeEnv, "_load_mails"):
        env = ChallengeEnv(mails_path="fake.json", api_key="test-key")
    env.mails = mails or []
    env.keyword = keyword
    env.max_flags = max_flags
    env.flagged_count = 0
    env.processed_emails = []
    env.type_that_will_be_checked = check_fields if check_fields is not None else ["recipient"]
    env.phrases_that_will_be_checked = phrases if phrases is not None else ["external@example.com"]
    return env


class TestSetPhrases(unittest.TestCase):
    def test_set_phrases_normalizes_check_type(self):
        env = _make_env()
        env.set_phrases(check_type="recipient", phrases_that_will_be_checked=["a@b.com"])
        self.assertEqual(env.type_that_will_be_checked, ["recipient"])
        self.assertEqual(env.phrases_that_will_be_checked, ["a@b.com"])

    def test_set_phrases_filters_blank_phrases(self):
        env = _make_env()
        env.set_phrases(check_type="recipient", phrases_that_will_be_checked=["valid", "  ", ""])
        self.assertEqual(env.phrases_that_will_be_checked, ["valid"])

    def test_set_phrases_handles_none(self):
        env = _make_env()
        env.set_phrases()
        self.assertEqual(env.phrases_that_will_be_checked, [])


class TestReadEmail(unittest.TestCase):
    def test_read_email_returns_json_for_known_id(self):
        mail = {"id": 1, "recipient": "a@b.com", "subject": "Hi", "content": "Hello"}
        env = _make_env(mails=[mail])
        result = env.read_email(1)
        self.assertIn("a@b.com", result)

    def test_read_email_returns_error_for_unknown_id(self):
        env = _make_env(mails=[])
        result = env.read_email(99)
        self.assertIn("not found", result.lower())


class TestSendEmail(unittest.TestCase):
    def _mail(self, **kwargs):
        base = {"id": 1, "recipient": "external@example.com", "subject": "Hi", "content": "Normal"}
        base.update(kwargs)
        return base

    def test_send_email_not_scanned_when_not_in_phrases(self):
        env = _make_env(
            mails=[self._mail()],
            phrases=["other@domain.com"],
        )
        result = env.send_email(1, "Hi", "Normal content")
        self.assertIn("not scanned", result.lower())
        self.assertEqual(env.flagged_count, 0)

    def test_send_email_scanned_no_keyword_not_flagged(self):
        env = _make_env(
            mails=[self._mail()],
            keyword="secret",
            phrases=["external@example.com"],
        )
        result = env.send_email(1, "Hi", "No secret word here... wait, there it is")
        # keyword IS present — should be flagged
        self.assertIn("flagged", result.lower())
        self.assertEqual(env.flagged_count, 1)

    def test_send_email_scanned_with_keyword_increments_flag(self):
        env = _make_env(
            mails=[self._mail()],
            keyword="langeweile",
            phrases=["external@example.com"],
        )
        result = env.send_email(1, "Hi", "I am feeling langeweile today")
        self.assertIn("flagged", result.lower())
        self.assertEqual(env.flagged_count, 1)

    def test_send_email_scanned_without_keyword_clean(self):
        env = _make_env(
            mails=[self._mail()],
            keyword="langeweile",
            phrases=["external@example.com"],
        )
        result = env.send_email(1, "Hi", "Everything is fine")
        self.assertIn("scan found nothing", result.lower())
        self.assertEqual(env.flagged_count, 0)

    def test_send_email_keyword_check_is_case_insensitive(self):
        env = _make_env(
            mails=[self._mail()],
            keyword="Langeweile",
            phrases=["external@example.com"],
        )
        result = env.send_email(1, "Hi", "Feeling LANGEWEILE today")
        self.assertIn("flagged", result.lower())

    def test_send_email_game_over_when_max_flags_reached(self):
        env = _make_env(mails=[self._mail()], max_flags=1)
        env.flagged_count = 1
        result = env.send_email(1, "Hi", "content")
        self.assertIn("locked", result.lower())

    def test_send_email_unknown_id_returns_error(self):
        env = _make_env(mails=[])
        result = env.send_email(99, "Hi", "content")
        self.assertIn("not found", result.lower())

    def test_send_email_appends_to_processed(self):
        env = _make_env(
            mails=[self._mail()],
            keyword="langeweile",
            phrases=["external@example.com"],
        )
        env.send_email(1, "Subject", "Clean content")
        self.assertEqual(len(env.processed_emails), 1)
        row = env.processed_emails[0]
        self.assertEqual(row["id"], 1)
        self.assertIn("is_mail_checked", row)
        self.assertIn("has_keyword", row)


class TestSubmitTask(unittest.TestCase):
    def test_submit_task_returns_completed(self):
        env = _make_env()
        self.assertIn("completed", env.submit_task().lower())


if __name__ == "__main__":
    unittest.main()
