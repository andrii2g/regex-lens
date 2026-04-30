from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .markdown import render_markdown
from .parser import parse_regex


def default_output_path(input_path: Path, cwd: Path | None = None) -> Path:
    cwd = cwd or Path.cwd()
    return cwd / f"{input_path.stem}.explanation.md"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="regex-lens", description="Explain a regex pattern as Markdown.")
    parser.add_argument("input_file", help="Path to a plaintext file containing one regex pattern.")
    parser.add_argument("-o", "--output", dest="output_file", help="Path to the Markdown output file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_path = Path(args.input_file)

    try:
        if not input_path.exists() or input_path.is_dir():
            raise OSError
        raw_text = input_path.read_text(encoding="utf-8")
    except OSError:
        print(f"Error: cannot read input file: {input_path}", file=sys.stderr)
        return 1

    pattern = raw_text.rstrip("\r\n")

    try:
        explanation = parse_regex(pattern)
        markdown = render_markdown(explanation, input_path)
    except Exception:
        print("Error: internal generation error", file=sys.stderr)
        return 2

    output_path = Path(args.output_file) if args.output_file else default_output_path(input_path)
    try:
        output_path.write_text(markdown, encoding="utf-8")
    except OSError:
        print(f"Error: cannot write output file: {output_path}", file=sys.stderr)
        return 1

    print(f"Wrote regex explanation to {output_path}")
    return 0
