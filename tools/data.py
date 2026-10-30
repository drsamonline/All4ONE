"""Data — JSON, CSV, XML, YAML, INI and SQLite."""

from __future__ import annotations

import csv
import io
import json
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import human_size, need_file, out_path, read_text, report_table, write_csv, write_text


def _json_input(v) -> object:
    path = str(v.get("file") or "").strip()
    raw = read_text(need_file(path)) if path else str(v.get("text") or "")
    if not raw.strip():
        raise ToolError("Paste some JSON, or choose a file")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToolError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def _save(v, ctx, text: str, name: str, preview: int = 5000) -> str:
    if str(v.get("output") or "").strip():
        target = write_text(out_path(v["output"], name), text)
        ctx.output(str(target))
        ctx.log(f"Saved to {target}")
    if len(text) > preview:
        ctx.log(text[:preview] + f"\n… {len(text) - preview} more characters")
        return f"{len(text)} characters"
    ctx.log(text)
    return ""


# --------------------------------------------------------------------------
# JSON
# --------------------------------------------------------------------------
@tool(id="json-format", name="Format JSON", category="Data",
      summary="Pretty-print or minify JSON, with sorted keys and a chosen indent.",
      keywords="json pretty format beautify minify indent",
      fields=[F.multi("text", "JSON", rows=10),
              F.file("file", "…or read a JSON file", required=False, filters="JSON (*.json)"),
              F.choice("mode", "Output", ["Pretty", "Minified"], "Pretty"),
              F.integer("indent", "Indent spaces", 2, minimum=0, maximum=8),
              F.flag("sort_keys", "Sort keys alphabetically", False),
              F.save("output", "Save result to", required=False)])
def json_format(v, ctx):
    data = _json_input(v)
    if v["mode"] == "Minified":
        text = json.dumps(data, separators=(",", ":"), sort_keys=v["sort_keys"], ensure_ascii=False)
    else:
        text = json.dumps(data, indent=v["indent"] or None, sort_keys=v["sort_keys"],
                          ensure_ascii=False)
    return _save(v, ctx, text, "formatted.json")


@tool(id="json-validate", name="Validate JSON", category="Data",
      summary="Check JSON syntax and report the exact line and column of any problem.",
      keywords="json validate check syntax error lint",
      fields=[F.multi("text", "JSON", rows=10),
              F.file("file", "…or read a JSON file", required=False)])
def json_validate(v, ctx):
    path = str(v.get("file") or "").strip()
    raw = read_text(need_file(path)) if path else str(v.get("text") or "")
    if not raw.strip():
        raise ToolError("Nothing to validate")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        ctx.log(f"✕ Invalid at line {exc.lineno}, column {exc.colno}")
        ctx.log(f"  {exc.msg}")
        line = raw.splitlines()[exc.lineno - 1] if exc.lineno <= len(raw.splitlines()) else ""
        ctx.log(f"  {line}")
        ctx.log("  " + " " * max(0, exc.colno - 1) + "^")
        return {"valid": False, "line": exc.lineno, "column": exc.colno, "message": exc.msg}
    kind = type(data).__name__
    size = len(data) if isinstance(data, (list, dict)) else 1
    return {"valid": True, "top_level_type": kind, "items": size,
            "bytes": len(raw.encode("utf-8"))}


@tool(id="json-extract", name="Extract JSON Path", category="Data",
      summary="Pull one value out of nested JSON with a dotted path like data.users.0.name.",
      keywords="json path extract get key value query",
      fields=[F.multi("text", "JSON", rows=8),
              F.file("file", "…or read a JSON file", required=False),
              F.text("path", "Path", "data.items.0.name", required=True,
                     help="Dots between keys, numbers for list positions"),
              F.save("output", "Save value to", required=False)])
def json_extract(v, ctx):
    data = _json_input(v)
    current = data
    for step in [p for p in v["path"].strip().split(".") if p]:
        if isinstance(current, list):
            try:
                current = current[int(step)]
                continue
            except (ValueError, IndexError):
                raise ToolError(f"No list item {step!r}")
        if not isinstance(current, dict) or step not in current:
            available = ", ".join(list(current)[:12]) if isinstance(current, dict) else "not an object"
            raise ToolError(f"No key {step!r} (available: {available})")
        current = current[step]
    text = json.dumps(current, indent=2, ensure_ascii=False) if isinstance(current, (dict, list)) else str(current)
    return _save(v, ctx, text, "value.json")


@tool(id="json-to-csv", name="JSON to CSV", category="Data",
      summary="Flatten an array of JSON objects into a CSV table, one row per record.",
      keywords="json csv convert table flatten export",
      fields=[F.file("file", "JSON file", filters="JSON (*.json)"),
              F.save("output", "Save CSV to", required=True),
              F.text("delimiter", "Delimiter", ","),
              F.integer("limit", "Maximum rows (0 = all)", 0, minimum=0)])
def json_to_csv(v, ctx):
    data = _json_input(v)
    if isinstance(data, dict):
        for key in ("data", "items", "records", "results", "rows"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
        else:
            data = [data]
    if not isinstance(data, list):
        raise ToolError("Expected a JSON array of objects")
    rows = []
    for record in data[:v["limit"] or None]:
        if not isinstance(record, dict):
            rows.append({"value": record})
            continue
        flat: dict[str, object] = {}

        def flatten(prefix: str, value):
            if isinstance(value, dict):
                for key, inner in value.items():
                    flatten(f"{prefix}{key}.", inner)
            elif isinstance(value, list):
                flat[prefix.rstrip(".")] = json.dumps(value, ensure_ascii=False)
            else:
                flat[prefix.rstrip(".")] = value

        flatten("", record)
        rows.append(flat)
    columns = list(dict.fromkeys(key for row in rows for key in row))
    target = write_csv(out_path(v["output"], "data.csv"), rows, columns)
    ctx.output(str(target))
    return f"{len(rows)} row(s), {len(columns)} column(s) → {target}"


@tool(id="json-merge", name="Merge JSON Files", category="Data",
      summary="Combine several JSON files into one array, or deep-merge objects.",
      keywords="json merge combine join files",
      fields=[F.files("files", "JSON files", filters="JSON (*.json)"),
              F.choice("mode", "Combine as", ["Array of documents", "Deep merge objects"], "Array of documents"),
              F.save("output", "Save result to", required=True)])
def json_merge(v, ctx):
    files = v["files"] if isinstance(v["files"], list) else [f for f in v["files"].split("|") if f]
    if not files:
        raise ToolError("Choose at least one JSON file")
    documents = []
    for raw in files:
        path = need_file(raw)
        try:
            documents.append(json.loads(read_text(path)))
        except json.JSONDecodeError as exc:
            raise ToolError(f"{path.name} is not valid JSON: {exc.msg}") from exc
    if v["mode"] == "Array of documents":
        merged: object = documents
    else:
        merged = {}
        for doc in documents:
            if not isinstance(doc, dict):
                raise ToolError("Deep merge needs JSON objects at the top level")

            def deep(target: dict, source: dict):
                for key, value in source.items():
                    if isinstance(value, dict) and isinstance(target.get(key), dict):
                        deep(target[key], value)
                    else:
                        target[key] = value

            deep(merged, doc)
    text = json.dumps(merged, indent=2, ensure_ascii=False)
    target = write_text(out_path(v["output"], "merged.json"), text)
    ctx.output(str(target))
    return f"Merged {len(files)} file(s) → {target}"


@tool(id="json-diff", name="Compare JSON", category="Data",
      summary="Show which keys were added, removed or changed between two JSON documents.",
      keywords="json diff compare changes keys",
      fields=[F.file("file_a", "First JSON", filters="JSON (*.json)"),
              F.file("file_b", "Second JSON", filters="JSON (*.json)")])
def json_diff(v, ctx):
    a = _json_input({"file": v["file_a"]})
    b = _json_input({"file": v["file_b"]})
    changes: list[dict] = []

    def walk(x, y, path: str = ""):
        if type(x) is not type(y):
            changes.append({"path": path or "(root)", "change": "type",
                            "before": type(x).__name__, "after": type(y).__name__})
            return
        if isinstance(x, dict):
            for key in x.keys() - y.keys():
                changes.append({"path": f"{path}.{key}".lstrip("."), "change": "removed",
                                "before": json.dumps(x[key], ensure_ascii=False)[:80], "after": ""})
            for key in y.keys() - x.keys():
                changes.append({"path": f"{path}.{key}".lstrip("."), "change": "added",
                                "before": "", "after": json.dumps(y[key], ensure_ascii=False)[:80]})
            for key in x.keys() & y.keys():
                walk(x[key], y[key], f"{path}.{key}".lstrip("."))
        elif isinstance(x, list):
            if len(x) != len(y):
                changes.append({"path": path or "(root)", "change": "length",
                                "before": str(len(x)), "after": str(len(y))})
            for index, (item_a, item_b) in enumerate(zip(x, y)):
                walk(item_a, item_b, f"{path}.{index}".lstrip("."))
        elif x != y:
            changes.append({"path": path or "(root)", "change": "changed",
                            "before": json.dumps(x, ensure_ascii=False)[:80],
                            "after": json.dumps(y, ensure_ascii=False)[:80]})

    walk(a, b)
    if not changes:
        return "The two documents are identical."
    ctx.log(report_table(changes[:200], ["path", "change", "before", "after"]))
    return f"{len(changes)} difference(s)"


@tool(id="ndjson", name="JSON Lines ↔ JSON", category="Data",
      summary="Convert between newline-delimited JSON (JSONL) and a JSON array.",
      keywords="ndjson jsonl json lines array convert stream",
      fields=[F.file("file", "File", filters="JSON or JSONL (*.json *.jsonl *.ndjson)"),
              F.choice("direction", "Convert",
                       ["JSONL → JSON array", "JSON array → JSONL"], "JSONL → JSON array"),
              F.save("output", "Save result to", required=True)])
def ndjson(v, ctx):
    path = need_file(v["file"])
    raw = read_text(path)
    if v["direction"].startswith("JSONL"):
        records = []
        for number, line in enumerate(raw.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ToolError(f"Line {number} is not valid JSON: {exc.msg}") from exc
        text = json.dumps(records, indent=2, ensure_ascii=False)
        count = len(records)
    else:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ToolError(f"Invalid JSON: {exc.msg}") from exc
        if not isinstance(data, list):
            raise ToolError("Expected a JSON array")
        text = "\n".join(json.dumps(item, ensure_ascii=False) for item in data)
        count = len(data)
    target = write_text(out_path(v["output"], "converted.json"), text)
    ctx.output(str(target))
    return f"{count} record(s) → {target.name}"


# --------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------
def _csv_read(path: Path, delimiter: str = "") -> tuple[list[str], list[dict]]:
    raw = read_text(path)
    if not raw.strip():
        raise ToolError("The file is empty")
    candidate = (delimiter or "").strip()
    if len(candidate) == 1:
        delim = candidate
    else:
        first = raw.splitlines()[0]
        delim = "," if "," in first else "\t" if "\t" in first else ";" if ";" in first else "|" if "|" in first else ","
    reader = csv.DictReader(io.StringIO(raw), delimiter=delim)
    rows = [dict(row) for row in reader]
    return list(reader.fieldnames or []), rows


@tool(id="csv-preview", name="Preview CSV", category="Data",
      summary="Show a CSV's columns, row count and first rows without opening Excel.",
      keywords="csv preview head inspect columns rows",
      fields=[F.file("file", "CSV file", filters="CSV (*.csv *.tsv)"),
              F.integer("rows", "Rows to show", 15, minimum=1, maximum=200),
              F.text("delimiter", "Delimiter", "", help="Leave blank to detect")])
def csv_preview(v, ctx):
    columns, rows = _csv_read(need_file(v["file"]), v["delimiter"])
    ctx.log(report_table(rows[:v["rows"]], columns))
    return {"columns": columns, "rows": len(rows), "showing": min(v["rows"], len(rows))}


@tool(id="csv-info", name="CSV Column Report", category="Data",
      summary="Per column: type, blanks, distinct values, min, max and mean.",
      keywords="csv columns types statistics nulls summary",
      fields=[F.file("file", "CSV file", filters="CSV (*.csv *.tsv)"),
              F.text("delimiter", "Delimiter", ""),
              F.save("report", "Save report to", required=False)])
def csv_info(v, ctx):
    columns, rows = _csv_read(need_file(v["file"]), v["delimiter"])
    report = []
    for column in columns:
        values = [str(row.get(column) or "").strip() for row in rows]
        blanks = sum(1 for val in values if not val)
        present = [val for val in values if val]
        numbers = []
        for val in present:
            try:
                numbers.append(float(val.replace(",", "").replace("%", "")))
            except ValueError:
                pass
        numeric = bool(present) and len(numbers) == len(present)
        entry = {"column": column, "type": "number" if numeric else "text",
                 "filled": len(present), "blanks": blanks,
                 "distinct": len(set(present))}
        if numeric and numbers:
            entry.update({"min": round(min(numbers), 4), "max": round(max(numbers), 4),
                          "mean": round(sum(numbers) / len(numbers), 4)})
        else:
            longest = max(present, key=len) if present else ""
            entry.update({"min": "", "max": "", "mean": f"longest: {longest[:20]}"})
        report.append(entry)
    ctx.log(report_table(report, ["column", "type", "filled", "blanks", "distinct", "mean"]))
    if v["report"].strip():
        target = write_csv(out_path(v["report"], "csv-report.csv"), report)
        ctx.output(str(target))
    return f"{len(columns)} column(s), {len(rows)} row(s)"


@tool(id="csv-query", name="Filter & Sort CSV", category="Data",
      summary="Filter rows by a condition, sort by any column and keep only the columns you want.",
      keywords="csv filter query sort where select sql",
      fields=[F.file("file", "CSV file", filters="CSV (*.csv *.tsv)"),
              F.text("column", "Filter column", help="Leave blank for no filter"),
              F.choice("operator", "Condition",
                       ["contains", "equals", "not equals", "greater than", "less than",
                        "is empty", "is not empty"], "contains"),
              F.text("value", "Value"),
              F.text("sort_by", "Sort by column", help="Optional"),
              F.flag("descending", "Sort descending", False),
              F.text("keep", "Keep only columns", help="Comma separated; blank keeps all"),
              F.integer("limit", "Maximum rows (0 = all)", 0, minimum=0),
              F.save("output", "Save result to", required=True)])
def csv_query(v, ctx):
    columns, rows = _csv_read(need_file(v["file"]))
    column = v["column"].strip()
    if column:
        if column not in columns:
            raise ToolError(f"No column {column!r}. Columns: {', '.join(columns)}")
        op, value = v["operator"], v["value"]
        def keep(row: dict) -> bool:
            cell = str(row.get(column) or "")
            if op == "contains":
                return value.lower() in cell.lower()
            if op == "equals":
                return cell == value
            if op == "not equals":
                return cell != value
            if op in ("greater than", "less than"):
                try:
                    left, right = float(cell), float(value)
                except ValueError:
                    return False
                return left > right if op == "greater than" else left < right
            if op == "is empty":
                return not cell.strip()
            return bool(cell.strip())
        rows = [row for row in rows if keep(row)]
    if v["sort_by"].strip():
        key = v["sort_by"].strip()
        if key not in columns:
            raise ToolError(f"No column {key!r} to sort by")
        def sort_key(row: dict):
            cell = str(row.get(key) or "")
            try:
                return (0, float(cell.replace(",", "")))
            except ValueError:
                return (1, cell.lower())
        rows.sort(key=sort_key, reverse=v["descending"])
    if v["keep"].strip():
        wanted = [c.strip() for c in v["keep"].split(",") if c.strip()]
        missing = [c for c in wanted if c not in columns]
        if missing:
            raise ToolError(f"Unknown column(s): {', '.join(missing)}")
        rows = [{c: row.get(c, "") for c in wanted} for row in rows]
        columns = wanted
    if v["limit"]:
        rows = rows[:v["limit"]]
    target = write_csv(out_path(v["output"], "filtered.csv"), rows, columns)
    ctx.output(str(target))
    return f"{len(rows)} row(s) → {target}"


@tool(id="csv-sort", name="Sort CSV", category="Data",
      summary="Sort a CSV by one or more columns, treating numbers as numbers.",
      keywords="csv sort order by column numeric",
      fields=[F.file("file", "CSV file", filters="CSV (*.csv *.tsv)"),
              F.text("columns", "Sort by (comma separated)", required=True),
              F.flag("descending", "Descending", False),
              F.save("output", "Save result to", required=True)])
def csv_sort(v, ctx):
    columns, rows = _csv_read(need_file(v["file"]))
    keys = [c.strip() for c in v["columns"].split(",") if c.strip()]
    for key in keys:
        if key not in columns:
            raise ToolError(f"No column {key!r}")
    def value_of(row: dict, key: str):
        cell = str(row.get(key) or "")
        try:
            return (0, float(cell.replace(",", "")))
        except ValueError:
            return (1, cell.lower())
    rows.sort(key=lambda row: tuple(value_of(row, key) for key in keys), reverse=v["descending"])
    target = write_csv(out_path(v["output"], "sorted.csv"), rows, columns)
    ctx.output(str(target))
    return f"Sorted {len(rows)} row(s) by {', '.join(keys)}"


@tool(id="csv-dedupe", name="Remove Duplicate Rows", category="Data",
      summary="Drop repeated rows, either on every column or on the ones you choose.",
      keywords="csv duplicates dedupe unique rows",
      fields=[F.file("file", "CSV file", filters="CSV (*.csv *.tsv)"),
              F.text("columns", "Compare only these columns", help="Blank compares whole rows"),
              F.save("output", "Save result to", required=True)])
def csv_dedupe(v, ctx):
    columns, rows = _csv_read(need_file(v["file"]))
    keys = [c.strip() for c in v["columns"].split(",") if c.strip()] or columns
    seen = set()
    unique = []
    for row in rows:
        signature = tuple(str(row.get(key) or "").strip().lower() for key in keys)
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(row)
    target = write_csv(out_path(v["output"], "deduped.csv"), unique, columns)
    ctx.output(str(target))
    return f"Removed {len(rows) - len(unique)} duplicate row(s); {len(unique)} remain"


@tool(id="csv-columns", name="Select / Rename Columns", category="Data",
      summary="Keep or drop columns and rename headers in one pass.",
      keywords="csv columns select drop rename headers",
      fields=[F.file("file", "CSV file", filters="CSV (*.csv *.tsv)"),
              F.text("keep", "Keep columns", help="Comma separated; blank keeps all"),
              F.text("drop", "Drop columns", help="Comma separated"),
              F.text("rename", "Rename", help="old=new, old2=new2"),
              F.save("output", "Save result to", required=True)])
def csv_columns(v, ctx):
    columns, rows = _csv_read(need_file(v["file"]))
    if v["keep"].strip():
        wanted = [c.strip() for c in v["keep"].split(",") if c.strip()]
        missing = [c for c in wanted if c not in columns]
        if missing:
            raise ToolError(f"Unknown column(s): {', '.join(missing)}")
        columns = wanted
    if v["drop"].strip():
        unwanted = {c.strip() for c in v["drop"].split(",") if c.strip()}
        columns = [c for c in columns if c not in unwanted]
    renames = {}
    for pair in v["rename"].split(","):
        if "=" in pair:
            old, _, new = pair.partition("=")
            renames[old.strip()] = new.strip()
    out_rows = []
    for row in rows:
        out_rows.append({renames.get(col, col): row.get(col, "") for col in columns})
    new_columns = [renames.get(col, col) for col in columns]
    target = write_csv(out_path(v["output"], "columns.csv"), out_rows, new_columns)
    ctx.output(str(target))
    return f"{len(out_rows)} row(s), {len(new_columns)} column(s) → {target}"


@tool(id="csv-merge", name="Merge CSV Files", category="Data",
      summary="Stack several CSVs into one, aligning columns by header name.",
      keywords="csv merge combine append join stack",
      fields=[F.files("files", "CSV files", filters="CSV (*.csv *.tsv)"),
              F.save("output", "Save result to", required=True),
              F.flag("add_source", "Add a column naming the source file", False)])
def csv_merge(v, ctx):
    files = v["files"] if isinstance(v["files"], list) else [f for f in v["files"].split("|") if f]
    if not files:
        raise ToolError("Choose at least one CSV file")
    all_rows: list[dict] = []
    columns: list[str] = []
    for raw in files:
        path = need_file(raw)
        cols, rows = _csv_read(path)
        for col in cols:
            if col not in columns:
                columns.append(col)
        if v["add_source"]:
            for row in rows:
                row["source_file"] = path.name
            if "source_file" not in columns:
                columns.append("source_file")
        all_rows.extend(rows)
    target = write_csv(out_path(v["output"], "merged.csv"), all_rows, columns)
    ctx.output(str(target))
    return f"{len(all_rows)} row(s) from {len(files)} file(s) → {target}"


@tool(id="csv-split", name="Split CSV by Rows", category="Data",
      summary="Cut a large CSV into several smaller files of N rows each.",
      keywords="csv split chunk rows parts",
      fields=[F.file("file", "CSV file", filters="CSV (*.csv *.tsv)"),
              F.integer("rows", "Rows per file", 1000, minimum=1),
              F.folder("output", "Output folder", required=False)])
def csv_split(v, ctx):
    path = need_file(v["file"])
    columns, rows = _csv_read(path)
    out_dir = Path(v["output"]) if v["output"].strip() else path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    size = v["rows"]
    parts = 0
    for start in range(0, len(rows), size):
        parts += 1
        chunk = rows[start:start + size]
        target = out_dir / f"{path.stem}-part{parts:03d}.csv"
        write_csv(target, chunk, columns)
        ctx.output(str(target))
        ctx.log(f"{target.name}  {len(chunk)} rows")
    return f"{parts} file(s) from {len(rows)} row(s)"


@tool(id="delimiter-convert", name="Change Delimiter", category="Data",
      summary="Convert between CSV, TSV, semicolon and pipe-separated files.",
      keywords="csv tsv delimiter separator convert semicolon pipe",
      fields=[F.file("file", "Delimited file"),
              F.choice("from_delim", "From", ["Auto-detect", "Comma", "Tab", "Semicolon", "Pipe"],
                       "Auto-detect"),
              F.choice("to_delim", "To", ["Comma", "Tab", "Semicolon", "Pipe"], "Tab"),
              F.flag("quote_all", "Quote every field", False),
              F.save("output", "Save result to", required=True)])
def delimiter_convert(v, ctx):
    path = need_file(v["file"])
    lookup = {"Comma": ",", "Tab": "\t", "Semicolon": ";", "Pipe": "|"}
    source = "" if v["from_delim"] == "Auto-detect" else lookup[v["from_delim"]]
    columns, rows = _csv_read(path, source)
    target = out_path(v["output"], "converted.csv")
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, delimiter=lookup[v["to_delim"]],
                                quoting=csv.QUOTE_ALL if v["quote_all"] else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)
    ctx.output(str(target))
    return f"{len(rows)} row(s) → {target}"


# --------------------------------------------------------------------------
# XML / YAML / INI
# --------------------------------------------------------------------------
@tool(id="xml-format", name="Format XML", category="Data",
      summary="Indent XML so it can be read, or collapse it to a single line.",
      keywords="xml pretty format indent beautify minify",
      fields=[F.file("file", "XML file", filters="XML (*.xml)"),
              F.integer("indent", "Indent spaces", 2, minimum=0, maximum=8),
              F.save("output", "Save result to", required=False)])
def xml_format(v, ctx):
    path = need_file(v["file"], "XML file")
    try:
        root = ET.fromstring(read_text(path))
    except ET.ParseError as exc:
        raise ToolError(f"Invalid XML: {exc}") from exc
    if v["indent"]:
        ET.indent(root, space=" " * v["indent"])
    text = ET.tostring(root, encoding="unicode")
    return _save(v, ctx, text, "formatted.xml")


@tool(id="xml-to-json", name="XML to JSON", category="Data",
      summary="Turn an XML document into JSON, keeping attributes and repeated elements.",
      keywords="xml json convert transform",
      fields=[F.file("file", "XML file", filters="XML (*.xml)"),
              F.flag("attributes", "Include attributes", True),
              F.save("output", "Save result to", required=True)])
def xml_to_json(v, ctx):
    path = need_file(v["file"], "XML file")
    try:
        root = ET.fromstring(read_text(path))
    except ET.ParseError as exc:
        raise ToolError(f"Invalid XML: {exc}") from exc

    def convert(element) -> object:
        node: dict[str, object] = {}
        if v["attributes"] and element.attrib:
            node["@attributes"] = dict(element.attrib)
        children = list(element)
        if children:
            grouped: dict[str, list] = {}
            for child in children:
                grouped.setdefault(child.tag, []).append(convert(child))
            for tag, items in grouped.items():
                node[tag] = items[0] if len(items) == 1 else items
        text = (element.text or "").strip()
        if text and not children:
            return text
        if text:
            node["#text"] = text
        return node

    result = {root.tag: convert(root)}
    target = write_text(out_path(v["output"], "converted.json"),
                        json.dumps(result, indent=2, ensure_ascii=False))
    ctx.output(str(target))
    return f"{target.name} written"


@tool(id="json-to-xml", name="JSON to XML", category="Data",
      summary="Render a JSON document as XML with a root element you name.",
      keywords="json xml convert transform",
      fields=[F.file("file", "JSON file", filters="JSON (*.json)"),
              F.text("root", "Root element name", "root"),
              F.save("output", "Save result to", required=True)])
def json_to_xml(v, ctx):
    data = _json_input(v)
    root_name = v["root"].strip() or "root"

    def build(parent, value, name: str):
        if isinstance(value, dict):
            node = ET.SubElement(parent, name)
            for key, inner in value.items():
                build(node, inner, str(key))
        elif isinstance(value, list):
            for item in value:
                build(parent, item, name)
        else:
            node = ET.SubElement(parent, name)
            node.text = "" if value is None else str(value)

    root = ET.Element(root_name)
    if isinstance(data, dict):
        for key, value in data.items():
            build(root, value, str(key))
    else:
        build(root, data, "item")
    ET.indent(root, space="  ")
    target = write_text(out_path(v["output"], "converted.xml"),
                        ET.tostring(root, encoding="unicode"))
    ctx.output(str(target))
    return f"{target.name} written"


@tool(id="yaml-validate", name="Validate YAML", category="Data",
      summary="Parse a YAML file and report structure or the exact error line.",
      keywords="yaml validate check parse lint",
      fields=[F.file("file", "YAML file", filters="YAML (*.yaml *.yml)")])
def yaml_validate(v, ctx):
    path = need_file(v["file"], "YAML file")
    raw = read_text(path)
    try:
        import yaml  # noqa: PLC0415
    except ImportError:
        ctx.log("PyYAML is not installed, so only basic structure is checked.")
        if "\t" in raw:
            ctx.log("! Tabs are not allowed for indentation in YAML")
        depth = max((len(line) - len(line.lstrip())) for line in raw.splitlines() if line.strip()) if raw.strip() else 0
        return {"parser": "basic", "lines": len(raw.splitlines()), "max_indent": depth,
                "note": "pip install pyyaml for full validation"}
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        if mark:
            raise ToolError(f"Invalid YAML at line {mark.line + 1}, column {mark.column + 1}: "
                            f"{getattr(exc, 'problem', exc)}") from exc
        raise ToolError(f"Invalid YAML: {exc}") from exc
    kind = type(data).__name__
    count = len(data) if isinstance(data, (dict, list)) else 1
    return {"parser": "PyYAML", "valid": True, "top_level_type": kind, "items": count}


@tool(id="yaml-to-json", name="YAML to JSON", category="Data",
      summary="Convert a YAML document to JSON, or JSON back to YAML.",
      keywords="yaml json convert transform",
      needs=("pyyaml",),
      fields=[F.file("file", "File"),
              F.choice("direction", "Convert", ["YAML → JSON", "JSON → YAML"], "YAML → JSON"),
              F.save("output", "Save result to", required=True)])
def yaml_to_json(v, ctx):
    path = need_file(v["file"])
    raw = read_text(path)
    try:
        import yaml  # noqa: PLC0415
    except ImportError as exc:
        raise ToolError("This tool needs PyYAML — pip install pyyaml") from exc
    if v["direction"].startswith("YAML"):
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise ToolError(f"Invalid YAML: {exc}") from exc
        text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        name = "converted.json"
    else:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ToolError(f"Invalid JSON: {exc.msg}") from exc
        text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        name = "converted.yaml"
    target = write_text(out_path(v["output"], name), text)
    ctx.output(str(target))
    return f"{target.name} written"


@tool(id="ini-tool", name="INI / Config File Tool", category="Data",
      summary="Read, list or rewrite keys in an INI file, keeping other sections intact.",
      keywords="ini config settings cfg key value",
      fields=[F.file("file", "INI file", filters="Config (*.ini *.cfg *.conf)"),
              F.choice("action", "Action", ["Show contents", "Get a key", "Set a key",
                                            "Delete a key"], "Show contents"),
              F.text("section", "Section"),
              F.text("key", "Key"),
              F.text("value", "Value"),
              F.flag("apply", "Write changes back", False)])
def ini_tool(v, ctx):
    import configparser
    path = need_file(v["file"], "INI file")
    parser = configparser.ConfigParser()
    parser.optionxform = str  # keep key case
    parser.read(path, encoding="utf-8")
    action = v["action"]
    if action == "Show contents":
        for section in parser.sections():
            ctx.log(f"[{section}]")
            for key, value in parser.items(section):
                ctx.log(f"  {key} = {value}")
        if not parser.sections():
            ctx.log("(no sections)")
        return f"{len(parser.sections())} section(s)"
    section = v["section"].strip()
    key = v["key"].strip()
    if not section or not key:
        raise ToolError("This action needs both a section and a key")
    if action == "Get a key":
        if not parser.has_option(section, key):
            raise ToolError(f"No [{section}] {key}")
        return parser.get(section, key)
    if action == "Set a key":
        if not parser.has_section(section):
            parser.add_section(section)
        parser.set(section, key, v["value"])
    else:
        if not parser.has_option(section, key):
            raise ToolError(f"No [{section}] {key}")
        parser.remove_option(section, key)
    if not v["apply"]:
        return "Preview only — tick 'Write changes back' to save"
    with open(path, "w", encoding="utf-8") as fh:
        parser.write(fh)
    return f"{action} applied to {path.name}"


# --------------------------------------------------------------------------
# SQLite
# --------------------------------------------------------------------------
@tool(id="sqlite-tables", name="SQLite Tables", category="Data",
      summary="List the tables, row counts and columns of a SQLite database.",
      keywords="sqlite database tables schema columns rows",
      fields=[F.file("file", "SQLite database", filters="Database (*.db *.sqlite *.sqlite3)")])
def sqlite_tables(v, ctx):
    path = need_file(v["file"], "Database")
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        cursor = connection.cursor()
        tables = [row[0] for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        rows = []
        for table in tables:
            count = cursor.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            columns = [info[1] for info in cursor.execute(f'PRAGMA table_info("{table}")')]
            rows.append({"table": table, "rows": count, "columns": ", ".join(columns)[:80]})
        ctx.log(report_table(rows, ["table", "rows", "columns"]))
        return f"{len(tables)} table(s) in {path.name}"
    finally:
        connection.close()


@tool(id="sqlite-query", name="Run SQL Query", category="Data",
      summary="Run a read-only SELECT against a SQLite file and save or show the result.",
      keywords="sqlite sql query select database report",
      fields=[F.file("file", "SQLite database", filters="Database (*.db *.sqlite *.sqlite3)"),
              F.multi("sql", "SQL", "SELECT * FROM sqlite_master LIMIT 20;", rows=6),
              F.integer("limit", "Maximum rows shown", 100, minimum=1, maximum=10000),
              F.save("output", "Save result as CSV to", required=False)])
def sqlite_query(v, ctx):
    path = need_file(v["file"], "Database")
    statement = v["sql"].strip()
    if not statement:
        raise ToolError("Write a query")
    if not statement.lstrip().lower().startswith(("select", "with", "pragma", "explain")):
        raise ToolError("Only read-only queries (SELECT / WITH / PRAGMA) are allowed here")
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        cursor = connection.execute(statement)
        columns = [d[0] for d in cursor.description or []]
        rows = [dict(zip(columns, row)) for row in cursor.fetchmany(v["limit"])]
        ctx.log(report_table(rows[:200], columns))
        if v["output"].strip():
            target = write_csv(out_path(v["output"], "query.csv"), rows, columns)
            ctx.output(str(target))
            ctx.log(f"Saved {len(rows)} row(s) to {target}")
        return f"{len(rows)} row(s)"
    except sqlite3.Error as exc:
        raise ToolError(f"SQL error: {exc}") from exc
    finally:
        connection.close()


@tool(id="csv-to-sqlite", name="CSV to SQLite", category="Data",
      summary="Load one or more CSVs into a SQLite database, one table per file.",
      keywords="csv sqlite database import load table",
      fields=[F.files("files", "CSV files", filters="CSV (*.csv *.tsv)"),
              F.save("output", "Database file", required=True,
                     filters="Database (*.db *.sqlite)"),
              F.flag("replace", "Replace existing tables", True)])
def csv_to_sqlite(v, ctx):
    files = v["files"] if isinstance(v["files"], list) else [f for f in v["files"].split("|") if f]
    if not files:
        raise ToolError("Choose at least one CSV file")
    target = out_path(v["output"], "data.db")
    connection = sqlite3.connect(target)
    try:
        for raw in files:
            path = need_file(raw)
            columns, rows = _csv_read(path)
            table = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in path.stem)
            if v["replace"]:
                connection.execute(f'DROP TABLE IF EXISTS "{table}"')
            column_sql = ", ".join(f'"{c}" TEXT' for c in columns)
            connection.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({column_sql})')
            placeholders = ", ".join("?" for _ in columns)
            connection.executemany(
                f'INSERT INTO "{table}" VALUES ({placeholders})',
                [[row.get(c, "") for c in columns] for row in rows])
            ctx.log(f"{table}: {len(rows)} row(s)")
        connection.commit()
    finally:
        connection.close()
    ctx.output(str(target))
    return f"{len(files)} table(s) written to {target}"


@tool(id="sqlite-to-csv", name="SQLite Table to CSV", category="Data",
      summary="Export a whole table from a SQLite database into a CSV file.",
      keywords="sqlite csv export table dump",
      fields=[F.file("file", "SQLite database", filters="Database (*.db *.sqlite *.sqlite3)"),
              F.text("table", "Table", required=True),
              F.save("output", "Save CSV to", required=True)])
def sqlite_to_csv(v, ctx):
    path = need_file(v["file"], "Database")
    table = v["table"].strip()
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        cursor = connection.execute(f'SELECT * FROM "{table}"')
        columns = [d[0] for d in cursor.description or []]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    except sqlite3.Error as exc:
        raise ToolError(f"Could not read {table!r}: {exc}") from exc
    finally:
        connection.close()
    target = write_csv(out_path(v["output"], f"{table}.csv"), rows, columns)
    ctx.output(str(target))
    return f"{len(rows)} row(s) → {target} ({human_size(target.stat().st_size)})"


@tool(id="json-to-sqlite", name="JSON to SQLite", category="Data",
      summary="Load an array of JSON objects into a SQLite table.",
      keywords="json sqlite database import load",
      fields=[F.file("file", "JSON file", filters="JSON (*.json)"),
              F.text("table", "Table name", "records"),
              F.save("output", "Database file", required=True, filters="Database (*.db)")])
def json_to_sqlite(v, ctx):
    data = _json_input(v)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ToolError("Expected an array of JSON objects")
    columns = list(dict.fromkeys(key for item in data for key in item))
    table = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in (v["table"] or "records"))
    target = out_path(v["output"], "data.db")
    connection = sqlite3.connect(target)
    try:
        connection.execute(f'DROP TABLE IF EXISTS "{table}"')
        column_sql = ", ".join('"' + str(column) + '" TEXT' for column in columns)
        connection.execute(f'CREATE TABLE "{table}" ({column_sql})')
        connection.executemany(
            f'INSERT INTO "{table}" VALUES ({", ".join("?" for _ in columns)})',
            [[json.dumps(item.get(c), ensure_ascii=False) if isinstance(item.get(c), (dict, list))
              else item.get(c) for c in columns] for item in data])
        connection.commit()
    finally:
        connection.close()
    ctx.output(str(target))
    return f"{len(data)} row(s), {len(columns)} column(s) → {target}"
