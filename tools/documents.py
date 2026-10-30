"""Documents — Word, Excel, OCR and format conversion."""

from __future__ import annotations

import re
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import (human_size, need_dir, need_file, out_path, report_table,
                    require, run_command, write_csv, write_text, which)

DOCX_FILTER = "Word document (*.docx)"
XLSX_FILTER = "Excel workbook (*.xlsx *.xlsm)"


def _xlsx(raw: str):
    require("openpyxl", "openpyxl")
    from openpyxl import load_workbook
    path = need_file(raw, "Excel workbook")
    try:
        return load_workbook(path, data_only=True, read_only=True), path
    except Exception as exc:  # noqa: BLE001
        raise ToolError(f"Could not open {path.name}: {exc}") from exc


@tool(id="xlsx-info", name="Excel Workbook Info", category="Documents",
      summary="Sheets, used ranges, row counts and whether formulas or macros are present.",
      keywords="excel xlsx info sheets rows columns workbook",
      needs=("openpyxl",),
      fields=[F.file("file", "Excel workbook", filters=XLSX_FILTER)])
def xlsx_info(v, ctx):
    workbook, path = _xlsx(v["file"])
    rows = []
    for sheet in workbook.worksheets:
        try:
            used = sheet.calculate_dimension()
        except Exception:  # noqa: BLE001 - read-only sheets vary by openpyxl version
            used = ""
        rows.append({"sheet": sheet.title, "rows": sheet.max_row or 0,
                     "columns": sheet.max_column or 0, "range": used})
    ctx.log(report_table(rows, ["sheet", "rows", "columns", "range"]))
    total_rows = sum(r["rows"] for r in rows)
    return {"file": path.name, "sheets": len(rows), "total_rows": total_rows,
            "size": human_size(path.stat().st_size),
            "macro_enabled": path.suffix.lower() == ".xlsm"}


@tool(id="xlsx-to-csv", name="Excel to CSV", category="Documents",
      summary="Export a worksheet — or every worksheet — to CSV files.",
      keywords="excel xlsx csv export convert sheet",
      needs=("openpyxl",),
      fields=[F.file("file", "Excel workbook", filters=XLSX_FILTER),
              F.text("sheet", "Sheet name", help="Blank = every sheet"),
              F.folder("output", "Save into", required=False),
              F.text("delimiter", "Delimiter", ",")])
def xlsx_to_csv(v, ctx):
    workbook, path = _xlsx(v["file"])
    out_dir = Path(v["output"]) if v["output"].strip() else path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    wanted = v["sheet"].strip()
    sheets = [s for s in workbook.worksheets if not wanted or s.title.lower() == wanted.lower()]
    if not sheets:
        raise ToolError(f"No sheet called {wanted!r}. Sheets: "
                        f"{', '.join(s.title for s in workbook.worksheets)}")
    made = []
    for sheet in sheets:
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            ctx.log(f"{sheet.title}: empty, skipped")
            continue
        header = [str(cell) if cell is not None else f"column_{i + 1}"
                  for i, cell in enumerate(rows[0])]
        body = [dict(zip(header, ("" if cell is None else cell for cell in row)))
                for row in rows[1:]]
        target = out_dir / f"{path.stem}-{sheet.title}.csv"
        write_csv(target, body, header)
        made.append(target)
        ctx.output(str(target))
        ctx.log(f"{target.name}  {len(body)} row(s)")
    if not made:
        raise ToolError("Nothing to export")
    return f"{len(made)} CSV file(s) written to {out_dir}"


@tool(id="csv-to-xlsx", name="CSV to Excel", category="Documents",
      summary="Turn one or more CSV files into a single Excel workbook, one sheet each.",
      keywords="csv excel xlsx convert workbook sheets",
      needs=("openpyxl",),
      fields=[F.files("files", "CSV files", filters="CSV (*.csv *.tsv)"),
              F.save("output", "Save workbook as", required=True, filters=XLSX_FILTER),
              F.flag("bold_header", "Bold the header row", True),
              F.flag("autofit", "Widen columns to fit", True)])
def csv_to_xlsx(v, ctx):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter
    from .data import _csv_read
    files = v["files"] if isinstance(v["files"], list) else [f for f in v["files"].split("|") if f]
    if not files:
        raise ToolError("Choose at least one CSV file")
    workbook = Workbook()
    workbook.remove(workbook.active)
    for raw in files:
        path = need_file(raw)
        columns, rows = _csv_read(path)
        sheet = workbook.create_sheet(title=path.stem[:31] or "Sheet")
        sheet.append(columns)
        for row in rows:
            sheet.append([row.get(col, "") for col in columns])
        if v["bold_header"]:
            for cell in sheet[1]:
                cell.font = Font(bold=True)
        if v["autofit"]:
            for index, column in enumerate(columns, start=1):
                width = max(len(str(column)), *(len(str(r.get(column, ""))) for r in rows[:200])) if rows else len(column)
                sheet.column_dimensions[get_column_letter(index)].width = min(60, width + 2)
        sheet.freeze_panes = "A2"
    target = out_path(v["output"], "workbook.xlsx")
    if target.suffix.lower() not in (".xlsx", ".xlsm"):
        target = target.with_suffix(".xlsx")
    workbook.save(target)
    ctx.output(str(target))
    return f"{len(files)} sheet(s) → {target.name}"


@tool(id="xlsx-merge", name="Merge Excel Workbooks", category="Documents",
      summary="Combine several workbooks into one file, keeping every sheet.",
      keywords="excel merge combine workbooks xlsx join",
      needs=("openpyxl",),
      fields=[F.files("files", "Excel workbooks", filters=XLSX_FILTER),
              F.save("output", "Save merged workbook as", required=True, filters=XLSX_FILTER)])
def xlsx_merge(v, ctx):
    from openpyxl import Workbook
    files = v["files"] if isinstance(v["files"], list) else [f for f in v["files"].split("|") if f]
    if len(files) < 2:
        raise ToolError("Choose at least two workbooks")
    merged = Workbook()
    merged.remove(merged.active)
    for raw in files:
        workbook, path = _xlsx(raw)
        for sheet in workbook.worksheets:
            title = f"{path.stem[:20]}-{sheet.title}"[:31]
            target = merged.create_sheet(title=title)
            for row in sheet.iter_rows(values_only=True):
                target.append(list(row))
            ctx.log(f"+ {path.name} / {sheet.title}  ({sheet.max_row or 0} rows)")
    out = out_path(v["output"], "merged.xlsx")
    merged.save(out)
    ctx.output(str(out))
    return f"{len(merged.worksheets)} sheet(s) → {out.name}"


@tool(id="docx-to-text", name="Word to Text", category="Documents",
      summary="Extract the text of a .docx, keeping paragraph and table order.",
      keywords="word docx text extract convert plain",
      needs=("docx",),
      fields=[F.file("file", "Word document", filters=DOCX_FILTER),
              F.flag("tables", "Include tables", True),
              F.save("output", "Save text to", required=False)])
def docx_to_text(v, ctx):
    require("docx", "docx")
    import docx as docx_module
    path = need_file(v["file"], "Word document")
    try:
        document = docx_module.Document(str(path))
    except Exception as exc:  # noqa: BLE001
        raise ToolError(f"Could not open {path.name}: {exc}") from exc
    blocks = [paragraph.text for paragraph in document.paragraphs]
    if v["tables"]:
        for number, table in enumerate(document.tables, start=1):
            blocks.append(f"\n[table {number}]")
            for row in table.rows:
                blocks.append(" | ".join(cell.text.strip() for cell in row.cells))
    text = "\n".join(blocks)
    if v["output"].strip():
        target = write_text(out_path(v["output"], path.stem + ".txt"), text)
        ctx.output(str(target))
        ctx.log(f"Saved to {target}")
    else:
        ctx.log(text[:4000] + ("\n…" if len(text) > 4000 else ""))
    return f"{len(document.paragraphs)} paragraph(s), {len(document.tables)} table(s), " \
           f"{len(text.split())} words"


@tool(id="docx-info", name="Word Document Info", category="Documents",
      summary="Paragraph, word, table and image counts plus core properties.",
      keywords="word docx info statistics properties author",
      needs=("docx",),
      fields=[F.file("file", "Word document", filters=DOCX_FILTER)])
def docx_info(v, ctx):
    require("docx", "docx")
    import docx as docx_module
    path = need_file(v["file"], "Word document")
    document = docx_module.Document(str(path))
    words = sum(len(p.text.split()) for p in document.paragraphs)
    props = document.core_properties
    return {
        "file": path.name,
        "size": human_size(path.stat().st_size),
        "paragraphs": len(document.paragraphs),
        "tables": len(document.tables),
        "images": len(document.inline_shapes),
        "sections": len(document.sections),
        "words": words,
        "title": props.title or "",
        "author": props.author or "",
        "created": str(props.created or ""),
        "modified": str(props.modified or ""),
    }


@tool(id="text-to-docx", name="Text to Word", category="Documents",
      summary="Turn plain text or Markdown-ish text into a formatted .docx.",
      keywords="word docx create text convert markdown",
      needs=("docx",),
      fields=[F.multi("text", "Text", rows=12),
              F.file("file", "…or read a text file", required=False),
              F.text("title", "Document title", help="Optional heading"),
              F.save("output", "Save as", required=True, filters=DOCX_FILTER),
              F.flag("markdown", "Interpret # headings and - bullets", True)])
def text_to_docx(v, ctx):
    require("docx", "docx")
    import docx as docx_module
    from ._util import read_text
    path = str(v["file"] or "").strip()
    text = read_text(need_file(path)) if path else v["text"]
    if not text.strip():
        raise ToolError("Type some text, or choose a file")
    document = docx_module.Document()
    if v["title"].strip():
        document.add_heading(v["title"].strip(), level=0)
    for line in text.splitlines():
        stripped = line.strip()
        if v["markdown"] and stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            document.add_heading(stripped.lstrip("#").strip(), level=min(level, 4))
        elif v["markdown"] and stripped.startswith(("- ", "* ")):
            document.add_paragraph(stripped[2:], style="List Bullet")
        elif stripped:
            document.add_paragraph(stripped)
    target = out_path(v["output"], "document.docx")
    if target.suffix.lower() != ".docx":
        target = target.with_suffix(".docx")
    document.save(target)
    ctx.output(str(target))
    return f"{target.name} written ({human_size(target.stat().st_size)})"


@tool(id="docx-find-replace", name="Word Find & Replace", category="Documents",
      summary="Replace text throughout a .docx, including inside tables.",
      keywords="word docx replace find text batch",
      needs=("docx",),
      fields=[F.file("file", "Word document", filters=DOCX_FILTER),
              F.text("find", "Find", required=True),
              F.text("replace", "Replace with"),
              F.flag("apply", "Save the change", False),
              F.save("output", "Save as", required=False, filters=DOCX_FILTER)])
def docx_find_replace(v, ctx):
    require("docx", "docx")
    import docx as docx_module
    path = need_file(v["file"], "Word document")
    document = docx_module.Document(str(path))
    count = 0

    def swap(paragraph):
        nonlocal count
        for run in paragraph.runs:
            if v["find"] in run.text:
                count += run.text.count(v["find"])
                run.text = run.text.replace(v["find"], v["replace"])

    for paragraph in document.paragraphs:
        swap(paragraph)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    swap(paragraph)
    ctx.log(f"{count} replacement(s)")
    if not v["apply"]:
        return "Preview only — tick 'Save the change' to write it"
    target = out_path(v["output"], path.stem + "-replaced.docx") if v["output"].strip() \
        else path
    if target.suffix.lower() != ".docx":
        target = target.with_suffix(".docx")
    document.save(target)
    ctx.output(str(target))
    return f"Saved {target.name}"


@tool(id="office-to-pdf", name="Convert to PDF", category="Documents",
      summary="Convert Word, Excel or PowerPoint files to PDF using LibreOffice.",
      keywords="pdf convert office word excel powerpoint libreoffice docx",
      needs=("libreoffice",),
      fields=[F.files("files", "Documents", filters="Documents (*.docx *.xlsx *.pptx *.odt *.rtf)"),
              F.folder("output", "Save PDFs into", required=False)])
def office_to_pdf(v, ctx):
    exe = which("soffice") or which("soffice.exe") or which("libreoffice")
    if not exe:
        raise ToolError("LibreOffice (soffice) was not found on PATH")
    files = v["files"] if isinstance(v["files"], list) else [f for f in v["files"].split("|") if f]
    if not files:
        raise ToolError("Choose at least one document")
    out_dir = Path(v["output"]) if v["output"].strip() else Path(files[0]).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    made = 0
    for raw in files:
        path = need_file(raw)
        code, _, err = run_command([exe, "--headless", "--convert-to", "pdf",
                                    "--outdir", str(out_dir), str(path)], ctx=ctx, timeout=300)
        if code == 0:
            made += 1
            ctx.output(str(out_dir / (path.stem + ".pdf")))
        else:
            ctx.log(f"! {path.name}: {err.strip()[:150]}")
    return f"{made} of {len(files)} document(s) converted to PDF in {out_dir}"


@tool(id="ocr-image", name="OCR an Image", category="Documents",
      summary="Read the text out of a photo or screenshot with Tesseract.",
      keywords="ocr text image scan tesseract read recognise",
      needs=("tesseract",),
      fields=[F.file("file", "Image", filters="Images (*.png *.jpg *.jpeg *.tif *.bmp)"),
              F.text("language", "Language code", "eng", help="eng, hin, guj, mar …"),
              F.save("output", "Save text to", required=False)])
def ocr_image(v, ctx):
    exe = which("tesseract") or which("tesseract.exe")
    if not exe:
        raise ToolError("Tesseract was not found on PATH")
    path = need_file(v["file"], "Image")
    target = out_path(v["output"], path.stem + ".txt") if v["output"].strip() else path.with_suffix(".ocr.txt")
    code, out, err = run_command([exe, str(path), str(target.with_suffix("")),
                                  "-l", v["language"] or "eng"], ctx=ctx, timeout=600)
    if code != 0:
        raise ToolError(f"Tesseract failed: {err.strip()[:200]}")
    text = read_file_text(target)
    ctx.output(str(target))
    ctx.log(text[:2000])
    return f"{len(text.split())} word(s) recognised → {target.name}"


def read_file_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


@tool(id="ocr-pdf", name="OCR a Scanned PDF", category="Documents",
      summary="Turn a scanned PDF into searchable text, page by page.",
      keywords="ocr pdf scan searchable text tesseract poppler",
      needs=("tesseract", "pdftoppm"),
      fields=[F.file("file", "PDF file", filters="PDF (*.pdf)"),
              F.text("language", "Language code", "eng"),
              F.integer("dpi", "Render resolution", 300, minimum=100, maximum=600),
              F.save("output", "Save text to", required=False)])
def ocr_pdf(v, ctx):
    import tempfile
    tesseract = which("tesseract") or which("tesseract.exe")
    pdftoppm = which("pdftoppm") or which("pdftoppm.exe")
    if not (tesseract and pdftoppm):
        raise ToolError("This tool needs both Tesseract and Poppler on PATH")
    path = need_file(v["file"], "PDF file")
    with tempfile.TemporaryDirectory() as folder:
        base = str(Path(folder) / "page")
        code, _, err = run_command([pdftoppm, "-r", str(v["dpi"]), "-png", str(path), base],
                                   ctx=ctx, timeout=900)
        if code != 0:
            raise ToolError(f"pdftoppm failed: {err.strip()[:200]}")
        pages = sorted(Path(folder).glob("page*.png"))
        if not pages:
            raise ToolError("No pages were rendered")
        chunks = []
        for index, page in enumerate(pages, start=1):
            ctx.check_cancel()
            out_base = str(Path(folder) / f"text{index}")
            run_command([tesseract, str(page), out_base, "-l", v["language"] or "eng"],
                        ctx=ctx, timeout=300)
            text = read_file_text(Path(out_base + ".txt"))
            chunks.append(f"----- page {index} -----\n{text}")
            ctx.progress(index / len(pages) * 100, f"page {index}")
        body = "\n\n".join(chunks)
    target = write_text(out_path(v["output"], path.stem + ".ocr.txt"), body)
    ctx.output(str(target))
    return f"{len(pages)} page(s) recognised → {target.name} ({len(body.split())} words)"


@tool(id="docx-images", name="Extract Images From Word", category="Documents",
      summary="Pull every image embedded in a .docx out into a folder.",
      keywords="word docx images extract media pictures",
      needs=("docx",),
      fields=[F.file("file", "Word document", filters=DOCX_FILTER),
              F.folder("output", "Save into", required=False)])
def docx_images(v, ctx):
    import zipfile
    path = need_file(v["file"], "Word document")
    out_dir = Path(v["output"]) if v["output"].strip() else path.parent / f"{path.stem}-images"
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.startswith("word/media/"):
                target = out_dir / Path(name).name
                target.write_bytes(archive.read(name))
                ctx.output(str(target))
                ctx.log(f"{target.name}  {human_size(target.stat().st_size)}")
                saved += 1
    return f"{saved} image(s) extracted into {out_dir}"


@tool(id="xlsx-search", name="Search a Workbook", category="Documents",
      summary="Find a value anywhere in an Excel file and report the exact cell.",
      keywords="excel search find cell value xlsx lookup",
      needs=("openpyxl",),
      fields=[F.file("file", "Excel workbook", filters=XLSX_FILTER),
              F.text("needle", "Find", required=True),
              F.flag("case_sensitive", "Match case", False)])
def xlsx_search(v, ctx):
    workbook, path = _xlsx(v["file"])
    needle = v["needle"] if v["case_sensitive"] else v["needle"].lower()
    hits = []
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                text = str(cell.value)
                haystack = text if v["case_sensitive"] else text.lower()
                if needle in haystack:
                    hits.append({"sheet": sheet.title, "cell": cell.coordinate,
                                 "value": text[:60]})
                    if len(hits) > 500:
                        break
    if not hits:
        return f"No match for {v['needle']!r}."
    ctx.log(report_table(hits[:80], ["sheet", "cell", "value"]))
    return f"{len(hits)} match(es) in {path.name}"
