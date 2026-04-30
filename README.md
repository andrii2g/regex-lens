# regex-lens

`regex-lens` is a small CLI that reads one regex pattern from a plaintext file and writes a Markdown explanation with a Mermaid diagram.

## Requirements

- Python 3.14

## Local Setup

```bash
python -m pip install -e .
```

This project uses a `src/` layout, so install it before running `python -m regex_lens` or `regex-lens`.

## Usage

```bash
regex-lens pattern.txt
regex-lens pattern.txt --output explained.md
python -m regex_lens pattern.txt
```

Default output:

```text
./pattern.explanation.md
```

## Sample Input

```regex
^(?<date>\d{4}-\d{2}-\d{2})\s+(?<level>INFO|WARN|ERROR):\s+(?<message>.*)$
```

## Sample Output Shape

The generated Markdown includes:

- the original pattern in a fenced `regex` block
- a summary section
- a groups table
- a step-by-step explanation table
- a left-to-right Mermaid flowchart

## Notes

Version 1 explains common regex syntax and produces a simple explanatory Mermaid flowchart. It does not validate engine compatibility or execute the regex.
