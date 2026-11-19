"""Focused tests for Add Up Times (``duration-sum``).

The sweep proves the tool *runs*. These cases pin what makes it honest:

* the same duration written six ways is the same duration;
* a two-part time is read the way the user chose, and the choice is visible;
* a colon form's parts are not free numbers (``1:75`` is refused);
* ``1h 30`` is refused — 30 of what is not written down;
* a time of day (``9:00 AM``) is not a duration;
* a total is never partial: one unreadable line refuses the whole sum;
* hours do not wrap at 24, and milliseconds survive the sum.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import registry  # noqa: E402
from core.runner import execute  # noqa: E402

HOURS = "Hours and minutes (1:30 = 1h 30m)"
MINUTES = "Minutes and seconds (1:30 = 1m 30s)"


def run(times: str, two_part: str = HOURS, bare: str = "Minutes"):
    """Returns (ok, console text, error)."""
    tool = registry.get("duration-sum")
    payload = {"times": times, "two_part": two_part, "bare": bare, "output": ""}
    result = execute(tool, payload)
    return result.ok, result.text, result.error


def total(times: str, **kwargs) -> str:
    ok, text, error = run(times, **kwargs)
    if not ok:
        raise AssertionError(f"tool refused: {error}\n{text}")
    for line in text.splitlines():
        if line.startswith("Total"):
            return line.split()[-1]
    raise AssertionError(f"no total in:\n{text}")


class SameDurationEveryWay(unittest.TestCase):
    """One length of time, six spellings, one answer."""

    def test_all_spellings_agree(self):
        for written in ("1:30", "90m", "1h 30m", "1.5h", "5400s", "90"):
            with self.subTest(written=written):
                self.assertEqual(total(written), "01:30:00")

    def test_no_space_between_units(self):
        self.assertEqual(total("1h30m45s"), "01:30:45")

    def test_plural_and_short_units(self):
        for written in ("2 hrs", "2 hours", "2h"):
            with self.subTest(written=written):
                self.assertEqual(total(written), "02:00:00")

    def test_days_are_a_duration_too(self):
        self.assertEqual(total("2d"), "48:00:00")

    def test_whitespace_from_a_paste_is_ignored(self):
        self.assertEqual(total("1h\u00a030m"), "01:30:00")
        self.assertEqual(total("  45m\t"), "00:45:00")

    def test_blank_lines_are_not_errors(self):
        self.assertEqual(total("1:00\n\n0:30\n"), "01:30:00")


class TheChoiceIsTheUsers(unittest.TestCase):
    """``1:30`` is read the way the user said, and the reading is shown."""

    def test_two_part_as_hours_and_minutes(self):
        self.assertEqual(total("1:30", two_part=HOURS), "01:30:00")

    def test_two_part_as_minutes_and_seconds(self):
        self.assertEqual(total("1:30", two_part=MINUTES), "00:01:30")

    def test_three_part_is_always_h_m_s(self):
        self.assertEqual(total("1:30:00", two_part=MINUTES), "01:30:00")

    def test_bare_number_follows_the_bare_choice(self):
        self.assertEqual(total("90", bare="Minutes"), "01:30:00")
        self.assertEqual(total("2", bare="Hours"), "02:00:00")
        self.assertEqual(total("5400", bare="Seconds"), "01:30:00")

    def test_the_table_shows_what_each_line_became(self):
        ok, text, _ = run("1:30", two_part=MINUTES)
        self.assertTrue(ok)
        self.assertIn("00:01:30", text)


class Refusals(unittest.TestCase):
    """Nothing is guessed, and nothing is half-added."""

    def test_a_unit_less_trailing_number_is_refused(self):
        ok, _, error = run("1h 30")
        self.assertFalse(ok)
        self.assertIn("has no unit", error)

    def test_minutes_over_59_in_a_colon_form_are_refused(self):
        ok, _, error = run("1:75")
        self.assertFalse(ok)
        self.assertIn("0-59", error)

    def test_a_time_of_day_is_refused_by_name(self):
        for written in ("9:00 AM", "5:30 pm", "9 o'clock"):
            with self.subTest(written=written):
                ok, _, error = run(written)
                self.assertFalse(ok)
                self.assertIn("time of day", error)

    def test_negative_is_refused(self):
        ok, _, error = run("-1:30")
        self.assertFalse(ok)
        self.assertIn("negative", error)

    def test_unknown_unit_is_refused(self):
        ok, _, error = run("90 furlongs")
        self.assertFalse(ok)
        self.assertIn("unknown unit", error)

    def test_words_are_not_a_duration(self):
        ok, _, _ = run("alpha beta gamma")
        self.assertFalse(ok)

    def test_empty_input_is_refused(self):
        ok, _, error = run("")
        self.assertFalse(ok)
        self.assertIn("one per line", error)

    def test_one_bad_line_refuses_the_whole_sum(self):
        """A partial total is a wrong total — the good lines are not added."""
        ok, text, error = run("1:00\nnonsense\n0:30")
        self.assertFalse(ok)
        self.assertNotIn("Total", text)
        self.assertIn("line 2", error)

    def test_every_bad_line_is_named(self):
        ok, _, error = run("1h 30\n1:75\n1:00")
        self.assertFalse(ok)
        self.assertIn("line 1", error)
        self.assertIn("line 2", error)
        self.assertNotIn("line 3", error)


class TheTotalIsArithmetic(unittest.TestCase):
    """Hours do not wrap at 24, and no time is lost to float rounding."""

    def test_hours_do_not_wrap_at_a_day(self):
        self.assertEqual(total("23:00\n2:00"), "25:00:00")

    def test_days_are_named_beside_the_total(self):
        ok, text, _ = run("23:00\n2:00")
        self.assertTrue(ok)
        self.assertIn("1 day(s) and 01:00:00", text)

    def test_milliseconds_survive_the_sum(self):
        self.assertEqual(total("0:00:00.5\n0:00:00.5"), "00:00:01")

    def test_a_fraction_of_a_second_is_kept_when_it_is_real(self):
        self.assertEqual(total("0:00:00.25\n0:00:00.25"), "00:00:00.500")

    def test_decimal_hours_are_reported_for_billing(self):
        ok, text, _ = run("1:15\n0:00")
        self.assertTrue(ok)
        self.assertIn("1.25 for billing", text)

    def test_twenty_lines_of_float_minutes_do_not_drift(self):
        """0.1 h ten times is exactly one hour, not 1:00:00.0000000001."""
        self.assertEqual(total("\n".join(["0.1h"] * 10)), "01:00:00")


if __name__ == "__main__":
    unittest.main(verbosity=2)
