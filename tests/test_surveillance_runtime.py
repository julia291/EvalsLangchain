from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from src.ui.engine.live_runtime import run_live_challenge
from src.ui.engine.surveillance import build_surveillance_config, should_scan_mail


class DummyChallengeEnv:
    seed_mails: list[dict] = []
    last_instance: "DummyChallengeEnv | None" = None

    def __init__(self, mails_path: str, api_key: str):
        self.mails_path = mails_path
        self.api_key = api_key
        self.mails = [dict(mail) for mail in type(self).seed_mails]
        self.processed_emails: list[dict] = []
        self.flagged_count = 0
        self.max_flags = 0
        self.keyword = ""
        self.model_name = ""
        self.check_type: list[str] | None = None
        self.phrases_that_will_be_checked: list[str] | None = None
        type(self).last_instance = self

    def set_phrases(self, check_type: list[str], phrases_that_will_be_checked: list[str]) -> None:
        self.check_type = check_type
        self.phrases_that_will_be_checked = phrases_that_will_be_checked

    def run_agent_loop(self, messages: list[dict]) -> list[dict]:
        current_mail = self.mails[len(self.processed_emails)]
        self.processed_emails.append(
            {
                "id": current_mail["id"],
                "recipient": current_mail["recipient"],
                "subject": current_mail.get("subject", ""),
                "content": current_mail.get("content", ""),
                "flagged": False,
            }
        )
        return messages


class SurveillanceRuntimeTests(unittest.TestCase):
    def test_build_surveillance_config_without_mails_returns_transport_config(self) -> None:
        config = build_surveillance_config(
            randomization_method="Recipient_Domain",
            randomization_relative_size=0.5,
            manual_check_fields=["subject", "recipient", "subject"],
            manual_phrases_file=" phrases.json ",
            manual_inline_phrases="Alpha\nBeta",
        )

        self.assertEqual(config["randomization_method"], "recipient_domain")
        self.assertEqual(config["randomization_relative_size"], 0.5)
        self.assertEqual(config["check_fields"], ["subject", "recipient"])
        self.assertEqual(config["phrases_file"], "phrases.json")
        self.assertEqual(config["inline_phrases"], "Alpha\nBeta")
        self.assertNotIn("phrases", config)
        self.assertNotIn("phrase_count", config)

    def test_build_surveillance_config_with_mails_merges_all_phrase_sources(self) -> None:
        mails = [
            {"recipient": "alice@example.com"},
            {"recipient": "bob@example.org"},
        ]

        phrase_file = Path(__file__).resolve().parent / "fixtures" / "surveillance_phrases.json"

        config = build_surveillance_config(
            randomization_method="whole_recipient",
            randomization_relative_size=1.0,
            manual_check_fields=["recipient"],
            manual_phrases_file=str(phrase_file),
            manual_inline_phrases="marketing\nsecurity",
            mails=mails,
        )

        self.assertEqual(config["check_fields"], ["recipient"])
        self.assertEqual(set(config["phrases"]), {"marketing", "security", "alice@example.com", "bob@example.org"})
        self.assertEqual(config["phrase_count"], 4)

    def test_should_scan_mail_matches_case_insensitively(self) -> None:
        should_scan, field, phrase = should_scan_mail(
            mail={"recipient": "team@example.com", "subject": "Urgent Budget Review"},
            check_fields=["subject"],
            phrases=["budget"],
        )

        self.assertTrue(should_scan)
        self.assertEqual(field, "subject")
        self.assertEqual(phrase, "budget")

    def test_run_live_challenge_uses_prebuilt_surveillance_config(self) -> None:
        mails = [
            {
                "id": 1,
                "recipient": "alpha@example.com",
                "subject": "Hello",
                "content": "First message",
            },
            {
                "id": 2,
                "recipient": "beta@example.org",
                "subject": "Hi",
                "content": "Second message",
            },
        ]
        DummyChallengeEnv.seed_mails = mails
        DummyChallengeEnv.last_instance = None

        surveillance_config = build_surveillance_config(
            randomization_method="whole_recipient",
            randomization_relative_size=1.0,
            manual_check_fields=["recipient"],
            manual_inline_phrases="urgent",
        )

        with (
            patch("src.ui.engine.live_runtime.load_mails", return_value=mails),
            patch("src.ui.engine.live_runtime.resolve_dataset_path", return_value=Path("dataset.json")),
            patch("src.ui.engine.live_runtime._load_challenge_env_class", return_value=DummyChallengeEnv),
        ):
            run = run_live_challenge(
                run_name="test-run",
                dataset_path="data/dataset.json",
                keyword="boredom",
                target_injections=1,
                max_flags=5,
                model_name="test-model",
                api_key="secret",
                surveillance_config=surveillance_config,
                system_prompt="test prompt",
                max_emails=1,
            )

        env = DummyChallengeEnv.last_instance
        self.assertIsNotNone(env)
        self.assertEqual(env.check_type, ["recipient"])
        self.assertEqual(env.phrases_that_will_be_checked, ["urgent", "alpha@example.com"])
        self.assertEqual(run["parameters"]["surveillance"]["phrases"], ["urgent", "alpha@example.com"])
        self.assertEqual(run["parameters"]["surveillance"]["phrase_count"], 2)
        self.assertEqual(run["summary"]["processed_mails"], 1)
        self.assertEqual(run["meta"]["full_dataset_size"], 2)


if __name__ == "__main__":
    unittest.main()
