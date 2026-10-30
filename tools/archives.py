"""Archives — zip, tar, gzip and 7-Zip."""

from __future__ import annotations

import bz2
import gzip
import shutil
import tarfile
import zipfile
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import (
    human_size,
    iter_files,
    need_dir,
    need_file,
    out_path,
    report_table,
    run_command,
    stamp,
)


def _safe_member(name: str, target: Path) -> Path:
    """Refuse archive entries that would escape the destination (zip-slip)."""
    resolved = (target / name).resolve()
    if target.resolve() not in resolved.parents and resolved != target.resolve():
        raise ToolError(f"Refusing unsafe archive path: {name}")
    return resolved


@tool(id="zip-create", name="Create ZIP", category="Archives",
      summary="Zip a folder or a set of files, with a compression level you choose.",
      keywords="zip compress archive pack shrink",
      fields=[F.folder("folder", "Folder to zip", required=False),
              F.save("output", "Save ZIP as", required=True, filters="ZIP archive (*.zip)"),
              F.integer("level", "Compression level", 6, minimum=0, maximum=9),
              F.flag("include_hidden", "Include hidden files", False)])
def zip_create(v, ctx):
    src = need_dir(v["folder"])
    target = out_path(v["output"], "archive.zip")
    if target.suffix.lower() != ".zip":
        target = target.with_suffix(".zip")
    count = 0
    total = 0
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=v["level"]) as zf:
        for path in iter_files(src, True, "*", skip_hidden=not v["include_hidden"]):
            arcname = str(path.relative_to(src))
            zf.write(path, arcname)
            count += 1
            total += path.stat().st_size
            if count % 50 == 0:
                ctx.check_cancel()
                ctx.progress(count)
    ctx.output(str(target))
    ratio = (1 - target.stat().st_size / total) * 100 if total else 0
    return (f"{count} file(s) · {human_size(total)} → {human_size(target.stat().st_size)} "
            f"({ratio:.0f}% smaller)")


@tool(id="zip-extract", name="Extract ZIP", category="Archives",
      summary="Unpack a ZIP safely — refuses entries that try to escape the folder.",
      keywords="unzip extract expand unpack",
      fields=[F.file("archive", "ZIP file", filters="ZIP archive (*.zip)"),
              F.folder("destination", "Extract into", required=False),
              F.flag("overwrite", "Overwrite existing files", False)])
def zip_extract(v, ctx):
    archive = need_file(v["archive"], "ZIP file")
    dest = Path(v["destination"]) if v["destination"].strip() else archive.parent / archive.stem
    dest.mkdir(parents=True, exist_ok=True)
    extracted = 0
    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
            target = _safe_member(member.filename, dest)
            if target.exists() and not v["overwrite"]:
                ctx.log(f"skip {member.filename}")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
            extracted += 1
            if extracted % 50 == 0:
                ctx.check_cancel()
    return f"Extracted {extracted} file(s) into {dest}"


@tool(id="archive-list", name="List Archive Contents", category="Archives",
      summary="Show every file inside a ZIP or TAR without extracting it.",
      keywords="list contents inspect archive entries",
      fields=[F.file("archive", "Archive", filters="Archives (*.zip *.tar *.gz *.tgz *.bz2)"),
              F.flag("sizes", "Include sizes and dates", True)])
def archive_list(v, ctx):
    path = need_file(v["archive"], "Archive")
    rows = []
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                rows.append({"name": info.filename,
                             "size": human_size(info.file_size),
                             "compressed": human_size(info.compress_size),
                             "modified": "%04d-%02d-%02d %02d:%02d" % info.date_time[:5]})
    elif tarfile.is_tarfile(path):
        with tarfile.open(path) as tf:
            for member in tf.getmembers():
                rows.append({"name": member.name, "size": human_size(member.size),
                             "compressed": "", "modified": stamp(member.mtime)})
    else:
        raise ToolError("Not a ZIP or TAR archive — try the 7-Zip tool")
    cols = ["name", "size", "compressed", "modified"] if v["sizes"] else ["name"]
    ctx.log(report_table(rows[:500], cols))
    return f"{len(rows)} entries in {path.name}"


@tool(id="archive-test", name="Test Archive Integrity", category="Archives",
      summary="Verify every entry in a ZIP reads back correctly and report corruption.",
      keywords="verify corrupt crc test integrity archive",
      fields=[F.file("archive", "ZIP file", filters="ZIP archive (*.zip)")])
def archive_test(v, ctx):
    path = need_file(v["archive"], "ZIP file")
    bad = []
    good = 0
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            try:
                with zf.open(info) as fh:
                    while fh.read(1 << 20):
                        pass
                good += 1
            except Exception as exc:  # noqa: BLE001 - report, do not crash
                bad.append((info.filename, str(exc)))
                ctx.log(f"✕ {info.filename}: {exc}")
    return {"archive": path.name, "healthy_entries": good, "corrupt_entries": len(bad),
            "verdict": "OK" if not bad else "CORRUPT"}


@tool(id="tar-create", name="Create TAR", category="Archives",
      summary="Pack a folder into a tar, tar.gz or tar.bz2 archive.",
      keywords="tar tarball gzip bzip2 pack linux",
      fields=[F.folder("folder", "Folder"),
              F.save("output", "Save archive as", required=True),
              F.choice("format", "Format", ["tar.gz", "tar", "tar.bz2"], "tar.gz")])
def tar_create(v, ctx):
    src = need_dir(v["folder"])
    fmt = v["format"]
    target = out_path(v["output"], f"{src.name}.{fmt}")
    mode = {"tar.gz": "w:gz", "tar": "w", "tar.bz2": "w:bz2"}[fmt]
    with tarfile.open(target, mode) as tf:
        tf.add(src, arcname=src.name)
    ctx.output(str(target))
    return f"Created {target.name} ({human_size(target.stat().st_size)})"


@tool(id="tar-extract", name="Extract TAR", category="Archives",
      summary="Unpack a tar, tar.gz or tar.bz2 archive, safely.",
      keywords="untar extract tar gz bz2 unpack",
      fields=[F.file("archive", "Archive"),
              F.folder("destination", "Extract into", required=False)])
def tar_extract(v, ctx):
    archive = need_file(v["archive"], "Archive")
    dest = Path(v["destination"]) if v["destination"].strip() else archive.parent
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    with tarfile.open(archive) as tf:
        for member in tf.getmembers():
            _safe_member(member.name, dest)
        tf.extractall(dest, filter="data") if hasattr(tarfile, "data_filter") else tf.extractall(dest)
        count = len([m for m in tf.getmembers() if m.isfile()])
    return f"Extracted {count} file(s) into {dest}"


@tool(id="gzip-file", name="Gzip / Gunzip", category="Archives",
      summary="Compress one file to .gz, or expand a .gz back to its original.",
      keywords="gzip gunzip compress decompress gz",
      fields=[F.file("path", "File"),
              F.choice("action", "Action", ["Compress", "Decompress"], "Compress")])
def gzip_file(v, ctx):
    src = need_file(v["path"])
    if v["action"] == "Compress":
        target = src.with_suffix(src.suffix + ".gz")
        with open(src, "rb") as fh, gzip.open(target, "wb", compresslevel=6) as out:
            shutil.copyfileobj(fh, out)
        ctx.output(str(target))
        ratio = (1 - target.stat().st_size / max(src.stat().st_size, 1)) * 100
        return f"{src.name}: {human_size(src.stat().st_size)} → {human_size(target.stat().st_size)} ({ratio:.0f}% smaller)"
    if src.suffix != ".gz":
        raise ToolError("That file is not a .gz archive")
    target = src.with_suffix("")
    with gzip.open(src, "rb") as fh, open(target, "wb") as out:
        shutil.copyfileobj(fh, out)
    ctx.output(str(target))
    return f"Expanded to {target.name} ({human_size(target.stat().st_size)})"


@tool(id="bzip2-file", name="Bzip2 / Bunzip2", category="Archives",
      summary="Compress a file with bzip2, or expand a .bz2 archive.",
      keywords="bzip2 bunzip2 compress bz2",
      fields=[F.file("path", "File"),
              F.choice("action", "Action", ["Compress", "Decompress"], "Compress")])
def bzip2_file(v, ctx):
    src = need_file(v["path"])
    if v["action"] == "Compress":
        target = src.with_suffix(src.suffix + ".bz2")
        target.write_bytes(bz2.compress(src.read_bytes(), compresslevel=9))
        ctx.output(str(target))
        return f"{src.name} → {target.name} ({human_size(target.stat().st_size)})"
    if src.suffix != ".bz2":
        raise ToolError("That file is not a .bz2 archive")
    target = src.with_suffix("")
    target.write_bytes(bz2.decompress(src.read_bytes()))
    ctx.output(str(target))
    return f"Expanded to {target.name} ({human_size(target.stat().st_size)})"


@tool(id="zip-add", name="Add Files to ZIP", category="Archives",
      summary="Append files or a folder to an existing ZIP without rebuilding it.",
      keywords="add append update zip insert",
      fields=[F.file("archive", "ZIP file", filters="ZIP archive (*.zip)"),
              F.folder("folder", "Folder to add", required=False),
              F.text("prefix", "Store inside subfolder", help="Optional")])
def zip_add(v, ctx):
    archive = need_file(v["archive"], "ZIP file")
    folder = need_dir(v["folder"])
    prefix = v["prefix"].strip().strip("/")
    added = 0
    with zipfile.ZipFile(archive, "a", zipfile.ZIP_DEFLATED) as zf:
        for path in iter_files(folder, True):
            arcname = str(path.relative_to(folder))
            if prefix:
                arcname = f"{prefix}/{arcname}"
            zf.write(path, arcname)
            added += 1
    return f"Added {added} file(s) to {archive.name}"


@tool(id="zip-remove", name="Remove From ZIP", category="Archives",
      summary="Delete matching entries from a ZIP, rewriting it without them.",
      keywords="remove delete entries zip strip",
      fields=[F.file("archive", "ZIP file", filters="ZIP archive (*.zip)"),
              F.text("pattern", "Remove entries containing", required=True),
              F.flag("apply", "Apply (otherwise preview)", False)])
def zip_remove(v, ctx):
    archive = need_file(v["archive"], "ZIP file")
    needle = v["pattern"].strip().lower()
    with zipfile.ZipFile(archive) as zf:
        keep = [i for i in zf.infolist() if needle not in i.filename.lower()]
        drop = [i for i in zf.infolist() if needle in i.filename.lower()]
        for info in drop:
            ctx.log(f"− {info.filename}")
        if not v["apply"]:
            return f"{len(drop)} entr(ies) would be removed (preview only)"
        if not drop:
            return "Nothing matched."
        temp = archive.with_suffix(".tmpzip")
        with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as out:
            for info in keep:
                if not info.is_dir():
                    out.writestr(info, zf.read(info.filename))
    temp.replace(archive)
    return f"Removed {len(drop)} entr(ies) from {archive.name}"


@tool(id="zip-split", name="Split ZIP by Size", category="Archives",
      summary="Create several smaller ZIPs so each one fits a size limit (email, uploads).",
      keywords="split zip parts size limit upload email",
      fields=[F.folder("folder", "Folder to zip"),
              F.number("part_mb", "Maximum size per part (MB)", 20.0, minimum=1.0, maximum=2048),
              F.folder("output", "Output folder", required=False)])
def zip_split(v, ctx):
    src = need_dir(v["folder"])
    limit = int(v["part_mb"] * 1024 * 1024)
    out_dir = Path(v["output"]) if v["output"].strip() else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(iter_files(src, True), key=lambda p: p.stat().st_size, reverse=True)
    parts: list[list[Path]] = [[]]
    size = 0
    for path in files:
        weight = path.stat().st_size
        if size + weight > limit and parts[-1]:
            parts.append([])
            size = 0
        parts[-1].append(path)
        size += weight
    made = []
    for index, group in enumerate(parts, start=1):
        target = out_dir / f"{src.name}-part{index:02d}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in group:
                zf.write(path, str(path.relative_to(src)))
        made.append(target)
        ctx.log(f"{target.name}  {len(group)} file(s)  {human_size(target.stat().st_size)}")
        ctx.output(str(target))
    return f"Created {len(made)} ZIP part(s) under {human_size(limit)} each"


@tool(id="sevenzip", name="7-Zip (Extract / Create)", category="Archives",
      summary="Handle 7z, RAR and other formats through 7-Zip if it is installed.",
      keywords="7z rar extract create archive",
      needs=("7z",),
      fields=[F.file("archive", "Archive (or source folder for create)", required=False),
              F.folder("folder", "Folder to compress", required=False),
              F.folder("destination", "Extract into / save to", required=False),
              F.choice("action", "Action", ["Extract", "Create"], "Extract"),
              F.text("password", "Password", help="Optional; passed to 7-Zip directly")])
def sevenzip(v, ctx):
    exe = shutil.which("7z") or shutil.which("7z.exe") or shutil.which("7za")
    if not exe:
        raise ToolError("7-Zip was not found on PATH")
    if v["action"] == "Extract":
        archive = need_file(v["archive"], "Archive")
        dest = v["destination"].strip() or str(archive.parent / archive.stem)
        args = [exe, "x", str(archive), f"-o{dest}", "-y"]
    else:
        folder = need_dir(v["folder"])
        dest = v["destination"].strip() or str(folder.parent / f"{folder.name}.7z")
        args = [exe, "a", dest, str(folder / "*"), "-y"]
    if v["password"]:
        args.append(f"-p{v['password']}")
    code, out, err = run_command(args, ctx=ctx, timeout=600)
    if code != 0:
        raise ToolError(f"7-Zip failed with code {code}: {err.strip()[:300]}")
    return "Done" if v["action"] == "Create" else f"Extracted into {dest}"


@tool(id="archive-report", name="Archive Report", category="Archives",
      summary="CSV listing of every entry in an archive, with sizes and compression ratio.",
      keywords="report csv archive audit listing",
      fields=[F.file("archive", "ZIP file", filters="ZIP archive (*.zip)"),
              F.save("report", "Save CSV to", required=True)])
def archive_report(v, ctx):
    archive = need_file(v["archive"], "ZIP file")
    from ._util import write_csv
    rows = []
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            ratio = (1 - info.compress_size / info.file_size) * 100 if info.file_size else 0
            rows.append({"name": info.filename, "bytes": info.file_size,
                         "compressed_bytes": info.compress_size,
                         "saved_percent": round(ratio, 1)})
    target = write_csv(out_path(v["report"], "archive-report.csv"), rows)
    ctx.output(str(target))
    return f"{len(rows)} entries written to {target}"
