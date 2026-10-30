"""Comparison tools — the same job done properly across file types."""

from __future__ import annotations

import difflib
import json
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import hash_file, human_size, iter_files, need_dir, need_file, report_table, write_csv


@tool(id="image-compare", name="Compare Two Images", category="Images",
      summary="How different two images are, as a percentage, with an optional diff image.",
      needs=("pillow",),
      fields=[F.file("first", "First image"),
              F.file("second", "Second image"),
              F.save("diff_output", "Save a difference image to", required=False)])
def image_compare(v, ctx):
    from PIL import Image, ImageChops
    first = Image.open(need_file(v["first"], "First image")).convert("RGB")
    second = Image.open(need_file(v["second"], "Second image")).convert("RGB")
    if first.size != second.size:
        second = second.resize(first.size, Image.LANCZOS)
        ctx.log("! Sizes differed — the second image was scaled to match")
    difference = ImageChops.difference(first, second)
    histogram = difference.convert("L").histogram()
    total_pixels = first.width * first.height
    changed = sum(histogram[8:])
    percent = changed / total_pixels * 100
    if v["diff_output"].strip():
        from ._util import out_path
        target = out_path(v["diff_output"], "difference.png")
        if target.suffix.lower() not in (".png", ".jpg", ".jpeg", ".bmp", ".webp"):
            target = target.with_suffix(".png")
        difference.point(lambda value: min(255, value * 4)).save(target)
        ctx.output(str(target))
        ctx.log(f"Difference image saved to {target}")
    verdict = ("identical" if percent < 0.01 else
               "nearly identical" if percent < 1 else
               "similar" if percent < 10 else "clearly different")
    ctx.log(f"{percent:.2f}% of pixels differ — {verdict}")
    return {"size": f"{first.width}×{first.height}", "differing_pixels_percent": round(percent, 2),
            "verdict": verdict}


@tool(id="duplicate-images", name="Find Duplicate Images", category="Images",
      summary="Spot visually identical images even when they have been resized or re-encoded.",
      needs=("pillow",),
      fields=[F.folder("folder", "Folder of images"),
              F.integer("threshold", "Similarity threshold", 96, minimum=80, maximum=100,
                        suffix="%"),
              F.save("report", "Save CSV to", required=False)])
def duplicate_images(v, ctx):
    from PIL import Image
    root = need_dir(v["folder"])
    signatures: list[tuple[list[int], Path]] = []
    for path in iter_files(root, True):
        if path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif"):
            continue
        try:
            with Image.open(path) as image:
                thumb = image.convert("L").resize((12, 12), Image.LANCZOS)
                signatures.append((list(thumb.getdata()), path))
        except Exception:  # noqa: BLE001
            continue
        ctx.check_cancel()
    if len(signatures) < 2:
        raise ToolError("Not enough images to compare")
    groups: list[list[Path]] = []
    used = set()
    for index, (first_sig, first_path) in enumerate(signatures):
        if index in used:
            continue
        group = [first_path]
        for other_index in range(index + 1, len(signatures)):
            if other_index in used:
                continue
            other_sig, other_path = signatures[other_index]
            diff = sum(abs(a - b) for a, b in zip(first_sig, other_sig)) / len(first_sig)
            similarity = max(0.0, 100 - diff / 2.55)
            if similarity >= v["threshold"]:
                group.append(other_path)
                used.add(other_index)
        if len(group) > 1:
            used.add(index)
            groups.append(group)
    if not groups:
        return f"No duplicates above {v['threshold']}% similarity."
    rows = []
    for group in groups:
        ctx.log(f"\n{len(group)} look-alikes:")
        for path in group:
            ctx.log(f"   {path.relative_to(root)}  ({human_size(path.stat().st_size)})")
            rows.append({"group": len(rows) + 1, "path": str(path.relative_to(root))})
    if v["report"].strip():
        from ._util import out_path
        target = write_csv(out_path(v["report"], "duplicate-images.csv"), rows)
        ctx.output(str(target))
    return f"{len(groups)} group(s) of duplicate images"


@tool(id="csv-compare", name="Compare Two CSVs", category="Data",
      summary="Row-level differences between two CSVs, keyed on a column you choose.",
      fields=[F.file("first", "First CSV", filters="CSV (*.csv)"),
              F.file("second", "Second CSV", filters="CSV (*.csv)"),
              F.text("key", "Key column", help="Leave blank to compare row by row"),
              F.save("report", "Save differences to", required=False)])
def csv_compare(v, ctx):
    from .data import _csv_read
    columns_a, rows_a = _csv_read(need_file(v["first"]))
    columns_b, rows_b = _csv_read(need_file(v["second"]))
    key = v["key"].strip()
    changes = []
    if key:
        if key not in columns_a or key not in columns_b:
            raise ToolError(f"{key!r} must exist in both files")
        map_a = {str(row.get(key)): row for row in rows_a}
        map_b = {str(row.get(key)): row for row in rows_b}
        for missing in sorted(set(map_a) - set(map_b)):
            changes.append({"key": missing, "change": "only in first", "detail": ""})
        for added in sorted(set(map_b) - set(map_a)):
            changes.append({"key": added, "change": "only in second", "detail": ""})
        for shared in sorted(set(map_a) & set(map_b)):
            differences = [column for column in columns_a
                           if column in columns_b
                           and str(map_a[shared].get(column)) != str(map_b[shared].get(column))]
            if differences:
                changes.append({"key": shared, "change": "changed",
                                "detail": ", ".join(differences[:5])})
    else:
        if len(rows_a) != len(rows_b):
            changes.append({"key": "-", "change": "row count",
                            "detail": f"{len(rows_a)} vs {len(rows_b)}"})
        for index, (row_a, row_b) in enumerate(zip(rows_a, rows_b), start=2):
            differences = [column for column in columns_a
                           if str(row_a.get(column)) != str(row_b.get(column))]
            if differences:
                changes.append({"key": f"row {index}", "change": "changed",
                                "detail": ", ".join(differences[:5])})
    if not changes:
        return "The two files are identical."
    ctx.log(report_table(changes[:200], ["key", "change", "detail"]))
    if v["report"].strip():
        from ._util import out_path
        target = write_csv(out_path(v["report"], "csv-differences.csv"), changes)
        ctx.output(str(target))
    return f"{len(changes)} difference(s)"


@tool(id="excel-compare", name="Compare Two Workbooks", category="Documents",
      summary="Cell-by-cell differences between two Excel files, sheet by sheet.",
      needs=("openpyxl",),
      fields=[F.file("first", "First workbook", filters="Excel (*.xlsx)"),
              F.file("second", "Second workbook", filters="Excel (*.xlsx)"),
              F.integer("limit", "Report at most", 200, minimum=1, maximum=2000)])
def excel_compare(v, ctx):
    from openpyxl import load_workbook
    first = load_workbook(need_file(v["first"]), data_only=True)
    second = load_workbook(need_file(v["second"]), data_only=True)
    changes = []
    for name in sorted(set(first.sheetnames) | set(second.sheetnames)):
        if name not in first.sheetnames:
            changes.append({"sheet": name, "cell": "-", "change": "sheet only in second"})
            continue
        if name not in second.sheetnames:
            changes.append({"sheet": name, "cell": "-", "change": "sheet only in first"})
            continue
        sheet_a, sheet_b = first[name], second[name]
        rows = max(sheet_a.max_row or 0, sheet_b.max_row or 0)
        cols = max(sheet_a.max_column or 0, sheet_b.max_column or 0)
        for row in range(1, rows + 1):
            for column in range(1, cols + 1):
                value_a = sheet_a.cell(row=row, column=column).value
                value_b = sheet_b.cell(row=row, column=column).value
                if value_a != value_b:
                    changes.append({"sheet": name,
                                    "cell": sheet_a.cell(row=row, column=column).coordinate,
                                    "change": f"{value_a!r} → {value_b!r}"[:70]})
                    if len(changes) >= v["limit"]:
                        break
            if len(changes) >= v["limit"]:
                break
        ctx.check_cancel()
    if not changes:
        return "The workbooks match cell for cell."
    ctx.log(report_table(changes[:200], ["sheet", "cell", "change"]))
    return f"{len(changes)} differing cell(s)"


@tool(id="pdf-compare", name="Compare Two PDFs", category="PDF",
      summary="Text differences between two PDFs, page by page — catches re-issued documents.",
      needs=("pypdf",),
      fields=[F.file("first", "First PDF", filters="PDF (*.pdf)"),
              F.file("second", "Second PDF", filters="PDF (*.pdf)"),
              F.integer("context", "Context lines", 2, minimum=0, maximum=10)])
def pdf_compare(v, ctx):
    from pypdf import PdfReader
    readers = []
    for key in ("first", "second"):
        try:
            readers.append(PdfReader(str(need_file(v[key]))))
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"Could not read the {key} PDF: {exc}") from exc
    def text_of(reader) -> list[str]:
        out = []
        for page in reader.pages:
            try:
                out.extend((page.extract_text() or "").splitlines())
            except Exception:  # noqa: BLE001
                continue
        return out
    left, right = text_of(readers[0]), text_of(readers[1])
    diff = list(difflib.unified_diff(left, right, fromfile="first", tofile="second",
                                     lineterm="", n=v["context"]))
    if not diff:
        return f"Identical text ({len(readers[0].pages)} pages)."
    ctx.log("\n".join(diff[:400]))
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    return (f"{len(readers[0].pages)} vs {len(readers[1].pages)} pages · "
            f"{added} line(s) added, {removed} removed")


@tool(id="text-similarity", name="Text Similarity", category="Text",
      summary="How alike two texts are, with the longest matching runs highlighted.",
      fields=[F.multi("text_a", "First text", rows=8),
              F.multi("text_b", "Second text", rows=8)])
def text_similarity(v, ctx):
    left, right = v["text_a"], v["text_b"]
    if not left.strip() or not right.strip():
        raise ToolError("Give both texts")
    ratio = difflib.SequenceMatcher(None, left, right).ratio() * 100
    words = difflib.SequenceMatcher(None, left.split(), right.split()).ratio() * 100
    blocks = difflib.SequenceMatcher(None, left.split(), right.split()).get_matching_blocks()
    shared = [" ".join(left.split()[block.a:block.a + block.size]) for block in blocks
              if block.size >= 4]
    for chunk in shared[:8]:
        ctx.log(f"shared: {chunk[:100]}")
    return {"character_similarity": f"{ratio:.1f}%", "word_similarity": f"{words:.1f}%",
            "shared_phrases": len(shared)}


@tool(id="backup-verify", name="Verify a Backup", category="Files",
      summary="Compare a source folder against its backup by hash and list what is missing.",
      fields=[F.folder("source", "Original folder"),
              F.folder("backup", "Backup folder"),
              F.flag("by_hash", "Compare contents, not just sizes", True)])
def backup_verify(v, ctx):
    source = need_dir(v["source"], "Original folder")
    backup = need_dir(v["backup"], "Backup folder")
    missing, different, ok = [], [], 0
    for path in iter_files(source, True):
        relative = path.relative_to(source)
        target = backup / relative
        if not target.exists():
            missing.append(str(relative))
            continue
        if target.stat().st_size != path.stat().st_size or \
                (v["by_hash"] and hash_file(path) != hash_file(target)):
            different.append(str(relative))
        else:
            ok += 1
        if ok % 50 == 0:
            ctx.check_cancel()
    extra = [str(path.relative_to(backup)) for path in iter_files(backup, True)
             if not (source / path.relative_to(backup)).exists()]
    if missing:
        ctx.log(f"Missing from the backup ({len(missing)}):")
        for name in missing[:40]:
            ctx.log(f"  − {name}")
    if different:
        ctx.log(f"Differing ({len(different)}):")
        for name in different[:40]:
            ctx.log(f"  ≠ {name}")
    if extra:
        ctx.log(f"Only in the backup: {len(extra)}")
    verdict = "complete" if not missing and not different else "INCOMPLETE"
    return (f"{verdict}: {ok} matching file(s), {len(missing)} missing, "
            f"{len(different)} different, {len(extra)} extra")


@tool(id="same-name-different", name="Same Name, Different Content", category="Files",
      summary="Files sharing a name across folders but holding different content.",
      fields=[F.folder("folder", "Folder")])
def same_name_different(v, ctx):
    root = need_dir(v["folder"])
    by_name: dict[str, list[Path]] = {}
    for path in iter_files(root, True):
        by_name.setdefault(path.name.lower(), []).append(path)
    clashes = []
    for name, paths in by_name.items():
        if len(paths) < 2:
            continue
        digests = {}
        for path in paths:
            try:
                digests.setdefault(hash_file(path), []).append(path)
            except OSError:
                continue
        if len(digests) > 1:
            clashes.append((name, list(digests.values())))
    if not clashes:
        return "Every repeated filename holds identical content."
    for name, groups in clashes[:40]:
        ctx.log(f"\n{name} — {len(groups)} different versions")
        for group in groups:
            ctx.log(f"   {group[0].relative_to(root)}  ({human_size(group[0].stat().st_size)})")
    return f"{len(clashes)} name(s) with differing content"


@tool(id="docx-compare", name="Compare Two Word Files", category="Documents",
      summary="Text differences between two .docx files, as a readable diff.",
      needs=("docx",),
      fields=[F.file("first", "First document", filters="Word (*.docx)"),
              F.file("second", "Second document", filters="Word (*.docx)")])
def docx_compare(v, ctx):
    import docx as docx_module
    texts = []
    for key in ("first", "second"):
        document = docx_module.Document(str(need_file(v[key])))
        texts.append([paragraph.text for paragraph in document.paragraphs])
    diff = list(difflib.unified_diff(texts[0], texts[1], fromfile="first", tofile="second",
                                     lineterm="", n=2))
    if not diff:
        return "The documents have identical text."
    ctx.log("\n".join(diff[:400]))
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    return f"{added} paragraph(s) added, {removed} removed"


@tool(id="json-schema-lite", name="Validate JSON Shape", category="Data",
      summary="Check a JSON document against a compact schema: required keys, types and lengths.",
      fields=[F.file("file", "JSON file", filters="JSON (*.json)"),
              F.multi("schema", "Schema", rows=8,
                      default='{\n  "type": "object",\n  "required": ["id", "name"],\n'
                              '  "properties": {\n    "id": {"type": "number"},\n'
                              '    "name": {"type": "string"}\n  }\n}')])
def json_schema_lite(v, ctx):
    from ._util import read_text
    try:
        data = json.loads(read_text(need_file(v["file"])))
        schema = json.loads(v["schema"])
    except json.JSONDecodeError as exc:
        raise ToolError(f"Invalid JSON: {exc.msg} at line {exc.lineno}") from exc
    problems: list[str] = []
    type_names = {"object": dict, "array": list, "string": str, "number": (int, float),
                  "integer": int, "boolean": bool, "null": type(None)}

    def check(value, spec, path: str) -> None:
        expected = spec.get("type")
        if expected and expected in type_names:
            wanted = type_names[expected]
            if expected == "number" and isinstance(value, bool):
                problems.append(f"{path}: expected number, found boolean")
            elif not isinstance(value, wanted):
                problems.append(f"{path}: expected {expected}, found {type(value).__name__}")
                return
        if "required" in spec and isinstance(value, dict):
            for key in spec["required"]:
                if key not in value:
                    problems.append(f"{path}: missing required key {key!r}")
        for key, sub in (spec.get("properties") or {}).items():
            if isinstance(value, dict) and key in value:
                check(value[key], sub, f"{path}.{key}".lstrip("."))
        if "items" in spec and isinstance(value, list):
            for index, item in enumerate(value[:50]):
                check(item, spec["items"], f"{path}[{index}]")

    check(data, schema, "root")
    if not problems:
        return "Valid — the document matches the schema."
    for problem in problems[:40]:
        ctx.log(f"✕ {problem}")
    return f"{len(problems)} schema problem(s)"


@tool(id="file-twin-finder", name="Similar Filenames", category="Files",
      summary="Near-duplicate filenames such as report.pdf, report (1).pdf and report-final.pdf.",
      fields=[F.folder("folder", "Folder"),
              F.number("threshold", "Similarity threshold", 0.85, minimum=0.5, maximum=1.0,
                       step=0.05)])
def file_twin_finder(v, ctx):
    root = need_dir(v["folder"])
    names = sorted({path.stem for path in iter_files(root, True)})
    groups: list[list[str]] = []
    used: set[str] = set()
    for index, name in enumerate(names):
        if name in used:
            continue
        group = [name]
        for other in names[index + 1:]:
            if other in used:
                continue
            if difflib.SequenceMatcher(None, name.lower(), other.lower()).ratio() >= v["threshold"]:
                group.append(other)
                used.add(other)
        if len(group) > 1:
            used.add(name)
            groups.append(group)
    if not groups:
        return "No similar filenames found."
    for group in groups[:40]:
        ctx.log("  |  ".join(group))
    return f"{len(groups)} group(s) of similar names"
