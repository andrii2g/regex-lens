from __future__ import annotations

import unittest

from regex_lens.mermaid import render_mermaid
from regex_lens.model import RegexExplanation, RegexStep


class MermaidTests(unittest.TestCase):
    def test_mermaid_structure(self) -> None:
        explanation = RegexExplanation(
            pattern="foo",
            steps=[
                RegexStep(1, 'a"b', "literal", "line 1\nline 2", 0),
                RegexStep(2, "c", "literal", "plain", 0),
            ],
            groups=[],
        )
        mermaid = render_mermaid(explanation)
        self.assertTrue(mermaid.startswith("flowchart LR"))
        self.assertIn("N0([Start])", mermaid)
        self.assertIn("([End])", mermaid)
        self.assertIn('a\\"b', mermaid)
        self.assertIn("<br/>", mermaid)
        self.assertIn("N0 --> N1", mermaid)
        self.assertIn("N1 --> N2", mermaid)


if __name__ == "__main__":
    unittest.main()
