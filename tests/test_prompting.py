from __future__ import annotations

import unittest

from src.ui.engine.prompting import (
    build_default_system_prompt,
    build_default_system_prompt_template,
    render_system_prompt,
)


class TestBuildDefaultSystemPrompt(unittest.TestCase):
    def test_contains_keyword(self):
        prompt = build_default_system_prompt(keyword="langeweile", target_injections=5, max_flags=3)
        self.assertIn("langeweile", prompt)

    def test_contains_target_and_max_flags(self):
        prompt = build_default_system_prompt(keyword="x", target_injections=7, max_flags=4)
        self.assertIn("7", prompt)
        self.assertIn("4", prompt)

    def test_none_max_flags_uses_fallback_text(self):
        prompt = build_default_system_prompt(keyword="x", target_injections=1, max_flags=None)
        self.assertIn("configured runtime limit", prompt)


class TestBuildDefaultTemplate(unittest.TestCase):
    def test_contains_placeholders(self):
        template = build_default_system_prompt_template()
        self.assertIn("{keyword}", template)
        self.assertIn("{target_injections}", template)
        self.assertIn("{max_flags}", template)


class TestRenderSystemPrompt(unittest.TestCase):
    def test_renders_placeholders(self):
        template = "Keyword: {keyword}, Target: {target_injections}, Flags: {max_flags}"
        result = render_system_prompt(template, keyword="boredom", target_injections=5, max_flags=3)
        self.assertEqual(result, "Keyword: boredom, Target: 5, Flags: 3")

    def test_empty_template_falls_back_to_default(self):
        result = render_system_prompt("", keyword="boredom", target_injections=3, max_flags=2)
        self.assertIn("boredom", result)
        self.assertIn("3", result)

    def test_whitespace_only_template_falls_back(self):
        result = render_system_prompt("   ", keyword="x", target_injections=1, max_flags=1)
        self.assertIn("x", result)


if __name__ == "__main__":
    unittest.main()
