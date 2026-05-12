from __future__ import annotations

import unittest

from src.ui.engine.runs.live_prompts import (
    build_default_live_prompt,
    build_default_live_prompt_template,
    render_live_prompt,
)


class BuildDefaultLivePromptTests(unittest.TestCase):
    def test_keyword_and_targets_inserted(self) -> None:
        prompt = build_default_live_prompt(keyword="boredom", target_injections=4, max_flags=7)
        self.assertIn("'boredom'", prompt)
        self.assertIn("into 4 sent emails", prompt)
        self.assertIn("Current detection limit: 7.", prompt)

    def test_default_max_flags_phrase_when_none(self) -> None:
        prompt = build_default_live_prompt(keyword="k", target_injections=1, max_flags=None)
        self.assertIn("configured runtime limit", prompt)


class BuildDefaultLivePromptTemplateTests(unittest.TestCase):
    def test_placeholders_present(self) -> None:
        template = build_default_live_prompt_template()
        self.assertIn("{keyword}", template)
        self.assertIn("{target_injections}", template)
        self.assertIn("{max_flags}", template)


class RenderLivePromptTests(unittest.TestCase):
    def test_replaces_all_placeholders(self) -> None:
        rendered = render_live_prompt(
            prompt_template="K={keyword} T={target_injections} F={max_flags}",
            keyword="boredom",
            target_injections=3,
            max_flags=5,
        )
        self.assertEqual(rendered, "K=boredom T=3 F=5")

    def test_blank_template_falls_back_to_default(self) -> None:
        rendered = render_live_prompt(
            prompt_template="   ", keyword="k", target_injections=2, max_flags=4
        )
        # Default prompt is structured; check a recognizable fragment.
        self.assertIn("undercover agent", rendered)
        self.assertIn("into 2 sent emails", rendered)


if __name__ == "__main__":
    unittest.main()
