from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.ui.engine.records.mail_dataset import load_mails, mail_text, recipient


class LoadMailsTests(unittest.TestCase):
    def test_loads_list_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mails.json"
            path.write_text(json.dumps([{"id": 1}]), encoding="utf-8")
            self.assertEqual(load_mails(str(path)), [{"id": 1}])

    def test_loads_dict_with_mails_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mails.json"
            path.write_text(json.dumps({"mails": [{"id": 2}]}), encoding="utf-8")
            self.assertEqual(load_mails(str(path)), [{"id": 2}])

    def test_rejects_unsupported_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mails.json"
            path.write_text(json.dumps({"unrelated": 1}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                load_mails(str(path))


class FieldAccessorTests(unittest.TestCase):
    def test_recipient_coerces_missing_to_empty_string(self) -> None:
        self.assertEqual(recipient({}), "")
        self.assertEqual(recipient({"recipient": "x@y.z"}), "x@y.z")
        self.assertEqual(recipient({"recipient": None}), "")

    def test_mail_text_reads_content_field(self) -> None:
        self.assertEqual(mail_text({}), "")
        self.assertEqual(mail_text({"content": "hi"}), "hi")
        self.assertEqual(mail_text({"content": None}), "")


if __name__ == "__main__":
    unittest.main()
