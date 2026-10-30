"""PDF — merge, split, extract, protect and inspect (needs pypdf)."""

from __future__ import annotations

import re
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import human_size, need_file, out_path, report_table, require, write_text

PDF_FILTER = "PDF (*.pdf)"


def _reader(raw: str, password: str = ""):
    require("pypdf", "pypdf")
    from pypdf import PdfReader
    path = need_file(raw, "PDF file")
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            if not password:
                raise ToolError(f"{path.name} is password protected — give the password")
            if not reader.decrypt(password):
                raise ToolError("That password did not open the PDF")
        return reader, path
    except ToolError:
        raise
    except Exception as exc:  # noqa: BLE001 - pypdf raises various
        raise ToolError(f"Could not read {path.name}: {exc}") from exc


def _writer():
    require("pypdf", "pypdf")
    from pypdf import PdfWriter
    return PdfWriter()


def _pages(spec: str, total: int) -> list[int]:
    """'1-3,7,9-' → zero-based page indexes."""
    if not spec.strip():
        return list(range(total))
    chosen: list[int] = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start_text, _, end_text = chunk.partition("-")
            start = int(start_text) if start_text.strip() else 1
            end = int(end_text) if end_text.strip() else total
            chosen.extend(range(start, end + 1))
        else:
            chosen.append(int(chunk))
    indexes = [n - 1 for n in chosen if 1 <= n <= total]
    if not indexes:
        raise ToolError(f"No pages matched {spec!r} (this PDF has {total})")
    return indexes


def _finish(writer, target: Path, ctx, message: str) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "wb") as fh:
        writer.write(fh)
    ctx.output(str(target))
    return f"{message} → {target.name} ({human_size(target.stat().st_size)})"


@tool(id="pdf-info", name="PDF Info", category="PDF",
      summary="Page count, page sizes, version, metadata and encryption status.",
      keywords="pdf info pages metadata properties version",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.secret("password", "Password", help="Only if the PDF is locked")])
def pdf_info(v, ctx):
    reader, path = _reader(v["file"], v["password"])
    first = reader.pages[0].mediabox
    width = float(first.width) / 72
    height = float(first.height) / 72
    sizes = {}
    for page in reader.pages:
        box = page.mediabox
        label = f"{float(box.width) / 72:.1f} × {float(box.height) / 72:.1f} in"
        sizes[label] = sizes.get(label, 0) + 1
    meta = reader.metadata or {}
    info = {
        "file": path.name,
        "pages": len(reader.pages),
        "size": human_size(path.stat().st_size),
        "first_page": f"{width:.2f} × {height:.2f} in ({width * 25.4:.0f} × {height * 25.4:.0f} mm)",
        "page_sizes": sizes,
        "encrypted": reader.is_encrypted,
        "title": str(meta.get("/Title", "") or ""),
        "author": str(meta.get("/Author", "") or ""),
        "creator": str(meta.get("/Creator", "") or ""),
        "producer": str(meta.get("/Producer", "") or ""),
        "pdf_version": getattr(reader, "pdf_header", ""),
    }
    return info


@tool(id="pdf-merge", name="Merge PDFs", category="PDF",
      summary="Combine several PDFs into one, in the order you list them.",
      keywords="pdf merge combine join append",
      needs=("pypdf",),
      fields=[F.files("files", "PDF files", filters=PDF_FILTER),
              F.save("output", "Save merged PDF as", required=True, filters=PDF_FILTER),
              F.flag("bookmarks", "Add a bookmark per source file", True)])
def pdf_merge(v, ctx):
    files = v["files"] if isinstance(v["files"], list) else [f for f in v["files"].split("|") if f]
    if len(files) < 2:
        raise ToolError("Choose at least two PDFs to merge")
    writer = _writer()
    total = 0
    for raw in files:
        reader, path = _reader(raw)
        start = total
        for page in reader.pages:
            writer.add_page(page)
            total += 1
        if v["bookmarks"]:
            writer.add_outline_item(path.stem, start)
        ctx.log(f"+ {path.name}  ({len(reader.pages)} pages)")
    return _finish(writer, out_path(v["output"], "merged.pdf"), ctx, f"{total} pages from {len(files)} files")


@tool(id="pdf-split", name="Split PDF Into Pages", category="PDF",
      summary="Save every page of a PDF as its own file.",
      keywords="pdf split pages separate extract each",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.folder("output", "Save into", required=False),
              F.secret("password", "Password", help="Only if the PDF is locked")])
def pdf_split(v, ctx):
    reader, path = _reader(v["file"], v["password"])
    out_dir = Path(v["output"]) if v["output"].strip() else path.parent / f"{path.stem}-pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    for index, page in enumerate(reader.pages, start=1):
        ctx.check_cancel()
        writer = _writer()
        writer.add_page(page)
        target = out_dir / f"{path.stem}-p{index:03d}.pdf"
        with open(target, "wb") as fh:
            writer.write(fh)
        ctx.output(str(target))
        ctx.progress(index / len(reader.pages) * 100, f"page {index}")
    return f"{len(reader.pages)} page file(s) in {out_dir}"


@tool(id="pdf-extract-pages", name="Extract Pages", category="PDF",
      summary="Pull specific pages out of a PDF — '1-3,7,10-' style ranges.",
      keywords="pdf extract pages select range subset",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.text("pages", "Pages", "1-3", required=True,
                     help="Comma separated, ranges allowed: 1-3,7,10-"),
              F.save("output", "Save as", required=True, filters=PDF_FILTER),
              F.secret("password", "Password")])
def pdf_extract_pages(v, ctx):
    reader, path = _reader(v["file"], v["password"])
    indexes = _pages(v["pages"], len(reader.pages))
    writer = _writer()
    for index in indexes:
        writer.add_page(reader.pages[index])
    return _finish(writer, out_path(v["output"], "extracted.pdf"), ctx,
                   f"{len(indexes)} page(s) from {path.name}")


@tool(id="pdf-delete-pages", name="Delete Pages", category="PDF",
      summary="Remove pages from a PDF and keep everything else, in the original order.",
      keywords="pdf delete remove pages drop",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.text("pages", "Pages to delete", "1", required=True),
              F.save("output", "Save as", required=True, filters=PDF_FILTER),
              F.secret("password", "Password")])
def pdf_delete_pages(v, ctx):
    reader, path = _reader(v["file"], v["password"])
    drop = set(_pages(v["pages"], len(reader.pages)))
    writer = _writer()
    kept = 0
    for index, page in enumerate(reader.pages):
        if index in drop:
            continue
        writer.add_page(page)
        kept += 1
    if kept == 0:
        raise ToolError("That would delete every page")
    return _finish(writer, out_path(v["output"], "trimmed.pdf"), ctx,
                   f"Removed {len(drop)} page(s), {kept} remain")


@tool(id="pdf-rotate", name="Rotate Pages", category="PDF",
      summary="Turn pages 90, 180 or 270 degrees — fixes sideways scans.",
      keywords="pdf rotate landscape portrait sideways turn",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.choice("angle", "Rotate", ["90", "180", "270"], "90"),
              F.text("pages", "Pages", help="Blank = every page"),
              F.save("output", "Save as", required=True, filters=PDF_FILTER)])
def pdf_rotate(v, ctx):
    reader, path = _reader(v["file"])
    indexes = set(_pages(v["pages"], len(reader.pages)))
    writer = _writer()
    for index, page in enumerate(reader.pages):
        if index in indexes:
            page.rotate(int(v["angle"]))
        writer.add_page(page)
    return _finish(writer, out_path(v["output"], "rotated.pdf"), ctx,
                   f"Rotated {len(indexes)} page(s) by {v['angle']}°")


@tool(id="pdf-reorder", name="Reorder Pages", category="PDF",
      summary="Rebuild a PDF in any page order you type — duplicates allowed.",
      keywords="pdf reorder arrange page order reverse",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.text("order", "New order", "3,1,2", required=True,
                     help="Page numbers in the order you want them"),
              F.flag("reverse", "Just reverse every page", False),
              F.save("output", "Save as", required=True, filters=PDF_FILTER)])
def pdf_reorder(v, ctx):
    reader, path = _reader(v["file"])
    total = len(reader.pages)
    order = list(range(total, 0, -1)) if v["reverse"] else [
        int(x) for x in re.findall(r"\d+", v["order"])]
    bad = [n for n in order if not 1 <= n <= total]
    if bad:
        raise ToolError(f"Page(s) {bad} do not exist — this PDF has {total}")
    writer = _writer()
    for number in order:
        writer.add_page(reader.pages[number - 1])
    return _finish(writer, out_path(v["output"], "reordered.pdf"), ctx,
                   f"{len(order)} page(s) in the new order")


@tool(id="pdf-extract-text", name="Extract PDF Text", category="PDF",
      summary="Pull the text layer out of a PDF, page by page, into a text file.",
      keywords="pdf text extract copy content words",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.text("pages", "Pages", help="Blank = all pages"),
              F.flag("page_breaks", "Mark page boundaries", True),
              F.save("output", "Save text to", required=False)])
def pdf_extract_text(v, ctx):
    reader, path = _reader(v["file"])
    indexes = _pages(v["pages"], len(reader.pages))
    chunks = []
    empty = 0
    for index in indexes:
        ctx.check_cancel()
        try:
            text = reader.pages[index].extract_text() or ""
        except Exception as exc:  # noqa: BLE001
            text = ""
            ctx.log(f"! page {index + 1}: {exc}")
        if not text.strip():
            empty += 1
        if v["page_breaks"]:
            chunks.append(f"----- page {index + 1} -----\n{text}")
        else:
            chunks.append(text)
        ctx.progress((index + 1) / len(reader.pages) * 100, f"page {index + 1}")
    body = "\n\n".join(chunks)
    if not body.strip():
        raise ToolError("No text layer found — this is probably a scan; use the OCR tool")
    if empty:
        ctx.log(f"! {empty} page(s) had no text (scanned images need OCR)")
    if v["output"].strip():
        target = write_text(out_path(v["output"], path.stem + ".txt"), body)
        ctx.output(str(target))
        ctx.log(f"Saved {len(body)} characters to {target}")
    else:
        ctx.log(body[:4000] + ("\n…" if len(body) > 4000 else ""))
    return f"{len(body.split())} words from {len(indexes)} page(s)"


@tool(id="pdf-extract-images", name="Extract Images From PDF", category="PDF",
      summary="Save every embedded image in a PDF as a picture file.",
      keywords="pdf images extract pictures photos save",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.folder("output", "Save into", required=False)])
def pdf_extract_images(v, ctx):
    reader, path = _reader(v["file"])
    out_dir = Path(v["output"]) if v["output"].strip() else path.parent / f"{path.stem}-images"
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    for index, page in enumerate(reader.pages, start=1):
        ctx.check_cancel()
        try:
            images = list(page.images)
        except Exception:  # noqa: BLE001
            continue
        for number, image in enumerate(images, start=1):
            name = image.name if image.name and "." in image.name else f"image.png"
            target = out_dir / f"p{index:03d}-{number}-{Path(name).name}"
            try:
                target.write_bytes(image.data)
                ctx.output(str(target))
                saved += 1
            except Exception as exc:  # noqa: BLE001
                ctx.log(f"! {name}: {exc}")
    if not saved:
        return "No embedded images found in this PDF."
    return f"{saved} image(s) extracted into {out_dir}"


@tool(id="pdf-encrypt", name="Password-Protect PDF", category="PDF",
      summary="Encrypt a PDF with a password so it needs one to open.",
      keywords="pdf password protect encrypt secure lock",
      needs=("pypdf",),
      destructive=True,
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.secret("password", "Password", required=True),
              F.secret("owner_password", "Owner password", help="Optional, for permissions"),
              F.choice("algorithm", "Encryption", ["AES-256", "AES-128", "RC4-128"], "AES-256"),
              F.save("output", "Save as", required=True, filters=PDF_FILTER)])
def pdf_encrypt(v, ctx):
    reader, path = _reader(v["file"])
    writer = _writer()
    for page in reader.pages:
        writer.add_page(page)
    algorithm = {"AES-256": "AES-256", "AES-128": "AES-128", "RC4-128": "RC4-128"}[v["algorithm"]]
    writer.encrypt(user_password=v["password"],
                   owner_password=v["owner_password"] or v["password"],
                   algorithm=algorithm)
    return _finish(writer, out_path(v["output"], path.stem + "-locked.pdf"), ctx,
                   f"Encrypted with {v['algorithm']}")


@tool(id="pdf-decrypt", name="Remove PDF Password", category="PDF",
      summary="Save an unlocked copy of a PDF you already have the password for.",
      keywords="pdf password remove unlock decrypt",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.secret("password", "Password", required=True),
              F.save("output", "Save as", required=True, filters=PDF_FILTER)])
def pdf_decrypt(v, ctx):
    reader, path = _reader(v["file"], v["password"])
    writer = _writer()
    for page in reader.pages:
        writer.add_page(page)
    return _finish(writer, out_path(v["output"], path.stem + "-unlocked.pdf"), ctx,
                   "Saved without a password")


@tool(id="pdf-metadata", name="Edit PDF Metadata", category="PDF",
      summary="Set the title, author, subject and keywords, or clear them completely.",
      keywords="pdf metadata title author subject keywords edit",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.text("title", "Title"),
              F.text("author", "Author"),
              F.text("subject", "Subject"),
              F.text("keywords", "Keywords", help="Comma separated"),
              F.flag("clear", "Remove all metadata instead", False),
              F.save("output", "Save as", required=True, filters=PDF_FILTER)])
def pdf_metadata(v, ctx):
    reader, path = _reader(v["file"])
    writer = _writer()
    for page in reader.pages:
        writer.add_page(page)
    if v["clear"]:
        writer.add_metadata({})
        message = "Metadata cleared"
    else:
        writer.add_metadata({
            "/Title": v["title"], "/Author": v["author"],
            "/Subject": v["subject"], "/Keywords": v["keywords"],
            "/Producer": "All4one",
        })
        message = "Metadata updated"
    return _finish(writer, out_path(v["output"], path.stem + "-meta.pdf"), ctx, message)


@tool(id="pdf-compress", name="Compress PDF", category="PDF",
      summary="Rewrite a PDF more compactly — strips unused objects and downsamples nothing.",
      keywords="pdf compress shrink smaller optimise",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.flag("remove_metadata", "Also drop metadata", True),
              F.save("output", "Save as", required=True, filters=PDF_FILTER)])
def pdf_compress(v, ctx):
    from pypdf import PdfWriter
    reader, path = _reader(v["file"])
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    for page in writer.pages:
        try:
            page.compress_content_streams()
        except Exception:  # noqa: BLE001
            pass
    if v["remove_metadata"]:
        writer.add_metadata({})
    target = out_path(v["output"], path.stem + "-compressed.pdf")
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "wb") as fh:
        writer.write(fh)
    before, after = path.stat().st_size, target.stat().st_size
    ctx.output(str(target))
    change = (1 - after / before) * 100 if before else 0
    return f"{human_size(before)} → {human_size(after)}  ({change:.0f}% change)  {target.name}"


@tool(id="pdf-from-images", name="Images to PDF", category="PDF",
      summary="Build a PDF from a folder of images, one image per page.",
      keywords="images pdf create scan combine photos",
      needs=("pillow",),
      fields=[F.folder("folder", "Folder of images"),
              F.save("output", "Save PDF as", required=True, filters=PDF_FILTER),
              F.flag("sort_by_name", "Order by filename", True),
              F.integer("quality", "JPEG quality", 88, minimum=30, maximum=100)])
def pdf_from_images(v, ctx):
    from ._util import iter_files, need_dir
    from .images import _open
    root = need_dir(v["folder"])
    files = [p for p in iter_files(root, False, "*")
             if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")]
    if not files:
        raise ToolError("No images found in that folder")
    if v["sort_by_name"]:
        files.sort(key=lambda p: p.name.lower())
    pages = []
    for path in files:
        image = _open(path).convert("RGB")
        pages.append(image)
        ctx.progress(len(pages) / len(files) * 100, path.name)
    target = out_path(v["output"], "images.pdf")
    if target.suffix.lower() != ".pdf":
        target = target.with_suffix(".pdf")
    pages[0].save(target, "PDF", save_all=True, append_images=pages[1:], quality=v["quality"])
    ctx.output(str(target))
    return f"{len(pages)} page(s) → {target.name} ({human_size(target.stat().st_size)})"


@tool(id="pdf-search", name="Search a PDF", category="PDF",
      summary="Find a word or phrase and report the pages and lines it appears on.",
      keywords="pdf search find text grep word pages",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.text("needle", "Find", required=True),
              F.flag("case_sensitive", "Match case", False)])
def pdf_search(v, ctx):
    reader, path = _reader(v["file"])
    needle = v["needle"] if v["case_sensitive"] else v["needle"].lower()
    hits = []
    for index, page in enumerate(reader.pages, start=1):
        ctx.check_cancel()
        try:
            text = page.extract_text() or ""
        except Exception:  # noqa: BLE001
            continue
        haystack = text if v["case_sensitive"] else text.lower()
        if needle not in haystack:
            continue
        lines = [line.strip() for line in text.splitlines()
                 if needle in (line if v["case_sensitive"] else line.lower())]
        hits.append({"page": index, "count": haystack.count(needle),
                     "context": lines[0][:90] if lines else ""})
    if not hits:
        return f"No matches for {v['needle']!r}."
    ctx.log(report_table(hits, ["page", "count", "context"]))
    return f"{sum(h['count'] for h in hits)} match(es) on {len(hits)} page(s)"


@tool(id="pdf-bookmarks", name="PDF Bookmarks", category="PDF",
      summary="Show the document outline, or list every page's text as a flat index.",
      keywords="pdf bookmarks outline toc contents index",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER)])
def pdf_bookmarks(v, ctx):
    reader, path = _reader(v["file"])
    try:
        outline = reader.outline
    except Exception:  # noqa: BLE001
        outline = []
    lines: list[str] = []

    def walk(items, depth: int = 0):
        for item in items:
            if isinstance(item, list):
                walk(item, depth + 1)
            else:
                try:
                    number = reader.get_destination_page_number(item) + 1
                except Exception:  # noqa: BLE001
                    number = "?"
                lines.append(f"{'  ' * depth}• {item.title}  (page {number})")

    walk(outline)
    if not lines:
        ctx.log("This PDF has no bookmarks. Page starts:")
        for index, page in enumerate(reader.pages[:40], start=1):
            try:
                text = (page.extract_text() or "").strip().splitlines()
            except Exception:  # noqa: BLE001
                text = []
            ctx.log(f"  p{index}: {text[0][:70] if text else '(no text)'}")
        return f"{len(reader.pages)} page(s), no outline"
    ctx.log("\n".join(lines))
    return f"{len(lines)} bookmark(s)"


@tool(id="pdf-attachments", name="PDF Attachments", category="PDF",
      summary="List or extract files embedded inside a PDF.",
      keywords="pdf attachments embedded files extract portfolio",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.folder("output", "Extract into", required=False),
              F.flag("extract", "Extract the files", False)])
def pdf_attachments(v, ctx):
    reader, path = _reader(v["file"])
    try:
        attachments = reader.attachments
    except Exception:  # noqa: BLE001
        attachments = {}
    if not attachments:
        return "This PDF has no embedded attachments."
    names = list(attachments.keys())
    ctx.log("\n".join(names))
    if v["extract"]:
        out_dir = Path(v["output"]) if v["output"].strip() else path.parent / f"{path.stem}-attachments"
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, contents in attachments.items():
            target = out_dir / name
            target.write_bytes(contents[0])
            ctx.output(str(target))
        return f"{len(names)} attachment(s) extracted to {out_dir}"
    return f"{len(names)} attachment(s)"


@tool(id="pdf-form-fields", name="PDF Form Fields", category="PDF",
      summary="List a PDF's fillable form fields, or fill them from key=value pairs.",
      keywords="pdf form fields fill acroform list",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.text("values", "Fill with", help="field=value, field2=value2"),
              F.save("output", "Save as", required=False, filters=PDF_FILTER)])
def pdf_form_fields(v, ctx):
    reader, path = _reader(v["file"])
    fields = reader.get_fields() or {}
    if not fields:
        return "This PDF has no fillable form fields."
    for name, field in fields.items():
        ctx.log(f"  {name}  [{field.get('/FT', '?')}]")
    if not v["values"].strip():
        return f"{len(fields)} field(s) — fill them by typing field=value pairs"
    pairs = {}
    for chunk in v["values"].split(","):
        if "=" in chunk:
            key, _, value = chunk.partition("=")
            pairs[key.strip()] = value.strip()
    writer = _writer()
    writer.append(str(path))
    for page in writer.pages:
        try:
            writer.update_page_form_field_values(page, pairs, auto_regenerate=False)
        except Exception as exc:  # noqa: BLE001
            ctx.log(f"! {exc}")
    target = out_path(v["output"], path.stem + "-filled.pdf")
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "wb") as fh:
        writer.write(fh)
    ctx.output(str(target))
    return f"Filled {len(pairs)} field(s) → {target.name}"


@tool(id="pdf-add-blank", name="Insert Blank Pages", category="PDF",
      summary="Add blank pages at chosen positions — for notes and printing spreads.",
      keywords="pdf blank page insert add notes",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.integer("after_page", "Insert after page", 1, minimum=0),
              F.integer("count", "How many", 1, minimum=1, maximum=50),
              F.save("output", "Save as", required=True, filters=PDF_FILTER)])
def pdf_add_blank(v, ctx):
    reader, path = _reader(v["file"])
    writer = _writer()
    position = v["after_page"]
    for index, page in enumerate(reader.pages, start=1):
        writer.add_page(page)
        if index == position:
            for _ in range(v["count"]):
                writer.add_blank_page(width=float(page.mediabox.width),
                                      height=float(page.mediabox.height))
    return _finish(writer, out_path(v["output"], "with-blanks.pdf"), ctx,
                   f"Added {v['count']} blank page(s) after page {position}")


@tool(id="pdf-page-report", name="PDF Page Report", category="PDF",
      summary="Per-page size, rotation and text length — spot the odd page in a scan.",
      keywords="pdf pages report sizes rotation text audit",
      needs=("pypdf",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.save("report", "Save CSV to", required=False)])
def pdf_page_report(v, ctx):
    from ._util import write_csv
    reader, path = _reader(v["file"])
    rows = []
    for index, page in enumerate(reader.pages, start=1):
        box = page.mediabox
        try:
            words = len((page.extract_text() or "").split())
        except Exception:  # noqa: BLE001
            words = -1
        rows.append({"page": index,
                     "width_mm": round(float(box.width) / 72 * 25.4),
                     "height_mm": round(float(box.height) / 72 * 25.4),
                     "rotation": page.get("/Rotate", 0),
                     "words": words})
    ctx.log(report_table(rows[:40]))
    if v["report"].strip():
        target = write_csv(out_path(v["report"], path.stem + "-pages.csv"), rows)
        ctx.output(str(target))
    return f"{len(rows)} page(s)"


@tool(id="pdf-to-images", name="PDF Pages to Images", category="PDF",
      summary="Render each PDF page as a PNG using Poppler's pdftoppm.",
      keywords="pdf render images png pages screenshot poppler",
      needs=("pdftoppm",),
      fields=[F.file("file", "PDF file", filters=PDF_FILTER),
              F.integer("dpi", "Resolution (DPI)", 150, minimum=50, maximum=600),
              F.folder("output", "Save into", required=False)])
def pdf_to_images(v, ctx):
    from ._util import run_command
    path = need_file(v["file"], "PDF file")
    out_dir = Path(v["output"]) if v["output"].strip() else path.parent / f"{path.stem}-pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    code, _, err = run_command(["pdftoppm", "-png", "-r", str(v["dpi"]),
                                str(path), str(out_dir / path.stem)], ctx=ctx, timeout=600)
    if code != 0:
        raise ToolError(f"pdftoppm failed: {err.strip()[:200]}")
    made = sorted(out_dir.glob(path.stem + "*.png"))
    for item in made:
        ctx.output(str(item))
    return f"{len(made)} page image(s) at {v['dpi']} DPI in {out_dir}"
