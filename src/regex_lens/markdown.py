from __future__ import annotations

from pathlib import Path

from .mermaid import render_mermaid
from .model import RegexExplanation


def render_markdown(explanation: RegexExplanation, input_path: Path) -> str:
    named_groups = sum(1 for group in explanation.groups if group.name)
    alternations = sum(1 for step in explanation.steps if step.kind == "alternation")
    quantifiers = sum(1 for step in explanation.steps if step.kind == "quantifier")

    group_rows = ["| # | Name | Kind | Depth |", "|---:|---|---|---:|"]
    if explanation.groups:
        for group in explanation.groups:
            group_rows.append(
                f"| {group.index} | {escape_table_cell(group.name or '')} | {escape_table_cell(group.kind)} | {group.depth} |"
            )
    else:
        group_rows.append("| - |  |  |  |")

    step_rows = ["| # | Depth | Token | Type | Explanation |", "|---:|---:|---|---|---|"]
    for step in explanation.steps:
        step_rows.append(
            f"| {step.index} | {step.depth} | {format_token(step.token)} | {escape_table_cell(step.kind)} | {escape_table_cell(step.description)} |"
        )

    mermaid = render_mermaid(explanation)
    return "\n".join(
        [
            "# Regex Explanation",
            "",
            "## Source",
            "",
            f"`{input_path.name}`",
            "",
            "## Pattern",
            "",
            "```regex",
            explanation.pattern,
            "```",
            "",
            "## Summary",
            "",
            f"- Steps: {len(explanation.steps)}",
            f"- Groups: {len(explanation.groups)}",
            f"- Named groups: {named_groups}",
            f"- Alternations: {alternations}",
            f"- Quantifiers: {quantifiers}",
            "",
            "## Groups",
            "",
            *group_rows,
            "",
            "## Step-by-step Explanation",
            "",
            *step_rows,
            "",
            "## Mermaid Diagram",
            "",
            "```mermaid",
            mermaid,
            "```",
        ]
    )


def escape_table_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")


def format_token(token: str) -> str:
    escaped = escape_table_cell(token)
    if "`" in escaped:
        return escaped.replace("`", "\\`")
    return f"`{escaped}`"
