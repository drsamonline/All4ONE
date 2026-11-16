"""Focused tests for the dates-in-text tool.

The sweep proves the tool *runs*. These cases pin what makes it honest: the
same date written four ways lands on the same day, a date that could be read
two ways is LEFT ALONE unless the user settles it, a date that does not exist
is never invented, and a version number is not a date.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import registry  # noqa: E402
from core.runner import execute  # noqa: E402

REFUSE = "Refuse (leave them as they are)"
DAY_FIRST = "Day first (03/04 = 3 April)"
MONTH_FIRST = "Month first (03/04 = 4 March)"
ISO = "ISO 8601 (2025-04-03)"
SLASHED = "Day first (03/04/2025)"
LONG = "Month name (3 April 2025)"


def run(text: str, style: str = ISO, policy: str = REFUSE):
    """Returns (rewritten text, summary line, full console output)."""
    tool = registry.get("dates-in-text")
    payload = {"text": text, "file": "", "style": style, "policy": policy,
               "output": ""}
    result = execute(tool, payload)
    if not result.ok:
        raise AssertionError(f"tool failed: {result.error}\n{result.text}")
    lines = result.text.splitlines()
    summary = lines[-1]
    table = "\n".join(lines[:-1])
    return table, summary


class SameDayEveryWay(unittest.TestCase):
    """One date, four spellings, one answer."""

    def test_iso_is_already_iso(self):
        table, summary = run("Filed 2025-04-03.")
        self.assertIn("2025-04-03", table)
        self.assertIn("1 date(s) found, 0 rewritten", summary)

    def test_day_month_name(self):
        table, _ = run("Filed 3 April 2025.")
        self.assertIn("2025-04-03", table)

    def test_month_day_name_with_comma(self):
        table, _ = run("Filed April 3, 2025.")
        self.assertIn("2025-04-03", table)

    def test_abbreviated_with_ordinal_and_dashes(self):
        table, _ = run("Filed 3rd-Apr-25.")
        self.assertIn("2025-04-03", table)

    def test_unambiguous_slashed(self):
        table, _ = run("Filed 25/04/2025.")
        self.assertIn("2025-04-25", table)

    def test_unambiguous_month_first(self):
        table, _ = run("Filed 04/25/2025.")
        self.assertIn("2025-04-25", table)

    def test_style_choice_changes_the_writing(self):
        table, _ = run("Filed 2025-04-03.", style=SLASHED)
        self.assertIn("03/04/2025", table)
        table, _ = run("Filed 2025-04-03.", style=LONG)
        self.assertIn("3 April 2025", table)


class NeverGuess(unittest.TestCase):
    """03/04 is 3 April in India and 4 March in the US — so ask, don't assume."""

    def test_ambiguous_is_left_alone_by_default(self):
        table, summary = run("Filed 03/04/2025.")
        self.assertIn("could be either", table)
        self.assertIn("1 left alone as ambiguous", summary)
        self.assertIn("0 rewritten", summary)

    def test_day_first_settles_it(self):
        table, summary = run("Filed 03/04/2025.", policy=DAY_FIRST)
        self.assertIn("2025-04-03", table)
        self.assertIn("settled by your day/month choice", table)
        self.assertIn("1 rewritten", summary)

    def test_month_first_settles_the_other_way(self):
        table, _ = run("Filed 03/04/2025.", policy=MONTH_FIRST)
        self.assertIn("2025-03-04", table)

    def test_equal_numbers_are_not_ambiguous(self):
        table, _ = run("Filed 04/04/2025.", style=SLASHED)
        self.assertIn("04/04/2025", table)

    def test_impossible_date_is_listed_not_invented(self):
        table, summary = run("Filed 31/02/2025.")
        self.assertIn("no such date", table)
        self.assertIn("1 not a real date", summary)
        self.assertIn("0 rewritten", summary)

    def test_impossible_iso_date_is_listed(self):
        table, summary = run("Filed 2025-02-31.")
        self.assertIn("no such date", table)
        self.assertIn("1 not a real date", summary)


class NotADate(unittest.TestCase):
    """Things that look like dates and are not."""

    def test_version_number_untouched(self):
        table, summary = run("Upgrade to v1.2.34 then rebuild.")
        self.assertEqual(summary, "No dates found.")

    def test_dotted_date_is_a_date_and_still_ambiguous(self):
        """03.04.2025 is a real European spelling — and still two ways round."""
        table, _ = run("Filed 03.04.2025.")
        self.assertIn("could be either", table)
        table, _ = run("Filed 03.04.2025.", policy=DAY_FIRST)
        self.assertIn("2025-04-03", table)

    def test_time_is_untouched(self):
        table, summary = run("The job ran at 12:30:45.")
        self.assertEqual(summary, "No dates found.")

    def test_no_dates_at_all(self):
        table, summary = run("Nothing to see here.")
        self.assertEqual(summary, "No dates found.")


class TwoDigitYears(unittest.TestCase):
    """The POSIX pivot: 69-99 are the 1900s, 00-68 are the 2000s."""

    def test_sixty_nine_is_nineteen_sixty_nine(self):
        table, _ = run("Signed 3 Apr 69.")
        self.assertIn("1969-04-03", table)

    def test_sixty_eight_is_twenty_sixty_eight(self):
        table, _ = run("Signed 3 Apr 68.")
        self.assertIn("2068-04-03", table)


class Counting(unittest.TestCase):
    def test_each_date_counted_once(self):
        table, summary = run("From 2025-04-03 to 12 June 2026.")
        self.assertIn("2 date(s) found, 1 rewritten", summary)

    def test_the_text_around_the_dates_survives(self):
        """The rewrite must not eat the words on either side."""
        tool = registry.get("dates-in-text")
        result = execute(tool, {"text": "Due 3 April 2025, paid 2025-04-09.",
                                "file": "", "style": ISO, "policy": REFUSE,
                                "output": ""})
        self.assertTrue(result.ok, result.error)
        self.assertIn("Due 2025-04-03, paid 2025-04-09.", result.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
