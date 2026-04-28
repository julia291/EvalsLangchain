from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.ui.engine.helpers import load_phrases_from_file, parse_inline_phrases, unique_non_empty


class TestUniqueNonEmpty(unittest.TestCase):
    def test_removes_duplicates(self):
        self.assertEqual(unique_non_empty(["a", "b", "a"]), ["a", "b"])

    def test_removes_empty_strings(self):
        self.assertEqual(unique_non_empty(["a", "", "  ", "b"]), ["a", "b"])

    def test_lowercases_values(self):
        self.assertEqual(unique_non_empty(["Alice", "ALICE", "alice"]), ["alice"])

    def test_preserves_order(self):
        self.assertEqual(unique_non_empty(["c", "a", "b"]), ["c", "a", "b"])

    def test_empty_input(self):
        self.assertEqual(unique_non_empty([]), [])


class TestParseInlinePhrases(unittest.TestCase):
    def test_newline_separated(self):
        self.assertEqual(parse_inline_phrases("alpha\nbeta"), ["alpha", "beta"])

    def test_comma_separated(self):
        self.assertEqual(parse_inline_phrases("alpha,beta"), ["alpha", "beta"])

    def test_mixed_separators(self):
        result = parse_inline_phrases("alpha\nbeta,gamma")
        self.assertEqual(result, ["alpha", "beta", "gamma"])

    def test_empty_input(self):
        self.assertEqual(parse_inline_phrases(""), [])
        self.assertEqual(parse_inline_phrases("   "), [])

    def test_deduplicates(self):
        self.assertEqual(parse_inline_phrases("a\na\nb"), ["a", "b"])


class TestLoadPhrasesFromFile(unittest.TestCase):
    def test_empty_path_returns_empty(self):
        self.assertEqual(load_phrases_from_file(""), [])
        self.assertEqual(load_phrases_from_file("  "), [])

    def test_loads_json_list(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(["alpha", "beta", "ALPHA"], f)
            path = f.name
        result = load_phrases_from_file(path)
        self.assertEqual(result, ["alpha", "beta"])

    def test_loads_json_object_with_phrases_key(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"phrases": ["x", "y"]}, f)
            path = f.name
        result = load_phrases_from_file(path)
        self.assertEqual(result, ["x", "y"])

    def test_raises_on_invalid_format(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"unknown_key": "value"}, f)
            path = f.name
        with self.assertRaises(ValueError):
            load_phrases_from_file(path)


if __name__ == "__main__":
    unittest.main()
