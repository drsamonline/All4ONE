"""Mutation check for Amortisation Schedule: every mutation must turn the suite red.

Each mutation is a small edit to tools/numbers.py that a careless implementation
would plausibly have made. If a mutation survives, the tests are not pinning the
behaviour they claim to pin.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path("/scratch/work/All4ONE")
SOURCE = ROOT / "tools/numbers.py"

MUTATIONS = [
    ("total interest from the formula, not the rows",
     '    interest_paid = sum(row["interest"] for row in rows)',
     '    interest_paid = emi * len(rows) - principal'),
    ("the last instalment is the usual one, so the loan ends on a paisa",
     "        if month == months:\n"
     "            # The last instalment is the balance and its interest: rounding the\n"
     "            # instalment to the paisa always leaves a few paise, and charging a\n"
     "            # 61st payment of ₹0.02 to a 60-month loan is not a schedule.\n"
     "            payment = balance + interest\n"
     "        else:\n"
     "            payment = min(emi + extra, balance + interest)",
     "        payment = min(emi + extra, balance + interest)"),
    ("the extra payment is not counted",
     "        saved = plain_interest - interest_paid",
     "        saved = 0"),
    ("months saved is not counted",
     '"months_saved": months - len(rows)',
     '"months_saved": 0'),
    ("the zero-rate branch is gone",
     "    if monthly_rate == 0:\n"
     "        emi = -(-principal // months)      # rounded up, so the last one is the small one\n"
     "    else:\n",
     "    if False:\n"
     "        emi = -(-principal // months)\n"
     "    else:\n"),
    ("the last payment is not capped at the balance",
     "            payment = min(emi + extra, balance + interest)",
     "            payment = emi + extra"),
    ("the part-year note is dropped",
     '        if len(rows) % 12:\n'
     '            ctx.log(f"(the last year holds {len(rows) % 12} instalment(s), not 12)")',
     "        pass"),
    ("interest is rounded to whole rupees, so a month is charged the wrong interest",
     "        interest = round(balance * monthly_rate)",
     "        interest = round(balance * monthly_rate / 100) * 100"),
    ("the year grouping starts at year zero",
     "            year = (row[\"month\"] - 1) // 12 + 1",
     "            year = row[\"month\"] // 12 + 1"),
    ("a zero-month tenure is allowed",
     '    if months <= 0:\n'
     '        raise ToolError("A tenure of 0 months has no instalments in it — give it at least "\n'
     '                        "one month.")',
     "    months = max(months, 1)"),
]


def run_suite() -> bool:
    """True when the suite is green."""
    result = subprocess.run([sys.executable, "tests/test_amortisation.py"],
                            cwd=ROOT, capture_output=True, text=True, timeout=120)
    return result.returncode == 0


def main() -> int:
    original = SOURCE.read_text()
    if not run_suite():
        print("the suite is already red — nothing to measure")
        return 1
    survived = []
    try:
        for name, old, new in MUTATIONS:
            if original.count(old) != 1:
                print(f"SKIP  {name}: the source no longer matches")
                survived.append(name)
                continue
            SOURCE.write_text(original.replace(old, new))
            try:
                green = run_suite()
            except subprocess.TimeoutExpired:
                green = False          # a hang is caught, not survived
            SOURCE.write_text(original)
            print(f"{'SURVIVED' if green else 'killed  '}  {name}")
            if green:
                survived.append(name)
    finally:
        SOURCE.write_text(original)
    print(f"\n{len(MUTATIONS) - len(survived)} of {len(MUTATIONS)} mutations killed")
    return 1 if survived else 0


if __name__ == "__main__":
    raise SystemExit(main())
