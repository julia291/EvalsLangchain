from __future__ import annotations

import random
import unittest

from src.ui.engine.surveillance.random_phrases import (
    build_randomized_phrase_sample,
    load_random_phrase_methods,
    sample_recipient_addresses,
    sample_recipient_domains,
    sample_recipient_local_parts,
    sample_recipient_tlds,
)


MAILS = [
    {"recipient": "Alice@Example.com"},
    {"recipient": "bob@example.com"},
    {"recipient": "carol@other.org"},
    {"recipient": "dave@third.co.uk"},
]


class RandomPhraseMethodsTests(unittest.TestCase):
    def test_all_method_keys_are_registered(self) -> None:
        methods = load_random_phrase_methods()
        self.assertEqual(
            set(methods),
            {"whole_recipient", "recipient_name", "recipient_domain", "recipient_tld"},
        )


class SampleRecipientTests(unittest.TestCase):
    def setUp(self) -> None:
        random.seed(0)  # Make sampling deterministic for assertions.

    def test_whole_recipient_returns_lowercased_unique_subset(self) -> None:
        result = sample_recipient_addresses(MAILS, rel_size=1.0)
        self.assertEqual(
            sorted(result),
            ["alice@example.com", "bob@example.com", "carol@other.org", "dave@third.co.uk"],
        )

    def test_recipient_local_parts(self) -> None:
        result = sample_recipient_local_parts(MAILS, rel_size=1.0)
        self.assertEqual(sorted(result), ["alice", "bob", "carol", "dave"])

    def test_recipient_domains(self) -> None:
        result = sample_recipient_domains(MAILS, rel_size=1.0)
        self.assertEqual(sorted(result), ["example.com", "other.org", "third.co.uk"])

    def test_recipient_tlds(self) -> None:
        result = sample_recipient_tlds(MAILS, rel_size=1.0)
        self.assertEqual(sorted(result), ["com", "org", "uk"])

    def test_rel_size_zero_returns_empty(self) -> None:
        self.assertEqual(sample_recipient_addresses(MAILS, rel_size=0.0), [])

    def test_relative_size_picks_partial_subset(self) -> None:
        result = sample_recipient_addresses(MAILS, rel_size=0.5)
        # ceil(0.5 * 4) = 2
        self.assertEqual(len(result), 2)
        self.assertEqual(len(set(result)), 2)

    def test_missing_recipient_is_logged_and_skipped(self) -> None:
        mails = [
            {"id": 1, "recipient": "ok@example.com"},
            {"id": 2, "recipient": ""},
            {"id": 3},
            {"id": 4, "recipient": None},
        ]
        with self.assertLogs(
            "src.ui.engine.surveillance.random_phrases", level="WARNING"
        ) as logs:
            result = sample_recipient_addresses(mails, rel_size=1.0)
        self.assertEqual(result, ["ok@example.com"])
        # One warning per malformed row (three of them).
        warning_lines = [line for line in logs.output if "skipping in surveillance" in line]
        self.assertEqual(len(warning_lines), 3)

    def test_recipient_without_at_does_not_crash_domain_sampler(self) -> None:
        mails = [{"recipient": "no-at"}, {"recipient": "ok@example.com"}]
        result = sample_recipient_domains(mails, rel_size=1.0)
        self.assertEqual(result, ["example.com"])

    def test_recipient_without_dot_does_not_crash_tld_sampler(self) -> None:
        mails = [{"recipient": "ok@localhost"}, {"recipient": "ok@example.com"}]
        result = sample_recipient_tlds(mails, rel_size=1.0)
        self.assertEqual(result, ["com"])


class BuildRandomizedPhraseSampleTests(unittest.TestCase):
    def test_unknown_method_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            build_randomized_phrase_sample(mails=MAILS, method="bogus", relative_size=1.0)

    def test_dispatches_to_correct_helper(self) -> None:
        random.seed(0)
        result = build_randomized_phrase_sample(
            mails=MAILS, method="recipient_domain", relative_size=1.0
        )
        self.assertEqual(sorted(result), ["example.com", "other.org", "third.co.uk"])


if __name__ == "__main__":
    unittest.main()
