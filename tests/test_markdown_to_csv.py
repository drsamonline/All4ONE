"""Focused tests for the markdown-table-to-csv tool.

The sweep in ``tests/sweep.py`` proves every tool *runs*; it cannot prove one is
*right*. These cases pin the behaviour that a naive ``split("|")`` gets wrong:
an escaped pipe, a pipe inside inline code, a table with no outer pipes, a
ragged row, and picking one table out of several.
"""

from __future__ import annotations

import csv
import io
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import registry  # noqa: E402
from core.runner import execute  # noqa: E402


def run(**values) -> str:
    tool = registry.get("markdown-table-to-csv")
    payload = {"text": "", "file": "", "table": 1, "delimiter": ",", "output": ""}
    payload.update(values)
    result = execute(tool, payload)
    if not result.ok:
        raise AssertionError(f"tool failed: {result.error}\n{result.text}")
    return result.text


LOG = re.compile(r"^\d+ table\(s\), \d+ data row\(s\)$")


def csv_rows(text: str) -> list[list[str]]:
    """The emitted CSV parsed back, without the tool's own log lines."""
    lines = [line for line in text.splitlines() if not LOG.match(line.strip())]
    while lines and not lines[0].strip():
        lines.pop(0)
    return [row for row in csv.reader(io.StringIO("\n".join(lines)))]


class SimpleTable(unittest.TestCase):
    def test_header_and_rows_become_csv(self):
        out = run(text="| name | city | amount |\n"
                       "|---|---|---:|\n"
                       "| Aarav | Mumbai | 1200 |\n"
                       "| Diya | Delhi | 800 |\n")
        rows = csv_rows(out)
        self.assertEqual(rows[0], ["name", "city", "amount"])
        self.assertEqual(rows[1], ["Aarav", "Mumbai", "1200"])
        self.assertEqual(rows[2], ["Diya", "Delhi", "800"])

    def test_table_without_outer_pipes(self):
        out = run(text="name | amount\n--- | ---\nAarav | 1200\n")
        rows = csv_rows(out)
        self.assertEqual(rows[0], ["name", "amount"])
        self.assertEqual(rows[1], ["Aarav", "1200"])

    def test_short_row_is_padded_to_the_header(self):
        out = run(text="| a | b | c |\n|---|---|---|\n| 1 | 2 |\n")
        self.assertEqual(csv_rows(out)[1], ["1", "2", ""])

    def test_delimiter_is_configurable(self):
        out = run(text="| a | b |\n|---|---|\n| 1 | 2 |\n", delimiter=";")
        self.assertIn("a;b", out)
        self.assertIn("1;2", out)


class AwkwardCells(unittest.TestCase):
    def test_escaped_pipe_stays_inside_the_cell(self):
        out = run(text="| expr | note |\n|---|---|\n| a \\| b | or |\n")
        rows = csv_rows(out)
        self.assertEqual(rows[1], ["a | b", "or"])

    def test_pipe_inside_inline_code_is_not_a_column_break(self):
        out = run(text="| code | meaning |\n|---|---|\n| `a|b` | pipe |\n")
        rows = csv_rows(out)
        self.assertEqual(rows[1], ["`a|b`", "pipe"])

    def test_empty_cell_survives(self):
        out = run(text="| a | b |\n|---|---|\n| 1 |  |\n")
        self.assertEqual(csv_rows(out)[1], ["1", ""])


class ChoosingATable(unittest.TestCase):
    DOC = ("| first |\n|---|\n| one |\n"
           "\n"
           "Some prose between the two tables.\n"
           "\n"
           "| second |\n|---|\n| two |\n")

    def test_second_table_by_number(self):
        out = run(text=self.DOC, table=2)
        self.assertIn("two", out)
        self.assertNotIn("one", out)

    def test_zero_writes_every_table(self):
        out = run(text=self.DOC, table=0)
        self.assertIn("one", out)
        self.assertIn("two", out)

    def test_asking_for_a_table_that_is_not_there_is_an_error(self):
        tool = registry.get("markdown-table-to-csv")
        result = execute(tool, {"text": self.DOC, "file": "", "table": 7,
                                "delimiter": ",", "output": ""})
        self.assertFalse(result.ok)
        self.assertIn("no table 7", result.error or "")


class NoTable(unittest.TestCase):
    def test_plain_prose_is_reported_not_raised(self):
        out = run(text="alpha beta gamma\nsecond line\n")
        self.assertIn("No Markdown table found", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
