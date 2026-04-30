# regex-lens

`regex-lens` is a small CLI that reads one regex pattern from a plaintext file and writes a Markdown explanation with a Mermaid diagram.

## Requirements

- Python 3.12+

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

If your Linux distribution blocks direct `pip` installs into the system Python with an `externally-managed-environment` error, use the virtual environment flow above.

This project uses a `src/` layout, so install it before running `python -m regex_lens` or `regex-lens`.

## Usage

Create a file containing one regex pattern, for example:

```text
pattern.txt
```

with contents:

```regex
^(?<date>\d{4}-\d{2}-\d{2})$
```

Run the tool with the installed console script:

```bash
regex-lens pattern.txt
regex-lens pattern.txt --output explained.md
```

Or run it as a Python module after installation:

```bash
python -m regex_lens pattern.txt
python -m regex_lens pattern.txt --output explained.md
```

Default output:

```text
./pattern.explanation.md
```

## Test

```bash
python -m unittest discover -s tests
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
