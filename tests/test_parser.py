from __future__ import annotations

import unittest

from regex_lens.parser import parse_regex


class ParserTests(unittest.TestCase):
    def test_date_regex(self) -> None:
        explanation = parse_regex(r"^\d{4}-\d{2}-\d{2}$")
        tokens = [step.token for step in explanation.steps]
        self.assertIn("^", tokens)
        self.assertIn(r"\d", tokens)
        self.assertIn("{4}", tokens)
        self.assertIn("-", tokens)
        self.assertIn("$", tokens)

    def test_extended_anchors_shortcuts_and_dot(self) -> None:
        explanation = parse_regex(r"\A\b\B\D\w\W\s\S.\Z\z")
        kinds_by_token = {step.token: step.kind for step in explanation.steps}
        for token in [r"\A", r"\b", r"\B", r"\Z", r"\z"]:
            self.assertEqual(kinds_by_token[token], "anchor")
        for token in [r"\D", r"\w", r"\W", r"\s", r"\S"]:
            self.assertEqual(kinds_by_token[token], "character_shortcut")
        self.assertEqual(kinds_by_token["."], "wildcard")

    def test_named_group_syntaxes(self) -> None:
        explanation = parse_regex(r"(?P<date>\d{4})(?<level>INFO)(?'message'.*)")
        self.assertEqual(len(explanation.groups), 3)
        self.assertEqual([group.name for group in explanation.groups], ["date", "level", "message"])
        self.assertTrue(all(group.kind == "named_capturing_group" for group in explanation.groups))
        self.assertIn("group_end", [step.kind for step in explanation.steps])
        self.assertEqual(explanation.steps[-1].depth, 1)

    def test_special_groups(self) -> None:
        explanation = parse_regex(r"(?:abc)(?=def)(?!ghi)(?<=jkl)(?<!mno)(?>pqr)")
        kinds = [group.kind for group in explanation.groups]
        for kind in [
            "non_capturing_group",
            "positive_lookahead",
            "negative_lookahead",
            "positive_lookbehind",
            "negative_lookbehind",
            "atomic_group",
        ]:
            self.assertIn(kind, kinds)

    def test_inline_flag_is_not_group(self) -> None:
        explanation = parse_regex(r"(?i)^abc$")
        self.assertEqual(explanation.steps[0].kind, "inline_flags")
        self.assertEqual(explanation.steps[0].token, "(?i)")
        self.assertEqual(explanation.groups, [])
        self.assertNotIn("group_end", [step.kind for step in explanation.steps[:1]])
        anchors = [step for step in explanation.steps if step.token in {"^", "$"}]
        self.assertTrue(all(step.depth == 0 for step in anchors))

    def test_scoped_inline_flags_group(self) -> None:
        explanation = parse_regex(r"(?imx:abc)")
        self.assertEqual(len(explanation.groups), 1)
        self.assertEqual(explanation.groups[0].kind, "scoped_flags_group")
        self.assertEqual(explanation.groups[0].depth, 1)
        self.assertIn("group_end", [step.kind for step in explanation.steps])
        self.assertEqual(explanation.steps[-1].kind, "group_end")

    def test_alternation_and_literal_aggregation(self) -> None:
        explanation = parse_regex(r"INFO|WARN|ERROR")
        literals = [step.token for step in explanation.steps if step.kind == "literal"]
        self.assertEqual(literals, ["INFO", "WARN", "ERROR"])
        self.assertEqual(sum(step.kind == "alternation" for step in explanation.steps), 2)

    def test_character_classes(self) -> None:
        explanation = parse_regex(r"^[A-Z][^,]+$")
        classes = [step.token for step in explanation.steps if step.kind == "character_class"]
        self.assertIn("[A-Z]", classes)
        self.assertIn("[^,]", classes)
        self.assertIn("+", [step.token for step in explanation.steps if step.kind == "quantifier"])

    def test_escaped_whitespace_and_literals(self) -> None:
        explanation = parse_regex(r"\n\r\t\.\+\(\)")
        tokens = {step.token: step.kind for step in explanation.steps}
        for token in [r"\n", r"\r", r"\t"]:
            self.assertEqual(tokens[token], "escaped_whitespace")
        for token in [r"\.", r"\+", r"\(", r"\)"]:
            self.assertEqual(tokens[token], "escaped_literal")

    def test_lazy_and_possessive_quantifiers(self) -> None:
        explanation = parse_regex(r"a*?b++c{2,4}?d{3}+e??f?+")
        quantifiers = [step.token for step in explanation.steps if step.kind == "quantifier"]
        for token in ["*?", "++", "{2,4}?", "{3}+", "??", "?+"]:
            self.assertIn(token, quantifiers)

    def test_group_closing_depth_behavior(self) -> None:
        explanation = parse_regex(r"(a(?:b)c)")
        self.assertEqual(explanation.groups[0].depth, 1)
        self.assertEqual(explanation.groups[1].depth, 2)
        self.assertTrue(all(step.depth >= 0 for step in explanation.steps))

    def test_unmatched_closing_parenthesis(self) -> None:
        explanation = parse_regex(r"abc)")
        self.assertIn("unmatched_closing_parenthesis", [step.kind for step in explanation.steps])
        self.assertTrue(all(step.depth >= 0 for step in explanation.steps))

    def test_multiline_pattern_preservation(self) -> None:
        pattern = "(?x)\n^ foo\n$"
        explanation = parse_regex(pattern)
        self.assertEqual(explanation.pattern, pattern)
        self.assertEqual(explanation.steps[0].token, "(?x)")

    def test_unknown_special_group_fallback(self) -> None:
        explanation = parse_regex(r"(?foo)abc(?#comment)")
        self.assertEqual([group.kind for group in explanation.groups], ["unknown_special_group", "unknown_special_group"])
        start_tokens = [step.token for step in explanation.steps if step.kind == "group_start"]
        self.assertIn("(?foo", start_tokens)
        self.assertIn("(?#comment", start_tokens)
        self.assertTrue(all(group.kind != "capturing_group" for group in explanation.groups))
        self.assertTrue(all(step.depth >= 0 for step in explanation.steps))

    def test_unterminated_character_class_falls_back_to_literal(self) -> None:
        explanation = parse_regex("abc[def")
        self.assertNotIn("character_class", [step.kind for step in explanation.steps])
        literals = [step.token for step in explanation.steps if step.kind == "literal"]
        self.assertIn("[", literals)
        self.assertIn("def", literals)

    def test_invalid_braced_sequences_fall_back_to_literal(self) -> None:
        explanation = parse_regex(r"a{,3}b{2,x}c{2,,3}d{abc}e{4")
        quantifiers = [step.token for step in explanation.steps if step.kind == "quantifier"]
        for token in ["{,3}", "{2,x}", "{2,,3}", "{abc}"]:
            self.assertNotIn(token, quantifiers)
        literals = [step.token for step in explanation.steps if step.kind == "literal"]
        for token in ["{,3}", "{2,x}", "{2,,3}", "{abc}", "{"]:
            self.assertIn(token, literals)


if __name__ == "__main__":
    unittest.main()
