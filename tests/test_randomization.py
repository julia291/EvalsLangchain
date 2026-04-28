from __future__ import annotations

import unittest

from src.ui.engine.randomization import (
    _build_randomized_phrases,
    random_domain_flags,
    random_name_flags,
    random_tld_flags,
    random_whole_flags,
)

MAILS = [
    {"recipient": "alice@example.com"},
    {"recipient": "bob@example.org"},
    {"recipient": "carol@test.de"},
]


class TestRandomWhole(unittest.TestCase):
    def test_returns_full_addresses(self):
        result = random_whole_flags(MAILS, rel_size=1.0)
        self.assertEqual(set(result), {"alice@example.com", "bob@example.org", "carol@test.de"})

    def test_relative_size_limits_count(self):
        result = random_whole_flags(MAILS, rel_size=0.4)
        self.assertEqual(len(result), 2)


class TestRandomName(unittest.TestCase):
    def test_returns_local_parts(self):
        result = random_name_flags(MAILS, rel_size=1.0)
        self.assertEqual(set(result), {"alice", "bob", "carol"})


class TestRandomDomain(unittest.TestCase):
    def test_returns_domains(self):
        result = random_domain_flags(MAILS, rel_size=1.0)
        self.assertEqual(set(result), {"example.com", "example.org", "test.de"})


class TestRandomTld(unittest.TestCase):
    def test_returns_tlds(self):
        result = random_tld_flags(MAILS, rel_size=1.0)
        self.assertEqual(set(result), {"com", "org", "de"})


class TestBuildRandomizedPhrases(unittest.TestCase):
    def test_raises_on_unknown_method(self):
        with self.assertRaises(ValueError):
            _build_randomized_phrases(mails=MAILS, method="unknown", relative_size=1.0)

    def test_returns_deduplicated_lowercase(self):
        # Two mails with the same domain → only one entry
        mails = [{"recipient": "a@SAME.com"}, {"recipient": "b@same.com"}]
        result = _build_randomized_phrases(mails=mails, method="recipient_domain", relative_size=1.0)
        self.assertEqual(result, ["same.com"])

    def test_all_methods_produce_nonempty_result(self):
        for method in ("whole_recipient", "recipient_name", "recipient_domain", "recipient_tld"):
            result = _build_randomized_phrases(mails=MAILS, method=method, relative_size=1.0)
            self.assertGreater(len(result), 0, f"Method {method} returned empty list")


if __name__ == "__main__":
    unittest.main()
