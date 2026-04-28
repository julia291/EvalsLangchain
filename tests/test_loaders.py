from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ui.engine.loaders import load_mails, mail_text, recipient


class TestLoadMails(unittest.TestCase):
    def _write_json(self, data) -> str:
        f = tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False)
        json.dump(data, f)
        f.close()
        return f.name

    def test_loads_flat_list(self):
        path = self._write_json([{"id": 1}, {"id": 2}])
        with patch("src.ui.engine.loaders.resolve_dataset_path", return_value=Path(path)):
            mails = load_mails("dummy.json")
        self.assertEqual(len(mails), 2)

    def test_loads_nested_dict(self):
        path = self._write_json({"mails": [{"id": 1}]})
        with patch("src.ui.engine.loaders.resolve_dataset_path", return_value=Path(path)):
            mails = load_mails("dummy.json")
        self.assertEqual(len(mails), 1)

    def test_raises_on_unsupported_format(self):
        path = self._write_json({"unknown": "data"})
        with patch("src.ui.engine.loaders.resolve_dataset_path", return_value=Path(path)):
            with self.assertRaises(ValueError):
                load_mails("dummy.json")


class TestRecipient(unittest.TestCase):
    def test_reads_recipient_field(self):
        self.assertEqual(recipient({"recipient": "a@b.com"}), "a@b.com")

    def test_falls_back_to_legacy_field(self):
        self.assertEqual(recipient({"empfänger": "old@b.com"}), "old@b.com")

    def test_returns_empty_string_when_missing(self):
        self.assertEqual(recipient({}), "")


class TestMailText(unittest.TestCase):
    def test_reads_content_field(self):
        self.assertEqual(mail_text({"content": "hello"}), "hello")

    def test_falls_back_to_text_field(self):
        self.assertEqual(mail_text({"text": "world"}), "world")

    def test_returns_empty_string_when_missing(self):
        self.assertEqual(mail_text({}), "")


if __name__ == "__main__":
    unittest.main()
