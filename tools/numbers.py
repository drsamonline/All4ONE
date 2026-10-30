"""Numbers — units, money, dates, statistics and everyday calculations."""

from __future__ import annotations

import math
import statistics as stats
from datetime import date, datetime, timedelta, timezone

from core.tool import F, ToolError, tool

from ._util import report_table

UNITS = {
    "Length": {"mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0, "inch": 0.0254,
               "foot": 0.3048, "yard": 0.9144, "mile": 1609.344, "nautical mile": 1852.0},
    "Mass": {"mg": 1e-6, "g": 0.001, "kg": 1.0, "tonne": 1000.0, "ounce": 0.0283495,
             "pound": 0.453592, "stone": 6.35029},
    "Area": {"mm²": 1e-6, "cm²": 1e-4, "m²": 1.0, "km²": 1e6, "hectare": 10000.0,
             "acre": 4046.86, "sq foot": 0.092903, "sq yard": 0.836127, "bigha": 2529.28,
             "guntha": 101.17},
    "Volume": {"ml": 0.001, "litre": 1.0, "m³": 1000.0, "cup": 0.24, "pint": 0.473,
               "gallon (US)": 3.785, "gallon (UK)": 4.546, "tablespoon": 0.0148},
    "Speed": {"m/s": 1.0, "km/h": 0.277778, "mph": 0.44704, "knot": 0.514444, "ft/s": 0.3048},
    "Data": {"byte": 1.0, "KB": 1024.0, "MB": 1024.0 ** 2, "GB": 1024.0 ** 3,
             "TB": 1024.0 ** 4, "PB": 1024.0 ** 5, "bit": 0.125, "kbit": 128.0,
             "Mbit": 131072.0, "Gbit": 134217728.0},
    "Time": {"millisecond": 0.001, "second": 1.0, "minute": 60.0, "hour": 3600.0,
             "day": 86400.0, "week": 604800.0, "month (30d)": 2592000.0,
             "year (365d)": 31536000.0},
    "Energy": {"joule": 1.0, "calorie": 4.184, "kilocalorie": 4184.0, "kWh": 3.6e6,
               "BTU": 1055.06},
    "Pressure": {"pascal": 1.0, "kPa": 1000.0, "bar": 100000.0, "psi": 6894.76,
                 "mmHg": 133.322, "atm": 101325.0},
}

TEMPERATURES = ["Celsius", "Fahrenheit", "Kelvin"]


@tool(id="unit-convert", name="Unit Converter", category="Numbers",
      summary="Convert length, mass, area, volume, speed, data, time, energy or pressure.",
      fields=[F.choice("category", "What", list(UNITS), "Length"),
              F.number("value", "Value", 1.0),
              F.text("from_unit", "From unit", "km"),
              F.text("to_unit", "To unit", "mile")])
def unit_convert(v, ctx):
    table = UNITS[v["category"]]
    source, target = v["from_unit"].strip(), v["to_unit"].strip()
    lower = {key.lower(): key for key in table}
    if source.lower() not in lower:
        raise ToolError(f"Unknown unit {source!r}. Try: {', '.join(table)}")
    if target.lower() not in lower:
        raise ToolError(f"Unknown unit {target!r}. Try: {', '.join(table)}")
    result = v["value"] * table[lower[source.lower()]] / table[lower[target.lower()]]
    ctx.log(f"{v['value']:g} {lower[source.lower()]} = {result:,.6g} {lower[target.lower()]}")
    return {"value": v["value"], "from": lower[source.lower()],
            "to": lower[target.lower()], "result": round(result, 6)}


@tool(id="temperature-convert", name="Temperature Converter", category="Numbers",
      summary="Convert between Celsius, Fahrenheit and Kelvin, with fever bands for reference.",
      fields=[F.number("value", "Temperature", 37.0),
              F.choice("from_unit", "From", TEMPERATURES, "Celsius")])
def temperature_convert(v, ctx):
    value = v["value"]
    unit = v["from_unit"]
    celsius = (value if unit == "Celsius" else
               (value - 32) * 5 / 9 if unit == "Fahrenheit" else value - 273.15)
    result = {"Celsius": round(celsius, 2),
              "Fahrenheit": round(celsius * 9 / 5 + 32, 2),
              "Kelvin": round(celsius + 273.15, 2)}
    ctx.log(report_table([{"scale": k, "value": str(val)} for k, val in result.items()]))
    if 36.1 <= celsius <= 37.2:
        ctx.log("In the normal human body-temperature range")
    elif celsius > 38:
        ctx.log("Above 38 °C — that is a fever (see a doctor if it persists)")
    return result


@tool(id="bytes-units", name="Data Size Converter", category="Numbers",
      summary="Convert between bytes, KB, MB, GB and TB, and show what a file costs to transfer.",
      fields=[F.number("value", "Value", 1.0),
              F.choice("from_unit", "From", ["byte", "KB", "MB", "GB", "TB"], "MB"),
              F.number("speed_mbps", "…at this connection speed (Mbps)", 0.0, minimum=0.0)])
def bytes_units(v, ctx):
    factors = {"byte": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3, "TB": 1024 ** 4}
    total = v["value"] * factors[v["from_unit"]]
    rows = [{"unit": unit, "value": f"{total / factor:,.4f}"} for unit, factor in factors.items()]
    ctx.log(report_table(rows))
    result = {unit: round(total / factor, 4) for unit, factor in factors.items()}
    if v["speed_mbps"] > 0:
        seconds = total * 8 / (v["speed_mbps"] * 1_000_000)
        ctx.log(f"Transfer time at {v['speed_mbps']:g} Mbps: {seconds:.1f} seconds")
        result["transfer_seconds"] = round(seconds, 1)
    return result


@tool(id="base-convert", name="Number Base Converter", category="Numbers",
      summary="Convert a number between binary, octal, decimal, hex and any base up to 36.",
      fields=[F.text("number", "Number", "255", required=True),
              F.integer("from_base", "From base", 10, minimum=2, maximum=36),
              F.integer("to_base", "To base", 16, minimum=2, maximum=36)])
def base_convert(v, ctx):
    try:
        value = int(str(v["number"]).strip(), v["from_base"])
    except ValueError as exc:
        raise ToolError(f"{v['number']!r} is not a base-{v['from_base']} number") from exc
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if v["to_base"] == 10:
        converted = str(value)
    else:
        out = []
        remaining = abs(value)
        while remaining:
            out.append(digits[remaining % v["to_base"]])
            remaining //= v["to_base"]
        converted = ("-" if value < 0 else "") + ("".join(reversed(out)) or "0")
    ctx.log(f"binary:  {value:b}")
    ctx.log(f"octal:   {value:o}")
    ctx.log(f"decimal: {value}")
    ctx.log(f"hex:     {value:X}")
    return {"value": value, "base": v["to_base"], "result": converted}


@tool(id="percentage", name="Percentage Calculator", category="Numbers",
      summary="What is X% of Y, what percent is X of Y, and percent increase or decrease.",
      fields=[F.number("x", "X", 25.0),
              F.number("y", "Y", 200.0),
              F.choice("mode", "Work out",
                       ["X% of Y", "X is what % of Y", "Change from X to Y",
                        "Y increased by X%", "Y decreased by X%"], "X% of Y")])
def percentage(v, ctx):
    x, y = v["x"], v["y"]
    mode = v["mode"]
    if mode == "X% of Y":
        result = y * x / 100
        ctx.log(f"{x:g}% of {y:g} = {result:,.4g}")
    elif mode == "X is what % of Y":
        if y == 0:
            raise ToolError("Y cannot be zero here")
        result = x / y * 100
        ctx.log(f"{x:g} is {result:.2f}% of {y:g}")
    elif mode == "Change from X to Y":
        if x == 0:
            raise ToolError("The starting value cannot be zero")
        result = (y - x) / abs(x) * 100
        direction = "increase" if result >= 0 else "decrease"
        ctx.log(f"{direction} of {abs(result):.2f}%")
    elif mode == "Y increased by X%":
        result = y * (1 + x / 100)
        ctx.log(f"{y:g} + {x:g}% = {result:,.4g}")
    else:
        result = y * (1 - x / 100)
        ctx.log(f"{y:g} − {x:g}% = {result:,.4g}")
    return {"mode": mode, "result": round(result, 6)}


@tool(id="gst-calc", name="GST Calculator", category="Numbers",
      summary="Add or remove GST at any rate, and split CGST/SGST or IGST correctly.",
      fields=[F.number("amount", "Amount (₹)", 10000.0, minimum=0.0),
              F.choice("rate", "GST rate", ["5", "12", "18", "28", "0.25", "3"], "18"),
              F.choice("mode", "Amount is", ["Before GST (add it)", "Including GST (remove it)"],
                       "Before GST (add it)"),
              F.choice("supply", "Supply type", ["Intra-state (CGST + SGST)", "Inter-state (IGST)"],
                       "Intra-state (CGST + SGST)")])
def gst_calc(v, ctx):
    rate = float(v["rate"])
    amount = v["amount"]
    if v["mode"].startswith("Before"):
        base = amount
        gst = amount * rate / 100
        total = base + gst
    else:
        total = amount
        base = amount / (1 + rate / 100)
        gst = total - base
    if v["supply"].startswith("Intra"):
        split = {"CGST": gst / 2, "SGST": gst / 2}
    else:
        split = {"IGST": gst}
    rows = [{"line": "Taxable value", "amount": f"₹{base:,.2f}"}]
    rows += [{"line": f"{name} @ {rate / (2 if len(split) == 2 else 1):g}%",
              "amount": f"₹{value:,.2f}"} for name, value in split.items()]
    rows.append({"line": "Total", "amount": f"₹{total:,.2f}"})
    ctx.log(report_table(rows, ["line", "amount"]))
    return {"taxable_value": round(base, 2), "gst": round(gst, 2),
            "total": round(total, 2), "rate": rate,
            "breakdown": {name: round(value, 2) for name, value in split.items()}}


@tool(id="emi-calc", name="Loan EMI Calculator", category="Numbers",
      summary="Monthly EMI, total interest and a year-by-year repayment split.",
      fields=[F.number("principal", "Loan amount (₹)", 500000.0, minimum=1.0),
              F.number("rate", "Annual interest rate (%)", 9.5, minimum=0.0, maximum=50.0),
              F.integer("years", "Tenure (years)", 5, minimum=1, maximum=40),
              F.integer("months", "…plus months", 0, minimum=0, maximum=11)])
def emi_calc(v, ctx):
    months = v["years"] * 12 + v["months"]
    monthly_rate = v["rate"] / 12 / 100
    principal = v["principal"]
    if monthly_rate == 0:
        emi = principal / months
    else:
        factor = (1 + monthly_rate) ** months
        emi = principal * monthly_rate * factor / (factor - 1)
    total = emi * months
    rows = []
    balance = principal
    for year in range(1, v["years"] + 1):
        paid_interest = 0.0
        paid_principal = 0.0
        for _ in range(12):
            if balance <= 0:
                break
            interest = balance * monthly_rate
            principal_part = emi - interest
            paid_interest += interest
            paid_principal += principal_part
            balance -= principal_part
        rows.append({"year": year, "principal_paid": f"₹{paid_principal:,.0f}",
                     "interest_paid": f"₹{paid_interest:,.0f}",
                     "balance": f"₹{max(0, balance):,.0f}"})
    ctx.log(report_table(rows, ["year", "principal_paid", "interest_paid", "balance"]))
    return {"monthly_emi": round(emi, 2), "months": months,
            "total_payment": round(total, 2),
            "total_interest": round(total - principal, 2),
            "interest_share": f"{(total - principal) / total * 100:.1f}%"}


@tool(id="compound-interest", name="Compound Interest", category="Numbers",
      summary="Growth of an investment with monthly, quarterly or yearly compounding.",
      fields=[F.number("principal", "Amount invested (₹)", 100000.0, minimum=0.0),
              F.number("rate", "Annual return (%)", 12.0, minimum=0.0, maximum=100.0),
              F.integer("years", "Years", 10, minimum=1, maximum=80),
              F.choice("frequency", "Compounded", ["Yearly", "Half-yearly", "Quarterly", "Monthly"],
                       "Yearly"),
              F.number("monthly_add", "…plus monthly contribution (₹)", 0.0, minimum=0.0)])
def compound_interest(v, ctx):
    periods = {"Yearly": 1, "Half-yearly": 2, "Quarterly": 4, "Monthly": 12}[v["frequency"]]
    rate = v["rate"] / 100 / periods
    balance = v["principal"]
    monthly_rate = v["rate"] / 100 / 12
    rows = []
    for year in range(1, v["years"] + 1):
        for _ in range(periods):
            balance *= (1 + rate)
        if v["monthly_add"]:
            for _ in range(12):
                balance += v["monthly_add"]
                balance *= (1 + monthly_rate)
        rows.append({"year": year, "balance": f"₹{balance:,.0f}"})
    invested = v["principal"] + v["monthly_add"] * 12 * v["years"]
    ctx.log(report_table(rows[::max(1, v["years"] // 10)] or rows, ["year", "balance"]))
    return {"final_value": round(balance, 2), "invested": round(invested, 2),
            "gain": round(balance - invested, 2),
            "multiple": round(balance / invested, 2) if invested else 0}


@tool(id="simple-interest", name="Simple Interest", category="Numbers",
      summary="Straight-line interest on a principal, as used for many loans and deposits.",
      fields=[F.number("principal", "Principal (₹)", 100000.0, minimum=0.0),
              F.number("rate", "Annual rate (%)", 8.0, minimum=0.0),
              F.number("years", "Time (years)", 3.0, minimum=0.0, maximum=100.0)])
def simple_interest(v, ctx):
    interest = v["principal"] * v["rate"] * v["years"] / 100
    return {"principal": v["principal"], "interest": round(interest, 2),
            "total": round(v["principal"] + interest, 2),
            "per_month": round(interest / max(v["years"] * 12, 1), 2)}


@tool(id="discount", name="Discount Calculator", category="Numbers",
      summary="Sale price, amount saved, and the effective discount between two prices.",
      fields=[F.number("price", "Original price (₹)", 2499.0, minimum=0.0),
              F.number("discount", "Discount (%)", 30.0, minimum=0.0, maximum=100.0),
              F.number("extra", "Extra coupon off (₹)", 0.0, minimum=0.0)])
def discount(v, ctx):
    after_percent = v["price"] * (1 - v["discount"] / 100)
    final = max(0.0, after_percent - v["extra"])
    saved = v["price"] - final
    return {"final_price": round(final, 2), "you_save": round(saved, 2),
            "effective_discount": f"{saved / v['price'] * 100:.1f}%" if v["price"] else "0%"}


@tool(id="indian-currency", name="Format Indian Currency", category="Numbers",
      summary="Write an amount the Indian way — lakhs, crores and 2,34,567 grouping.",
      fields=[F.number("amount", "Amount", 12345678.0),
              F.flag("words", "Also write it in words", True)])
def indian_currency(v, ctx):
    amount = v["amount"]
    negative = amount < 0
    whole = int(abs(amount))
    paise = round((abs(amount) - whole) * 100)
    text = str(whole)
    if len(text) > 3:
        head, tail = text[:-3], text[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        text = ",".join(groups) + "," + tail
    formatted = ("-" if negative else "") + "₹" + text
    if paise:
        formatted += f".{paise:02d}"
    ctx.log(formatted)
    if whole >= 10_000_000:
        ctx.log(f"≈ ₹{whole / 10_000_000:,.2f} crore")
    elif whole >= 100_000:
        ctx.log(f"≈ ₹{whole / 100_000:,.2f} lakh")
    result = {"formatted": formatted, "crore": round(whole / 10_000_000, 4),
              "lakh": round(whole / 100_000, 4)}
    if v["words"]:
        result["words"] = _indian_words(whole)
        ctx.log(result["words"])
    return result


def _indian_words(number: int) -> str:
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
            "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
            "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

    def below_hundred(value: int) -> str:
        if value < 20:
            return ones[value]
        return (tens[value // 10] + (" " + ones[value % 10] if value % 10 else "")).strip()

    if number == 0:
        return "zero rupees"
    parts = []
    for divisor, label in ((10_000_000, "crore"), (100_000, "lakh"), (1000, "thousand")):
        if number >= divisor:
            chunk = number // divisor
            number %= divisor
            parts.append(f"{below_hundred(chunk) if chunk < 100 else _indian_words(chunk).replace(' rupees', '')} {label}")
    if number >= 100:
        parts.append(f"{below_hundred(number // 100)} hundred")
        number %= 100
    if number:
        parts.append(below_hundred(number))
    return " ".join(parts) + " rupees"


@tool(id="date-diff", name="Date Difference", category="Numbers",
      summary="Days, weeks, months and working days between two dates.",
      fields=[F.text("from_date", "From (YYYY-MM-DD)", "2024-01-01", required=True),
              F.text("to_date", "To (YYYY-MM-DD)", "2025-01-01", required=True)])
def date_diff(v, ctx):
    try:
        start = datetime.strptime(v["from_date"].strip(), "%Y-%m-%d").date()
        end = datetime.strptime(v["to_date"].strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ToolError("Use dates in the form YYYY-MM-DD") from exc
    days = (end - start).days
    working = sum(1 for offset in range(abs(days))
                  if (start + timedelta(days=offset * (1 if days >= 0 else -1))).weekday() < 5)
    months = (end.year - start.year) * 12 + end.month - start.month
    if end.day < start.day:
        months -= 1
    return {"days": days, "weeks": round(days / 7, 2), "months": months,
            "years": round(days / 365.25, 2), "working_days": working,
            "from": str(start), "to": str(end)}


@tool(id="date-add", name="Add to a Date", category="Numbers",
      summary="Add or subtract days, weeks, months or years from a date.",
      fields=[F.text("start", "Start date (YYYY-MM-DD)", help="Blank = today"),
              F.integer("days", "Days", 0),
              F.integer("weeks", "Weeks", 0),
              F.integer("months", "Months", 0),
              F.integer("years", "Years", 0)])
def date_add(v, ctx):
    text = v["start"].strip()
    if text:
        try:
            start = datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ToolError("Use YYYY-MM-DD") from exc
    else:
        start = date.today()
    month = start.month - 1 + v["months"] + v["years"] * 12
    year = start.year + month // 12
    month = month % 12 + 1
    day = min(start.day, [31, 29 if year % 4 == 0 and (year % 100 or year % 400 == 0) else 28,
                          31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    result = date(year, month, day) + timedelta(days=v["days"] + v["weeks"] * 7)
    return {"start": str(start), "result": str(result),
            "weekday": result.strftime("%A"), "iso_week": result.isocalendar()[1]}


@tool(id="age-calc", name="Age Calculator", category="Numbers",
      summary="Exact age in years, months and days, plus the next birthday countdown.",
      fields=[F.text("birthdate", "Date of birth (YYYY-MM-DD)", "1990-05-15", required=True)])
def age_calc(v, ctx):
    try:
        born = datetime.strptime(v["birthdate"].strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ToolError("Use YYYY-MM-DD") from exc
    today = date.today()
    if born > today:
        raise ToolError("That date is in the future")
    years = today.year - born.year
    months = today.month - born.month
    days = today.day - born.day
    if days < 0:
        months -= 1
        previous_month = (today.month - 1) or 12
        previous_year = today.year if today.month > 1 else today.year - 1
        days += [31, 29 if previous_year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30,
                 31, 30, 31][previous_month - 1]
    if months < 0:
        years -= 1
        months += 12
    next_birthday = date(today.year, born.month, min(born.day, 28 if born.month == 2 else born.day))
    if next_birthday < today:
        next_birthday = date(today.year + 1, born.month, min(born.day, 28 if born.month == 2 else born.day))
    return {"age": f"{years} years, {months} months, {days} days",
            "total_days": (today - born).days,
            "next_birthday": str(next_birthday),
            "days_until_birthday": (next_birthday - today).days,
            "born_on_a": born.strftime("%A")}


@tool(id="epoch-convert", name="Epoch / Timestamp Converter", category="Numbers",
      summary="Convert between Unix timestamps and readable dates, in your local time and UTC.",
      fields=[F.text("value", "Timestamp or date", "now",
                     help="Seconds, milliseconds, ISO date, or 'now'"),
              F.flag("milliseconds", "The timestamp is in milliseconds", False)])
def epoch_convert(v, ctx):
    raw = v["value"].strip().lower() or "now"
    if raw in ("now", "today"):
        moment = datetime.now()
    elif raw.replace(".", "", 1).lstrip("-").isdigit():
        number = float(raw)
        if v["milliseconds"] or abs(number) > 1e11:
            number /= 1000
        moment = datetime.fromtimestamp(number)
    else:
        text = raw.replace("Z", "+00:00")
        try:
            moment = datetime.fromisoformat(text)
        except ValueError:
            for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y"):
                try:
                    moment = datetime.strptime(text, pattern)
                    break
                except ValueError:
                    continue
            else:
                raise ToolError("Give a Unix timestamp, an ISO date, or 'now'")
    utc = moment.astimezone(timezone.utc) if moment.tzinfo else \
        moment.replace(tzinfo=None)
    return {
        "local": moment.strftime("%Y-%m-%d %H:%M:%S"),
        "utc": (utc.strftime("%Y-%m-%d %H:%M:%S") if utc else ""),
        "iso_8601": moment.isoformat(),
        "unix_seconds": int(moment.timestamp()),
        "unix_milliseconds": int(moment.timestamp() * 1000),
        "weekday": moment.strftime("%A"),
        "day_of_year": moment.timetuple().tm_yday,
        "iso_week": moment.isocalendar()[1],
    }


@tool(id="timezone-convert", name="Time Zone Converter", category="Numbers",
      summary="Turn a moment in one time zone into the same moment in another.",
      fields=[F.text("when", "Date and time (YYYY-MM-DD HH:MM)", "2026-01-15 09:00"),
              F.text("from_zone", "From (UTC offset or name)", "IST"),
              F.text("to_zone", "To", "UTC")])
def timezone_convert(v, ctx):
    offsets = {"IST": 5.5, "UTC": 0.0, "GMT": 0.0, "EST": -5.0, "EDT": -4.0, "CST": -6.0,
               "PST": -8.0, "CET": 1.0, "CEST": 2.0, "JST": 9.0, "AEST": 10.0,
               "GST": 4.0, "SGT": 8.0, "HKT": 8.0, "MSK": 3.0, "BRT": -3.0}
    try:
        moment = datetime.strptime(v["when"].strip(), "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise ToolError("Use YYYY-MM-DD HH:MM") from exc

    def offset_of(name: str) -> float:
        text = name.strip().upper()
        if text in offsets:
            return offsets[text]
        try:
            return float(text.replace("UTC", "").replace("+", "").strip() or 0)
        except ValueError as exc:
            raise ToolError(f"Unknown zone {name!r}. Try IST, UTC, EST, or an offset like +5.5") from exc

    source = offset_of(v["from_zone"])
    target = offset_of(v["to_zone"])
    utc_moment = moment - timedelta(hours=source)
    converted = utc_moment + timedelta(hours=target)
    return {"input": f"{moment:%Y-%m-%d %H:%M} {v['from_zone'].upper()}",
            "utc": f"{utc_moment:%Y-%m-%d %H:%M}",
            "converted": f"{converted:%Y-%m-%d %H:%M} {v['to_zone'].upper()}",
            "difference_hours": target - source}


@tool(id="working-days", name="Working Days", category="Numbers",
      summary="Count business days in a month or between two dates, skipping weekends.",
      fields=[F.text("start", "From (YYYY-MM-DD)", help="Blank = the 1st of this month"),
              F.text("end", "To (YYYY-MM-DD)", help="Blank = the last day of this month"),
              F.text("holidays", "Holidays (YYYY-MM-DD, comma separated)", "")])
def working_days(v, ctx):
    today = date.today()
    start_text = v["start"].strip()
    end_text = v["end"].strip()
    try:
        start = datetime.strptime(start_text, "%Y-%m-%d").date() if start_text else today.replace(day=1)
        end = datetime.strptime(end_text, "%Y-%m-%d").date() if end_text else (
            today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    except ValueError as exc:
        raise ToolError("Use YYYY-MM-DD") from exc
    holidays = set()
    for chunk in v["holidays"].split(","):
        chunk = chunk.strip()
        if chunk:
            try:
                holidays.add(datetime.strptime(chunk, "%Y-%m-%d").date())
            except ValueError:
                raise ToolError(f"{chunk!r} is not a YYYY-MM-DD date")
    total = 0
    working = 0
    moment = start
    while moment <= end:
        total += 1
        if moment.weekday() < 5 and moment not in holidays:
            working += 1
        moment += timedelta(days=1)
    return {"from": str(start), "to": str(end), "total_days": total,
            "working_days": working, "weekend_days": total - working,
            "holidays_excluded": len([d for d in holidays if start <= d <= end])}


@tool(id="roman", name="Roman Numerals", category="Numbers",
      summary="Convert a number to Roman numerals, or Roman numerals back to a number.",
      fields=[F.text("value", "Number or numerals", "2026", required=True)])
def roman(v, ctx):
    text = v["value"].strip().upper()
    if text.isdigit():
        number = int(text)
        if not 0 < number < 4000:
            raise ToolError("Roman numerals here cover 1 to 3999")
        table = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
                 (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
        out = ""
        for value_, symbol in table:
            count, number = divmod(number, value_)
            out += symbol * count
        return {"number": int(text), "roman": out}
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    if not all(ch in values for ch in text):
        raise ToolError("That is not a Roman numeral")
    total = 0
    for index, ch in enumerate(text):
        value_ = values[ch]
        if index + 1 < len(text) and values[text[index + 1]] > value_:
            total -= value_
        else:
            total += value_
    return {"roman": text, "number": total}


@tool(id="number-words", name="Number to Words", category="Numbers",
      summary="Write a number out in English, using the Indian lakh/crore system.",
      fields=[F.number("number", "Number", 1234567.0)])
def number_words(v, ctx):
    whole = int(v["number"])
    text = _indian_words(abs(whole))
    if whole < 0:
        text = "minus " + text
    ctx.log(text)
    return {"number": whole, "words": text}


@tool(id="prime", name="Prime Check & Factorise", category="Numbers",
      summary="Test whether a number is prime, and break any number into its prime factors.",
      fields=[F.integer("number", "Number", 360, minimum=1, maximum=10 ** 12)])
def prime(v, ctx):
    number = v["number"]
    if number < 2:
        return {"number": number, "prime": False, "note": "1 and below are not prime"}
    is_prime = True
    divisor = 2
    while divisor * divisor <= number:
        if number % divisor == 0:
            is_prime = False
            break
        divisor += 1 if divisor == 2 else 2
    factors = []
    remaining = number
    divisor = 2
    while divisor * divisor <= remaining:
        while remaining % divisor == 0:
            factors.append(divisor)
            remaining //= divisor
        divisor += 1 if divisor == 2 else 2
    if remaining > 1:
        factors.append(remaining)
    expression = " × ".join(str(factor) for factor in factors)
    ctx.log(f"{number} = {expression}")
    return {"number": number, "prime": is_prime, "factors": factors,
            "factorisation": expression,
            "divisor_count": _divisor_count(factors)}


def _divisor_count(factors: list[int]) -> int:
    counts: dict[int, int] = {}
    for factor in factors:
        counts[factor] = counts.get(factor, 0) + 1
    total = 1
    for count in counts.values():
        total *= count + 1
    return total


@tool(id="gcd-lcm", name="GCD & LCM", category="Numbers",
      summary="Greatest common divisor and least common multiple of a list of numbers.",
      fields=[F.text("numbers", "Numbers (comma separated)", "24, 36, 60", required=True)])
def gcd_lcm(v, ctx):
    try:
        values = [int(chunk.strip()) for chunk in v["numbers"].split(",") if chunk.strip()]
    except ValueError as exc:
        raise ToolError("Give whole numbers separated by commas") from exc
    if len(values) < 2:
        raise ToolError("Give at least two numbers")
    divisor = values[0]
    multiple = values[0]
    for value in values[1:]:
        divisor = math.gcd(divisor, value)
        multiple = multiple * value // math.gcd(multiple, value)
    return {"numbers": values, "gcd": divisor, "lcm": multiple}


@tool(id="statistics", name="Statistics", category="Numbers",
      summary="Mean, median, mode, standard deviation, quartiles and outliers for a list.",
      fields=[F.text("numbers", "Numbers (comma or space separated)", required=True),
              F.flag("outliers", "Flag outliers (1.5 × IQR rule)", True)])
def statistics_tool(v, ctx):
    raw = v["numbers"].replace(",", " ").split()
    try:
        values = [float(item) for item in raw]
    except ValueError:
        raise ToolError("Give numbers separated by commas or spaces")
    if len(values) < 2:
        raise ToolError("Give at least two numbers")
    values.sort()
    quartiles = stats.quantiles(values, n=4) if len(values) >= 4 else [values[0], values[len(values) // 2], values[-1]]
    result = {
        "count": len(values),
        "sum": round(sum(values), 6),
        "mean": round(stats.mean(values), 6),
        "median": round(stats.median(values), 6),
        "mode": stats.multimode(values)[:5],
        "min": min(values), "max": max(values),
        "range": round(max(values) - min(values), 6),
        "std_dev_sample": round(stats.stdev(values), 6) if len(values) > 1 else 0,
        "std_dev_population": round(stats.pstdev(values), 6),
        "q1": round(quartiles[0], 6), "q3": round(quartiles[2], 6),
        "iqr": round(quartiles[2] - quartiles[0], 6),
    }
    if v["outliers"]:
        low = quartiles[0] - 1.5 * (quartiles[2] - quartiles[0])
        high = quartiles[2] + 1.5 * (quartiles[2] - quartiles[0])
        result["outliers"] = [value for value in values if value < low or value > high]
    ctx.log(report_table([{"measure": k, "value": str(val)} for k, val in result.items()]))
    return result


@tool(id="quadratic", name="Quadratic Solver", category="Numbers",
      summary="Roots, vertex and discriminant for ax² + bx + c = 0.",
      fields=[F.number("a", "a", 1.0), F.number("b", "b", -3.0), F.number("c", "c", 2.0)])
def quadratic(v, ctx):
    a, b, c = v["a"], v["b"], v["c"]
    if a == 0:
        if b == 0:
            raise ToolError("That is not an equation with a solution")
        return {"linear_root": round(-c / b, 6)}
    discriminant = b * b - 4 * a * c
    vertex_x = -b / (2 * a)
    vertex_y = a * vertex_x ** 2 + b * vertex_x + c
    if discriminant > 0:
        root = math.sqrt(discriminant)
        roots = [round((-b + root) / (2 * a), 6), round((-b - root) / (2 * a), 6)]
        nature = "two real roots"
    elif discriminant == 0:
        roots = [round(vertex_x, 6)]
        nature = "one repeated real root"
    else:
        real = round(vertex_x, 6)
        imaginary = round(math.sqrt(-discriminant) / (2 * a), 6)
        roots = [f"{real} + {abs(imaginary)}i", f"{real} - {abs(imaginary)}i"]
        nature = "two complex roots"
    return {"a": a, "b": b, "c": c, "discriminant": discriminant, "nature": nature,
            "roots": roots, "vertex": {"x": round(vertex_x, 6), "y": round(vertex_y, 6)}}


@tool(id="ratio", name="Simplify a Ratio", category="Numbers",
      summary="Reduce a ratio to its simplest form, and split an amount in that ratio.",
      fields=[F.text("ratio", "Ratio", "16:9", required=True),
              F.number("total", "Split this amount", 0.0, minimum=0.0)])
def ratio(v, ctx):
    parts = [chunk.strip() for chunk in v["ratio"].replace("/", ":").split(":") if chunk.strip()]
    try:
        values = [float(part) for part in parts]
    except ValueError as exc:
        raise ToolError("A ratio looks like 16:9 or 3:2:1") from exc
    if len(values) < 2:
        raise ToolError("Give at least two parts")
    scaled = [int(round(value * 1000)) for value in values]
    divisor = scaled[0]
    for value in scaled[1:]:
        divisor = math.gcd(divisor, value)
    simplified = [int(value // divisor) for value in scaled]
    result = {"ratio": v["ratio"], "simplified": ":".join(str(part) for part in simplified),
              "decimal": round(values[0] / values[1], 4)}
    if v["total"] > 0:
        total_parts = sum(values)
        shares = [round(v["total"] * value / total_parts, 2) for value in values]
        result["shares"] = shares
        ctx.log("Split: " + ", ".join(f"{share:,.2f}" for share in shares))
    ctx.log(f"Simplified: {result['simplified']}")
    return result


@tool(id="aspect-ratio", name="Aspect Ratio Helper", category="Numbers",
      summary="Reduce a resolution to its aspect ratio, or work out a matching size.",
      fields=[F.integer("width", "Width", 1920, minimum=1),
              F.integer("height", "Height", 1080, minimum=1),
              F.integer("target_width", "New width (0 = ignore)", 0, minimum=0)])
def aspect_ratio(v, ctx):
    divisor = math.gcd(v["width"], v["height"])
    result = {"resolution": f"{v['width']}×{v['height']}",
              "ratio": f"{v['width'] // divisor}:{v['height'] // divisor}",
              "decimal": round(v["width"] / v["height"], 4),
              "megapixels": round(v["width"] * v["height"] / 1_000_000, 2)}
    if v["target_width"]:
        result["matching_height"] = round(v["target_width"] * v["height"] / v["width"])
        ctx.log(f"{v['target_width']} × {result['matching_height']}")
    ctx.log(f"Ratio {result['ratio']}")
    return result


@tool(id="rounding", name="Round Numbers", category="Numbers",
      summary="Round a list of numbers to a chosen precision, or to the nearest 5, 10 or 100.",
      fields=[F.text("numbers", "Numbers", "12.3456, 98.7654", required=True),
              F.integer("decimals", "Decimal places", 2, minimum=0, maximum=10),
              F.choice("mode", "Mode", ["Normal", "Always up", "Always down", "Nearest 5",
                                        "Nearest 10", "Nearest 100"], "Normal")])
def rounding(v, ctx):
    try:
        values = [float(item.strip()) for item in v["numbers"].split(",") if item.strip()]
    except ValueError as exc:
        raise ToolError("Give numbers separated by commas") from exc
    mode = v["mode"]
    out = []
    for value in values:
        if mode == "Normal":
            result = round(value, v["decimals"])
        elif mode == "Always up":
            factor = 10 ** v["decimals"]
            result = math.ceil(value * factor) / factor
        elif mode == "Always down":
            factor = 10 ** v["decimals"]
            result = math.floor(value * factor) / factor
        else:
            step = {"Nearest 5": 5, "Nearest 10": 10, "Nearest 100": 100}[mode]
            result = round(value / step) * step
        out.append(result)
    rows = [{"input": original, "rounded": rounded} for original, rounded in zip(values, out)]
    ctx.log(report_table(rows))
    return {"values": out, "total": round(sum(out), 6)}


@tool(id="bmi", name="BMI Calculator", category="Numbers",
      summary="Body mass index with WHO and Indian cut-offs, plus a healthy weight range.",
      fields=[F.number("weight_kg", "Weight (kg)", 70.0, minimum=1.0, maximum=500.0),
              F.number("height_cm", "Height (cm)", 170.0, minimum=30.0, maximum=260.0)])
def bmi(v, ctx):
    metres = v["height_cm"] / 100
    value = v["weight_kg"] / (metres ** 2)
    who = ("Underweight" if value < 18.5 else "Normal" if value < 25 else
           "Overweight" if value < 30 else "Obese class I" if value < 35 else
           "Obese class II" if value < 40 else "Obese class III")
    indian = ("Underweight" if value < 18.5 else "Normal" if value < 23 else
              "Overweight" if value < 25 else "Obese" if value < 30 else "Severely obese")
    healthy_low = 18.5 * metres ** 2
    healthy_high = 24.9 * metres ** 2
    ctx.log(f"BMI {value:.1f} — {who} (WHO), {indian} (Indian cut-offs)")
    return {"bmi": round(value, 1), "who_category": who, "indian_category": indian,
            "healthy_weight_range_kg": [round(healthy_low, 1), round(healthy_high, 1)],
            "note": "BMI is a screening measure, not a diagnosis"}


@tool(id="bmr-tdee", name="BMR & Daily Calories", category="Numbers",
      summary="Resting energy use (Mifflin-St Jeor) and daily calories by activity level.",
      fields=[F.number("weight_kg", "Weight (kg)", 70.0, minimum=1.0),
              F.number("height_cm", "Height (cm)", 170.0, minimum=30.0),
              F.integer("age", "Age (years)", 30, minimum=1, maximum=120),
              F.choice("sex", "Sex", ["Male", "Female"], "Male"),
              F.choice("activity", "Activity level",
                       ["Sedentary (desk, little exercise)", "Light (1–3 days a week)",
                        "Moderate (3–5 days a week)", "Active (6–7 days a week)",
                        "Very active (physical job or twice daily)"],
                       "Light (1–3 days a week)")])
def bmr_tdee(v, ctx):
    base = 10 * v["weight_kg"] + 6.25 * v["height_cm"] - 5 * v["age"]
    bmr = base + 5 if v["sex"] == "Male" else base - 161
    factors = {"Sedentary (desk, little exercise)": 1.2, "Light (1–3 days a week)": 1.375,
               "Moderate (3–5 days a week)": 1.55, "Active (6–7 days a week)": 1.725,
               "Very active (physical job or twice daily)": 1.9}
    tdee = bmr * factors[v["activity"]]
    rows = [{"goal": label, "calories": f"{int(tdee + delta)} kcal"} for label, delta in
            (("Lose 0.5 kg a week", -500), ("Maintain", 0), ("Gain 0.5 kg a week", 500))]
    ctx.log(report_table(rows))
    return {"bmr_kcal": round(bmr), "tdee_kcal": round(tdee),
            "protein_g": round(v["weight_kg"] * 1.6),
            "note": "Estimates only — adjust from real weight trends over 2–3 weeks"}


@tool(id="fluid-requirement", name="Daily Fluid Requirement", category="Numbers",
      summary="A maintenance fluid estimate by weight and activity, in litres and glasses.",
      fields=[F.number("weight_kg", "Weight (kg)", 70.0, minimum=1.0),
              F.choice("activity", "Activity", ["Resting", "Light", "Moderate", "Heavy"],
                       "Light"),
              F.number("hot_day_c", "Temperature (°C)", 30.0, minimum=0.0, maximum=50.0)])
def fluid_requirement(v, ctx):
    base_ml = v["weight_kg"] * 30
    extra = {"Resting": 0, "Light": 300, "Moderate": 600, "Heavy": 1000}[v["activity"]]
    heat = max(0.0, (v["hot_day_c"] - 25) * 50)
    total = base_ml + extra + heat
    return {"litres": round(total / 1000, 2), "ml": round(total),
            "glasses_250ml": round(total / 250),
            "note": "General guidance; heart or kidney conditions need individual advice"}
