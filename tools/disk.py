"""Disk — space, drives, cleanup and health."""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import (
    IS_WINDOWS,
    human_size,
    iter_files,
    need_dir,
    out_path,
    report_table,
    run_command,
    stamp,
    which,
)


def _powershell(script: str, ctx=None, timeout: int = 180) -> str:
    exe = which("powershell") or which("powershell.exe") or which("pwsh")
    if not exe:
        raise ToolError("PowerShell was not found")
    code, out, err = run_command([exe, "-NoProfile", "-NonInteractive", "-Command", script],
                                 ctx=ctx, timeout=timeout)
    if code != 0 and not out.strip():
        raise ToolError(f"PowerShell failed: {err.strip()[:300]}")
    return out


@tool(id="disk-space", name="Disk Space", category="Disk",
      summary="Every drive with total, used and free space, and how full it is.",
      fields=[])
def disk_space(v, ctx):
    rows = []
    if IS_WINDOWS:
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            root = Path(f"{letter}:\\")
            if root.exists():
                try:
                    usage = shutil.disk_usage(root)
                except OSError:
                    continue
                rows.append({"drive": f"{letter}:", "total": human_size(usage.total),
                             "used": human_size(usage.used), "free": human_size(usage.free),
                             "full": f"{usage.used / usage.total * 100:.0f}%"})
    else:
        for mount in ("/", "/home", "/tmp"):
            root = Path(mount)
            if not root.exists():
                continue
            try:
                usage = shutil.disk_usage(root)
            except OSError:
                continue
            rows.append({"drive": mount, "total": human_size(usage.total),
                         "used": human_size(usage.used), "free": human_size(usage.free),
                         "full": f"{usage.used / usage.total * 100:.0f}%"})
    if not rows:
        raise ToolError("No drives could be read")
    ctx.log(report_table(rows, ["drive", "total", "used", "free", "full"]))
    return f"{len(rows)} drive(s)"


@tool(id="folder-size-tree", name="Folder Size Tree", category="Disk",
      summary="Recursive sizes for a folder tree — where the space actually goes.",
      fields=[F.folder("folder", "Folder"),
              F.integer("depth", "Depth", 2, minimum=1, maximum=6),
              F.integer("top", "Show top entries per level", 10, minimum=1, maximum=100)])
def folder_size_tree(v, ctx):
    root = need_dir(v["folder"])

    def size_of(folder: Path, level: int) -> int:
        total = 0
        try:
            entries = list(folder.iterdir())
        except OSError:
            return 0
        for entry in entries:
            ctx.check_cancel()
            try:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir() and level < v["depth"]:
                    total += size_of(entry, level + 1)
                elif entry.is_dir():
                    total += sum(f.stat().st_size for f in iter_files(entry) if f.exists())
            except OSError:
                continue
        return total

    children = []
    for entry in root.iterdir():
        if entry.is_dir():
            size = size_of(entry, 1)
            children.append((size, entry.name + "/"))
    children.sort(reverse=True)
    rows = [{"folder": name, "size": human_size(size)} for size, name in children[:v["top"]]]
    ctx.log(report_table(rows, ["folder", "size"]))
    total = sum(size for size, _ in children)
    return f"{root}: {human_size(total)} across {len(children)} folder(s)"


@tool(id="big-folders", name="Biggest Folders", category="Disk",
      summary="Rank subfolders by total size at any depth — find the real space hogs.",
      fields=[F.folder("folder", "Folder to scan"),
              F.integer("depth", "Depth", 2, minimum=1, maximum=5),
              F.integer("top", "Show top", 15, minimum=1, maximum=100)])
def big_folders(v, ctx):
    root = need_dir(v["folder"])
    totals: dict[str, int] = {}

    def walk(folder: Path, depth: int, label: str) -> int:
        total = 0
        try:
            entries = list(folder.iterdir())
        except OSError:
            return 0
        for entry in entries:
            ctx.check_cancel()
            try:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    if depth < v["depth"]:
                        total += walk(entry, depth + 1, label or entry.name)
                    else:
                        sub = sum(f.stat().st_size for f in iter_files(entry) if f.exists())
                        totals[str(entry.relative_to(root))] = sub
                        total += sub
            except OSError:
                continue
        return total

    grand = walk(root, 0, "")
    rows = [{"folder": name, "size": human_size(size)}
            for name, size in sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:v["top"]]]
    ctx.log(report_table(rows, ["folder", "size"]))
    return f"{human_size(grand)} total in {root}"


@tool(id="old-files", name="Old Files", category="Disk",
      summary="Files not modified for a long time — the safest things to archive or delete.",
      fields=[F.folder("folder", "Folder"),
              F.integer("days", "Not modified for (days)", 365, minimum=1, maximum=7300),
              F.number("min_mb", "Ignore files smaller than (MB)", 1.0, minimum=0.0),
              F.integer("limit", "Show", 50, minimum=1, maximum=1000),
              F.save("report", "Save CSV to", required=False)])
def old_files(v, ctx):
    from ._util import write_csv
    root = need_dir(v["folder"])
    cutoff = time.time() - v["days"] * 86400
    found = []
    for path in iter_files(root, True):
        try:
            stat = path.stat()
        except OSError:
            continue
        if stat.st_mtime < cutoff and stat.st_size >= v["min_mb"] * 1024 * 1024:
            found.append({"modified": stamp(stat.st_mtime), "size": human_size(stat.st_size),
                          "name": path.name, "folder": str(path.parent), "bytes": stat.st_size})
        if len(found) % 100 == 0 and found:
            ctx.check_cancel()
    found.sort(key=lambda row: row["bytes"], reverse=True)
    ctx.log(report_table(found[:v["limit"]], ["modified", "size", "name", "folder"]))
    if v["report"].strip():
        target = write_csv(out_path(v["report"], "old-files.csv"), found)
        ctx.output(str(target))
    return f"{len(found)} file(s) untouched for {v['days']} days, {human_size(sum(r['bytes'] for r in found))}"


@tool(id="file-age-report", name="File Age Report", category="Disk",
      summary="How many files fall into each age bucket, and how much space they take.",
      fields=[F.folder("folder", "Folder")])
def file_age_report(v, ctx):
    root = need_dir(v["folder"])
    buckets = [("Today", 1), ("This week", 7), ("This month", 30), ("This year", 365),
               ("Older", 100000)]
    counts = {label: {"files": 0, "bytes": 0} for label, _ in buckets}
    now = time.time()
    for path in iter_files(root, True):
        try:
            age_days = (now - path.stat().st_mtime) / 86400
            size = path.stat().st_size
        except OSError:
            continue
        for label, limit in buckets:
            if age_days <= limit:
                counts[label]["files"] += 1
                counts[label]["bytes"] += size
                break
        ctx.check_cancel()
    rows = [{"age": label, "files": data["files"], "size": human_size(data["bytes"])}
            for label, data in counts.items()]
    ctx.log(report_table(rows, ["age", "files", "size"]))
    return f"{sum(r['files'] for r in rows)} file(s) in {root}"


@tool(id="file-count", name="Count Files and Folders", category="Disk",
      summary="How many files and folders sit under a path, at any depth.",
      fields=[F.folder("folder", "Folder"),
              F.text("pattern", "Only files matching", "*")])
def file_count(v, ctx):
    root = need_dir(v["folder"])
    files = 0
    total = 0
    for path in iter_files(root, True, v["pattern"] or "*"):
        files += 1
        try:
            total += path.stat().st_size
        except OSError:
            pass
        if files % 500 == 0:
            ctx.progress(files % 100, f"{files} files")
            ctx.check_cancel()
    folders = sum(1 for _ in os.walk(root))
    return {"folder": str(root), "files": files, "folders": folders - 1,
            "total_size": human_size(total)}


@tool(id="cleanup-report", name="Cleanup Opportunities", category="Disk",
      summary="Sizes of the usual junk folders — temp, caches, downloads, recycle bin.",
      fields=[F.flag("include_downloads", "Include the Downloads folder", True)])
def cleanup_report(v, ctx):
    home = Path.home()
    candidates = {
        "Windows Temp": Path(os.environ.get("WINDIR", "C:\\Windows")) / "Temp" if IS_WINDOWS else Path("/tmp"),
        "User Temp": Path(tempfile.gettempdir()),
        "Downloads": home / "Downloads",
        "Windows Prefetch": Path(os.environ.get("WINDIR", "C:\\Windows")) / "Prefetch" if IS_WINDOWS else None,
        "SoftwareDistribution": Path(os.environ.get("WINDIR", "C:\\Windows")) / "SoftwareDistribution/Download" if IS_WINDOWS else None,
        "Chrome cache": home / "AppData/Local/Google/Chrome/User Data/Default/Cache" if IS_WINDOWS else home / ".cache/google-chrome",
        "Edge cache": home / "AppData/Local/Microsoft/Edge/User Data/Default/Cache" if IS_WINDOWS else home / ".cache/microsoft-edge",
        "pip cache": home / "AppData/Local/pip/Cache" if IS_WINDOWS else home / ".cache/pip",
        "npm cache": home / "AppData/Local/npm-cache" if IS_WINDOWS else home / ".npm",
    }
    if not v["include_downloads"]:
        candidates.pop("Downloads", None)
    rows = []
    total = 0
    for label, folder in candidates.items():
        if folder is None or not Path(folder).is_dir():
            continue
        size = 0
        count = 0
        for path in iter_files(Path(folder), True):
            try:
                size += path.stat().st_size
                count += 1
            except OSError:
                continue
        rows.append({"location": label, "files": count, "size": human_size(size), "path": str(folder)})
        total += size
        ctx.check_cancel()
    rows.sort(key=lambda row: row["files"], reverse=True)
    ctx.log(report_table(rows, ["location", "files", "size"]))
    return f"{human_size(total)} in cleanable caches and temporary files"


@tool(id="temp-clean", name="Clean Temporary Files", category="Disk",
      summary="Delete files from the temp folders, skipping anything in use.",
      destructive=True,
      fields=[F.flag("user_temp", "Clean the user temp folder", True),
              F.flag("windows_temp", "Clean the Windows temp folder", True),
              F.flag("preview", "Preview only (recommended first)", True)])
def temp_clean(v, ctx):
    targets = []
    if v["user_temp"]:
        targets.append(Path(tempfile.gettempdir()))
    if v["windows_temp"] and IS_WINDOWS:
        targets.append(Path(os.environ.get("WINDIR", "C:\\Windows")) / "Temp")
    if not targets:
        raise ToolError("Choose at least one folder to clean")
    removed = 0
    freed = 0
    skipped = 0
    for folder in targets:
        if not folder.is_dir():
            continue
        for path in folder.iterdir():
            ctx.check_cancel()
            try:
                if path.is_file():
                    size = path.stat().st_size
                    if v["preview"]:
                        ctx.log(f"would delete {path.name}  ({human_size(size)})")
                    else:
                        path.unlink()
                        removed += 1
                        freed += size
                elif path.is_dir():
                    if v["preview"]:
                        ctx.log(f"would delete folder {path.name}/")
                    else:
                        shutil.rmtree(path, ignore_errors=True)
                        removed += 1
            except OSError:
                skipped += 1
    if v["preview"]:
        return "Preview only — nothing was deleted. Untick preview to clean."
    return f"Removed {removed} item(s), freeing {human_size(freed)} ({skipped} in use, skipped)"


@tool(id="recycle-bin", name="Empty Recycle Bin", category="Disk",
      summary="Clear the Windows Recycle Bin and report how much space that frees.",
      platforms=("win",), destructive=True,
      fields=[F.flag("confirm", "Yes, empty it", False)])
def recycle_bin(v, ctx):
    if not v["confirm"]:
        return "Tick the confirmation box to empty the Recycle Bin"
    out = _powershell("$s=(Get-ChildItem 'C:\\$Recycle.Bin' -Recurse -Force "
                      "-ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum; "
                      "Clear-RecycleBin -Force -ErrorAction SilentlyContinue; "
                      "[math]::Round($s/1MB,1)", ctx=ctx, timeout=180)
    return f"Recycle Bin emptied (about {out.strip() or '0'} MB reclaimed)"


@tool(id="disk-health", name="Disk Health (S.M.A.R.T.)", category="Disk",
      summary="Physical disk health, media type and whether SMART predicts a failure.",
      platforms=("win",),
      fields=[])
def disk_health(v, ctx):
    import json as jsonlib
    out = _powershell("Get-PhysicalDisk | Select-Object FriendlyName,MediaType,HealthStatus,"
                      "OperationalStatus,Size | ConvertTo-Json -Depth 2", ctx=ctx, timeout=180)
    data = jsonlib.loads(out or "[]")
    if isinstance(data, dict):
        data = [data]
    rows = [{"disk": str(item.get("FriendlyName", ""))[:40],
             "type": str(item.get("MediaType", "")),
             "health": str(item.get("HealthStatus", "")),
             "status": str(item.get("OperationalStatus", "")),
             "size": human_size(item.get("Size", 0) or 0)} for item in data]
    ctx.log(report_table(rows, ["disk", "type", "health", "status", "size"]))
    unhealthy = sum(1 for row in rows if row["health"] not in ("Healthy", ""))
    return f"{len(rows)} disk(s), {unhealthy} reporting a problem"


@tool(id="partition-list", name="Partitions", category="Disk",
      summary="Partitions with their sizes, filesystems and drive letters.",
      fields=[])
def partition_list(v, ctx):
    if IS_WINDOWS:
        import json as jsonlib
        out = _powershell("Get-Partition | Select-Object DiskNumber,PartitionNumber,DriveLetter,"
                          "Size,Type | ConvertTo-Json -Depth 2", ctx=ctx, timeout=180)
        data = jsonlib.loads(out or "[]")
        if isinstance(data, dict):
            data = [data]
        rows = [{"disk": item.get("DiskNumber"), "partition": item.get("PartitionNumber"),
                 "letter": item.get("DriveLetter") or "-",
                 "size": human_size(item.get("Size", 0) or 0),
                 "type": str(item.get("Type", ""))[:20]} for item in data]
    else:
        code, out, _ = run_command(["lsblk", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINT"], timeout=60)
        ctx.log(out)
        return f"{max(0, len(out.splitlines()) - 1)} block device(s)"
    ctx.log(report_table(rows, ["disk", "partition", "letter", "size", "type"]))
    return f"{len(rows)} partition(s)"


@tool(id="volume-info", name="Volume Information", category="Disk",
      summary="Volume labels, filesystems, serial numbers and free space.",
      fields=[])
def volume_info(v, ctx):
    if IS_WINDOWS:
        import json as jsonlib
        out = _powershell("Get-Volume | Select-Object DriveLetter,FileSystemLabel,FileSystem,"
                          "HealthStatus,SizeRemaining,Size | ConvertTo-Json -Depth 2",
                          ctx=ctx, timeout=180)
        data = jsonlib.loads(out or "[]")
        if isinstance(data, dict):
            data = [data]
        rows = [{"volume": item.get("DriveLetter") or "-",
                 "label": str(item.get("FileSystemLabel", "")),
                 "filesystem": str(item.get("FileSystem", "")),
                 "health": str(item.get("HealthStatus", "")),
                 "free": human_size(item.get("SizeRemaining", 0) or 0),
                 "size": human_size(item.get("Size", 0) or 0)} for item in data]
    else:
        code, out, _ = run_command(["df", "-hT"], timeout=60)
        ctx.log(out)
        return "Volumes listed above"
    ctx.log(report_table(rows, ["volume", "label", "filesystem", "health", "free", "size"]))
    return f"{len(rows)} volume(s)"


@tool(id="ntfs-streams", name="NTFS Alternate Streams", category="Disk",
      summary="Find hidden alternate data streams that can conceal files on NTFS.",
      platforms=("win",),
      fields=[F.folder("folder", "Folder")])
def ntfs_streams(v, ctx):
    root = need_dir(v["folder"])
    code, out, err = run_command(["cmd", "/c", "dir", "/s", "/r", str(root)],
                                 ctx=ctx, timeout=300)
    hits = [line.strip() for line in out.splitlines()
            if ":" in line and "$DATA" not in line and "Directory" not in line
            and line.count(":") > 1]
    if not hits:
        return "No alternate data streams found."
    ctx.log("\n".join(hits[:100]))
    return f"{len(hits)} line(s) mentioning alternate streams"


@tool(id="usb-devices", name="USB Devices", category="Disk",
      summary="Connected USB devices with their status — spot unknown sticks and gadgets.",
      platforms=("win",),
      fields=[])
def usb_devices(v, ctx):
    import json as jsonlib
    out = _powershell("Get-PnpDevice -Class USB -Status OK | Select-Object FriendlyName,"
                      "InstanceId,Status | ConvertTo-Json -Depth 2", ctx=ctx, timeout=180)
    data = jsonlib.loads(out or "[]")
    if isinstance(data, dict):
        data = [data]
    rows = [{"device": str(item.get("FriendlyName", ""))[:50],
             "status": str(item.get("Status", "")),
             "id": str(item.get("InstanceId", ""))[:40]} for item in data]
    ctx.log(report_table(rows, ["device", "status", "id"]))
    return f"{len(rows)} USB device(s)"


@tool(id="disk-speed-test", name="Disk Speed Test", category="Disk",
      summary="Measure sequential write and read speed on a drive with a temporary file.",
      fields=[F.folder("folder", "Folder to test in", required=False,
                       help="Blank uses the system temp folder"),
              F.integer("size_mb", "Test file size (MB)", 64, minimum=4, maximum=1024)])
def disk_speed_test(v, ctx):
    folder = Path(v["folder"]) if v["folder"].strip() else Path(tempfile.gettempdir())
    if not folder.is_dir():
        raise ToolError(f"{folder} is not a folder")
    size = v["size_mb"] * 1024 * 1024
    block = b"\0" * (1 << 20)
    target = folder / ".all4one-speedtest.bin"
    try:
        started = time.perf_counter()
        with open(target, "wb") as handle:
            for _ in range(v["size_mb"]):
                handle.write(block)
            handle.flush()
            os.fsync(handle.fileno())
        write_seconds = time.perf_counter() - started
        started = time.perf_counter()
        with open(target, "rb") as handle:
            while handle.read(1 << 20):
                pass
        read_seconds = time.perf_counter() - started
    finally:
        try:
            target.unlink()
        except OSError:
            pass
    return {
        "folder": str(folder),
        "file_size": human_size(size),
        "write_mb_per_s": round(v["size_mb"] / max(write_seconds, 0.001), 1),
        "read_mb_per_s": round(v["size_mb"] / max(read_seconds, 0.001), 1),
    }


@tool(id="free-space-alert", name="Free Space Check", category="Disk",
      summary="Flag any drive that is below a percentage you consider safe.",
      fields=[F.integer("threshold", "Warn below", 15, minimum=1, maximum=99, suffix="%")])
def free_space_alert(v, ctx):
    rows = []
    if IS_WINDOWS:
        letters = [f"{letter}:\\" for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ" if Path(f"{letter}:\\").exists()]
    else:
        letters = ["/", "/home"]
    for root in letters:
        try:
            usage = shutil.disk_usage(root)
        except OSError:
            continue
        percent = usage.free / usage.total * 100
        rows.append({"drive": root, "free": human_size(usage.free),
                     "free_percent": f"{percent:.0f}%",
                     "status": "LOW" if percent < v["threshold"] else "ok"})
    ctx.log(report_table(rows, ["drive", "free", "free_percent", "status"]))
    low = sum(1 for row in rows if row["status"] == "LOW")
    return f"{low} drive(s) below {v['threshold']}% free"


@tool(id="shadow-copies", name="Shadow Copies", category="Disk",
      summary="Volume shadow copies / restore points available for rollback.",
      platforms=("win",),
      fields=[])
def shadow_copies(v, ctx):
    code, out, err = run_command(["vssadmin", "list", "shadows"], ctx=ctx, timeout=180)
    if code != 0:
        raise ToolError("vssadmin needs administrator rights, or has no shadow copies")
    ctx.log(out.strip()[:3000])
    return "Shadow copies listed above"
