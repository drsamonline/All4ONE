"""Batch operations — do one thing to a whole folder, with progress and a report."""

from __future__ import annotations

import csv
import shutil
import zipfile
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import (hash_file, human_size, iter_files, need_dir, need_file,
                    out_path, report_table, require, write_csv, write_text)


@tool(id="hash-folder", name="Hash Every File", category="Encoding",
      summary="A CSV of SHA-256 (and friends) for every file in a folder — for manifests.",
      fields=[F.folder("folder", "Folder"),
              F.choice("algorithm", "Algorithm", ["sha256", "sha1", "md5", "blake2b"], "sha256"),
              F.save("report", "Save manifest to", required=True)])
def hash_folder(v, ctx):
    root = need_dir(v["folder"])
    rows = []
    for path in iter_files(root, True):
        ctx.check_cancel()
        try:
            rows.append({"path": str(path.relative_to(root)),
                         "bytes": path.stat().st_size,
                         v["algorithm"]: hash_file(path, v["algorithm"])})
        except OSError as exc:
            ctx.log(f"! {path.name}: {exc}")
        ctx.progress(len(rows) % 100, path.name)
    target = write_csv(out_path(v["report"], "manifest.csv"), rows,
                       ["path", "bytes", v["algorithm"]])
    ctx.output(str(target))
    return f"{len(rows)} file(s) hashed → {target}"


@tool(id="batch-watermark", name="Watermark a Folder", category="Images",
      summary="Stamp the same watermark onto every image in a folder.",
      needs=("pillow",),
      fields=[F.folder("folder", "Folder of images"),
              F.text("text", "Watermark text", "© All rights reserved"),
              F.choice("position", "Position",
                       ["Bottom right", "Bottom left", "Top right", "Top left", "Centre"],
                       "Bottom right"),
              F.integer("opacity", "Opacity", 45, minimum=5, maximum=100, suffix="%"),
              F.folder("output", "Save into", required=False)])
def batch_watermark(v, ctx):
    from PIL import Image, ImageDraw, ImageFont
    from .images import _open, _save
    root = need_dir(v["folder"])
    out_dir = Path(v["output"]) if v["output"].strip() else root / "watermarked"
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [p for p in iter_files(root, False, "*")
             if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp")]
    if not files:
        raise ToolError("No images found in that folder")
    for index, path in enumerate(files, start=1):
        ctx.check_cancel()
        image = _open(path).convert("RGBA")
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        size = max(10, image.height // 24)
        try:
            font = ImageFont.truetype("arial.ttf", size)
        except OSError:
            font = ImageFont.load_default()
        box = draw.textbbox((0, 0), v["text"], font=font)
        width, height = box[2] - box[0], box[3] - box[1]
        pad = max(8, image.width // 50)
        spots = {"Bottom right": (image.width - width - pad, image.height - height - pad * 2),
                 "Bottom left": (pad, image.height - height - pad * 2),
                 "Top right": (image.width - width - pad, pad),
                 "Top left": (pad, pad),
                 "Centre": ((image.width - width) // 2, (image.height - height) // 2)}
        draw.text(spots[v["position"]], v["text"], font=font,
                  fill=(255, 255, 255, int(255 * v["opacity"] / 100)))
        result = Image.alpha_composite(image, overlay)
        _save(result, out_dir / path.name, 92)
        ctx.progress(index / len(files) * 100, path.name)
    return f"{len(files)} image(s) watermarked into {out_dir}"


@tool(id="batch-strip-exif", name="Strip Metadata From a Folder", category="Images",
      summary="Remove EXIF, GPS and camera data from every photo in a folder at once.",
      needs=("pillow",),
      fields=[F.folder("folder", "Folder of photos"),
              F.folder("output", "Save into", required=False,
                       help="Blank overwrites in place — take a copy first")])
def batch_strip_exif(v, ctx):
    from PIL import Image
    root = need_dir(v["folder"])
    out_dir = Path(v["output"]) if v["output"].strip() else None
    files = [p for p in iter_files(root, True)
             if p.suffix.lower() in (".jpg", ".jpeg", ".tif", ".tiff", ".png", ".webp")]
    if not files:
        raise ToolError("No photos found in that folder")
    cleaned = 0
    for index, path in enumerate(files, start=1):
        ctx.check_cancel()
        try:
            with Image.open(path) as raw:
                raw.load()
                image = raw.copy()
            image.info = {}
            target = (out_dir or path.parent) / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            fmt = {"jpg": "JPEG", "jpeg": "JPEG", "tif": "TIFF"}.get(
                target.suffix.lower().lstrip("."), target.suffix.lstrip(".").upper() or "PNG")
            if fmt == "JPEG" and image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGB")
            image.save(target, format=fmt, exif=b"")
            cleaned += 1
        except Exception as exc:  # noqa: BLE001
            ctx.log(f"! {path.name}: {exc}")
        ctx.progress(index / len(files) * 100, path.name)
    return f"Cleaned {cleaned} of {len(files)} photo(s)"


@tool(id="batch-pdf-text", name="Extract Text From Many PDFs", category="PDF",
      summary="Turn a folder of PDFs into text files, or one combined text document.",
      needs=("pypdf",),
      fields=[F.folder("folder", "Folder of PDFs"),
              F.choice("output_mode", "Output", ["One .txt per PDF", "One combined file"],
                       "One .txt per PDF"),
              F.folder("output", "Save into", required=False),
              F.flag("page_marks", "Mark page boundaries", True)])
def batch_pdf_text(v, ctx):
    from pypdf import PdfReader
    root = need_dir(v["folder"])
    out_dir = Path(v["output"]) if v["output"].strip() else root / "extracted-text"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdfs = [p for p in iter_files(root, True) if p.suffix.lower() == ".pdf"]
    if not pdfs:
        raise ToolError("No PDF files found in that folder")
    combined: list[str] = []
    for index, path in enumerate(pdfs, start=1):
        ctx.check_cancel()
        try:
            reader = PdfReader(str(path))
        except Exception as exc:  # noqa: BLE001
            ctx.log(f"! {path.name}: {exc}")
            continue
        chunks = []
        for number, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception:  # noqa: BLE001
                text = ""
            chunks.append(f"----- page {number} -----\n{text}" if v["page_marks"] else text)
        body = "\n\n".join(chunks)
        if v["output_mode"] == "One combined file":
            combined.append(f"===== {path.name} =====\n{body}")
        else:
            target = out_dir / (path.stem + ".txt")
            write_text(target, body)
            ctx.output(str(target))
        ctx.progress(index / len(pdfs) * 100, path.name)
    if v["output_mode"] == "One combined file":
        target = out_dir / "all-pdfs.txt"
        write_text(target, "\n\n".join(combined))
        ctx.output(str(target))
        return f"{len(pdfs)} PDF(s) combined → {target}"
    return f"{len(pdfs)} PDF(s) extracted into {out_dir}"


@tool(id="batch-pdf-merge", name="Merge Every PDF in a Folder", category="PDF",
      summary="Combine all PDFs in a folder into one file, in filename order.",
      needs=("pypdf",),
      fields=[F.folder("folder", "Folder of PDFs"),
              F.flag("recursive", "Include subfolders", False),
              F.save("output", "Save merged PDF as", required=True, filters="PDF (*.pdf)")])
def batch_pdf_merge(v, ctx):
    from pypdf import PdfReader, PdfWriter
    root = need_dir(v["folder"])
    pdfs = sorted((p for p in iter_files(root, v["recursive"]) if p.suffix.lower() == ".pdf"),
                  key=lambda p: str(p).lower())
    if not pdfs:
        raise ToolError("No PDF files found in that folder")
    writer = PdfWriter()
    pages = 0
    for path in pdfs:
        ctx.check_cancel()
        try:
            reader = PdfReader(str(path))
        except Exception as exc:  # noqa: BLE001
            ctx.log(f"! skipped {path.name}: {exc}")
            continue
        for page in reader.pages:
            writer.add_page(page)
            pages += 1
        writer.add_outline_item(path.stem, pages - len(reader.pages))
        ctx.log(f"+ {path.name} ({len(reader.pages)} pages)")
    target = out_path(v["output"], "merged.pdf")
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "wb") as handle:
        writer.write(handle)
    ctx.output(str(target))
    return f"{len(pdfs)} PDF(s), {pages} pages → {target}"


@tool(id="batch-compress-images", name="Compress a Folder of Images", category="Images",
      summary="Re-encode every image to a smaller file, with a before/after total.",
      needs=("pillow",),
      fields=[F.folder("folder", "Folder of images"),
              F.integer("quality", "Quality", 72, minimum=10, maximum=95),
              F.integer("max_width", "Maximum width (0 = keep)", 1920, minimum=0),
              F.folder("output", "Save into", required=False),
              F.flag("recursive", "Include subfolders", True)])
def batch_compress_images(v, ctx):
    from PIL import Image
    from .images import _open, _save
    root = need_dir(v["folder"])
    out_dir = Path(v["output"]) if v["output"].strip() else root / "compressed"
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [p for p in iter_files(root, v["recursive"], "*")
             if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif")]
    if not files:
        raise ToolError("No images found in that folder")
    before = after = 0
    for index, path in enumerate(files, start=1):
        ctx.check_cancel()
        image = _open(path)
        if v["max_width"] and image.width > v["max_width"]:
            ratio = v["max_width"] / image.width
            image = image.resize((v["max_width"], max(1, int(image.height * ratio))), Image.LANCZOS)
        ext = ".jpg" if path.suffix.lower() in (".jpg", ".jpeg") else path.suffix
        target = out_dir / (path.stem + ext)
        _save(image, target, v["quality"])
        before += path.stat().st_size
        after += target.stat().st_size
        ctx.progress(index / len(files) * 100, path.name)
    saved = (1 - after / before) * 100 if before else 0
    return f"{len(files)} image(s): {human_size(before)} → {human_size(after)} ({saved:.0f}% smaller)"


@tool(id="batch-rename-from-csv", name="Rename From a CSV List", category="Files",
      summary="Rename files using a two-column CSV of old name and new name.",
      fields=[F.folder("folder", "Folder"),
              F.file("csv_file", "CSV with old,new columns", filters="CSV (*.csv)"),
              F.flag("apply", "Apply the rename", False)])
def batch_rename_from_csv(v, ctx):
    root = need_dir(v["folder"])
    path = need_file(v["csv_file"])
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ToolError("The CSV is empty")
    old_key = next((key for key in rows[0] if "old" in key.lower() or "from" in key.lower()),
                   list(rows[0])[0])
    new_key = next((key for key in rows[0] if "new" in key.lower() or "to" in key.lower()),
                   list(rows[0])[-1])
    plan = []
    for row in rows:
        old_name = (row.get(old_key) or "").strip()
        new_name = (row.get(new_key) or "").strip()
        if not old_name or not new_name:
            continue
        source = root / old_name
        if not source.exists():
            ctx.log(f"! not found: {old_name}")
            continue
        plan.append((source, root / new_name))
    for source, target in plan[:60]:
        ctx.log(f"{source.name}  →  {target.name}")
    if not plan:
        return "Nothing to rename."
    if not v["apply"]:
        return f"{len(plan)} file(s) would be renamed (preview only)"
    done = 0
    for source, target in plan:
        try:
            source.rename(target)
            done += 1
        except OSError as exc:
            ctx.log(f"! {source.name}: {exc}")
    return f"Renamed {done} file(s)"


@tool(id="batch-copy-list", name="Copy Files From a List", category="Files",
      summary="Copy every path listed in a text file into one destination folder.",
      fields=[F.file("list_file", "Text file of paths", filters="Text (*.txt *.csv)"),
              F.folder("destination", "Destination folder", required=False),
              F.flag("apply", "Do the copy", False)])
def batch_copy_list(v, ctx):
    listing = need_file(v["list_file"])
    raw = listing.read_text(encoding="utf-8", errors="replace")
    entries = [line.strip().strip('"') for line in raw.splitlines() if line.strip()]
    if not entries:
        raise ToolError("That file lists no paths")
    dest_raw = v["destination"].strip()
    if not dest_raw:
        raise ToolError("Give a destination folder")
    destination = Path(dest_raw)
    plan = []
    for entry in entries:
        source = Path(entry)
        if not source.exists():
            ctx.log(f"! missing: {entry}")
            continue
        plan.append((source, destination / source.name))
    for source, target in plan[:40]:
        ctx.log(f"{source}  →  {target}")
    if not v["apply"]:
        return f"{len(plan)} file(s) would be copied (preview only)"
    destination.mkdir(parents=True, exist_ok=True)
    copied = 0
    for source, target in plan:
        try:
            shutil.copy2(source, target)
            copied += 1
        except OSError as exc:
            ctx.log(f"! {source.name}: {exc}")
    return f"Copied {copied} of {len(plan)} file(s) to {destination}"


@tool(id="batch-delete-list", name="Delete Files From a List", category="Files",
      summary="Delete every path listed in a text file — preview first, then confirm.",
      destructive=True,
      fields=[F.file("list_file", "Text file of paths", filters="Text (*.txt *.csv)"),
              F.flag("apply", "Delete them", False),
              F.flag("confirm", "Confirmed — permanent", False, show_if="apply")])
def batch_delete_list(v, ctx):
    listing = need_file(v["list_file"])
    entries = [line.strip().strip('"') for line in
               listing.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    found = [Path(entry) for entry in entries if Path(entry).exists()]
    total = 0
    for path in found:
        try:
            total += path.stat().st_size if path.is_file() else 0
        except OSError:
            continue
    for path in found[:50]:
        ctx.log(f"would delete {path}")
    if not v["apply"]:
        return f"{len(found)} of {len(entries)} path(s) exist ({human_size(total)}) — preview only"
    if not v["confirm"]:
        raise ToolError("Tick the confirmation box to delete these files")
    removed = 0
    for path in found:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            removed += 1
        except OSError as exc:
            ctx.log(f"! {path}: {exc}")
    return f"Deleted {removed} of {len(found)} path(s)"


@tool(id="batch-line-endings", name="Fix Line Endings in a Folder", category="Text",
      summary="Convert every text file in a folder to one line-ending style.",
      fields=[F.folder("folder", "Folder"),
              F.text("pattern", "Only files matching", "*.txt"),
              F.choice("target", "Convert to", ["Windows (CRLF)", "Unix (LF)"], "Windows (CRLF)"),
              F.flag("recursive", "Include subfolders", True),
              F.flag("apply", "Write the changes", False)])
def batch_line_endings(v, ctx):
    root = need_dir(v["folder"])
    newline = "\r\n" if v["target"].startswith("Windows") else "\n"
    changed = 0
    for path in iter_files(root, v["recursive"], v["pattern"] or "*"):
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
        new_raw = text.replace("\n", newline).encode("utf-8")
        if new_raw == raw:
            continue
        changed += 1
        if v["apply"]:
            try:
                path.write_bytes(new_raw)
            except OSError as exc:
                ctx.log(f"! {path.name}: {exc}")
    verb = "Converted" if v["apply"] else "Would convert"
    return f"{verb} {changed} file(s) to {v['target']}"


@tool(id="batch-encoding", name="Convert Encodings in a Folder", category="Text",
      summary="Re-save every text file in a folder as UTF-8 (or another encoding).",
      fields=[F.folder("folder", "Folder"),
              F.text("pattern", "Only files matching", "*.txt"),
              F.choice("target", "Write as", ["UTF-8", "UTF-8 with BOM", "UTF-16",
                                              "Windows-1252"], "UTF-8"),
              F.flag("recursive", "Include subfolders", True),
              F.flag("apply", "Write the changes", False)])
def batch_encoding(v, ctx):
    from ._util import read_text
    root = need_dir(v["folder"])
    codec = {"UTF-8": "utf-8", "UTF-8 with BOM": "utf-8-sig", "UTF-16": "utf-16",
             "Windows-1252": "cp1252"}[v["target"]]
    changed = 0
    for path in iter_files(root, v["recursive"], v["pattern"] or "*"):
        try:
            text = read_text(path)
            current = path.read_bytes()
            new_data = text.encode(codec, errors="replace")
        except (OSError, UnicodeError):
            continue
        if new_data == current:
            continue
        changed += 1
        if v["apply"]:
            try:
                path.write_bytes(new_data)
            except OSError as exc:
                ctx.log(f"! {path.name}: {exc}")
    verb = "Converted" if v["apply"] else "Would convert"
    return f"{verb} {changed} file(s) to {v['target']}"


@tool(id="batch-zip-folders", name="Zip Every Subfolder", category="Archives",
      summary="Give each subfolder its own ZIP — one archive per project or album.",
      fields=[F.folder("folder", "Parent folder"),
              F.folder("output", "Save ZIPs into", required=False),
              F.integer("level", "Compression level", 6, minimum=0, maximum=9)])
def batch_zip_folders(v, ctx):
    root = need_dir(v["folder"])
    out_dir = Path(v["output"]) if v["output"].strip() else root
    out_dir.mkdir(parents=True, exist_ok=True)
    folders = [entry for entry in root.iterdir() if entry.is_dir()]
    if not folders:
        raise ToolError("That folder has no subfolders")
    made = 0
    for index, folder in enumerate(folders, start=1):
        ctx.check_cancel()
        target = out_dir / f"{folder.name}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=v["level"]) as archive:
            for path in iter_files(folder, True):
                archive.write(path, str(path.relative_to(folder)))
        made += 1
        ctx.output(str(target))
        ctx.progress(index / len(folders) * 100, folder.name)
    return f"{made} ZIP file(s) written to {out_dir}"


@tool(id="batch-json-to-csv", name="Convert Many JSON Files to CSV", category="Data",
      summary="Turn every JSON file in a folder into a CSV, one output per input.",
      fields=[F.folder("folder", "Folder of JSON files"),
              F.folder("output", "Save CSVs into", required=False)])
def batch_json_to_csv(v, ctx):
    root = need_dir(v["folder"])
    out_dir = Path(v["output"]) if v["output"].strip() else root / "csv"
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [p for p in iter_files(root, False, "*.json")]
    if not files:
        raise ToolError("No JSON files found in that folder")
    made = 0
    for index, path in enumerate(files, start=1):
        ctx.check_cancel()
        try:
            data = __import__("json").loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            ctx.log(f"! {path.name}: {exc}")
            continue
        if isinstance(data, dict):
            for key in ("data", "items", "records", "results", "rows"):
                if isinstance(data.get(key), list):
                    data = data[key]
                    break
            else:
                data = [data]
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            ctx.log(f"! {path.name}: not an array of objects, skipped")
            continue
        columns = list(dict.fromkeys(key for item in data for key in item))
        target = write_csv(out_dir / (path.stem + ".csv"), data, columns)
        ctx.output(str(target))
        made += 1
        ctx.progress(index / len(files) * 100, path.name)
    return f"{made} of {len(files)} file(s) converted into {out_dir}"


@tool(id="batch-thumbnails-folder", name="Thumbnail a Folder Tree", category="Images",
      summary="Make thumbnails for every image under a folder, keeping the folder structure.",
      needs=("pillow",),
      fields=[F.folder("folder", "Folder to scan"),
              F.integer("size", "Thumbnail size (px)", 300, minimum=32, maximum=2000),
              F.folder("output", "Save thumbnails into", required=False)])
def batch_thumbnails_folder(v, ctx):
    from PIL import Image
    from .images import _open, _save
    root = need_dir(v["folder"])
    out_dir = Path(v["output"]) if v["output"].strip() else root / "thumbnails"
    files = [p for p in iter_files(root, True)
             if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif")]
    if not files:
        raise ToolError("No images found")
    for index, path in enumerate(files, start=1):
        ctx.check_cancel()
        try:
            image = _open(path)
            image.thumbnail((v["size"], v["size"]), Image.LANCZOS)
            relative = path.relative_to(root)
            target = out_dir / relative.parent / (path.stem + ".jpg")
            _save(image, target, 82)
        except Exception as exc:  # noqa: BLE001
            ctx.log(f"! {path.name}: {exc}")
        ctx.progress(index / len(files) * 100, path.name)
    return f"{len(files)} thumbnail(s) in {out_dir}"


@tool(id="folder-summary", name="Folder Summary Card", category="Files",
      summary="One screen of facts about a folder: counts, sizes, newest file and top types.",
      fields=[F.folder("folder", "Folder")])
def folder_summary(v, ctx):
    root = need_dir(v["folder"])
    files = 0
    total = 0
    newest = (0, "")
    oldest = (float("inf"), "")
    extensions: dict[str, int] = {}
    for path in iter_files(root, True):
        try:
            stat = path.stat()
        except OSError:
            continue
        files += 1
        total += stat.st_size
        if stat.st_mtime > newest[0]:
            newest = (stat.st_mtime, path.name)
        if stat.st_mtime < oldest[0]:
            oldest = (stat.st_mtime, path.name)
        ext = path.suffix.lower() or "(none)"
        extensions[ext] = extensions.get(ext, 0) + 1
        if files % 200 == 0:
            ctx.check_cancel()
    from ._util import stamp
    top = sorted(extensions.items(), key=lambda kv: kv[1], reverse=True)[:8]
    ctx.log(report_table([{"extension": ext, "files": count} for ext, count in top],
                         ["extension", "files"]))
    return {"folder": str(root), "files": files,
            "folders": sum(1 for _ in root.rglob("*") if _.is_dir()),
            "total_size": human_size(total),
            "average_file": human_size(total / files) if files else "0 B",
            "newest": f"{newest[1]} ({stamp(newest[0])})" if files else "",
            "oldest": f"{oldest[1]} ({stamp(oldest[0])})" if files else "",
            "distinct_types": len(extensions)}
