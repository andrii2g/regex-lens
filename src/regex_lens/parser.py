from __future__ import annotations

from .model import RegexExplanation, RegexGroup, RegexStep


ANCHOR_DESCRIPTIONS = {
    "^": "Matches the start of the string or line, depending on regex mode.",
    "$": "Matches the end of the string or line, depending on regex mode.",
    r"\A": "Matches the start of the string.",
    r"\Z": "Matches the end of the string.",
    r"\z": "Matches the absolute end of the string in engines that support it.",
    r"\b": "Matches a word boundary.",
    r"\B": "Matches a non-word boundary.",
}

SHORTCUT_DESCRIPTIONS = {
    r"\d": "Matches a digit character.",
    r"\D": "Matches a non-digit character.",
    r"\w": "Matches a word character.",
    r"\W": "Matches a non-word character.",
    r"\s": "Matches a whitespace character.",
    r"\S": "Matches a non-whitespace character.",
}

ESCAPED_WHITESPACE_DESCRIPTIONS = {
    r"\n": "Matches a newline character.",
    r"\r": "Matches a carriage return character.",
    r"\t": "Matches a tab character.",
}

INLINE_FLAG_CHARS = set("AaiLmnsux")


def parse_regex(pattern: str) -> RegexExplanation:
    steps: list[RegexStep] = []
    groups: list[RegexGroup] = []
    group_stack: list[str] = []
    depth = 0
    capture_count = 0
    i = 0

    def add_step(token: str, kind: str, description: str, step_depth: int | None = None) -> None:
        steps.append(
            RegexStep(
                index=len(steps) + 1,
                token=token,
                kind=kind,
                description=description,
                depth=depth if step_depth is None else step_depth,
            )
        )

    def add_group(name: str | None, kind: str, group_depth: int) -> None:
        groups.append(
            RegexGroup(
                index=len(groups) + 1,
                name=name,
                kind=kind,
                depth=group_depth,
            )
        )

    def is_escaped(index: int) -> bool:
        backslashes = 0
        j = index - 1
        while j >= 0 and pattern[j] == "\\":
            backslashes += 1
            j -= 1
        return backslashes % 2 == 1

    def parse_character_class(start: int) -> tuple[str, int] | None:
        j = start + 1
        while j < len(pattern):
            if pattern[j] == "]" and not is_escaped(j):
                return pattern[start : j + 1], j + 1
            j += 1
        return None

    def parse_braced_quantifier(start: int) -> tuple[str, int] | None:
        if pattern[start] != "{":
            return None
        end = pattern.find("}", start + 1)
        if end == -1:
            return None
        token = pattern[start : end + 1]
        inner = token[1:-1]
        if not inner:
            return None
        if inner.count(",") > 1:
            return None
        if "," in inner:
            left, right = inner.split(",", 1)
            if not left.isdigit():
                return None
            if right and not right.isdigit():
                return None
        elif not inner.isdigit():
            return None
        suffix = ""
        next_index = end + 1
        if next_index < len(pattern) and pattern[next_index] in "?+":
            suffix = pattern[next_index]
            next_index += 1
        return token + suffix, next_index

    def parse_invalid_braced_literal(start: int) -> tuple[str, int]:
        end = pattern.find("}", start + 1)
        if end == -1:
            return "{", start + 1
        return pattern[start : end + 1], end + 1

    def parse_inline_flags(spec: str) -> bool:
        if not spec:
            return False
        parts = spec.split("-")
        if len(parts) > 2:
            return False
        if len(parts) == 1:
            return all(ch in INLINE_FLAG_CHARS for ch in parts[0])
        left, right = parts
        if left and not all(ch in INLINE_FLAG_CHARS for ch in left):
            return False
        if right and not all(ch in INLINE_FLAG_CHARS for ch in right):
            return False
        return bool(left or right)

    def parse_unknown_special_group(start: int) -> tuple[str, int]:
        j = start + 2
        while j < len(pattern):
            if pattern[j] in ":)" and not is_escaped(j):
                if pattern[j] == ":":
                    return pattern[start : j + 1], j + 1
                return pattern[start:j], j
            j += 1
        return pattern[start:], len(pattern)

    def group_description(kind: str, token: str, name: str | None) -> str:
        descriptions = {
            "capturing_group": "Starts a capturing group.",
            "non_capturing_group": "Starts a non-capturing group.",
            "positive_lookahead": "Starts a positive lookahead assertion.",
            "negative_lookahead": "Starts a negative lookahead assertion.",
            "positive_lookbehind": "Starts a positive lookbehind assertion.",
            "negative_lookbehind": "Starts a negative lookbehind assertion.",
            "atomic_group": "Starts an atomic group.",
            "scoped_flags_group": "Starts a scoped inline-flags group.",
            "unknown_special_group": "Starts an unrecognized special regex group.",
        }
        if kind == "named_capturing_group":
            return f"Starts a named capturing group called `{name}`."
        return descriptions[kind]

    def literal_description(token: str) -> str:
        return f"Matches the literal text `{token}`."

    def escaped_literal_description(token: str) -> str:
        literal_char = token[1:] if len(token) > 1 else token
        return f"Matches the literal character `{literal_char}`."

    while i < len(pattern):
        char = pattern[i]

        if char == "[" and not is_escaped(i):
            parsed_class = parse_character_class(i)
            if parsed_class is None:
                add_step("[", "literal", literal_description("["))
                i += 1
                continue
            token, next_i = parsed_class
            if token.startswith("[^"):
                description = f"Matches one character not in the character class `{token}`."
            else:
                description = f"Matches one character from the character class `{token}`."
            add_step(token, "character_class", description)
            i = next_i
            continue

        if char == "(" and not is_escaped(i):
            if i + 1 < len(pattern) and pattern[i + 1] == "?":
                marker_index = i + 2
                end_paren = marker_index
                end_colon = marker_index
                while end_paren < len(pattern):
                    if pattern[end_paren] == ")" and not is_escaped(end_paren):
                        break
                    end_paren += 1
                while end_colon < len(pattern):
                    if pattern[end_colon] == ":" and not is_escaped(end_colon):
                        break
                    end_colon += 1
                paren_exists = end_paren < len(pattern)
                colon_exists = end_colon < len(pattern)
                if paren_exists and (not colon_exists or end_paren < end_colon):
                    spec = pattern[marker_index:end_paren]
                    if parse_inline_flags(spec):
                        token = pattern[i : end_paren + 1]
                        add_step(token, "inline_flags", "Applies inline regex flags from this point.")
                        i = end_paren + 1
                        continue
                if colon_exists and (not paren_exists or end_colon < end_paren):
                    spec = pattern[marker_index:end_colon]
                    if parse_inline_flags(spec):
                        depth += 1
                        token = pattern[i : end_colon + 1]
                        add_step(token, "group_start", "Starts a scoped inline-flags group.", depth)
                        add_group(None, "scoped_flags_group", depth)
                        group_stack.append("scoped_flags_group")
                        i = end_colon + 1
                        continue

                known_groups = [
                    ("?P<", "named_capturing_group"),
                    ("?<=", "positive_lookbehind"),
                    ("?<!", "negative_lookbehind"),
                    ("?<", "named_capturing_group"),
                    ("?'", "named_capturing_group"),
                    ("?:", "non_capturing_group"),
                    ("?=", "positive_lookahead"),
                    ("?!", "negative_lookahead"),
                    ("?>", "atomic_group"),
                ]
                matched_known = False
                for prefix, kind in known_groups:
                    if pattern.startswith(prefix, i + 1):
                        token, next_i, name = _consume_group_token(pattern, i, prefix, kind)
                        depth += 1
                        add_step(token, "group_start", group_description(kind, token, name), depth)
                        add_group(name, kind, depth)
                        group_stack.append(kind)
                        i = next_i
                        if kind in {"capturing_group", "named_capturing_group"}:
                            capture_count += 1
                        matched_known = True
                        break
                if matched_known:
                    continue

                token, next_i = parse_unknown_special_group(i)
                depth += 1
                add_step(token, "group_start", "Starts an unrecognized special regex group.", depth)
                add_group(None, "unknown_special_group", depth)
                group_stack.append("unknown_special_group")
                i = next_i
                continue

            depth += 1
            capture_count += 1
            add_step("(", "group_start", "Starts a capturing group.", depth)
            add_group(None, "capturing_group", depth)
            group_stack.append("capturing_group")
            i += 1
            continue

        if char == ")" and not is_escaped(i):
            if group_stack:
                add_step(")", "group_end", "Ends the current group.", depth)
                group_stack.pop()
                depth = max(0, depth - 1)
            else:
                add_step(")", "unmatched_closing_parenthesis", "Encountered a closing parenthesis with no open group.", 0)
            i += 1
            continue

        if char == "\\" and i + 1 < len(pattern):
            token = pattern[i : i + 2]
            if token in ANCHOR_DESCRIPTIONS:
                add_step(token, "anchor", ANCHOR_DESCRIPTIONS[token])
            elif token in SHORTCUT_DESCRIPTIONS:
                add_step(token, "character_shortcut", SHORTCUT_DESCRIPTIONS[token])
            elif token in ESCAPED_WHITESPACE_DESCRIPTIONS:
                add_step(token, "escaped_whitespace", ESCAPED_WHITESPACE_DESCRIPTIONS[token])
            else:
                add_step(token, "escaped_literal", escaped_literal_description(token))
            i += 2
            continue

        if char == "{":
            quantifier = parse_braced_quantifier(i)
            if quantifier is not None:
                token, next_i = quantifier
                add_step(token, "quantifier", _describe_quantifier(token))
                i = next_i
                continue
            token, next_i = parse_invalid_braced_literal(i)
            add_step(token, "literal", literal_description(token))
            i = next_i
            continue

        if char in "*+?":
            token = char
            next_i = i + 1
            if next_i < len(pattern) and pattern[next_i] in "?+":
                token += pattern[next_i]
                next_i += 1
            add_step(token, "quantifier", _describe_quantifier(token))
            i = next_i
            continue

        if char in "^$":
            add_step(char, "anchor", ANCHOR_DESCRIPTIONS[char])
            i += 1
            continue

        if char == "|":
            add_step("|", "alternation", "Separates alternatives; the regex can match the expression on either side.")
            i += 1
            continue

        if char == ".":
            add_step(".", "wildcard", "Matches any character except newline, depending on regex mode.")
            i += 1
            continue

        j = i
        while j < len(pattern):
            current = pattern[j]
            if current in r"\^$|.*+?" and not is_escaped(j):
                break
            if current in "[({)}]" and not is_escaped(j):
                break
            if current == "{" and not is_escaped(j):
                break
            j += 1
        token = pattern[i:j] if j > i else pattern[i]
        add_step(token, "literal", literal_description(token))
        i += len(token)

    return RegexExplanation(pattern=pattern, steps=steps, groups=groups)


def _consume_group_token(pattern: str, start: int, prefix: str, kind: str) -> tuple[str, int, str | None]:
    if kind == "named_capturing_group":
        if prefix == "?P<":
            end = pattern.find(">", start + 3)
            if end == -1:
                return pattern[start:], len(pattern), None
            name = pattern[start + 4 : end]
            return pattern[start : end + 1], end + 1, name
        if prefix == "?<":
            end = pattern.find(">", start + 2)
            if end == -1:
                return pattern[start:], len(pattern), None
            name = pattern[start + 3 : end]
            return pattern[start : end + 1], end + 1, name
        if prefix == "?'":
            end = pattern.find("'", start + 3)
            if end == -1:
                return pattern[start:], len(pattern), None
            name = pattern[start + 3 : end]
            return pattern[start : end + 1], end + 1, name
    token = "(" + prefix
    return token, start + len(token), None


def _describe_quantifier(token: str) -> str:
    suffix = ""
    base = token
    if len(token) > 1 and token[-1] in "?+" and token[0] in "*+?{":
        suffix = token[-1]
        base = token[:-1]
    if base == "*":
        description = "Repeats the previous token zero or more times."
    elif base == "+":
        description = "Repeats the previous token one or more times."
    elif base == "?":
        description = "Repeats the previous token zero or one time."
    else:
        inner = base[1:-1]
        if inner.endswith(","):
            description = f"Repeats the previous token at least {inner[:-1]} times."
        elif "," in inner:
            left, right = inner.split(",", 1)
            description = f"Repeats the previous token between {left} and {right} times."
        else:
            description = f"Repeats the previous token exactly {inner} times."
    if suffix == "?":
        description += " Uses the lazy/non-greedy form."
    elif suffix == "+":
        description += " Uses the possessive form in engines that support it."
    return description
