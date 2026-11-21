"""Focused tests for Pace & Speed (``pace-calc``).

The sweep proves the tool *runs*. These cases pin what makes it honest:

* a distance and a time are two different numbers, and the pace is built from
  both — not from a unit conversion of one;
* a two-part time is read the way the user chose, and the reading is printed
  back in words, because a pace built on a guessed reading looks right;
* zero distance and zero time are both refused — neither has a pace;
* a time of day, an unstated unit and ``1:75`` are refused, not coerced;
* a paste with spaces around the colon (``27 : 30``) is the same time;
* the pace, the speed and the race projections agree with each other.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import registry  # noqa: E402
from core.runner import execute  # noqa: E402

MINS = "Minutes and seconds (27:30 = 27m 30s)"
HOURS = "Hours and minutes (27:30 = 27h 30m)"
KM_PER_MILE = 1.609344


def run(distance: float, time: str, unit: str = "km", two_part: str = MINS):
    """Returns (ok, console text, error)."""
    tool = registry.get("pace-calc")
    payload = {"distance": distance, "distance_unit": unit, "time": time,
               "two_part": two_part}
    result = execute(tool, payload)
    return result.ok, result.text, result.error


def text(distance: float, time: str, **kwargs) -> str:
    ok, out, error = run(distance, time, **kwargs)
    if not ok:
        raise AssertionError(f"tool refused: {error}\n{out}")
    return out


def refused(distance: float, time: str, **kwargs) -> str:
    ok, out, error = run(distance, time, **kwargs)
    if ok:
        raise AssertionError(f"tool accepted what it should refuse:\n{out}")
    return error


def seconds_of(pace: str) -> int:
    """``5:30`` -> 330, ``1:02:15`` -> 3735."""
    parts = [int(part) for part in pace.split(":")]
    total = 0
    for part in parts:
        total = total * 60 + part
    return total


class PaceAndSpeed(unittest.TestCase):
    # -- the arithmetic ---------------------------------------------------
    def test_five_km_in_27_30(self):
        out = text(5, "27:30")
        self.assertIn("5:30 per km", out)
        self.assertIn("8:51 per mile", out)
        self.assertIn("10.91 km/h", out)

    def test_metres_are_km_over_a_thousand(self):
        self.assertIn("4:00 per km", text(500, "2:00", unit="metres"))

    def test_ten_km_in_an_hour(self):
        out = text(10, "1:00:00")
        self.assertIn("6:00 per km", out)
        self.assertIn("10.00 km/h", out)

    def test_miles_in_gives_the_same_pace_per_km(self):
        # 5 miles in 44:14 is 8.04672 km, so the pace per km matches 5 km in 27:30.
        out = text(5, "44:14", unit="miles")
        self.assertIn("5:30 per km", out)
        self.assertIn("8:51 per mile", out)

    def test_pace_and_speed_agree(self):
        out = text(5, "27:30")
        pace = seconds_of(re.search(r"(\d+:\d\d) per km", out).group(1))
        speed = float(re.search(r"([\d.]+) km/h", out).group(1))
        self.assertAlmostEqual(3600 / pace, speed, delta=0.02)

    def test_hours_are_not_wrapped_at_24(self):
        out = text(100, "25:00:00")
        self.assertIn("25:00:00", out)
        self.assertIn("15:00 per km", out)

    def test_a_pace_past_an_hour_keeps_its_hours(self):
        self.assertIn("1:06:00 per km", text(1, "1:06:00"))

    # -- the reading of a two-part time, said out loud ---------------------
    def test_two_part_is_minutes_and_seconds_by_default(self):
        out = text(5, "27:30")
        self.assertIn("read as 27m 30s", out)

    def test_two_part_as_hours_and_minutes(self):
        out = text(5, "27:30", two_part=HOURS)
        self.assertIn("read as 27h 30m", out)
        self.assertIn("5:30:00 per km", out)

    def test_three_part_time_ignores_the_choice(self):
        self.assertIn("read as 1h 30m", text(10, "1:30:00", two_part=MINS))

    def test_fractional_seconds_survive(self):
        out = text(5, "27:30.5")
        self.assertIn("read as 27m 30.500s", out)
        self.assertIn("5:30 per km", out)

    def test_spaces_around_the_colon_are_the_same_time(self):
        self.assertEqual(text(5, "27 : 30"), text(5, "27:30"))

    # -- the race projections --------------------------------------------
    def test_projections_follow_the_pace(self):
        out = text(5, "27:30")
        self.assertIn("5K             00:27:30", out)
        self.assertIn("marathon       03:52:04", out)

    # -- refusals ---------------------------------------------------------
    def test_zero_distance_is_refused(self):
        self.assertIn("greater than zero", refused(0, "27:30"))

    def test_negative_distance_is_refused(self):
        self.assertIn("greater than zero", refused(-5, "27:30"))

    def test_zero_time_is_refused(self):
        self.assertIn("Zero time has no pace", refused(5, "0"))

    def test_a_time_of_day_is_refused(self):
        self.assertIn("time of day", refused(5, "9:00 AM"))

    def test_a_number_with_no_unit_is_refused(self):
        self.assertIn("no unit", refused(5, "1h 30"))

    def test_a_colon_part_above_59_is_refused(self):
        self.assertIn("0-59", refused(5, "1:75"))

    def test_an_unknown_unit_is_named(self):
        self.assertIn("Unknown distance unit", refused(5, "27:30", unit="furlongs"))

    # -- the shape of the tool -------------------------------------------
    def test_it_asks_for_a_distance_and_a_time(self):
        tool = registry.get("pace-calc")
        keys = [field.key for field in tool.fields]
        self.assertEqual(keys, ["distance", "distance_unit", "time", "two_part"])
        self.assertEqual(tool.category, "Numbers")
        self.assertGreaterEqual(len(tool.summary), 20)


if __name__ == "__main__":
    unittest.main(verbosity=2)
