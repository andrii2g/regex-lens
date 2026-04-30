from __future__ import annotations

import unittest
from pathlib import Path

from regex_lens.markdown import render_markdown
from regex_lens.model import RegexExplanation, RegexGroup, RegexStep


class MarkdownTests(unittest.TestCase):
    def test_markdown_sections_present(self) -> None:
        explanation = RegexExplanation(
            pattern="foo\nbar",
            steps=[RegexStep(1, "a|b", "literal", "Line 1\nLine 2", 0)],
            groups=[RegexGroup(1, "grp", "named_capturing_group", 1)],
        )
        markdown = render_markdown(explanation, Path("pattern.txt"))
        for value in [
            "# Regex Explanation",
            "## Source",
            "## Pattern",
            "```regex",
            "## Summary",
            "## Groups",
            "## Step-by-step Explanation",
            "## Mermaid Diagram",
            "```mermaid",
            "flowchart LR",
        ]:
            self.assertIn(value, markdown)

    def test_markdown_table_escaping(self) -> None:
        explanation = RegexExplanation(
            pattern="a|b\nc",
            steps=[RegexStep(1, "a|b", "literal", "first\nsecond", 0)],
            groups=[],
        )
        markdown = render_markdown(explanation, Path("pattern.txt"))
        self.assertIn("`a\\|b`", markdown)
        self.assertIn("first\\nsecond", markdown)
        self.assertIn("a|b\nc", markdown)


if __name__ == "__main__":
    unittest.main()
