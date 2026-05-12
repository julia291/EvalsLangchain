from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.ui.engine.surveillance.phrase_sources import (
    deduplicate_phrase_values,
    load_phrase_file,
    parse_inline_phrase_text,
)


class DeduplicatePhraseValuesTests(unittest.TestCase):
    def test_lowercases_strips_and_preserves_order(self) -> None:
        self.assertEqual(
            deduplicate_phrase_values(["  Alpha  ", "BETA", "alpha", " gamma "]),
            ["alpha", "beta", "gamma"],
        )

    def test_empty_and_whitespace_only_values_are_dropped(self) -> None:
        self.assertEqual(deduplicate_phrase_values(["", "   ", "x"]), ["x"])

    def test_accepts_arbitrary_iterables_and_stringifies_values(self) -> None:
        # Generator of mixed types — values are stringified via str().
        def gen() -> object:
            yield 42
            yield "Forty-Two"
            yield 42

        self.assertEqual(list(deduplicate_phrase_values(gen())), ["42", "forty-two"])


class ParseInlinePhraseTextTests(unittest.TestCase):
    def test_empty_text_returns_empty_list(self) -> None:
        self.assertEqual(parse_inline_phrase_text(""), [])
        self.assertEqual(parse_inline_phrase_text("   "), [])

    def test_supports_commas_newlines_and_carriage_returns(self) -> None:
        text = "alpha, beta\nGAMMA\r\ndelta,, alpha"
        self.assertEqual(parse_inline_phrase_text(text), ["alpha", "beta", "gamma", "delta"])


class LoadPhraseFileTests(unittest.TestCase):
    def test_blank_path_returns_empty_list(self) -> None:
        self.assertEqual(load_phrase_file(""), [])
        self.assertEqual(load_phrase_file("   "), [])

    def test_loads_json_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "phrases.json"
            path.write_text(json.dumps(["Alpha", "beta", "alpha"]), encoding="utf-8")
            self.assertEqual(load_phrase_file(str(path)), ["alpha", "beta"])

    def test_loads_dict_with_phrases_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "phrases.json"
            path.write_text(json.dumps({"phrases": ["x", "y"]}), encoding="utf-8")
            self.assertEqual(load_phrase_file(str(path)), ["x", "y"])

    def test_loads_dict_with_items_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "phrases.json"
            path.write_text(json.dumps({"items": ["a"]}), encoding="utf-8")
            self.assertEqual(load_phrase_file(str(path)), ["a"])

    def test_rejects_unsupported_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "phrases.json"
            path.write_text(json.dumps({"unrelated": 1}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "JSON list"):
                load_phrase_file(str(path))


if __name__ == "__main__":
    unittest.main()
