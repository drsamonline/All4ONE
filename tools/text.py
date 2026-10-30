"""Text — transform, analyse and clean."""

from __future__ import annotations

import html
import re
import unicodedata
from collections import Counter
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import (
    human_size,
    iter_files,
    need_dir,
    need_file,
    out_path,
    read_text,
    report_table,
    write_text,
)


def _input_fields(label="Text", rows=10):
    return [F.multi("text", label, rows=rows),
            F.file("file", "…or read from a file", required=False),
            F.save("output", "Save result to", required=False)]


def _text(v) -> str:
    path = str(v.get("file") or "").strip()
    if path:
        return read_text(need_file(path))
    text = str(v.get("text") or "")
    if not text:
        raise ToolError("Type something, or choose a file to read")
    return text


def _emit(v, ctx, text: str, name: str = "result.txt", preview: int = 6000) -> str:
    if str(v.get("output") or "").strip():
        target = write_text(out_path(v["output"], name), text)
        ctx.output(str(target))
        ctx.log(f"Saved to {target}")
    if len(text) > preview:
        ctx.log(text[:preview])
        ctx.log(f"… {len(text) - preview} more characters (save to a file to keep them all)")
        return f"{len(text)} characters produced"
    ctx.log(text)
    return ""


# --------------------------------------------------------------------------
# Measure
# --------------------------------------------------------------------------
@tool(id="word-count", name="Word Count", category="Text",
      summary="Words, characters, lines, sentences and reading time for any text or file.",
      keywords="count words characters lines statistics reading time",
      fields=_input_fields())
def word_count(v, ctx):
    text = _text(v)
    words = re.findall(r"\b[\w'’-]+\b", text, flags=re.UNICODE)
    sentences = [s for s in re.split(r"[.!?]+(?:\s|$)", text) if s.strip()]
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    result = {
        "characters": len(text),
        "characters_no_spaces": len(re.sub(r"\s", "", text)),
        "words": len(words),
        "unique_words": len({w.lower() for w in words}),
        "lines": text.count("\n") + (1 if text and not text.endswith("\n") else 0),
        "sentences": len(sentences),
        "paragraphs": len(paragraphs),
        "reading_time_minutes": round(len(words) / 220, 1),
        "speaking_time_minutes": round(len(words) / 130, 1),
    }
    ctx.log(report_table([{"measure": k.replace("_", " "), "value": val}
                          for k, val in result.items()]))
    return result


@tool(id="text-statistics", name="Readability Statistics", category="Text",
      summary="Average word and sentence length plus a Flesch reading-ease score.",
      keywords="readability flesch grade level complexity",
      fields=_input_fields())
def text_statistics(v, ctx):
    text = _text(v)
    words = re.findall(r"\b[\w'’-]+\b", text)
    sentences = [s for s in re.split(r"[.!?]+(?:\s|$)", text) if s.strip()]
    if not words or not sentences:
        raise ToolError("Not enough text to measure")
    syllables = 0
    for word in words:
        groups = re.findall(r"[aeiouy]+", word.lower())
        syllables += max(1, len(groups))
    wps = len(words) / len(sentences)
    spw = syllables / len(words)
    ease = 206.835 - 1.015 * wps - 84.6 * spw
    grade = 0.39 * wps + 11.8 * spw - 15.59
    verdict = ("Very easy" if ease >= 80 else "Easy" if ease >= 60 else
               "Plain" if ease >= 50 else "Fairly hard" if ease >= 30 else "Difficult")
    return {"flesch_reading_ease": round(ease, 1), "reading_level": verdict,
            "flesch_kincaid_grade": round(grade, 1),
            "words_per_sentence": round(wps, 1),
            "syllables_per_word": round(spw, 2),
            "average_word_length": round(sum(len(w) for w in words) / len(words), 1)}


@tool(id="word-frequency", name="Word Frequency", category="Text",
      summary="The words used most often, with counts and share of the whole text.",
      keywords="frequency keywords density common words top",
      fields=_input_fields() + [F.integer("limit", "Show top", 25, minimum=1, maximum=500),
                                F.integer("min_length", "Ignore words shorter than", 3, minimum=1),
                                F.flag("ignore_common", "Ignore common English words", True)])
def word_frequency(v, ctx):
    text = _text(v)
    words = [w.lower() for w in re.findall(r"\b[\w'’-]+\b", text)
             if len(w) >= v["min_length"]]
    stop = set("""the and for that with this from have not are was were you your they their
                  will can but all any out our has had how its into than then them these those
                  what when where which who why would should could about after also been before
                  being both does doing down during each few more most other over same some such
                  only own very just because while here there above below off once under again""".split())
    if v["ignore_common"]:
        words = [w for w in words if w not in stop]
    total = len(words) or 1
    rows = [{"word": word, "count": count, "share": f"{count / total * 100:.1f}%"}
            for word, count in Counter(words).most_common(v["limit"])]
    ctx.log(report_table(rows))
    return f"{len(words)} words counted, {len(set(words))} distinct"


@tool(id="keyword-density", name="Keyword Density", category="Text",
      summary="How often each phrase appears as a share of the text — SEO-style analysis.",
      keywords="density seo keywords phrases analysis",
      fields=_input_fields() + [F.integer("phrase_words", "Phrase length (words)", 2, minimum=1, maximum=4)])
def keyword_density(v, ctx):
    text = _text(v)
    words = re.findall(r"\b[\w'’-]+\b", text.lower())
    n = v["phrase_words"]
    if len(words) < n:
        raise ToolError("Text is shorter than the phrase length")
    grams = Counter(" ".join(words[i:i + n]) for i in range(len(words) - n + 1))
    total = sum(grams.values()) or 1
    rows = [{"phrase": phrase, "count": count, "density": f"{count / total * 100:.2f}%"}
            for phrase, count in grams.most_common(25)]
    ctx.log(report_table(rows))
    return f"{len(grams)} distinct {n}-word phrases"


# --------------------------------------------------------------------------
# Transform
# --------------------------------------------------------------------------
@tool(id="case-convert", name="Change Case", category="Text",
      summary="UPPER, lower, Title, Sentence, camelCase, snake_case, kebab-case or tOGGLE.",
      keywords="case upper lower title camel snake kebab toggle capitalise",
      fields=_input_fields() + [F.choice("mode", "Convert to",
                                         ["UPPER CASE", "lower case", "Title Case", "Sentence case",
                                          "camelCase", "snake_case", "kebab-case", "tOGGLE cASE",
                                          "Capitalise Each Word"], "UPPER CASE")])
def case_convert(v, ctx):
    text = _text(v)
    mode = v["mode"]
    if mode == "UPPER CASE":
        out = text.upper()
    elif mode == "lower case":
        out = text.lower()
    elif mode == "Title Case":
        out = text.title()
    elif mode == "Sentence case":
        out = re.sub(r"(^\s*|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text.lower())
    elif mode == "camelCase":
        parts = re.split(r"[\s_\-]+", text.strip())
        out = parts[0].lower() + "".join(p.capitalize() for p in parts[1:] if p)
    elif mode == "snake_case":
        out = "_".join(p for p in re.split(r"[\s\-]+", text.strip().lower()) if p)
    elif mode == "kebab-case":
        out = "-".join(p for p in re.split(r"[\s_]+", text.strip().lower()) if p)
    elif mode == "tOGGLE cASE":
        out = "".join(ch.lower() if ch.isupper() else ch.upper() for ch in text)
    else:
        out = " ".join(word[:1].upper() + word[1:] for word in text.split())
    return _emit(v, ctx, out)


@tool(id="find-replace-text", name="Find & Replace", category="Text",
      summary="Replace text with optional whole-word, case-sensitive and regex modes.",
      keywords="replace substitute swap find change",
      fields=[F.multi("text", "Text", rows=10),
              F.file("file", "…or read from a file", required=False),
              F.text("find", "Find", required=True),
              F.text("replace", "Replace with"),
              F.flag("case_sensitive", "Match case", False),
              F.flag("whole_word", "Whole words only", False),
              F.flag("regex", "Treat 'Find' as a regular expression", False),
              F.save("output", "Save result to", required=False)])
def find_replace_text(v, ctx):
    text = _text(v)
    find, repl = v["find"], v["replace"]
    flags = 0 if v["case_sensitive"] else re.IGNORECASE
    pattern = find
    if not v["regex"]:
        pattern = re.escape(find)
    if v["whole_word"]:
        pattern = rf"\b{pattern}\b"
    try:
        out, count = re.subn(pattern, repl.replace("\\", "\\\\") if not v["regex"] else repl,
                             text, flags=flags)
    except re.error as exc:
        raise ToolError(f"Bad regular expression: {exc}") from exc
    ctx.log(f"{count} replacement(s)")
    return _emit(v, ctx, out)


@tool(id="regex-replace", name="Regex Replace", category="Text",
      summary="Substitute with a full regular expression, including capture groups.",
      keywords="regex replace substitute groups pattern",
      fields=[F.multi("text", "Text", rows=8),
              F.file("file", "…or read from a file", required=False),
              F.text("pattern", "Pattern", r"(\w+)@(\w+)", required=True),
              F.text("replacement", "Replacement", r"\2 at \1",
                     help=r"Use \1, \2 … for capture groups"),
              F.flag("multiline", "Multiline (^ and $ per line)", True),
              F.flag("dotall", "Dot matches newlines", False),
              F.save("output", "Save result to", required=False)])
def regex_replace(v, ctx):
    text = _text(v)
    flags = 0
    if v["multiline"]:
        flags |= re.MULTILINE
    if v["dotall"]:
        flags |= re.DOTALL
    try:
        out, count = re.subn(v["pattern"], v["replacement"], text, flags=flags)
    except re.error as exc:
        raise ToolError(f"Bad regular expression: {exc}") from exc
    ctx.log(f"{count} match(es) replaced")
    return _emit(v, ctx, out)


@tool(id="regex-extract", name="Extract With Regex", category="Text",
      summary="Pull every match of a pattern out of text — emails, IDs, numbers, anything.",
      keywords="extract regex matches capture find all",
      fields=[F.multi("text", "Text", rows=8),
              F.file("file", "…or read from a file", required=False),
              F.text("pattern", "Pattern", r"[\w.+-]+@[\w-]+\.[\w.]+", required=True),
              F.flag("unique", "Remove duplicates", True),
              F.save("output", "Save matches to", required=False)])
def regex_extract(v, ctx):
    text = _text(v)
    try:
        found = re.findall(v["pattern"], text, flags=re.MULTILINE)
    except re.error as exc:
        raise ToolError(f"Bad regular expression: {exc}") from exc
    flat = [m if isinstance(m, str) else " | ".join(m) for m in found]
    if v["unique"]:
        flat = list(dict.fromkeys(flat))
    if not flat:
        return "No matches."
    ctx.log("\n".join(flat[:500]))
    if len(flat) > 500:
        ctx.log(f"… and {len(flat) - 500} more")
    return _emit(v, ctx, "\n".join(flat))


@tool(id="sort-lines", name="Sort Lines", category="Text",
      summary="Sort lines alphabetically, numerically, by length or in reverse.",
      keywords="sort order lines alphabetical numeric",
      fields=_input_fields() + [F.choice("order", "Order",
                                         ["A → Z", "Z → A", "Shortest first", "Longest first",
                                          "Numeric"], "A → Z"),
                                F.flag("unique", "Remove duplicates", False)])
def sort_lines(v, ctx):
    text = _text(v)
    lines = text.splitlines()
    if v["order"] == "A → Z":
        lines.sort(key=str.lower)
    elif v["order"] == "Z → A":
        lines.sort(key=str.lower, reverse=True)
    elif v["order"] == "Shortest first":
        lines.sort(key=len)
    elif v["order"] == "Longest first":
        lines.sort(key=len, reverse=True)
    else:
        def numeric(line: str) -> float:
            match = re.search(r"-?\d+(?:\.\d+)?", line)
            return float(match.group()) if match else float("inf")
        lines.sort(key=numeric)
    if v["unique"]:
        seen, keep = set(), []
        for line in lines:
            if line not in seen:
                seen.add(line)
                keep.append(line)
        lines = keep
    return _emit(v, ctx, "\n".join(lines))


@tool(id="dedupe-lines", name="Remove Duplicate Lines", category="Text",
      summary="Keep the first occurrence of every line and drop the repeats.",
      keywords="duplicate unique dedupe lines repeats",
      fields=_input_fields() + [F.flag("ignore_case", "Ignore case when comparing", False),
                                F.flag("keep_last", "Keep the last occurrence instead", False)])
def dedupe_lines(v, ctx):
    text = _text(v)
    lines = text.splitlines()
    seen: dict[str, int] = {}
    for index, line in enumerate(lines):
        key = line.lower() if v["ignore_case"] else line
        seen[key] = index
    keep = set(seen.values()) if v["keep_last"] else set()
    if not v["keep_last"]:
        first: dict[str, int] = {}
        for index, line in enumerate(lines):
            key = line.lower() if v["ignore_case"] else line
            first.setdefault(key, index)
        keep = set(first.values())
    out = [line for index, line in enumerate(lines) if index in keep]
    removed = len(lines) - len(out)
    ctx.log(f"Removed {removed} duplicate line(s)")
    return _emit(v, ctx, "\n".join(out))


@tool(id="remove-blank-lines", name="Remove Blank Lines", category="Text",
      summary="Delete empty and whitespace-only lines, optionally collapsing runs of them.",
      keywords="blank empty lines whitespace strip compress",
      fields=_input_fields() + [F.flag("collapse", "Collapse runs into a single blank line", False)])
def remove_blank_lines(v, ctx):
    text = _text(v)
    out = []
    for line in text.splitlines():
        if line.strip():
            out.append(line)
        elif v["collapse"] and out and out[-1] != "":
            out.append("")
    return _emit(v, ctx, "\n".join(out))


@tool(id="trim-lines", name="Trim Whitespace", category="Text",
      summary="Strip trailing spaces, leading spaces, or both, from every line.",
      keywords="trim trailing leading whitespace spaces tabs",
      fields=_input_fields() + [F.choice("where", "Remove from", ["Both ends", "End only", "Start only"],
                                         "Both ends"),
                                F.flag("blank_runs", "Also squash repeated spaces inside lines", False)])
def trim_lines(v, ctx):
    text = _text(v)
    out = []
    for line in text.splitlines():
        if v["where"] == "Both ends":
            line = line.strip()
        elif v["where"] == "End only":
            line = line.rstrip()
        else:
            line = line.lstrip()
        if v["blank_runs"]:
            line = re.sub(r"[ \t]{2,}", " ", line)
        out.append(line)
    return _emit(v, ctx, "\n".join(out))


@tool(id="add-line-numbers", name="Add Line Numbers", category="Text",
      summary="Prefix every line with a number, with a separator and start value you pick.",
      keywords="number lines prefix counter enumerate",
      fields=_input_fields() + [F.integer("start", "Start at", 1),
                                F.text("separator", "Separator", ". "),
                                F.integer("pad", "Zero-pad to width", 0, minimum=0, maximum=10)])
def add_line_numbers(v, ctx):
    text = _text(v)
    lines = text.splitlines()
    out = []
    for index, line in enumerate(lines, start=v["start"]):
        number = str(index).zfill(v["pad"]) if v["pad"] else str(index)
        out.append(f"{number}{v['separator']}{line}")
    return _emit(v, ctx, "\n".join(out))


@tool(id="join-lines", name="Join Lines", category="Text",
      summary="Merge every line into one paragraph, or into lines of N words.",
      keywords="join merge lines unwrap paragraph",
      fields=_input_fields() + [F.integer("per_line", "Words per output line (0 = one line)", 0,
                                          minimum=0),
                                F.flag("keep_paragraphs", "Keep paragraph breaks", False)])
def join_lines(v, ctx):
    text = _text(v)
    if v["keep_paragraphs"]:
        blocks = re.split(r"\n\s*\n", text)
        joined = [" ".join(block.split()) for block in blocks]
    else:
        joined = [" ".join(text.split())]
    if v["per_line"] > 0:
        words = " ".join(joined).split()
        joined = [" ".join(words[i:i + v["per_line"]])
                  for i in range(0, len(words), v["per_line"])]
    return _emit(v, ctx, "\n\n".join(joined))


@tool(id="wrap-text", name="Wrap Text", category="Text",
      summary="Re-wrap paragraphs at a fixed column width, preserving paragraph breaks.",
      keywords="wrap width column reflow format",
      fields=_input_fields() + [F.integer("width", "Width (characters)", 80, minimum=20, maximum=400),
                                F.flag("keep_indent", "Preserve indentation", False)])
def wrap_text(v, ctx):
    import textwrap
    text = _text(v)
    blocks = re.split(r"\n\s*\n", text)
    out = []
    for block in blocks:
        if v["keep_indent"]:
            out.append("\n".join(textwrap.wrap(block, width=v["width"],
                                               subsequent_indent=re.match(r"\s*", block).group())))
        else:
            out.append(textwrap.fill(" ".join(block.split()), width=v["width"]))
    return _emit(v, ctx, "\n\n".join(out))


@tool(id="strip-html", name="HTML to Text", category="Text",
      summary="Turn HTML into readable plain text, keeping or dropping link addresses.",
      keywords="html strip tags text convert clean",
      fields=[F.multi("text", "HTML", rows=10),
              F.file("file", "…or read from an HTML file", required=False,
                     filters="HTML (*.html *.htm)"),
              F.flag("links", "Show link addresses inline", True),
              F.flag("keep_breaks", "Keep line breaks for block elements", True),
              F.save("output", "Save result to", required=False)])
def strip_html(v, ctx):
    text = _text(v)
    if v["links"]:
        text = re.sub(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
                      lambda m: f"{re.sub(r'<[^>]+>', '', m.group(2))} ({m.group(1)})",
                      text, flags=re.I | re.S)
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.I | re.S)
    if v["keep_breaks"]:
        text = re.sub(r"</(p|div|h[1-6]|li|tr|br)>", "\n", text, flags=re.I)
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return _emit(v, ctx, text)


@tool(id="markdown-to-text", name="Markdown to Text", category="Text",
      summary="Strip Markdown syntax down to clean prose for pasting anywhere.",
      keywords="markdown strip plain text convert",
      fields=_input_fields())
def markdown_to_text(v, ctx):
    text = _text(v)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"^\s*[-*+]\s+", "• ", text, flags=re.M)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.M)
    text = re.sub(r"^\s*([-*_]\s*){3,}$", "", text, flags=re.M)
    return _emit(v, ctx, re.sub(r"\n{3,}", "\n\n", text).strip())


@tool(id="csv-to-markdown", name="CSV to Markdown Table", category="Text",
      summary="Turn CSV into a clean Markdown table ready to paste into notes or a README.",
      keywords="csv markdown table convert readme",
      fields=[F.file("file", "CSV file", filters="CSV (*.csv *.tsv)"),
              F.text("delimiter", "Delimiter", ",", help="Leave blank to detect"),
              F.flag("align_numbers", "Right-align numeric columns", True),
              F.save("output", "Save result to", required=False)])
def csv_to_markdown(v, ctx):
    import csv
    path = need_file(v["file"], "CSV file")
    raw = read_text(path)
    delim = v["delimiter"] or ("," if "," in raw.splitlines()[0] else "\t")
    rows = list(csv.reader(raw.splitlines(), delimiter=delim))
    if not rows:
        raise ToolError("The file is empty")
    header, body = rows[0], rows[1:]
    widths = [max(len(str(header[i])), *(len(str(r[i])) for r in body if i < len(r)))
              for i in range(len(header))]

    def numeric(col: int) -> bool:
        values = [r[col] for r in body if col < len(r) and r[col].strip()]
        return bool(values) and all(re.fullmatch(r"-?[\d.,%]+", val.strip()) for val in values)

    aligns = []
    for i in range(len(header)):
        if v["align_numbers"] and numeric(i):
            aligns.append("---:")
        else:
            aligns.append("---")
    lines = ["| " + " | ".join(str(header[i]).ljust(widths[i]) for i in range(len(header))) + " |",
             "| " + " | ".join(aligns) + " |"]
    for row in body:
        cells = [str(row[i]) if i < len(row) else "" for i in range(len(header))]
        lines.append("| " + " | ".join(
            cells[i].rjust(widths[i]) if aligns[i] == "---:" else cells[i].ljust(widths[i])
            for i in range(len(header))) + " |")
    return _emit(v, ctx, "\n".join(lines))


@tool(id="extract-emails", name="Extract Email Addresses", category="Text",
      summary="Pull every email address out of text, de-duplicated and sorted.",
      keywords="emails extract addresses contacts scrape",
      fields=_input_fields() + [F.flag("sort", "Sort alphabetically", True)])
def extract_emails(v, ctx):
    text = _text(v)
    found = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    unique = sorted(set(found), key=str.lower) if v["sort"] else list(dict.fromkeys(found))
    if not unique:
        return "No email addresses found."
    return _emit(v, ctx, "\n".join(unique))


@tool(id="extract-urls", name="Extract Links", category="Text",
      summary="Collect every URL in a text or page, optionally keeping only unique domains.",
      keywords="urls links http extract scrape domains",
      fields=_input_fields() + [F.flag("domains_only", "Show only unique domains", False)])
def extract_urls(v, ctx):
    text = _text(v)
    urls = re.findall(r"https?://[^\s<>\"')]+", text)
    if v["domains_only"]:
        from urllib.parse import urlparse
        urls = sorted({urlparse(u).netloc for u in urls})
    else:
        urls = list(dict.fromkeys(urls))
    if not urls:
        return "No links found."
    return _emit(v, ctx, "\n".join(urls))


@tool(id="extract-numbers", name="Extract Numbers", category="Text",
      summary="Grab every number from text — decimals, negatives and thousands separators.",
      keywords="numbers extract digits values parse",
      fields=_input_fields() + [F.flag("sum", "Also print the total", True)])
def extract_numbers(v, ctx):
    text = _text(v)
    raw = re.findall(r"-?\d[\d,]*(?:\.\d+)?", text)
    values = []
    for item in raw:
        try:
            values.append(float(item.replace(",", "")))
        except ValueError:
            continue
    ctx.log(", ".join(f"{n:g}" for n in values[:300]))
    if v["sum"] and values:
        ctx.log(f"count={len(values)}  sum={sum(values):g}  "
                f"min={min(values):g}  max={max(values):g}  mean={sum(values)/len(values):g}")
    return f"{len(values)} number(s)"


@tool(id="remove-duplicate-words", name="Remove Repeated Words", category="Text",
      summary="Collapse accidental repeats like 'the the' into a single word.",
      keywords="repeated words stutter duplicate collapse",
      fields=_input_fields())
def remove_duplicate_words(v, ctx):
    text = _text(v)
    out = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    removed = len(re.findall(r"\b(\w+)(\s+\1\b)+", text, flags=re.IGNORECASE))
    ctx.log(f"Collapsed {removed} repetition(s)")
    return _emit(v, ctx, out)


@tool(id="reverse-lines", name="Reverse Line Order", category="Text",
      summary="Flip the order of lines, or reverse the characters in each line.",
      keywords="reverse flip order lines backwards",
      fields=_input_fields() + [F.choice("what", "Reverse",
                                         ["Line order", "Each line's characters", "Both"],
                                         "Line order")])
def reverse_lines(v, ctx):
    text = _text(v)
    lines = text.splitlines()
    if v["what"] in ("Each line's characters", "Both"):
        lines = [line[::-1] for line in lines]
    if v["what"] in ("Line order", "Both"):
        lines.reverse()
    return _emit(v, ctx, "\n".join(lines))


@tool(id="slugify-text", name="Make URL Slug", category="Text",
      summary="Turn any title into a lowercase, hyphenated, ASCII-only slug.",
      keywords="slug url seo filename ascii",
      fields=_input_fields() + [F.choice("separator", "Separator", ["-", "_", ""], "-"),
                                F.flag("ascii", "Strip accents and non-ASCII", True)])
def slugify_text(v, ctx):
    from ._util import slugify
    text = _text(v).strip()
    out = slugify(text, v["separator"] or "", v["ascii"])
    return _emit(v, ctx, out)


@tool(id="fix-smart-quotes", name="Fix Smart Quotes & Dashes", category="Text",
      summary="Convert curly quotes, en dashes and ellipses into plain ASCII characters.",
      keywords="smart quotes curly apostrophe dash ellipsis ascii normalise",
      fields=_input_fields())
def fix_smart_quotes(v, ctx):
    text = _text(v)
    table = {"\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'", "\u201c": '"',
             "\u201d": '"', "\u201e": '"', "\u2013": "-", "\u2014": "-", "\u2015": "-",
             "\u2026": "...", "\u00a0": " ", "\u200b": "", "\u2212": "-", "\u00ad": ""}
    out = "".join(table.get(ch, ch) for ch in text)
    changed = sum(1 for ch in text if ch in table)
    ctx.log(f"Replaced {changed} character(s)")
    return _emit(v, ctx, out)


@tool(id="remove-accents", name="Remove Accents", category="Text",
      summary="Normalise accented letters to plain ASCII while keeping the text readable.",
      keywords="accents diacritics ascii unicode normalise",
      fields=_input_fields())
def remove_accents(v, ctx):
    text = _text(v)
    out = unicodedata.normalize("NFKD", text)
    out = "".join(ch for ch in out if not unicodedata.combining(ch))
    return _emit(v, ctx, out)


@tool(id="strip-ansi", name="Strip Colour Codes", category="Text",
      summary="Remove ANSI escape sequences from logs and terminal output.",
      keywords="ansi colour color escape codes terminal logs clean",
      fields=_input_fields())
def strip_ansi(v, ctx):
    text = _text(v)
    out = re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]", "", text)
    return _emit(v, ctx, out)


@tool(id="tab-to-spaces", name="Tabs ↔ Spaces", category="Text",
      summary="Convert leading tabs to spaces or spaces to tabs at a width you choose.",
      keywords="tabs spaces indent convert width",
      fields=_input_fields() + [F.choice("direction", "Convert",
                                         ["Tabs to spaces", "Spaces to tabs"], "Tabs to spaces"),
                                F.integer("width", "Tab width", 4, minimum=1, maximum=16)])
def tab_to_spaces(v, ctx):
    text = _text(v)
    width = v["width"]
    if v["direction"] == "Tabs to spaces":
        out = "\n".join(re.sub(r"^\t+", lambda m: " " * (width * len(m.group())), line)
                        for line in text.splitlines())
    else:
        def convert(line: str) -> str:
            stripped = line.lstrip(" ")
            indent = len(line) - len(stripped)
            return "\t" * (indent // width) + " " * (indent % width) + stripped
        out = "\n".join(convert(line) for line in text.splitlines())
    return _emit(v, ctx, out)


@tool(id="summarise-text", name="Text Summary", category="Text",
      summary="Pick the most representative sentences to make a quick extractive summary.",
      keywords="summary summarise abstract shorten condense",
      fields=_input_fields() + [F.integer("sentences", "Sentences to keep", 5, minimum=1, maximum=30)])
def summarise_text(v, ctx):
    text = _text(v)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]
    if len(sentences) <= v["sentences"]:
        return _emit(v, ctx, " ".join(sentences))
    words = re.findall(r"\b\w{4,}\b", text.lower())
    freq = Counter(words)
    top = dict(freq.most_common(60))
    scores = []
    for index, sentence in enumerate(sentences):
        tokens = re.findall(r"\b\w{4,}\b", sentence.lower())
        score = sum(top.get(t, 0) for t in tokens) / (len(tokens) + 1)
        scores.append((score, index, sentence))
    chosen = sorted(scores, key=lambda s: s[0], reverse=True)[:v["sentences"]]
    summary = " ".join(s for _, _, s in sorted(chosen, key=lambda s: s[1]))
    return _emit(v, ctx, summary)


@tool(id="split-sentences", name="Split Into Sentences", category="Text",
      summary="One sentence per line, ready for subtitles, cards or review.",
      keywords="sentences split lines subtitle",
      fields=_input_fields())
def split_sentences(v, ctx):
    text = _text(v)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(\[])", " ".join(text.split()))
    return _emit(v, ctx, "\n".join(p.strip() for p in parts if p.strip()))


@tool(id="longest-lines", name="Longest Lines", category="Text",
      summary="The longest lines in a text — useful for finding runaway paragraphs.",
      keywords="longest lines length paragraphs",
      fields=_input_fields() + [F.integer("limit", "Show", 10, minimum=1, maximum=200)])
def longest_lines(v, ctx):
    text = _text(v)
    lines = [(len(line), index + 1, line) for index, line in enumerate(text.splitlines())]
    lines.sort(reverse=True)
    for length, number, line in lines[:v["limit"]]:
        ctx.log(f"{length:>5}  line {number}: {line[:120]}")
    return f"{len(lines)} line(s)"


# --------------------------------------------------------------------------
# Whole-file operations
# --------------------------------------------------------------------------
@tool(id="line-endings", name="Convert Line Endings", category="Text",
      summary="Switch a file between Windows (CRLF), Unix (LF) and old Mac (CR) endings.",
      keywords="line endings crlf lf cr convert newline",
      fields=[F.file("file", "Text file"),
              F.choice("target", "Convert to",
                       ["Windows (CRLF)", "Unix (LF)", "Mac classic (CR)"], "Windows (CRLF)"),
              F.flag("apply", "Write the change back", False)])
def line_endings(v, ctx):
    path = need_file(v["file"], "Text file")
    raw = path.read_bytes()
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    cr = raw.count(b"\r") - crlf
    ctx.log(f"Found: {crlf} CRLF, {lf} LF, {cr} CR")
    newline = {"Windows (CRLF)": "\r\n", "Unix (LF)": "\n", "Mac classic (CR)": "\r"}[v["target"]]
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    out = text.replace("\n", newline)
    if not v["apply"]:
        return "Preview only — tick 'Write the change back' to save"
    path.write_bytes(out.encode("utf-8"))
    return f"Rewritten with {v['target']} endings"


@tool(id="encoding-convert", name="Convert Text Encoding", category="Text",
      summary="Re-save a text file in UTF-8, UTF-16, Windows-1252 or Latin-1.",
      keywords="encoding charset utf8 utf16 cp1252 latin1 convert",
      fields=[F.file("file", "Text file"),
              F.choice("target", "Write as", ["UTF-8", "UTF-8 with BOM", "UTF-16", "Windows-1252",
                                              "Latin-1"], "UTF-8"),
              F.save("output", "Save as", required=False,
                     help="Leave blank to overwrite a copy next to the original"),
              F.flag("overwrite", "Overwrite the original file", False)])
def encoding_convert(v, ctx):
    path = need_file(v["file"], "Text file")
    text = read_text(path)
    codec = {"UTF-8": "utf-8", "UTF-8 with BOM": "utf-8-sig", "UTF-16": "utf-16",
             "Windows-1252": "cp1252", "Latin-1": "latin-1"}[v["target"]]
    if v["overwrite"]:
        target = path
    elif v["output"].strip():
        target = out_path(v["output"], path.stem + ".txt")
    else:
        target = path.with_name(f"{path.stem}-{codec.replace('-', '')}{path.suffix}")
    data = text.encode(codec, errors="replace")
    target.write_bytes(data)
    ctx.output(str(target))
    return f"Wrote {human_size(len(data))} as {v['target']} → {target.name}"


@tool(id="batch-replace", name="Replace Across Files", category="Text",
      summary="Find and replace inside every matching file in a folder, with a preview.",
      keywords="batch replace across files bulk search replace folder",
      fields=[F.folder("folder", "Folder"),
              F.text("pattern", "Only files matching", "*.txt"),
              F.text("find", "Find", required=True),
              F.text("replace", "Replace with"),
              F.flag("regex", "Find is a regular expression", False),
              F.flag("case_sensitive", "Match case", False),
              F.flag("recursive", "Include subfolders", True),
              F.flag("apply", "Apply the change", False)])
def batch_replace(v, ctx):
    root = need_dir(v["folder"])
    flags = 0 if v["case_sensitive"] else re.IGNORECASE
    try:
        regex = re.compile(v["find"] if v["regex"] else re.escape(v["find"]), flags)
    except re.error as exc:
        raise ToolError(f"Bad regular expression: {exc}") from exc
    touched = 0
    total = 0
    for path in iter_files(root, v["recursive"], v["pattern"] or "*"):
        try:
            text = read_text(path)
        except OSError:
            continue
        if not regex.search(text):
            continue
        new_text, count = regex.subn(v["replace"], text)
        ctx.log(f"{path.relative_to(root)}  ({count})")
        total += count
        if v["apply"]:
            try:
                path.write_text(new_text, encoding="utf-8")
                touched += 1
            except OSError as exc:
                ctx.log(f"! {path.name}: {exc}")
    if not v["apply"]:
        return f"{total} match(es) in {touched or 'several'} file(s) — preview only"
    return f"Replaced {total} match(es) across {touched} file(s)"


@tool(id="split-text-by-lines", name="Split Text Into Files", category="Text",
      summary="Cut a long text file into several smaller files of N lines each.",
      keywords="split text lines files chunk divide",
      fields=[F.file("file", "Text file"),
              F.integer("lines", "Lines per file", 1000, minimum=1),
              F.folder("output", "Output folder", required=False)])
def split_text_by_lines(v, ctx):
    path = need_file(v["file"], "Text file")
    out_dir = Path(v["output"]) if v["output"].strip() else path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = read_text(path).splitlines()
    size = v["lines"]
    parts = 0
    for start in range(0, len(lines), size):
        parts += 1
        chunk = lines[start:start + size]
        target = out_dir / f"{path.stem}-part{parts:03d}{path.suffix or '.txt'}"
        write_text(target, "\n".join(chunk))
        ctx.output(str(target))
        ctx.log(f"{target.name}  {len(chunk)} lines")
    return f"{parts} file(s) from {len(lines)} lines"


@tool(id="batch-case-files", name="Change Case Across Files", category="Text",
      summary="Apply a case change to the contents of every matching file in a folder.",
      keywords="batch case files uppercase lowercase folder",
      fields=[F.folder("folder", "Folder"),
              F.text("pattern", "Only files matching", "*.txt"),
              F.choice("mode", "Convert to", ["UPPER", "lower", "Title"], "UPPER"),
              F.flag("recursive", "Include subfolders", True),
              F.flag("apply", "Write the changes", False)])
def batch_case_files(v, ctx):
    root = need_dir(v["folder"])
    convert = {"UPPER": str.upper, "lower": str.lower, "Title": str.title}[v["mode"]]
    count = 0
    for path in iter_files(root, v["recursive"], v["pattern"] or "*"):
        try:
            text = read_text(path)
        except OSError:
            continue
        new_text = convert(text)
        if new_text == text:
            continue
        count += 1
        if v["apply"]:
            path.write_text(new_text, encoding="utf-8")
    verb = "Converted" if v["apply"] else "Would convert"
    return f"{verb} {count} file(s) to {v['mode']}"
