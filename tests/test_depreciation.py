"""Focused tests for Depreciation Schedule (``depreciation-schedule``).

The sweep proves the tool *runs*. These cases pin what makes it honest:

* the charges add up to the depreciable amount **exactly**, in whole paise;
* the closing book value lands on the salvage value, not a few paise short;
* the last year is whatever is left, and the report says how far it differs;
* written-down value never falls below the salvage value in any year;
* the rate is derived from the life and the salvage value, so the two agree;
* a rate that contradicts the life is refused by name (₹0 salvage under WDV);
* a charge that cannot be held in paise is refused rather than printed as ₹0.00;
* bad input is refused by name: a ₹0 asset, a negative salvage, a salvage above
  cost, a life of 0 years.
"""

from __future__ import annotations

import itertools
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import registry  # noqa: E402
from core.runner import execute  # noqa: E402

STRAIGHT = "Straight line"
WDV = "Written-down value"


def run(cost=100000, salvage=10000, years=5, method=STRAIGHT, output=""):
    """Returns the whole execution result."""
    tool = registry.get("depreciation-schedule")
    payload = {"cost": cost, "salvage": salvage, "years": years,
               "method": method, "output": output}
    return execute(tool, payload)


def ok(**kwargs):
    result = run(**kwargs)
    if not result.ok:
        raise AssertionError(f"tool refused: {result.error}\n{result.text}")
    return result


def refused(**kwargs) -> str:
    result = run(**kwargs)
    if result.ok:
        raise AssertionError(f"tool answered when it should have refused:\n{result.text}")
    return result.error or ""


ROW = re.compile(r"Year (\d+)\s+(₹[\d,.]+)\s+(₹[\d,.]+)\s+(₹[\d,.]+)\s+([\d.]+%)")


def rows(text: str) -> list[list[str]]:
    """The table rows of the report, each as [year, opening, charge, closing, share]."""
    return [list(match.groups()) for match in ROW.finditer(text)]


def data(text: str) -> dict:
    """The tool's returned dict, which the runner prints as the last block."""
    lines = text.splitlines()
    start = max(i for i, line in enumerate(lines) if line.startswith("{"))
    return json.loads("\n".join(lines[start:]))


def paise(value: str) -> int:
    return int(round(float(value.replace("₹", "").replace(",", "")) * 100))


class StraightLine(unittest.TestCase):
    def test_equal_charges_and_the_salvage_value_at_the_end(self):
        result = ok()
        self.assertEqual(data(result.text)["yearly_charge"], 18000.0)
        self.assertEqual(data(result.text)["total_charge"], 90000.0)
        self.assertEqual(data(result.text)["closing_book_value"], 10000.0)
        self.assertIsNone(data(result.text)["rate_percent"])

    def test_the_charges_add_up_when_the_years_do_not_divide(self):
        result = ok(cost=1000, salvage=0, years=3)
        table = rows(result.text)
        self.assertEqual([paise(r[2]) for r in table], [33333, 33333, 33334])
        self.assertEqual(sum(paise(r[2]) for r in table), 100000)
        self.assertEqual(paise(table[-1][3]), 0)

    def test_the_last_year_is_the_remainder_and_the_report_says_so(self):
        result = ok(cost=1000, salvage=0, years=3)
        self.assertIn("Last year", result.text)
        self.assertIn("₹0.01 more than the usual ₹333.33", result.text)

    def test_a_single_year_writes_the_whole_thing_off(self):
        result = ok(cost=50000, salvage=5000, years=1)
        self.assertEqual(data(result.text)["total_charge"], 45000.0)
        self.assertEqual(data(result.text)["closing_book_value"], 5000.0)
        self.assertNotIn("Last year", result.text)   # nothing differs from the usual

    def test_an_asset_worth_its_cost_depreciates_nothing(self):
        result = ok(cost=50000, salvage=50000, years=5)
        self.assertEqual(data(result.text)["total_charge"], 0.0)
        self.assertEqual(data(result.text)["yearly_charge"], 0.0)
        self.assertEqual(data(result.text)["closing_book_value"], 50000.0)

    def test_a_sixty_year_life_still_adds_up(self):
        result = ok(cost=1234567.89, salvage=1000.0, years=60)
        table = rows(result.text)
        self.assertEqual(len(table), 60)
        self.assertEqual(sum(paise(r[2]) for r in table), paise("₹12,33,567.89"))


class WrittenDownValue(unittest.TestCase):
    def test_the_rate_is_derived_from_the_life_and_the_salvage(self):
        result = ok(method=WDV)
        self.assertAlmostEqual(data(result.text)["rate_percent"], 36.9043, places=3)
        self.assertIn("36.90%", result.text)

    def test_the_book_value_lands_on_the_salvage_value(self):
        result = ok(method=WDV)
        self.assertEqual(data(result.text)["closing_book_value"], 10000.0)
        self.assertEqual(paise(rows(result.text)[-1][3]), 1000000)

    def test_the_last_year_is_the_remainder_and_the_report_says_so(self):
        result = ok(method=WDV)
        self.assertIn("Last year", result.text)
        self.assertIn("less than the usual", result.text)
        self.assertEqual(data(result.text)["total_charge"], 90000.0)

    def test_the_balance_never_falls_below_the_salvage_value(self):
        for cost, salvage, years in itertools.product(
                [1000, 99999, 500000], [1, 100, 5000], [2, 7, 25]):
            if salvage * 100 >= cost * 100:
                continue
            table = rows(ok(cost=cost, salvage=salvage, years=years, method=WDV).text)
            floor = paise(f"₹{salvage:.2f}")
            for row in table:
                self.assertGreaterEqual(paise(row[3]), floor,
                                        f"{cost}/{salvage}/{years}: {row}")

    def test_a_rounded_charge_cannot_push_the_balance_through_the_salvage(self):
        """₹10.25 down to ₹10.00 over 14 years: at year 13 the rounded charge would
        take the balance one paisa below the salvage value, so it is capped."""
        result = ok(cost=10.25, salvage=10.0, years=14, method=WDV)
        table = rows(result.text)
        self.assertEqual(len(table), 14)
        for row in table:
            self.assertGreaterEqual(paise(row[3]), 1000, row)
        self.assertEqual(sum(paise(row[2]) for row in table), 25)

    def test_the_rate_is_printed_and_straight_line_prints_none(self):
        self.assertIn("on the opening balance", ok(method=WDV).text)
        self.assertNotIn("opening balance", ok().text)


class Arithmetic(unittest.TestCase):
    def test_every_row_closes_and_the_totals_match_the_table(self):
        for method in (STRAIGHT, WDV):
            for cost, salvage, years in itertools.product(
                    [1000, 25000, 750000.5], [0, 1, 9999], [1, 4, 13]):
                if method == WDV and salvage == 0:
                    continue
                if salvage > cost:
                    continue
                result = ok(cost=cost, salvage=salvage, years=years, method=method)
                table = rows(result.text)
                self.assertEqual(len(table), years)
                self.assertEqual(paise(table[0][1]), paise(f"₹{cost:.2f}"))
                for row in table:
                    self.assertEqual(paise(row[1]) - paise(row[2]), paise(row[3]),
                                     f"{method} {cost}/{salvage}/{years}: {row}")
                charges = sum(paise(row[2]) for row in table)
                self.assertEqual(charges, paise(f"₹{cost:.2f}") - paise(f"₹{salvage:.2f}"),
                                 f"{method} {cost}/{salvage}/{years}")
                self.assertEqual(data(result.text)["total_charge"], round(charges / 100, 2))

    def test_the_book_value_only_ever_falls(self):
        for method in (STRAIGHT, WDV):
            table = rows(ok(method=method).text)
            closings = [paise(row[3]) for row in table]
            self.assertEqual(closings, sorted(closings, reverse=True))

    def test_the_written_off_column_ends_at_the_depreciable_share(self):
        table = rows(ok().text)
        self.assertEqual(table[0][4], "18.0%")
        self.assertEqual(table[-1][4], "90.0%")

    def test_the_csv_holds_the_same_rows_as_the_table(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "dep.csv"
            result = ok(output=str(target))
            text = target.read_text().strip().splitlines()
            self.assertEqual(text[0], "year,opening,charge,closing")
            self.assertEqual(len(text), 6)
            table = rows(result.text)
            for line, row in zip(text[1:], table, strict=True):
                cells = line.split(",")
                self.assertEqual(cells[0], row[0])
                self.assertEqual(paise("₹" + cells[3]), paise(row[3]))


class Refusals(unittest.TestCase):
    def test_a_zero_cost_asset(self):
        self.assertIn("nothing to depreciate", refused(cost=0))

    def test_a_negative_cost_asset(self):
        self.assertIn("nothing to depreciate", refused(cost=-500))

    def test_a_negative_salvage_value(self):
        self.assertIn("cannot be negative", refused(salvage=-1))

    def test_a_salvage_value_above_the_cost(self):
        self.assertIn("more than the ₹100,000.00 the asset cost", refused(salvage=200000))

    def test_a_life_of_zero_years(self):
        self.assertIn("0 years has no years", refused(years=0))

    def test_written_down_value_with_no_salvage_is_refused_by_name(self):
        error = refused(method=WDV, salvage=0)
        self.assertIn("never reaches ₹0", error)
        self.assertIn("100% a year", error)

    def test_a_charge_too_small_to_hold_in_paise(self):
        error = refused(cost=0.02, salvage=0, years=5)
        self.assertIn("less than a paisa", error)


if __name__ == "__main__":
    unittest.main(verbosity=2)
