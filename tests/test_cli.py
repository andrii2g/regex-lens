from __future__ import annotations

import contextlib
import io
import os
import shutil
import unittest
import uuid
from pathlib import Path

from regex_lens.cli import main


class CliTests(unittest.TestCase):
    def make_tempdir(self) -> Path:
        path = Path(".tmp-test-" + uuid.uuid4().hex).resolve()
        path.mkdir()
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path

    def test_default_output_path(self) -> None:
        tempdir = self.make_tempdir()
        input_path = (tempdir / "pattern.txt").resolve()
        input_path.write_text(r"^\d+$" + "\n", encoding="utf-8")
        previous = Path.cwd()
        os.chdir(tempdir)
        try:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = main([str(input_path)])
            self.assertEqual(result, 0)
            self.assertTrue((tempdir / "pattern.explanation.md").exists())
        finally:
            os.chdir(previous)

    def test_custom_output_path(self) -> None:
        tempdir = self.make_tempdir()
        input_path = tempdir / "pattern.txt"
        output_path = tempdir / "out.md"
        input_path.write_text(r"^\d+$", encoding="utf-8")
        result = main([str(input_path), "--output", str(output_path)])
        self.assertEqual(result, 0)
        self.assertTrue(output_path.exists())

    def test_missing_input_file(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main(["missing.txt"])
        self.assertEqual(result, 1)

    def test_multiline_input_preserves_internal_newlines(self) -> None:
        tempdir = self.make_tempdir()
        input_path = tempdir / "pattern.txt"
        output_path = tempdir / "out.md"
        pattern = "(?x)\n^ foo\n$\n"
        input_path.write_text(pattern, encoding="utf-8")
        result = main([str(input_path), "--output", str(output_path)])
        self.assertEqual(result, 0)
        output = output_path.read_text(encoding="utf-8")
        self.assertIn("(?x)\n^ foo\n$", output)

    def test_reader_removes_only_final_trailing_newlines(self) -> None:
        tempdir = self.make_tempdir()
        input_path = tempdir / "pattern.txt"
        output_path = tempdir / "out.md"
        input_path.write_text("  foo\nbar\r\n", encoding="utf-8")
        result = main([str(input_path), "--output", str(output_path)])
        self.assertEqual(result, 0)
        output = output_path.read_text(encoding="utf-8")
        self.assertIn("  foo\nbar", output)
        self.assertNotIn("  foo\nbar\r\n```", output)


if __name__ == "__main__":
    unittest.main()
