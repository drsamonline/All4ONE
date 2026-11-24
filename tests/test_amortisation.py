"""Focused tests for Amortisation Schedule (``amortisation-schedule``).

The sweep proves the tool *runs*. These cases pin what makes it honest:

* the principal column adds up to the loan to the paisa — always, not usually;
* a loan runs for exactly the tenure it was given: rounding the instalment never
  adds a 61st payment of ₹0.02 to a 60-month loan;
* the last instalment is whatever is left, and the report says how far it differs;
* the interest total is summed from the rows, not from ``instalment × months``;
* a zero-rate loan charges nothing and still repays the whole principal;
* an extra payment's saving is read off the two schedules, never estimated;
* the year-by-year view and the month-by-month view agree on every total;
* a loan whose instalment rounds to nothing is refused by name, not looped on.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import registry  # noqa: E402
from core.runner import execute  # noqa: E402

LOAN = {"principal": 500000.0, "rate": 9.5, "years": 5, "months": 0,
        "extra": 0.0, "show": "Every month", "output": ""}


def run(**changes):
    payload = dict(LOAN)
    payload.update(changes)
    return execute(registry.get("amortisation-schedule"), payload)


class Answer(dict):
    """The tool's return value, with the console text and the files kept beside it."""

    text = ""
    outputs: list[str] = []


def good(**changes) -> Answer:
    result = run(**changes)
    if not result.ok:
        raise AssertionError(f"tool refused: {result.error}\n{result.text}")
    answer = Answer(value_of(result))
    answer.text = result.text
    answer.outputs = result.outputs
    return answer


def refused(**changes) -> str:
    result = run(**changes)
    if result.ok:
        raise AssertionError(f"tool answered when it should have refused:\n{result.text}")
    return result.error


def value_of(result) -> dict:
    """The tool's return value, which the runner renders as the last JSON block."""
    start = result.text.rindex("{")
    return json.loads(result.text[start:])


def table_rows(text: str) -> list[list[str]]:
    """The console table as rows of cells — header and rule dropped.

    Cells are separated by two or more spaces, so a label like "Year 1" stays
    one cell instead of becoming two.
    """
    lines = [line for line in text.splitlines() if line.strip()]
    body = []
    for line in lines[2:]:
        if line.startswith("Loan") or line.startswith("("):
            break
        body.append([cell.strip() for cell in re.split(r"\s{2,}", line.strip())])
    return body


def month_rows(**changes) -> list[list[str]]:
    return table_rows(good(show="Every month", **changes).text)


class PrincipalAddsUp(unittest.TestCase):
    """The one invariant a schedule cannot be allowed to break."""

    def check(self, principal, rate, years, months, extra):
        rows = month_rows(principal=principal, rate=rate, years=years, months=months,
                          extra=extra)
        repaid = sum(int(round(float(row[3].replace("₹", "").replace(",", "")) * 100))
                     for row in rows)
        self.assertEqual(repaid, int(round(principal * 100)),
                         f"{principal} at {rate}% over {years}y{months}m, extra {extra}")
        self.assertEqual(rows[-1][4], "₹0.00", "the balance must land on zero")

    def test_plain_loans(self):
        self.check(500000.0, 9.5, 5, 0, 0.0)
        self.check(100000.0, 0.0, 1, 0, 0.0)
        self.check(250000.0, 13.75, 7, 5, 0.0)
        self.check(99999.99, 8.4, 3, 7, 0.0)

    def test_with_an_extra_payment(self):
        self.check(500000.0, 9.5, 5, 0, 2000.0)
        self.check(100000.0, 0.0, 1, 0, 500.0)

    def test_a_rupee_amount_that_floats_cannot_hold(self):
        # ₹4.35 is 434.99999999999994 in binary. Read as a float the instalment
        # comes out ₹0.18 and the loan takes 25 months instead of 5.
        result = good(principal=4.35, rate=0.0, years=0, months=5)
        self.assertEqual(result["monthly_instalment"], 0.87)
        self.assertEqual(result["instalments"], 5)
        self.assertEqual([row[1] for row in month_rows(principal=4.35, rate=0.0,
                                                       years=0, months=5)],
                         ["₹0.87"] * 5)

    def test_a_rounding_hostile_amount(self):
        # 1/3 of a rupee per month, ten times: the old float schedule drifted here.
        self.check(10.01, 0.0, 0, 10, 0.0)


class TheTenureIsTheTenure(unittest.TestCase):
    def test_a_60_month_loan_has_60_instalments(self):
        result = good()
        self.assertEqual(result["instalments"], 60)
        self.assertEqual(len(month_rows()), 60)

    def test_the_rounding_goes_into_the_last_instalment(self):
        result = good()
        last = result["instalments"]
        self.assertEqual(result["months_saved"], 0)
        self.assertIn("Last one", result.text)
        self.assertIn("than the usual instalment", result.text)
        self.assertEqual(len(month_rows()), last)

    def test_a_long_loan_keeps_its_own_length(self):
        result = good(principal=2500000.0, rate=8.6, years=20, months=0)
        self.assertEqual(result["instalments"], 240)


class TheTotalsComeFromTheRows(unittest.TestCase):
    def test_interest_is_summed_not_multiplied(self):
        result = good()
        interest = sum(float(row[2].replace("₹", "").replace(",", ""))
                       for row in month_rows())
        self.assertAlmostEqual(result["total_interest"], round(interest, 2), places=2)
        instalment = result["monthly_instalment"]
        naive = round(instalment * 60 - 500000.0, 2)
        self.assertNotEqual(result["total_interest"], naive,
                            "a formula total would be the wrong total")

    def test_the_instalment_is_the_standard_one(self):
        # The textbook answer for ₹5,00,000 at 9.5% over 60 months.
        self.assertAlmostEqual(good()["monthly_instalment"], 10500.93, places=2)

    def test_the_first_month_charges_one_months_interest_on_the_whole_loan(self):
        # ₹5,00,000 at 9.5% is 0.095/12 of the balance a month: ₹3,958.33.
        rows = month_rows()
        self.assertEqual(rows[0][2], "₹3,958.33")
        self.assertEqual(rows[1][2], "₹3,906.54")

    def test_total_paid_is_principal_plus_interest(self):
        value = value_of(good())
        self.assertAlmostEqual(value["total_paid"],
                               round(value["total_interest"] + 500000.0, 2), places=2)


class ZeroRate(unittest.TestCase):
    def test_nothing_is_charged_and_everything_is_repaid(self):
        value = value_of(good(rate=0.0, principal=100000.0, years=1))
        self.assertEqual(value["total_interest"], 0.0)
        self.assertEqual(value["total_paid"], 100000.0)

    def test_an_uneven_principal_leaves_a_smaller_last_instalment(self):
        result = good(rate=0.0, principal=100000.0, years=1)
        rows = month_rows(rate=0.0, principal=100000.0, years=1)
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[-1][1], "₹8,333.26")
        self.assertIn("less than the usual instalment", result.text)


class ExtraPayments(unittest.TestCase):
    def test_the_saving_is_read_off_the_two_schedules(self):
        plain = value_of(good())
        early = value_of(good(extra=2000.0))
        self.assertLess(early["instalments"], plain["instalments"])
        self.assertEqual(early["months_saved"], plain["instalments"] - early["instalments"])
        self.assertAlmostEqual(early["interest_saved"],
                               round(plain["total_interest"] - early["total_interest"], 2),
                               places=2)

    def test_a_bigger_extra_saves_more(self):
        small = value_of(good(extra=500.0))
        large = value_of(good(extra=5000.0))
        self.assertGreater(small["interest_saved"], 0)
        self.assertGreater(large["interest_saved"], small["interest_saved"])
        self.assertGreater(large["months_saved"], small["months_saved"])

    def test_the_saved_line_is_printed_and_matches_the_figures(self):
        result = good(extra=2000.0)
        saved = result["interest_saved"]
        self.assertIn(f"Saved         ₹{saved:,.2f} of interest", result.text)
        self.assertIn(f"{result['months_saved']} instalment(s)", result.text)

    def test_no_extra_saves_nothing(self):
        value = value_of(good())
        self.assertEqual(value["interest_saved"], 0.0)
        self.assertEqual(value["months_saved"], 0)


class BothViewsAgree(unittest.TestCase):
    def test_the_year_table_and_the_month_table_add_up_the_same(self):
        monthly = month_rows()
        yearly = table_rows(good(show="Year by year").text)
        month_principal = sum(float(row[3].replace("₹", "").replace(",", "")) for row in monthly)
        year_principal = sum(float(row[1].replace("₹", "").replace(",", "")) for row in yearly)
        month_interest = sum(float(row[2].replace("₹", "").replace(",", "")) for row in monthly)
        year_interest = sum(float(row[2].replace("₹", "").replace(",", "")) for row in yearly)
        self.assertAlmostEqual(month_principal, year_principal, places=2)
        self.assertAlmostEqual(month_interest, year_interest, places=2)

    def test_each_year_row_closes_where_its_twelfth_month_closes(self):
        monthly = month_rows()
        yearly = table_rows(good(show="Year by year").text)
        for index, row in enumerate(yearly):
            twelfth = monthly[min(12 * (index + 1), len(monthly)) - 1]
            self.assertEqual(row[3], twelfth[4], f"year {index + 1} closes in the wrong place")
        self.assertEqual(yearly[0][0], "Year 1")

    def test_a_part_year_is_named_as_one(self):
        text = good(years=1, months=6, show="Year by year").text
        self.assertIn("the last year holds 6 instalment(s), not 12", text)


class TheCsvIsTheSchedule(unittest.TestCase):
    def test_the_file_holds_every_month_and_sums_to_the_loan(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "schedule.csv"
            result = good(output=str(target))
            with open(target, newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), result["instalments"])
            repaid = sum(int(round(float(row["principal"]) * 100)) for row in rows)
            self.assertEqual(repaid, 50000000)
            self.assertEqual(rows[-1]["balance"], "0.00")
            self.assertIn(str(target), result.outputs)


class Refusals(unittest.TestCase):
    def test_a_tenure_of_no_months_is_refused(self):
        self.assertIn("0 months", refused(years=0, months=0))

    def test_a_zero_loan_is_refused(self):
        self.assertIn("₹0", refused(principal=0.0))

    def test_a_negative_extra_is_refused(self):
        self.assertIn("cannot be negative", refused(extra=-100.0))

    def test_a_loan_whose_instalment_rounds_to_nothing_is_refused_by_name(self):
        error = refused(principal=1.0, rate=50.0, years=40, months=0)
        self.assertIn("Nothing would be repaid", error)
        self.assertIn("never end", error)


if __name__ == "__main__":
    unittest.main(verbosity=2)
