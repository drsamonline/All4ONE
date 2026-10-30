"""Generators — passwords, IDs, test data and dummy files."""

from __future__ import annotations

import json
import random
import secrets
import string
import uuid
from datetime import date, datetime, timedelta

from core.tool import F, ToolError, tool

from ._util import human_size, out_path, write_csv, write_text

WORDS = (
    "amber anchor apple arrow atlas autumn badge bamboo basket beacon berry birch "
    "blanket bloom bolt border bottle branch brass breeze bridge bronze brook bubble "
    "cabin cable cactus candle canyon canvas carbon carpet castle cedar chalk cherry "
    "cinder circle cliff cloud clover coast cobalt comet copper coral cotton crane "
    "crater crystal cypress dawn delta desert dune dusk eagle earth ember emerald "
    "falcon feather fern field fjord flame flint forest fossil fountain frost garden "
    "garnet geyser glacier glass globe granite grape grass grove harbor hazel heather "
    "heron hill hollow honey horizon island ivory jade jasper jungle kelp kettle lagoon "
    "lantern laurel lemon lilac linen lotus lunar maple marble meadow mesa meteor mint "
    "mist moss mountain nectar nickel nightingale north oak oasis ocean olive onyx "
    "opal orbit orchid otter palm paper pearl pebble pepper pine planet plum polar "
    "pond poppy prairie prism quartz quill rain raven reef ridge river robin rose "
    "ruby sage sail salt sand sapphire shadow shell silver sky slate snow solar "
    "sparrow spice spring spruce star steel stone storm summit sunset swift thistle "
    "thunder tide timber topaz torch trail tulip tundra turquoise valley velvet vine "
    "violet walnut wave willow window winter wolf wren zephyr"
).split()

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Ananya", "Diya", "Ishaan", "Kabir", "Meera",
               "Neha", "Rohan", "Priya", "Arjun", "Sneha", "Karan", "Riya", "Vikram",
               "Anjali", "Rahul", "Pooja", "Siddharth", "Tanvi", "Nikhil", "Shreya"]
LAST_NAMES = ["Sharma", "Patel", "Iyer", "Nair", "Reddy", "Gupta", "Desai", "Joshi",
              "Menon", "Kulkarni", "Bhatt", "Chopra", "Rao", "Singh", "Verma", "Mehta",
              "Kapoor", "Pillai", "Shetty", "Das"]
CITIES = ["Mumbai", "Delhi", "Bengaluru", "Chennai", "Kolkata", "Pune", "Ahmedabad",
          "Jaipur", "Hyderabad", "Surat", "Lucknow", "Indore", "Bhopal", "Nagpur"]


def _random_date(start: date, end: date) -> date:
    return start + timedelta(days=secrets.randbelow(max(1, (end - start).days)))


@tool(id="password-generate", name="Generate Passwords", category="Generators",
      summary="Strong random passwords with the exact character sets you allow.",
      fields=[F.integer("length", "Length", 20, minimum=6, maximum=128),
              F.integer("count", "How many", 5, minimum=1, maximum=100),
              F.flag("lower", "Lowercase letters", True),
              F.flag("upper", "Uppercase letters", True),
              F.flag("digits", "Digits", True),
              F.flag("symbols", "Symbols", True),
              F.flag("no_ambiguous", "Avoid look-alikes (0/O, 1/l/I)", True)])
def password_generate(v, ctx):
    pools = []
    if v["lower"]:
        pools.append(string.ascii_lowercase)
    if v["upper"]:
        pools.append(string.ascii_uppercase)
    if v["digits"]:
        pools.append(string.digits)
    if v["symbols"]:
        pools.append("!@#$%^&*()-_=+[]{};:,.?/")
    if not pools:
        raise ToolError("Allow at least one character set")
    alphabet = "".join(pools)
    if v["no_ambiguous"]:
        alphabet = alphabet.translate(str.maketrans("", "", "0O1lI|`'\""))
        pools = [pool.translate(str.maketrans("", "", "0O1lI|`'\"")) for pool in pools]
        pools = [pool for pool in pools if pool]
    passwords = []
    for _ in range(v["count"]):
        while True:
            candidate = "".join(secrets.choice(alphabet) for _ in range(v["length"]))
            if all(any(char in pool for char in candidate) for pool in pools):
                break
        passwords.append(candidate)
    ctx.log("\n".join(passwords))
    return f"{len(passwords)} password(s) of {v['length']} characters"


@tool(id="passphrase-generate", name="Generate Passphrases", category="Generators",
      summary="Memorable word-based passphrases — long, random and easy to type.",
      fields=[F.integer("words", "Words", 5, minimum=3, maximum=12),
              F.integer("count", "How many", 3, minimum=1, maximum=50),
              F.choice("separator", "Separator", ["-", ".", "_", " ", "+"], "-"),
              F.flag("capitalise", "Capitalise each word", True),
              F.flag("number", "Add a number at the end", True)])
def passphrase_generate(v, ctx):
    phrases = []
    for _ in range(v["count"]):
        chosen = [secrets.choice(WORDS) for _ in range(v["words"])]
        if v["capitalise"]:
            chosen = [word.capitalize() for word in chosen]
        phrase = v["separator"].join(chosen)
        if v["number"]:
            phrase += v["separator"] + str(secrets.randbelow(90) + 10)
        phrases.append(phrase)
    ctx.log("\n".join(phrases))
    entropy = v["words"] * 10.5
    return f"{len(phrases)} passphrase(s), about {entropy:.0f} bits of entropy"


@tool(id="pin-generate", name="Generate PINs", category="Generators",
      summary="Random numeric PINs, avoiding trivial patterns if you want.",
      fields=[F.integer("length", "Digits", 6, minimum=4, maximum=12),
              F.integer("count", "How many", 10, minimum=1, maximum=100),
              F.flag("avoid_patterns", "Avoid repeats like 1111 or 1234", True)])
def pin_generate(v, ctx):
    pins = []
    while len(pins) < v["count"]:
        pin = "".join(secrets.choice(string.digits) for _ in range(v["length"]))
        if v["avoid_patterns"]:
            if len(set(pin)) == 1:
                continue
            if pin in "0123456789" or pin in "9876543210":
                continue
        pins.append(pin)
    ctx.log("\n".join(pins))
    return f"{len(pins)} PIN(s) of {v['length']} digits"


@tool(id="uuid-generate", name="Generate UUIDs", category="Generators",
      summary="RFC 4122 version 4 identifiers, formatted the way you need them.",
      fields=[F.integer("count", "How many", 5, minimum=1, maximum=500),
              F.choice("style", "Style", ["Lowercase with dashes", "Uppercase with dashes",
                                          "No dashes", "Braces"], "Lowercase with dashes")])
def uuid_generate(v, ctx):
    values = []
    for _ in range(v["count"]):
        value = str(uuid.uuid4())
        if v["style"] == "Uppercase with dashes":
            value = value.upper()
        elif v["style"] == "No dashes":
            value = value.replace("-", "")
        elif v["style"] == "Braces":
            value = "{" + value + "}"
        values.append(value)
    ctx.log("\n".join(values))
    return f"{len(values)} UUID(s)"


@tool(id="nanoid", name="Short IDs (NanoID style)", category="Generators",
      summary="Compact URL-safe identifiers for records, links and test data.",
      fields=[F.integer("length", "Length", 21, minimum=4, maximum=64),
              F.integer("count", "How many", 10, minimum=1, maximum=500),
              F.text("prefix", "Prefix", help="Optional, e.g. usr_")])
def nanoid(v, ctx):
    alphabet = string.ascii_letters + string.digits + "-_"
    values = [f"{v['prefix']}{''.join(secrets.choice(alphabet) for _ in range(v['length']))}"
              for _ in range(v["count"])]
    ctx.log("\n".join(values))
    return f"{len(values)} ID(s)"


@tool(id="api-key", name="Generate API Keys", category="Generators",
      summary="Random API-style keys, with an optional prefix and hex or base64 form.",
      fields=[F.integer("bytes", "Random bytes", 32, minimum=8, maximum=128),
              F.integer("count", "How many", 3, minimum=1, maximum=50),
              F.text("prefix", "Prefix", "sk_live_"),
              F.choice("encoding", "Encoding", ["URL-safe base64", "Hex"], "URL-safe base64")])
def api_key(v, ctx):
    import base64
    keys = []
    for _ in range(v["count"]):
        raw = secrets.token_bytes(v["bytes"])
        body = (base64.urlsafe_b64encode(raw).decode().rstrip("=") if v["encoding"] == "URL-safe base64"
                else raw.hex())
        keys.append(f"{v['prefix']}{body}")
    ctx.log("\n".join(keys))
    return f"{len(keys)} key(s), {v['bytes'] * 8} bits of randomness each"


@tool(id="random-string", name="Random Strings", category="Generators",
      summary="Random text from any character set you choose.",
      fields=[F.integer("length", "Length", 16, minimum=1, maximum=500),
              F.integer("count", "How many", 5, minimum=1, maximum=200),
              F.choice("alphabet", "Characters",
                       ["Letters and digits", "Letters only", "Digits only", "Hex",
                        "Base32", "Readable (no look-alikes)"], "Letters and digits")])
def random_string(v, ctx):
    alphabets = {
        "Letters and digits": string.ascii_letters + string.digits,
        "Letters only": string.ascii_letters,
        "Digits only": string.digits,
        "Hex": "0123456789abcdef",
        "Base32": "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567",
        "Readable (no look-alikes)": "abcdefghjkmnpqrstuvwxyz23456789",
    }
    alphabet = alphabets[v["alphabet"]]
    values = ["".join(secrets.choice(alphabet) for _ in range(v["length"]))
              for _ in range(v["count"])]
    ctx.log("\n".join(values))
    return f"{len(values)} string(s)"


@tool(id="random-number", name="Random Numbers", category="Generators",
      summary="Random integers or decimals in a range, with or without duplicates.",
      fields=[F.number("minimum", "Minimum", 1.0),
              F.number("maximum", "Maximum", 100.0),
              F.integer("count", "How many", 10, minimum=1, maximum=1000),
              F.flag("integers", "Whole numbers only", True),
              F.flag("unique", "No duplicates", False)])
def random_number(v, ctx):
    if v["maximum"] < v["minimum"]:
        raise ToolError("The maximum must be at least the minimum")
    values: list = []
    if v["integers"]:
        low, high = int(v["minimum"]), int(v["maximum"])
        if v["unique"]:
            if high - low + 1 < v["count"]:
                raise ToolError("That range cannot hold that many unique numbers")
            values = random.sample(range(low, high + 1), v["count"])
        else:
            values = [random.randint(low, high) for _ in range(v["count"])]
    else:
        values = [round(random.uniform(v["minimum"], v["maximum"]), 4) for _ in range(v["count"])]
    ctx.log(", ".join(str(value) for value in values))
    return {"count": len(values), "sum": round(sum(values), 4),
            "mean": round(sum(values) / len(values), 4)}


@tool(id="lorem-ipsum", name="Lorem Ipsum", category="Generators",
      summary="Filler text by words, sentences or paragraphs — for layouts and mockups.",
      fields=[F.choice("unit", "Produce", ["Paragraphs", "Sentences", "Words"], "Paragraphs"),
              F.integer("count", "How many", 3, minimum=1, maximum=100),
              F.flag("classic_start", "Start with 'Lorem ipsum dolor sit amet'", True),
              F.save("output", "Save to file", required=False)])
def lorem_ipsum(v, ctx):
    words = ("lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor "
             "incididunt ut labore et dolore magna aliqua enim ad minim veniam quis nostrud "
             "exercitation ullamco laboris nisi aliquip ex ea commodo consequat duis aute "
             "irure in reprehenderit voluptate velit esse cillum eu fugiat nulla pariatur "
             "excepteur sint occaecat cupidatat non proident sunt culpa qui officia deserunt "
             "mollit anim id est laborum").split()

    def sentence() -> str:
        length = random.randint(8, 18)
        chosen = [random.choice(words) for _ in range(length)]
        return " ".join(chosen).capitalize() + "."

    if v["unit"] == "Words":
        text = " ".join(random.choice(words) for _ in range(v["count"]))
    elif v["unit"] == "Sentences":
        text = " ".join(sentence() for _ in range(v["count"]))
    else:
        text = "\n\n".join(" ".join(sentence() for _ in range(random.randint(3, 6)))
                           for _ in range(v["count"]))
    if v["classic_start"]:
        text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " + text
    if v["output"].strip():
        target = write_text(out_path(v["output"], "lorem.txt"), text)
        ctx.output(str(target))
        ctx.log(f"Saved to {target}")
    ctx.log(text[:2000])
    return f"{len(text.split())} word(s)"


@tool(id="dummy-csv", name="Dummy CSV", category="Generators",
      summary="Realistic test data as CSV — names, emails, cities, amounts and dates.",
      fields=[F.integer("rows", "Rows", 50, minimum=1, maximum=100000),
              F.text("columns", "Columns", "id,name,email,city,amount,signup_date"),
              F.save("output", "Save CSV to", required=True)])
def dummy_csv(v, ctx):
    columns = [column.strip() for column in v["columns"].split(",") if column.strip()]
    if not columns:
        raise ToolError("Give at least one column name")
    rows = []
    start = date.today() - timedelta(days=730)
    for index in range(1, v["rows"] + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        row = {}
        for column in columns:
            key = column.lower()
            if key in ("id", "index", "no", "number"):
                row[column] = index
            elif "email" in key:
                row[column] = f"{first.lower()}.{last.lower()}{index}@example.com"
            elif "first" in key and "name" in key:
                row[column] = first
            elif "last" in key or key == "surname":
                row[column] = last
            elif "name" in key:
                row[column] = f"{first} {last}"
            elif "phone" in key or "mobile" in key:
                row[column] = f"+91 9{secrets.randbelow(10)}{secrets.randbelow(900000000) + 100000000}"
            elif "city" in key:
                row[column] = random.choice(CITIES)
            elif "amount" in key or "price" in key or "salary" in key or "total" in key:
                row[column] = round(random.uniform(100, 100000), 2)
            elif "date" in key:
                row[column] = _random_date(start, date.today()).isoformat()
            elif "bool" in key or "active" in key:
                row[column] = random.choice(["true", "false"])
            else:
                row[column] = "".join(secrets.choice(string.ascii_lowercase)
                                      for _ in range(8))
        rows.append(row)
    target = write_csv(out_path(v["output"], "test-data.csv"), rows, columns)
    ctx.output(str(target))
    return f"{len(rows)} row(s) × {len(columns)} column(s) → {target}"


@tool(id="dummy-json", name="Dummy JSON", category="Generators",
      summary="A JSON array of mock records for API stubs and front-end work.",
      fields=[F.integer("records", "Records", 10, minimum=1, maximum=10000),
              F.flag("nested", "Include a nested address object", True),
              F.save("output", "Save JSON to", required=True)])
def dummy_json(v, ctx):
    records = []
    for index in range(1, v["records"] + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        record = {
            "id": index,
            "name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}{index}@example.com",
            "active": random.choice([True, False]),
            "score": round(random.uniform(0, 100), 1),
            "created_at": _random_date(date(2023, 1, 1), date.today()).isoformat(),
        }
        if v["nested"]:
            record["address"] = {
                "city": random.choice(CITIES),
                "state": random.choice(["MH", "DL", "KA", "TN", "GJ", "UP", "WB"]),
                "pincode": str(secrets.randbelow(900000) + 100000),
            }
            record["tags"] = random.sample(["new", "returning", "premium", "trial", "churn"],
                                           k=random.randint(0, 3))
        records.append(record)
    target = write_text(out_path(v["output"], "test-data.json"),
                        json.dumps(records, indent=2, ensure_ascii=False))
    ctx.output(str(target))
    return f"{len(records)} record(s) → {target}"


@tool(id="dummy-file", name="Dummy File", category="Generators",
      summary="Create a file of an exact size — for testing uploads, limits and copy speeds.",
      fields=[F.number("size_mb", "Size (MB)", 1.0, minimum=0.001, maximum=20480),
              F.choice("content", "Content", ["Zero bytes", "Random bytes", "Text lines"],
                       "Zero bytes"),
              F.save("output", "Save as", required=True)])
def dummy_file(v, ctx):
    size = int(v["size_mb"] * 1024 * 1024)
    target = out_path(v["output"], "dummy.bin")
    target.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(target, "wb") as handle:
        while written < size:
            chunk = min(1 << 20, size - written)
            if v["content"] == "Random bytes":
                block = secrets.token_bytes(chunk)
            elif v["content"] == "Text lines":
                block = (b"The quick brown fox jumps over the lazy dog. " * (chunk // 45 + 1))[:chunk]
            else:
                block = b"\0" * chunk
            handle.write(block)
            written += chunk
            ctx.progress(written / size * 100, human_size(written))
    ctx.output(str(target))
    return f"{target.name} created, {human_size(target.stat().st_size)}"


@tool(id="random-date", name="Random Dates", category="Generators",
      summary="Random dates in a range, formatted the way your system expects.",
      fields=[F.text("start", "From (YYYY-MM-DD)", "2020-01-01"),
              F.text("end", "To (YYYY-MM-DD)", "2026-12-31"),
              F.integer("count", "How many", 10, minimum=1, maximum=1000),
              F.choice("format", "Format", ["YYYY-MM-DD", "DD/MM/YYYY", "DD-MMM-YYYY",
                                            "Month DD, YYYY"], "YYYY-MM-DD"),
              F.flag("sorted", "Sort oldest first", True)])
def random_date(v, ctx):
    try:
        start = datetime.strptime(v["start"].strip() or "2020-01-01", "%Y-%m-%d").date()
        end = datetime.strptime(v["end"].strip() or "2026-12-31", "%Y-%m-%d").date()
    except ValueError as exc:
        raise ToolError("Use YYYY-MM-DD for both dates") from exc
    if end < start:
        raise ToolError("The end date is before the start date")
    dates = sorted(_random_date(start, end) for _ in range(v["count"])) if v["sorted"] else \
        [_random_date(start, end) for _ in range(v["count"])]
    patterns = {"YYYY-MM-DD": "%Y-%m-%d", "DD/MM/YYYY": "%d/%m/%Y",
                "DD-MMM-YYYY": "%d-%b-%Y", "Month DD, YYYY": "%B %d, %Y"}
    text = "\n".join(moment.strftime(patterns[v["format"]]) for moment in dates)
    ctx.log(text)
    return f"{len(dates)} date(s)"


@tool(id="dice-roll", name="Dice Roller", category="Generators",
      summary="Roll dice in standard notation — 2d6, 1d20+3 — with a breakdown.",
      fields=[F.text("notation", "Dice", "2d6", required=True,
                     help="Format: NdM+K — e.g. 3d8, 1d20+5, 4d6"),
              F.integer("rolls", "How many times", 1, minimum=1, maximum=100)])
def dice_roll(v, ctx):
    import re as regex
    match = regex.fullmatch(r"\s*(\d*)d(\d+)\s*([+-]\s*\d+)?\s*", v["notation"].lower())
    if not match:
        raise ToolError("Use notation like 2d6 or 1d20+3")
    count = int(match.group(1) or 1)
    sides = int(match.group(2))
    modifier = int(match.group(3).replace(" ", "") or 0) if match.group(3) else 0
    if count > 1000 or sides > 1000:
        raise ToolError("Keep it under 1000 dice and 1000 sides")
    totals = []
    for _ in range(v["rolls"]):
        results = [secrets.randbelow(sides) + 1 for _ in range(count)]
        total = sum(results) + modifier
        totals.append(total)
        ctx.log(f"{results} {'+' if modifier >= 0 else '-'} {abs(modifier)} = {total}"
                if modifier else f"{results} = {total}")
    return {"notation": v["notation"], "totals": totals,
            "average": round(sum(totals) / len(totals), 2)}


@tool(id="lottery-numbers", name="Number Picker", category="Generators",
      summary="Unique random numbers for lotteries, draws and sampling without repeats.",
      fields=[F.integer("lowest", "Lowest number", 1),
              F.integer("highest", "Highest number", 49, minimum=1),
              F.integer("picks", "How many to pick", 6, minimum=1),
              F.flag("sorted", "Show them in order", True)])
def lottery_numbers(v, ctx):
    span = v["highest"] - v["lowest"] + 1
    if v["picks"] > span:
        raise ToolError("You cannot pick more numbers than the range holds")
    picks = random.sample(range(v["lowest"], v["highest"] + 1), v["picks"])
    if v["sorted"]:
        picks.sort()
    ctx.log(", ".join(str(pick) for pick in picks))
    return {"picks": picks}


@tool(id="shuffle-lines", name="Shuffle a List", category="Generators",
      summary="Randomise the order of lines — for draws, assignments and test order.",
      fields=[F.multi("text", "One item per line", rows=10),
              F.file("file", "…or read a file", required=False),
              F.flag("number", "Number the results", False)])
def shuffle_lines(v, ctx):
    from ._util import need_file, read_text
    path = str(v["file"] or "").strip()
    lines = (read_text(need_file(path)) if path else v["text"]).splitlines()
    lines = [line for line in lines if line.strip()]
    if len(lines) < 2:
        raise ToolError("Give at least two items")
    random.shuffle(lines)
    if v["number"]:
        lines = [f"{index}. {line}" for index, line in enumerate(lines, start=1)]
    ctx.log("\n".join(lines))
    return f"{len(lines)} item(s) shuffled"


@tool(id="pick-from-list", name="Pick From a List", category="Generators",
      summary="Draw one or more winners from a list, without repeating a winner.",
      fields=[F.multi("text", "Entries, one per line", rows=10),
              F.integer("winners", "How many winners", 1, minimum=1, maximum=100)])
def pick_from_list(v, ctx):
    entries = [line.strip() for line in v["text"].splitlines() if line.strip()]
    if len(entries) < v["winners"]:
        raise ToolError("Not enough entries for that many winners")
    winners = random.sample(entries, v["winners"])
    for index, winner in enumerate(winners, start=1):
        ctx.log(f"{index}. {winner}")
    return f"{len(winners)} winner(s) from {len(entries)} entr(ies)"


@tool(id="team-split", name="Split Into Teams", category="Generators",
      summary="Divide a list of people into balanced random teams.",
      fields=[F.multi("text", "Names, one per line", rows=12),
              F.integer("teams", "Number of teams", 2, minimum=2, maximum=20),
              F.flag("number", "Number the members within each team", True)])
def team_split(v, ctx):
    names = [line.strip() for line in v["text"].splitlines() if line.strip()]
    if len(names) < v["teams"]:
        raise ToolError("You need at least one person per team")
    random.shuffle(names)
    groups: list[list[str]] = [[] for _ in range(v["teams"])]
    for index, name in enumerate(names):
        groups[index % v["teams"]].append(name)
    for number, group in enumerate(groups, start=1):
        ctx.log(f"\nTeam {number} ({len(group)})")
        for position, member in enumerate(group, start=1):
            ctx.log(f"  {position}. {member}" if v["number"] else f"  {member}")
    return f"{len(names)} people in {v['teams']} team(s)"


@tool(id="test-names", name="Sample Names & Emails", category="Generators",
      summary="A ready list of realistic Indian names, emails and cities for test data.",
      fields=[F.integer("count", "How many", 20, minimum=1, maximum=500),
              F.choice("format", "Format", ["Name — email", "Name,email", "CSV columns",
                                            "Just names"], "Name — email")])
def test_names(v, ctx):
    people = []
    used = set()
    while len(people) < v["count"]:
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        key = (first, last)
        if key in used and len(used) < len(FIRST_NAMES) * len(LAST_NAMES):
            continue
        used.add(key)
        people.append((f"{first} {last}", f"{first.lower()}.{last.lower()}@example.com",
                       random.choice(CITIES)))
    if v["format"] == "CSV columns":
        ctx.log("name,email,city")
        for name, email, city in people:
            ctx.log(f"{name},{email},{city}")
    elif v["format"] == "Name,email":
        ctx.log("\n".join(f"{name},{email}" for name, email, _ in people))
    elif v["format"] == "Just names":
        ctx.log("\n".join(name for name, _, _ in people))
    else:
        ctx.log("\n".join(f"{name} — {email}" for name, email, _ in people))
    return f"{len(people)} person/people generated"


@tool(id="colour-palette", name="Colour Palette", category="Generators",
      summary="A harmonious random palette with hex codes and a contrast check.",
      fields=[F.integer("colours", "How many colours", 5, minimum=2, maximum=12),
              F.choice("scheme", "Scheme", ["Analogous", "Complementary", "Triadic",
                                            "Monochrome", "Random"], "Analogous")])
def colour_palette(v, ctx):
    import colorsys
    base_hue = random.random()
    scheme = v["scheme"]
    hues = []
    for index in range(v["colours"]):
        if scheme == "Analogous":
            hue = (base_hue + index * 0.06) % 1.0
        elif scheme == "Complementary":
            hue = (base_hue + (0.5 if index % 2 else 0)) % 1.0
        elif scheme == "Triadic":
            hue = (base_hue + (index % 3) / 3) % 1.0
        elif scheme == "Monochrome":
            hue = base_hue
        else:
            hue = random.random()
        saturation = 0.55 + (index % 3) * 0.12
        lightness = 0.35 + (index / max(1, v["colours"] - 1)) * 0.4
        rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
        hues.append((tuple(int(channel * 255) for channel in rgb), hue))
    rows = []
    for rgb, hue in hues:
        hex_code = "#%02x%02x%02x" % rgb
        luminance = sum(channel / 255 * weight for channel, weight in
                        zip(rgb, (0.2126, 0.7152, 0.0722)))
        rows.append({"hex": hex_code, "rgb": f"{rgb[0]}, {rgb[1]}, {rgb[2]}",
                     "text on it": "dark text" if luminance > 0.5 else "light text"})
        ctx.log(f"{hex_code}   rgb({rows[-1]['rgb']})")
    return {"scheme": scheme, "colours": [row["hex"] for row in rows]}


@tool(id="placeholder-image", name="Placeholder Image", category="Generators",
      summary="A labelled placeholder image at any size — for mockups and layout tests.",
      needs=("pillow",),
      fields=[F.integer("width", "Width (px)", 1200, minimum=16, maximum=8000),
              F.integer("height", "Height (px)", 630, minimum=16, maximum=8000),
              F.color("background", "Background", "#1f2937"),
              F.color("text_colour", "Text colour", "#f9fafb"),
              F.text("label", "Label", "1200 × 630"),
              F.save("output", "Save as", required=True, filters="Image (*.png *.jpg)")])
def placeholder_image(v, ctx):
    from ._util import require
    require("PIL.Image", "pillow")
    from PIL import Image, ImageDraw, ImageFont
    background = v["background"] if str(v["background"]).startswith("#") else "#" + str(v["background"])
    text_colour = v["text_colour"] if str(v["text_colour"]).startswith("#") else "#" + str(v["text_colour"])
    image = Image.new("RGB", (v["width"], v["height"]), background)
    draw = ImageDraw.Draw(image)
    size = max(14, min(v["width"], v["height"]) // 8)
    try:
        font = ImageFont.truetype("arial.ttf", size)
    except OSError:
        font = ImageFont.load_default()
    label = v["label"] or f"{v['width']} × {v['height']}"
    box = draw.textbbox((0, 0), label, font=font)
    draw.text(((v["width"] - (box[2] - box[0])) / 2, (v["height"] - (box[3] - box[1])) / 2),
              label, font=font, fill=text_colour)
    draw.rectangle([0, 0, v["width"] - 1, v["height"] - 1],
                   outline=text_colour, width=max(2, size // 20))
    target = out_path(v["output"], f"placeholder-{v['width']}x{v['height']}.png")
    image.save(target)
    ctx.output(str(target))
    return f"{target.name} ({v['width']}×{v['height']})"


@tool(id="sequential-ids", name="Sequential IDs", category="Generators",
      summary="A clean run of IDs with a prefix, padding and separator — for bulk imports.",
      fields=[F.integer("start", "Start at", 1),
              F.integer("count", "How many", 20, minimum=1, maximum=100000),
              F.text("prefix", "Prefix", "ID-"),
              F.integer("padding", "Zero-pad to", 4, minimum=0, maximum=12),
              F.text("suffix", "Suffix", "")])
def sequential_ids(v, ctx):
    values = [f"{v['prefix']}{str(index).zfill(v['padding'])}{v['suffix']}"
              for index in range(v["start"], v["start"] + v["count"])]
    ctx.log("\n".join(values[:200]) + ("\n…" if len(values) > 200 else ""))
    return f"{len(values)} ID(s), {values[0]} to {values[-1]}"


@tool(id="otp-generate", name="Generate OTPs", category="Generators",
      summary="One-time codes of a chosen length, with an expiry note for testing flows.",
      fields=[F.integer("digits", "Digits", 6, minimum=4, maximum=10),
              F.integer("count", "How many", 10, minimum=1, maximum=200)])
def otp_generate(v, ctx):
    codes = [str(secrets.randbelow(10 ** v["digits"])).zfill(v["digits"])
             for _ in range(v["count"])]
    ctx.log("\n".join(codes))
    return f"{len(codes)} one-time code(s) of {v['digits']} digits"


@tool(id="password-batch", name="Password Batch", category="Generators",
      summary="A CSV of users with generated passwords — for seeding test accounts.",
      fields=[F.integer("count", "Accounts", 10, minimum=1, maximum=1000),
              F.integer("length", "Password length", 16, minimum=8, maximum=64),
              F.save("output", "Save CSV to", required=True)])
def password_batch(v, ctx):
    rows = []
    for index in range(1, v["count"] + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        password = "".join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*")
                           for _ in range(v["length"]))
        rows.append({"username": f"{first.lower()}.{last.lower()}{index}",
                     "email": f"{first.lower()}.{last.lower()}{index}@example.com",
                     "password": password})
    target = write_csv(out_path(v["output"], "test-accounts.csv"), rows,
                       ["username", "email", "password"])
    ctx.output(str(target))
    return f"{len(rows)} account(s) → {target}"
