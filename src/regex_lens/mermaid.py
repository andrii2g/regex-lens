from __future__ import annotations

from .model import RegexExplanation


def render_mermaid(explanation: RegexExplanation) -> str:
    lines = ["flowchart LR", "    N0([Start])"]

    for step in explanation.steps:
        label = f"Step {step.index}: {step.token}<br/>{step.description}"
        label = label.replace("\\", "\\\\").replace('"', '\\"').replace("\r\n", " ").replace("\n", "<br/>").replace("\r", " ")
        if len(label) > 80:
            label = label[:77] + "..."
        lines.append(f'    N{step.index}["{label}"]')

    end_id = len(explanation.steps) + 1
    lines.append(f"    N{end_id}([End])")

    previous = 0
    for step in explanation.steps:
        lines.append(f"    N{previous} --> N{step.index}")
        previous = step.index
    lines.append(f"    N{previous} --> N{end_id}")

    return "\n".join(lines)
