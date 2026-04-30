from dataclasses import dataclass


@dataclass(frozen=True)
class RegexStep:
    index: int
    token: str
    kind: str
    description: str
    depth: int = 0


@dataclass(frozen=True)
class RegexGroup:
    index: int
    name: str | None
    kind: str
    depth: int


@dataclass(frozen=True)
class RegexExplanation:
    pattern: str
    steps: list[RegexStep]
    groups: list[RegexGroup]
