"""Files and folders — inspect, rename, copy, compare, organise."""

from __future__ import annotations

import os
import re
import shutil
import stat
import time
from datetime import datetime
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import (
    hash_file,
    human_size,
    iter_files,
    need_dir,
    need_file,
    out_path,
    report_table,
    safe_name,
    stamp,
    write_csv,
)


# --------------------------------------------------------------------------
# Inspect
# --------------------------------------------------------------------------
@tool(id="file-info", name="File Info", category="Files",
      summary="Size, type, timestamps, permissions and a SHA-256 fingerprint for one file.",
      keywords="properties stat metadata detail",
      fields=[F.file("path", "File")])
def file_info(v, ctx):
    p = need_file(v["path"])
    st = p.stat()
    return {
        "path": str(p.resolve()),
        "name": p.name,
        "extension": p.suffix or "(none)",
        "size": human_size(st.st_size),
        "bytes": st.st_size,
        "created": stamp(st.st_ctime),
        "modified": stamp(st.st_mtime),
        "accessed": stamp(st.st_atime),
        "read_only": not os.access(p, os.W_OK),
        "sha256": hash_file(p),
    }


@tool(id="path-inspect", name="Path Inspector", category="Files",
      summary="Break a path into its parts and show the resolved absolute location.",
      keywords="parse path parts resolve absolute",
      fields=[F.text("path", "Path", placeholder=r"C:\Users\me\Desktop\notes.txt")])
def path_inspect(v, ctx):
    raw = v["path"].strip()
    if not raw:
        raise ToolError("Give a path to inspect")
    p = Path(os.path.expandvars(os.path.expanduser(raw)))
    parts = [part for part in p.parts]
    return {
        "raw": raw,
        "absolute": str(p.absolute()),
        "resolved": str(p.resolve()) if p.exists() else "(does not exist)",
        "name": p.name or "(none)",
        "stem": p.stem or "(none)",
        "extension": p.suffix or "(none)",
        "parent": str(p.parent),
        "depth": len(parts),
        "parts": parts,
        "exists": p.exists(),
        "is_file": p.is_file(),
        "is_dir": p.is_dir(),
        "is_symlink": p.is_symlink(),
        "length": len(str(p)),
    }


@tool(id="file-type-detect", name="File Type Detector", category="Files",
      summary="Identify a file from its magic bytes, not its extension.",
      keywords="magic bytes signature mime sniff",
      fields=[F.file("path", "File")])
def file_type_detect(v, ctx):
    p = need_file(v["path"])
    head = p.read_bytes()[:32]
    signatures = [
        (b"\x89PNG\r\n\x1a\n", "PNG image"), (b"\xff\xd8\xff", "JPEG image"),
        (b"GIF87a", "GIF image"), (b"GIF89a", "GIF image"),
        (b"BM", "BMP image"), (b"%PDF-", "PDF document"),
        (b"PK\x03\x04", "ZIP archive or Office document"),
        (b"\x1f\x8b", "GZIP archive"), (b"BZh", "BZIP2 archive"),
        (b"\xfd7zXZ", "XZ archive"), (b"7z\xbc\xaf\x27\x1c", "7-Zip archive"),
        (b"Rar!", "RAR archive"), (b"\x7fELF", "ELF executable"),
        (b"MZ", "Windows executable"),
        (b"SQLite format 3", "SQLite database"),
        (b"ID3", "MP3 audio"), (b"OggS", "OGG media"),
        (b"RIFF", "RIFF media (WAV/AVI/WebP)"), (b"\x00\x00\x01\x00", "Windows icon"),
        (b"{\\rtf", "RTF document"), (b"\x50\x4b\x05\x06", "Empty ZIP archive"),
    ]
    for sig, label in signatures:
        if head.startswith(sig):
            ctx.log(f"Header: {head[:8].hex(' ')}")
            return {"file": p.name, "detected": label, "extension": p.suffix or "(none)"}
    if head and all(32 <= b < 127 or b in (9, 10, 13) for b in head):
        return {"file": p.name, "detected": "Plain text", "extension": p.suffix or "(none)"}
    return {"file": p.name, "detected": "Unknown binary", "extension": p.suffix or "(none)",
            "header": head[:8].hex(" ")}


@tool(id="folder-size", name="Folder Size", category="Files",
      summary="Total size of a folder, with its biggest immediate children ranked.",
      keywords="size disk usage du weight",
      fields=[F.folder("folder", "Folder"),
              F.flag("include_files", "Include individual files in the ranking", True)])
def folder_size(v, ctx):
    root = need_dir(v["folder"])
    total = 0
    count = 0
    for path in iter_files(root, recursive=True):
        try:
            total += path.stat().st_size
            count += 1
        except OSError:
            continue
        if count % 500 == 0:
            ctx.check_cancel()
    children = []
    for entry in root.iterdir():
        try:
            if entry.is_dir():
                size = sum(f.stat().st_size for f in iter_files(entry) if f.exists())
                children.append({"name": entry.name + "/", "size": human_size(size), "bytes": size})
            elif v["include_files"]:
                size = entry.stat().st_size
                children.append({"name": entry.name, "size": human_size(size), "bytes": size})
        except OSError:
            continue
    children.sort(key=lambda r: r["bytes"], reverse=True)
    ctx.log(report_table(children[:20], ["name", "size"]))
    return {"folder": str(root), "total_size": human_size(total), "total_bytes": total,
            "files": count, "children": len(children)}


@tool(id="tree-view", name="Folder Tree", category="Files",
      summary="Print the folder structure as a tree, with optional sizes and a depth limit.",
      keywords="tree structure hierarchy listing",
      fields=[F.folder("folder", "Folder"),
              F.integer("depth", "Maximum depth", 3, minimum=1, maximum=12),
              F.flag("sizes", "Show sizes", False),
              F.text("pattern", "Only names matching", "*", help="e.g. *.py")])
def tree_view(v, ctx):
    root = need_dir(v["folder"])
    max_depth = v["depth"]
    lines = [root.name + "/"]
    shown = 0

    def walk(folder: Path, prefix: str, level: int) -> None:
        nonlocal shown
        if level > max_depth:
            return
        try:
            entries = sorted(folder.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except OSError:
            return
        for index, entry in enumerate(entries):
            last = index == len(entries) - 1
            branch = "└── " if last else "├── "
            if entry.is_dir():
                ctx.check_cancel()
                lines.append(f"{prefix}{branch}{entry.name}/")
                walk(entry, prefix + ("    " if last else "│   "), level + 1)
            elif re.fullmatch(v["pattern"].replace(".", r"\.").replace("*", ".*"),
                              entry.name, re.IGNORECASE) or v["pattern"] in ("*", ""):
                size = f"  ({human_size(entry.stat().st_size)})" if v["sizes"] else ""
                lines.append(f"{prefix}{branch}{entry.name}{size}")
                shown += 1

    walk(root, "", 1)
    ctx.log("\n".join(lines[:4000]))
    if len(lines) > 4000:
        ctx.log(f"… truncated at 4000 lines")
    return f"{shown} files shown under {root}"


@tool(id="file-search", name="Find Files", category="Files",
      summary="Search a folder by name pattern, size and text content.",
      keywords="find search grep locate query",
      fields=[F.folder("folder", "Folder to search"),
              F.text("pattern", "Name pattern", "*", help="Wildcards allowed: *.log, report-??.txt"),
              F.text("contains", "Content contains", "",
                     help="Leave blank to search by name only"),
              F.flag("recursive", "Include subfolders", True),
              F.integer("max_results", "Stop after", 200, minimum=1, maximum=5000)])
def file_search(v, ctx):
    root = need_dir(v["folder"])
    pattern = v["pattern"].strip() or "*"
    needle = v["contains"].strip().lower()
    hits = []
    scanned = 0
    for path in iter_files(root, v["recursive"], pattern):
        scanned += 1
        if scanned % 200 == 0:
            ctx.check_cancel()
        if needle:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            if needle not in text:
                continue
            line_no = next((i + 1 for i, line in enumerate(text.splitlines()) if needle in line), 0)
            hits.append({"name": path.name, "folder": str(path.parent), "line": line_no,
                         "size": human_size(path.stat().st_size)})
        else:
            hits.append({"name": path.name, "folder": str(path.parent), "line": "",
                         "size": human_size(path.stat().st_size)})
        if len(hits) >= v["max_results"]:
            break
    ctx.log(report_table(hits[:200]))
    return f"{len(hits)} match(es) in {scanned} file(s) scanned"


@tool(id="find-duplicates", name="Duplicate Finder", category="Files",
      summary="Find identical files by content hash and reclaim the wasted space.",
      keywords="dupes duplicate same content reclaim",
      fields=[F.folder("folder", "Folder"),
              F.integer("min_kb", "Ignore files smaller than (KB)", 1, minimum=0),
              F.flag("recursive", "Include subfolders", True),
              F.save("report", "Save CSV report to", help="Optional")])
def find_duplicates(v, ctx):
    root = need_dir(v["folder"])
    by_size: dict[int, list[Path]] = {}
    for path in iter_files(root, v["recursive"]):
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size < v["min_kb"] * 1024:
            continue
        by_size.setdefault(size, []).append(path)
        if len(by_size) % 100 == 0:
            ctx.check_cancel()

    groups = []
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        by_hash: dict[str, list[Path]] = {}
        for path in paths:
            try:
                by_hash.setdefault(hash_file(path, "sha256"), []).append(path)
            except OSError:
                continue
        for digest, same in by_hash.items():
            if len(same) >= 2:
                groups.append({"hash": digest[:16], "size": size, "files": [str(p) for p in same]})

    if not groups:
        return "No duplicates found."

    wasted = 0
    rows = []
    for group in sorted(groups, key=lambda g: g["size"] * (len(g["files"]) - 1), reverse=True):
        extra = group["size"] * (len(group["files"]) - 1)
        wasted += extra
        ctx.log(f"\n{human_size(group['size'])} × {len(group['files'])}  (wasted {human_size(extra)})")
        for path in group["files"]:
            ctx.log(f"   {path}")
            rows.append({"size_bytes": group["size"], "hash": group["hash"], "path": path})
    if v["report"]:
        path = write_csv(out_path(v["report"], "duplicates.csv"), rows,
                         ["size_bytes", "hash", "path"])
        ctx.output(str(path))
    return f"{len(groups)} duplicate group(s) · {human_size(wasted)} recoverable"


@tool(id="empty-folder-finder", name="Empty Folder Finder", category="Files",
      summary="List folders that contain nothing, optionally deleting them.",
      keywords="empty blank folders clean",
      fields=[F.folder("folder", "Folder"),
              F.flag("delete", "Delete the empty folders", False),
              F.flag("confirm", "I understand deletion is permanent", False, show_if="delete")])
def empty_folder_finder(v, ctx):
    root = need_dir(v["folder"])
    empties = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        folder = Path(dirpath)
        if folder == root:
            continue
        try:
            if not any(folder.iterdir()):
                empties.append(folder)
        except OSError:
            continue
    if not empties:
        return "No empty folders found."
    for folder in empties:
        ctx.log(str(folder))
    if v["delete"]:
        if not v["confirm"]:
            raise ToolError("Tick the confirmation box to delete these folders")
        removed = 0
        for folder in empties:
            try:
                folder.rmdir()
                removed += 1
            except OSError:
                pass
        return f"Removed {removed} of {len(empties)} empty folder(s)"
    return f"{len(empties)} empty folder(s) found (nothing deleted)"


@tool(id="recent-files", name="Recently Changed Files", category="Files",
      summary="Files modified within the last N hours or days, newest first.",
      keywords="recent modified changed latest",
      fields=[F.folder("folder", "Folder"),
              F.integer("hours", "Within the last (hours)", 24, minimum=1, maximum=8760),
              F.integer("limit", "Show at most", 50, minimum=1, maximum=1000)])
def recent_files(v, ctx):
    root = need_dir(v["folder"])
    cutoff = time.time() - v["hours"] * 3600
    found = []
    for path in iter_files(root, True):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime >= cutoff:
            found.append({"modified": stamp(mtime), "name": path.name,
                          "folder": str(path.parent), "size": human_size(path.stat().st_size),
                          "_m": mtime})
    found.sort(key=lambda r: r["_m"], reverse=True)
    rows = found[:v["limit"]]
    ctx.log(report_table(rows, ["modified", "name", "size", "folder"]))
    return f"{len(found)} file(s) changed in the last {v['hours']}h"


@tool(id="extension-report", name="File Type Report", category="Files",
      summary="Count files and bytes per extension, biggest offenders first.",
      keywords="extension types summary breakdown statistics",
      fields=[F.folder("folder", "Folder"),
              F.save("report", "Save CSV report to", help="Optional")])
def extension_report(v, ctx):
    root = need_dir(v["folder"])
    stats: dict[str, dict] = {}
    for path in iter_files(root):
        ext = path.suffix.lower() or "(none)"
        entry = stats.setdefault(ext, {"extension": ext, "files": 0, "bytes": 0})
        try:
            entry["bytes"] += path.stat().st_size
        except OSError:
            pass
        entry["files"] += 1
        if len(stats) % 50 == 0:
            ctx.check_cancel()
    rows = sorted(stats.values(), key=lambda r: r["bytes"], reverse=True)
    for row in rows:
        row["size"] = human_size(row["bytes"])
    ctx.log(report_table(rows, ["extension", "files", "size"]))
    if v["report"]:
        path = write_csv(out_path(v["report"], "extensions.csv"), rows)
        ctx.output(str(path))
    return f"{len(rows)} distinct extension(s)"


# --------------------------------------------------------------------------
# Rename & organise
# --------------------------------------------------------------------------
@tool(id="bulk-rename", name="Bulk Rename", category="Files",
      summary="Rename many files with a find/replace, regex, numbering or case change — preview first.",
      keywords="rename batch pattern regex number sequence",
      fields=[F.folder("folder", "Folder"),
              F.choice("mode", "Method", ["Find & replace", "Regular expression", "Add prefix",
                                          "Add suffix", "Sequence number", "Change case",
                                          "Replace spaces"], "Find & replace"),
              F.text("find", "Find / pattern", help="Used by find & replace and regex"),
              F.text("replace", "Replace with / text", help="Replacement, prefix or suffix"),
              F.choice("case", "Case", ["lower", "UPPER", "Title"], "lower", show_if=""),
              F.flag("recursive", "Include subfolders", False),
              F.text("pattern", "Only files matching", "*"),
              F.flag("apply", "Apply the rename", False),
              F.flag("confirm", "I have read the preview", False, show_if="apply")])
def bulk_rename(v, ctx):
    root = need_dir(v["folder"])
    mode = v["mode"]
    find, repl = v["find"], v["replace"]
    if mode == "Regular expression":
        try:
            regex = re.compile(find)
        except re.error as exc:
            raise ToolError(f"Bad regular expression: {exc}") from exc

    plan = []
    counter = 0
    for path in sorted(iter_files(root, v["recursive"], v["pattern"] or "*")):
        if not path.is_file():
            continue
        stem, suffix = path.stem, path.suffix
        if mode == "Find & replace":
            if not find:
                raise ToolError("Give something to find")
            new_stem = stem.replace(find, repl)
        elif mode == "Regular expression":
            new_stem = regex.sub(repl, stem)
        elif mode == "Add prefix":
            new_stem = f"{repl}{stem}"
        elif mode == "Add suffix":
            new_stem = f"{stem}{repl}"
        elif mode == "Sequence number":
            counter += 1
            new_stem = f"{repl}{counter:03d}_{stem}" if repl else f"{counter:03d}_{stem}"
        elif mode == "Change case":
            new_stem = stem.lower() if v["case"] == "lower" else (
                stem.upper() if v["case"] == "UPPER" else stem.title())
        else:  # Replace spaces
            new_stem = "_".join(stem.split())
        new_stem = safe_name(new_stem)
        if new_stem and new_stem != stem:
            plan.append((path, path.with_name(new_stem + suffix)))

    if not plan:
        return "Nothing to rename — no file matched or nothing changed."
    for old, new in plan[:100]:
        ctx.log(f"{old.name}  →  {new.name}")
    if len(plan) > 100:
        ctx.log(f"… and {len(plan) - 100} more")

    if not v["apply"]:
        return f"{len(plan)} file(s) would be renamed. Tick 'Apply the rename' to do it."
    if not v["confirm"]:
        raise ToolError("Tick the confirmation box after checking the preview")
    done, failed = 0, 0
    for old, new in plan:
        try:
            old.rename(new)
            done += 1
        except OSError as exc:
            failed += 1
            ctx.log(f"! {old.name}: {exc}")
    return f"Renamed {done} file(s)" + (f", {failed} failed" if failed else "")


@tool(id="rename-by-date", name="Rename by Date", category="Files",
      summary="Prefix each file with its modified date, so folders sort chronologically.",
      keywords="date timestamp sort rename chronological",
      fields=[F.folder("folder", "Folder"),
              F.choice("format", "Date format", ["%Y-%m-%d", "%Y%m%d", "%Y-%m-%d_%H%M"], "%Y-%m-%d"),
              F.text("pattern", "Only files matching", "*"),
              F.flag("apply", "Apply the rename", False)])
def rename_by_date(v, ctx):
    root = need_dir(v["folder"])
    plan = []
    for path in sorted(iter_files(root, False, v["pattern"] or "*")):
        if not path.is_file():
            continue
        day = datetime.fromtimestamp(path.stat().st_mtime).strftime(v["format"])
        if path.stem.startswith(day):
            continue
        plan.append((path, path.with_name(f"{day}_{path.stem}{path.suffix}")))
    for old, new in plan[:60]:
        ctx.log(f"{old.name}  →  {new.name}")
    if not plan:
        return "Nothing to rename."
    if not v["apply"]:
        return f"{len(plan)} file(s) would be renamed (preview only)"
    done = 0
    for old, new in plan:
        try:
            old.rename(new)
            done += 1
        except OSError:
            pass
    return f"Renamed {done} file(s)"


@tool(id="bulk-extension", name="Change Extensions", category="Files",
      summary="Give every file in a folder the same new extension.",
      keywords="extension suffix change convert rename",
      fields=[F.folder("folder", "Folder"),
              F.text("from_ext", "Current extension", "txt", help="Leave blank for all files"),
              F.text("to_ext", "New extension", "md", help="Without the dot"),
              F.flag("recursive", "Include subfolders", False),
              F.flag("apply", "Apply the change", False)])
def bulk_extension(v, ctx):
    root = need_dir(v["folder"])
    old_ext = v["from_ext"].strip().lstrip(".").lower()
    new_ext = v["to_ext"].strip().lstrip(".")
    if not new_ext:
        raise ToolError("Give the new extension")
    plan = []
    for path in iter_files(root, v["recursive"]):
        current = path.suffix.lstrip(".").lower()
        if old_ext and current != old_ext:
            continue
        if current == new_ext.lower():
            continue
        plan.append((path, path.with_suffix("." + new_ext)))
    for old, new in plan[:60]:
        ctx.log(f"{old.name}  →  {new.name}")
    if not plan:
        return "No file needed changing."
    if not v["apply"]:
        return f"{len(plan)} file(s) would change (preview only)"
    done = 0
    for old, new in plan:
        try:
            old.rename(new)
            done += 1
        except OSError:
            pass
    return f"Renamed {done} file(s) to .{new_ext}"


@tool(id="organise-by-type", name="Sort Into Type Folders", category="Files",
      summary="Move files into subfolders named after their extension.",
      keywords="organise sort tidy group folders",
      fields=[F.folder("folder", "Folder to tidy"),
              F.flag("apply", "Move the files", False),
              F.integer("min_files", "Only create a folder if it gets at least", 1, minimum=1)])
def organise_by_type(v, ctx):
    root = need_dir(v["folder"])
    buckets: dict[str, list[Path]] = {}
    for path in iter_files(root, False):
        if path.is_file():
            buckets.setdefault((path.suffix.lstrip(".").lower() or "no-extension"), []).append(path)
    moves = []
    for ext, files in sorted(buckets.items()):
        if len(files) < v["min_files"]:
            continue
        target = root / ext
        ctx.log(f"{ext}/  ←  {len(files)} file(s)")
        moves.extend((f, target / f.name) for f in files)
    if not moves:
        return "Nothing to organise."
    if not v["apply"]:
        return f"{len(moves)} file(s) would move (preview only)"
    moved = 0
    for src, dst in moves:
        try:
            dst.parent.mkdir(exist_ok=True)
            shutil.move(str(src), str(dst))
            moved += 1
        except OSError as exc:
            ctx.log(f"! {src.name}: {exc}")
    return f"Moved {moved} file(s)"


@tool(id="organise-by-month", name="Sort Into Month Folders", category="Files",
      summary="File photos and documents into Year/Month folders by their modified date.",
      keywords="organise photos date archive year month",
      fields=[F.folder("folder", "Folder to tidy"),
              F.text("pattern", "Only files matching", "*"),
              F.flag("apply", "Move the files", False)])
def organise_by_month(v, ctx):
    root = need_dir(v["folder"])
    moves = []
    for path in iter_files(root, False, v["pattern"] or "*"):
        if not path.is_file():
            continue
        when = datetime.fromtimestamp(path.stat().st_mtime)
        target = root / when.strftime("%Y") / when.strftime("%Y-%m")
        moves.append((path, target / path.name))
    if not moves:
        return "Nothing to organise."
    for src, dst in moves[:40]:
        ctx.log(f"{src.name}  →  {dst.relative_to(root)}")
    if not v["apply"]:
        return f"{len(moves)} file(s) would move (preview only)"
    moved = 0
    for src, dst in moves:
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved += 1
        except OSError:
            pass
    return f"Moved {moved} file(s)"


@tool(id="flatten-folder", name="Flatten Folder", category="Files",
      summary="Pull every file from nested subfolders up into one flat folder.",
      keywords="flatten collapse nested one level",
      fields=[F.folder("folder", "Folder"),
              F.flag("apply", "Move the files", False),
              F.flag("remove_empty", "Delete folders left empty", False)])
def flatten_folder(v, ctx):
    root = need_dir(v["folder"])
    plan = []
    for path in iter_files(root, True):
        if path.parent == root or not path.is_file():
            continue
        target = root / path.name
        plan.append((path, target))
    clashes = sum(1 for _, dst in plan if dst.exists())
    for src, dst in plan[:40]:
        ctx.log(f"{src.relative_to(root)}  →  {dst.name}")
    if not plan:
        return "Already flat."
    if clashes:
        ctx.log(f"! {clashes} name clash(es) will be numbered instead of overwritten")
    if not v["apply"]:
        return f"{len(plan)} file(s) would move (preview only)"
    moved = 0
    for src, dst in plan:
        try:
            if dst.exists():
                from ._util import unique
                dst = unique(dst)
            shutil.move(str(src), str(dst))
            moved += 1
        except OSError:
            pass
    if v["remove_empty"]:
        for dirpath, _, _ in os.walk(root, topdown=False):
            folder = Path(dirpath)
            if folder != root and not any(folder.iterdir()):
                try:
                    folder.rmdir()
                except OSError:
                    pass
    return f"Moved {moved} file(s) into {root.name}"


# --------------------------------------------------------------------------
# Copy, move, delete
# --------------------------------------------------------------------------
@tool(id="copy-folder", name="Copy Folder", category="Files",
      summary="Copy a folder tree with overwrite control and a verified byte count.",
      keywords="copy duplicate clone mirror backup",
      fields=[F.folder("source", "Source folder"),
              F.folder("destination", "Destination folder", required=False,
                       help="Created if it does not exist"),
              F.choice("on_exists", "If a file exists", ["Skip", "Overwrite", "Keep both"],
                       "Skip"),
              F.flag("verify", "Verify each file by size after copying", True)])
def copy_folder(v, ctx):
    src = need_dir(v["source"])
    dst_raw = v["destination"].strip()
    if not dst_raw:
        raise ToolError("Give a destination folder")
    dst = Path(os.path.expandvars(os.path.expanduser(dst_raw)))
    if src == dst or str(dst).startswith(str(src) + os.sep):
        raise ToolError("The destination cannot be inside the source")
    copied = skipped = 0
    total = 0
    for path in iter_files(src, True):
        relative = path.relative_to(src)
        target = dst / relative
        if target.exists():
            if v["on_exists"] == "Skip":
                skipped += 1
                continue
            if v["on_exists"] == "Keep both":
                from ._util import unique
                target = unique(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied += 1
        total += target.stat().st_size
        if v["verify"] and target.stat().st_size != path.stat().st_size:
            raise ToolError(f"Size mismatch after copying {path.name}")
        if copied % 50 == 0:
            ctx.check_cancel()
            ctx.progress(copied)
    return f"Copied {copied} file(s) ({human_size(total)}), skipped {skipped} → {dst}"


@tool(id="copy-with-verify", name="Verified Copy", category="Files",
      summary="Copy files and confirm each one with a SHA-256 comparison.",
      keywords="copy verify checksum integrity safe",
      fields=[F.files("files", "Files", filters="All files (*)"),
              F.folder("destination", "Destination folder", required=False)])
def copy_with_verify(v, ctx):
    files = v["files"]
    if isinstance(files, str):
        files = [f for f in files.split("|") if f]
    if not files:
        raise ToolError("Choose at least one file")
    dst_raw = v["destination"].strip()
    dst = Path(os.path.expandvars(os.path.expanduser(dst_raw))) if dst_raw else None
    ok = bad = 0
    for raw in files:
        src = need_file(raw)
        target = (dst or src.parent) / src.name
        if target == src:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        same = hash_file(src) == hash_file(target)
        ctx.log(f"{'✓' if same else '✕'} {src.name}")
        ok += same
        bad += not same
    return f"{ok} verified" + (f", {bad} mismatch(es)" if bad else "")


@tool(id="move-files", name="Move Files", category="Files",
      summary="Move a set of files into one destination folder, keeping their names.",
      keywords="move relocate transfer",
      fields=[F.files("files", "Files"),
              F.folder("destination", "Destination folder", required=False),
              F.flag("apply", "Do the move", False)])
def move_files(v, ctx):
    files = v["files"]
    if isinstance(files, str):
        files = [f for f in files.split("|") if f]
    dst_raw = v["destination"].strip()
    if not dst_raw:
        raise ToolError("Give a destination folder")
    dst = Path(os.path.expandvars(os.path.expanduser(dst_raw)))
    plan = [(need_file(raw), dst / Path(raw).name) for raw in files]
    for src, target in plan:
        ctx.log(f"{src}  →  {target}")
    if not v["apply"]:
        return f"{len(plan)} file(s) would move (preview only)"
    dst.mkdir(parents=True, exist_ok=True)
    moved = 0
    for src, target in plan:
        try:
            shutil.move(str(src), str(target))
            moved += 1
        except OSError as exc:
            ctx.log(f"! {src.name}: {exc}")
    return f"Moved {moved} of {len(plan)} file(s)"


@tool(id="delete-empty-files", name="Zero-Byte File Cleaner", category="Files",
      summary="Find files with nothing in them, optionally deleting them.",
      keywords="empty zero byte clean tidy",
      fields=[F.folder("folder", "Folder"),
              F.flag("delete", "Delete them", False),
              F.flag("confirm", "Confirmed — delete permanently", False, show_if="delete")])
def delete_empty_files(v, ctx):
    root = need_dir(v["folder"])
    found = [p for p in iter_files(root) if p.is_file() and p.stat().st_size == 0]
    if not found:
        return "No zero-byte files."
    for path in found[:200]:
        ctx.log(str(path))
    if not v["delete"]:
        return f"{len(found)} empty file(s) found (nothing deleted)"
    if not v["confirm"]:
        raise ToolError("Tick the confirmation box to delete")
    removed = 0
    for path in found:
        try:
            path.unlink()
            removed += 1
        except OSError:
            pass
    return f"Deleted {removed} file(s)"


@tool(id="split-file", name="Split File", category="Files",
      summary="Cut a large file into numbered chunks of a fixed size.",
      keywords="split chunk parts pieces size",
      fields=[F.file("path", "File"),
              F.number("size_mb", "Chunk size (MB)", 10.0, minimum=0.1, maximum=4096, step=0.5),
              F.folder("output", "Output folder", required=False)])
def split_file(v, ctx):
    src = need_file(v["path"])
    chunk = int(v["size_mb"] * 1024 * 1024)
    if chunk <= 0:
        raise ToolError("Chunk size must be positive")
    out_dir = Path(v["output"]) if v["output"].strip() else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    total = src.stat().st_size
    parts = 0
    with open(src, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            parts += 1
            target = out_dir / f"{src.name}.part{parts:03d}"
            target.write_bytes(block)
            ctx.output(str(target))
            ctx.log(f"{target.name}  ({human_size(len(block))})")
            ctx.progress(parts * chunk / max(total, 1) * 100)
            ctx.check_cancel()
    return f"Split {src.name} ({human_size(total)}) into {parts} part(s)"


@tool(id="join-files", name="Join File Parts", category="Files",
      summary="Reassemble a file that was split into numbered parts.",
      keywords="join merge parts reassemble combine",
      fields=[F.file("first_part", "First part", help="e.g. video.mp4.part001"),
              F.save("output", "Output file", required=True)])
def join_files(v, ctx):
    first = need_file(v["first_part"])
    pattern = re.sub(r"part\d+$", "", first.name)
    parts = sorted(p for p in first.parent.iterdir()
                   if p.name.startswith(pattern) and re.search(r"part\d+$", p.name))
    if not parts:
        raise ToolError("No numbered parts found next to the first part")
    target = out_path(v["output"], "joined.bin")
    with open(target, "wb") as out:
        for part in parts:
            out.write(part.read_bytes())
            ctx.log(f"+ {part.name} ({human_size(part.stat().st_size)})")
    ctx.output(str(target))
    return f"Joined {len(parts)} part(s) into {target} ({human_size(target.stat().st_size)})"


@tool(id="touch-file", name="Set File Timestamps", category="Files",
      summary="Rewrite a file's created/modified dates — handy for sorting and tests.",
      keywords="touch timestamp date modified created time",
      fields=[F.file("path", "File"),
              F.text("modified", "Modified (YYYY-MM-DD HH:MM)", help="Blank keeps the current value"),
              F.flag("apply", "Apply", False)])
def touch_file(v, ctx):
    p = need_file(v["path"])
    text = v["modified"].strip()
    if not text:
        raise ToolError("Give a date such as 2024-05-01 09:30")
    try:
        when = datetime.strptime(text, "%Y-%m-%d %H:%M").timestamp()
    except ValueError as exc:
        raise ToolError("Use the format YYYY-MM-DD HH:MM") from exc
    if not v["apply"]:
        return f"Would set {p.name} modified time to {stamp(when)}"
    os.utime(p, (when, when))
    return f"{p.name} now reads {stamp(when)}"


@tool(id="readonly-toggle", name="Read-Only Toggle", category="Files",
      summary="Make files read-only, or clear read-only so they can be edited again.",
      keywords="readonly permissions lock write protect",
      fields=[F.folder("folder", "Folder"),
              F.text("pattern", "Only files matching", "*"),
              F.choice("action", "Action", ["Make read-only", "Clear read-only"], "Make read-only"),
              F.flag("recursive", "Include subfolders", True)])
def readonly_toggle(v, ctx):
    root = need_dir(v["folder"])
    make_ro = v["action"] == "Make read-only"
    changed = 0
    for path in iter_files(root, v["recursive"], v["pattern"] or "*"):
        try:
            mode = path.stat().st_mode
            if make_ro:
                path.chmod(mode & ~stat.S_IWRITE)
            else:
                path.chmod(mode | stat.S_IWRITE)
            changed += 1
        except OSError as exc:
            ctx.log(f"! {path.name}: {exc}")
    return f"{'Locked' if make_ro else 'Unlocked'} {changed} file(s)"


@tool(id="permissions-report", name="Permissions Report", category="Files",
      summary="Show the read/write/execute bits for everything in a folder.",
      keywords="permissions chmod mode access rights",
      fields=[F.folder("folder", "Folder"),
              F.integer("limit", "Show at most", 60, minimum=1, maximum=1000)])
def permissions_report(v, ctx):
    root = need_dir(v["folder"])
    rows = []
    for path in iter_files(root, True):
        try:
            mode = path.stat().st_mode
        except OSError:
            continue
        rows.append({
            "name": path.name,
            "type": "dir" if path.is_dir() else "file",
            "mode": stat.filemode(mode),
            "owner": f"{(mode >> 6) & 7}",
            "group": f"{(mode >> 3) & 7}",
            "other": f"{mode & 7}",
        })
        if len(rows) >= v["limit"]:
            break
    ctx.log(report_table(rows, ["name", "type", "mode", "owner", "group", "other"]))
    return f"{len(rows)} entries"


# --------------------------------------------------------------------------
# Compare
# --------------------------------------------------------------------------
@tool(id="compare-files", name="Compare Two Files", category="Files",
      summary="Byte-level comparison of two files: identical, or where they first differ.",
      keywords="compare diff same different binary equal",
      fields=[F.file("file_a", "First file"), F.file("file_b", "Second file")])
def compare_files(v, ctx):
    a = need_file(v["file_a"], "First file")
    b = need_file(v["file_b"], "Second file")
    size_a, size_b = a.stat().st_size, b.stat().st_size
    if size_a != size_b:
        ctx.log(f"Sizes differ: {human_size(size_a)} vs {human_size(size_b)}")
    with open(a, "rb") as fa, open(b, "rb") as fb:
        offset = 0
        while True:
            block_a = fa.read(1 << 16)
            block_b = fb.read(1 << 16)
            if block_a != block_b:
                for i, (x, y) in enumerate(zip(block_a, block_b)):
                    if x != y:
                        return {"identical": False, "first_difference_at_byte": offset + i,
                                "byte_a": x, "byte_b": y,
                                "sizes": [size_a, size_b]}
                return {"identical": False, "first_difference_at_byte": offset + len(block_a),
                        "note": "One file ends first", "sizes": [size_a, size_b]}
            if not block_a:
                break
            offset += len(block_a)
            ctx.check_cancel()
    return {"identical": True, "size": human_size(size_a), "sha256": hash_file(a)}


@tool(id="compare-folders", name="Compare Two Folders", category="Files",
      summary="Show which files exist on only one side, and which differ in content.",
      keywords="compare folders sync mirror differences",
      fields=[F.folder("folder_a", "First folder"),
              F.folder("folder_b", "Second folder"),
              F.flag("by_hash", "Compare contents, not just names and sizes", False)])
def compare_folders(v, ctx):
    a = need_dir(v["folder_a"], "First folder")
    b = need_dir(v["folder_b"], "Second folder")
    map_a = {str(p.relative_to(a)): p for p in iter_files(a, True)}
    map_b = {str(p.relative_to(b)): p for p in iter_files(b, True)}
    only_a = sorted(set(map_a) - set(map_b))
    only_b = sorted(set(map_b) - set(map_a))
    differing = []
    for name in sorted(set(map_a) & set(map_b)):
        pa, pb = map_a[name], map_b[name]
        if pa.stat().st_size != pb.stat().st_size:
            differing.append(name)
        elif v["by_hash"] and hash_file(pa) != hash_file(pb):
            differing.append(name)
    ctx.log(f"Only in {a.name}: {len(only_a)}")
    for name in only_a[:40]:
        ctx.log(f"  − {name}")
    ctx.log(f"Only in {b.name}: {len(only_b)}")
    for name in only_b[:40]:
        ctx.log(f"  + {name}")
    ctx.log(f"Differing: {len(differing)}")
    for name in differing[:40]:
        ctx.log(f"  ≠ {name}")
    return (f"{len(only_a)} only left · {len(only_b)} only right · "
            f"{len(differing)} differ · {len(set(map_a) & set(map_b)) - len(differing)} identical")


@tool(id="hash-compare", name="Compare Against Checksum", category="Files",
      summary="Check a file against an expected hash and say plainly whether it matches.",
      keywords="verify checksum hash integrity download",
      fields=[F.file("path", "File"),
              F.text("expected", "Expected hash", required=True),
              F.choice("algorithm", "Algorithm", ["sha256", "md5", "sha1", "sha512", "blake2b"],
                       "sha256")])
def hash_compare(v, ctx):
    p = need_file(v["path"])
    expected = re.sub(r"[^0-9a-fA-F]", "", v["expected"]).lower()
    if not expected:
        raise ToolError("The expected hash contains no hex characters")
    actual = hash_file(p, v["algorithm"])
    match = actual == expected
    ctx.log(f"expected {expected}")
    ctx.log(f"actual   {actual}")
    return {"match": match, "algorithm": v["algorithm"], "file": p.name}


@tool(id="case-conflict-audit", name="Filename Conflict Audit", category="Files",
      summary="Find names that differ only by case or trailing space — breaks on Windows and shares.",
      keywords="case conflict collision sync onedrive share duplicate name",
      fields=[F.folder("folder", "Folder")])
def case_conflict_audit(v, ctx):
    root = need_dir(v["folder"])
    groups: dict[str, list[str]] = {}
    for path in iter_files(root, True):
        key = path.name.lower().rstrip(" .")
        groups.setdefault(key, []).append(str(path.relative_to(root)))
    clashes = {k: g for k, g in groups.items() if len(g) > 1}
    if not clashes:
        return "No case or whitespace conflicts found."
    for key, names in clashes.items():
        ctx.log(f"\n{key}")
        for name in names:
            ctx.log(f"   {name}")
    return f"{len(clashes)} conflicting name(s)"


@tool(id="long-path-audit", name="Long Path Audit", category="Files",
      summary="Find paths longer than 260 characters, which Windows tools silently fail on.",
      keywords="long path 260 max_path windows limit deep",
      fields=[F.folder("folder", "Folder"),
              F.integer("limit_chars", "Flag paths longer than", 260, minimum=100, maximum=32767)])
def long_path_audit(v, ctx):
    root = need_dir(v["folder"])
    limit = v["limit_chars"]
    offenders = []
    longest = 0
    for path in iter_files(root, True):
        length = len(str(path))
        longest = max(longest, length)
        if length > limit:
            offenders.append((length, str(path)))
        if len(offenders) % 100 == 0 and offenders:
            ctx.check_cancel()
    offenders.sort(reverse=True)
    for length, path in offenders[:80]:
        ctx.log(f"{length:>5}  {path}")
    return (f"{len(offenders)} path(s) over {limit} characters; longest seen was {longest}"
            if offenders else f"All paths are within {limit} characters (longest {longest})")


@tool(id="hidden-files-report", name="Hidden & System Files", category="Files",
      summary="List dotfiles and hidden entries that normal folder views skip.",
      keywords="hidden dotfile system invisible secret",
      fields=[F.folder("folder", "Folder")])
def hidden_files_report(v, ctx):
    root = need_dir(v["folder"])
    rows = []
    for path in iter_files(root, True, "*", skip_hidden=False):
        hidden = path.name.startswith(".")
        if not hidden and os.name == "nt":
            try:
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
                hidden = attrs != -1 and bool(attrs & 0x2)
            except Exception:
                hidden = False
        if hidden:
            rows.append({"name": path.name, "folder": str(path.parent),
                         "size": human_size(path.stat().st_size)})
    if not rows:
        return "No hidden files found."
    ctx.log(report_table(rows[:200], ["name", "size", "folder"]))
    return f"{len(rows)} hidden item(s)"


@tool(id="disk-hog-files", name="Largest Files", category="Files",
      summary="The biggest files under a folder, largest first — where the space went.",
      keywords="largest biggest files space hogs weight",
      fields=[F.folder("folder", "Folder"),
              F.number("min_mb", "Ignore files under (MB)", 10.0, minimum=0),
              F.integer("limit", "Show at most", 30, minimum=1, maximum=500)])
def disk_hog_files(v, ctx):
    root = need_dir(v["folder"])
    threshold = v["min_mb"] * 1024 * 1024
    found = []
    for path in iter_files(root, True):
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size >= threshold:
            found.append((size, path))
        if len(found) % 100 == 0 and found:
            ctx.check_cancel()
    found.sort(reverse=True)
    rows = [{"size": human_size(size), "name": p.name, "folder": str(p.parent)}
            for size, p in found[:v["limit"]]]
    ctx.log(report_table(rows, ["size", "name", "folder"]))
    total = sum(size for size, _ in found)
    return f"{len(found)} file(s) over {v['min_mb']} MB, {human_size(total)} in total"


@tool(id="safe-filename", name="Safe Filename Cleaner", category="Files",
      summary="Turn messy names into clean, cross-platform-safe filenames.",
      keywords="sanitise filename illegal characters clean slug",
      fields=[F.folder("folder", "Folder"),
              F.flag("apply", "Apply the rename", False),
              F.choice("spaces", "Spaces become", ["_", "-", "nothing"], "_")])
def safe_filename(v, ctx):
    root = need_dir(v["folder"])
    sep = {"_": "_", "-": "-", "nothing": ""}[v["spaces"]]
    plan = []
    for path in iter_files(root, False):
        if not path.is_file():
            continue
        cleaned = safe_name(path.stem)
        if sep:
            cleaned = sep.join(cleaned.replace(sep, " ").split())
        else:
            cleaned = "".join(cleaned.split())
        if cleaned and cleaned != path.stem:
            plan.append((path, path.with_name(cleaned + path.suffix)))
    for old, new in plan[:60]:
        ctx.log(f"{old.name}  →  {new.name}")
    if not plan:
        return "Every filename is already clean."
    if not v["apply"]:
        return f"{len(plan)} file(s) would be renamed (preview only)"
    done = 0
    for old, new in plan:
        try:
            old.rename(new)
            done += 1
        except OSError:
            pass
    return f"Renamed {done} file(s)"


@tool(id="sequence-renamer", name="Number Files in Order", category="Files",
      summary="Number files 001, 002, … in sorted order, keeping the original name.",
      keywords="sequence number order sort prefix batch",
      fields=[F.folder("folder", "Folder"),
              F.text("prefix", "Prefix", ""),
              F.integer("start", "Start at", 1, minimum=0),
              F.integer("digits", "Digits", 3, minimum=1, maximum=8),
              F.choice("sort_by", "Order by", ["Name", "Modified date", "Size"], "Name"),
              F.flag("apply", "Apply the rename", False)])
def sequence_renamer(v, ctx):
    root = need_dir(v["folder"])
    files = [p for p in root.iterdir() if p.is_file()]
    key = {"Name": lambda p: p.name.lower(),
           "Modified date": lambda p: p.stat().st_mtime,
           "Size": lambda p: p.stat().st_size}[v["sort_by"]]
    files.sort(key=key)
    plan = []
    for index, path in enumerate(files, start=v["start"]):
        number = str(index).zfill(v["digits"])
        plan.append((path, path.with_name(f"{v['prefix']}{number}_{path.name}")))
    for old, new in plan[:40]:
        ctx.log(f"{old.name}  →  {new.name}")
    if not v["apply"]:
        return f"{len(plan)} file(s) would be numbered (preview only)"
    done = 0
    for old, new in plan:
        try:
            old.rename(new)
            done += 1
        except OSError:
            pass
    return f"Numbered {done} file(s)"


@tool(id="folder-inventory", name="Folder Inventory", category="Files",
      summary="A full CSV inventory of a folder: name, size, dates, hashes.",
      keywords="inventory list csv export audit catalogue",
      fields=[F.folder("folder", "Folder"),
              F.flag("hashes", "Include SHA-256 for every file", False),
              F.save("report", "Save CSV to", required=True)])
def folder_inventory(v, ctx):
    root = need_dir(v["folder"])
    rows = []
    for path in iter_files(root, True):
        try:
            st = path.stat()
        except OSError:
            continue
        row = {"path": str(path.relative_to(root)), "bytes": st.st_size,
               "modified": stamp(st.st_mtime), "extension": path.suffix}
        if v["hashes"]:
            row["sha256"] = hash_file(path)
        rows.append(row)
        if len(rows) % 100 == 0:
            ctx.progress(min(99, len(rows) / 10))
            ctx.check_cancel()
    target = write_csv(out_path(v["report"], "inventory.csv"), rows)
    ctx.output(str(target))
    return f"{len(rows)} file(s) written to {target}"
