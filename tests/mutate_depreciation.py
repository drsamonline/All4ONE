"""Mutation check for Depreciation Schedule: every mutation must turn the suite red.

Each mutation is a small edit to ``tools/numbers.py`` that a careless implementation
would plausibly have made. If a mutation survives, the tests are not pinning the
behaviour they claim to pin.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tools" / "numbers.py"

MUTATIONS = [
    ("the last year is the usual charge, so the book value never lands on the salvage",
     "        if year == years:\n"
     "            charge = opening - salvage\n"
     "        elif rate is None:",
     "        if False:\n"
     "            charge = opening - salvage\n"
     "        elif rate is None:"),
    ("the written-down rate is salvage/cost spread over the life, not compounded",
     "    rate = None if method == \"Straight line\" else 1 - (salvage / cost) ** (1 / years)",
     "    rate = None if method == \"Straight line\" else 1 - (salvage / cost) / years"),
    ("a written-down charge is not capped, so the balance can cross the salvage value",
     "            charge = int(round(opening * rate))\n"
     "            charge = min(charge, opening - salvage)",
     "            charge = int(round(opening * rate))"),
    ("the charge is rounded to whole rupees, not paise",
     "            charge = int(round(depreciable / years))",
     "            charge = int(round(depreciable / years / 100)) * 100"),
    ("a salvage value above the cost is accepted",
     "    if salvage > cost:\n"
     "        raise ToolError(\n"
     "            f\"A salvage value of {_rupees(salvage)} is more than the {_rupees(cost)} the \"\n"
     "            \"asset cost, so the schedule would have to depreciate a negative amount.\")",
     "    if salvage > cost:\n"
     "        salvage = cost"),
    ("written-down value with no salvage is allowed, writing it all off in year one",
     "    if method == \"Written-down value\" and salvage == 0:",
     "    if False:"),
    ("a charge too small to hold in paise is printed as a column of zeroes",
     "    if depreciable > 0 and rows[0][\"charge\"] == 0:",
     "    if False:"),
    ("the written-off column is the year's share, not the running total",
     "                      \"written off\": f\"{written / cost * 100:.1f}%\"})",
     "                      \"written off\": f\"{row['charge'] / cost * 100:.1f}%\"})"),
    ("the note that the last year is the remainder is dropped",
     "    if rows[-1][\"charge\"] != usual:",
     "    if False:"),
    ("a life of zero years is quietly treated as one",
     "    if years <= 0:\n"
     "        raise ToolError(\"A useful life of 0 years has no years in it — give it at least one.\")",
     "    years = max(years, 1)"),
]


def run_suite() -> bool:
    """True when the suite is green."""
    result = subprocess.run([sys.executable, "tests/test_depreciation.py"],
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
