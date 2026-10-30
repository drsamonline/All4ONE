"""System — machine information, processes, services, registry and Windows settings."""

from __future__ import annotations

import json as jsonlib
import os
import platform
import sys
import time
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import IS_WINDOWS, human_size, out_path, report_table, run_command, which

WIN = ("win",)


def _json_list(text: str) -> list:
    """PowerShell ConvertTo-Json output -> list, tolerating an empty result."""
    stripped = (text or "").strip()
    if not stripped:
        return []
    try:
        data = jsonlib.loads(stripped)
    except ValueError as exc:
        raise ToolError(f"Could not read the PowerShell output: {exc}") from exc
    if isinstance(data, dict):
        return [data]
    return data if isinstance(data, list) else []


def _powershell(script: str, ctx=None, timeout: int = 120, lenient: bool = False) -> str:
    exe = which("powershell") or which("powershell.exe") or which("pwsh")
    if not exe:
        raise ToolError("PowerShell was not found — this tool needs Windows PowerShell")
    code, out, err = run_command([exe, "-NoProfile", "-NonInteractive", "-Command", script],
                                 ctx=ctx, timeout=timeout)
    if code != 0 and not out.strip() and not lenient:
        raise ToolError(f"PowerShell failed: {err.strip()[:300]}")
    return out


def _ps_json(script: str, ctx=None, timeout: int = 180) -> list:
    """Run a ConvertTo-Json query. Finding nothing is an empty list, not an error.

    A machine with no USB devices, no printers or no matching event log entries
    makes several of these cmdlets write to the error stream and exit non-zero.
    That is a valid answer, so the query is run leniently and the output parsed.
    """
    return _json_list(_powershell(script, ctx=ctx, timeout=timeout, lenient=True))


# --------------------------------------------------------------------------
# Machine information
# --------------------------------------------------------------------------
@tool(id="system-info", name="System Information", category="System",
      summary="Operating system, CPU, memory, uptime and Python runtime in one view.",
      fields=[])
def system_info(v, ctx):
    info = {
        "computer": platform.node(),
        "operating_system": f"{platform.system()} {platform.release()}",
        "version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor() or "(not reported)",
        "cpu_cores": os.cpu_count(),
        "python": sys.version.split()[0],
        "user": os.environ.get("USERNAME") or os.environ.get("USER") or "",
        "home": str(Path.home()),
    }
    try:
        import psutil
        memory = psutil.virtual_memory()
        info["memory_total"] = human_size(memory.total)
        info["memory_available"] = human_size(memory.available)
        info["uptime"] = f"{int((time.time() - psutil.boot_time()) // 3600)} hours"
    except ImportError:
        info["memory_total"] = "(install psutil for memory details)"
    ctx.log(report_table([{"field": k, "value": str(val)} for k, val in info.items()]))
    return info


@tool(id="uptime", name="Uptime", category="System",
      summary="How long since the machine last booted, and when that was.",
      fields=[])
def uptime(v, ctx):
    if IS_WINDOWS:
        # Ask PowerShell for elapsed seconds and the ISO stamp: the default
        # rendering of LastBootUpTime is culture-formatted and unparseable.
        out = _powershell(
            "$b=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime; "
            "[math]::Round(((Get-Date)-$b).TotalSeconds); $b.ToString('yyyy-MM-ddTHH:mm:ss')",
            lenient=True)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        try:
            seconds = float(lines[0])
        except (IndexError, ValueError) as exc:
            raise ToolError(f"Could not read the boot time: {out.strip()[:80]}") from exc
        boot_stamp = lines[1] if len(lines) > 1 else ""
        return {"last_boot": boot_stamp,
                "uptime": f"{int(seconds // 86400)}d {int(seconds % 86400 // 3600)}h "
                          f"{int(seconds % 3600 // 60)}m",
                "seconds": int(seconds)}
    with open("/proc/uptime", encoding="utf-8") as handle:
        seconds = float(handle.read().split()[0])
    return {"uptime": f"{int(seconds // 86400)}d {int(seconds % 86400 // 3600)}h "
                      f"{int(seconds % 3600 // 60)}m", "seconds": int(seconds)}


@tool(id="env-variables", name="Environment Variables", category="System",
      summary="List the environment this app runs with, or look up one variable.",
      fields=[F.text("filter", "Only names containing", help="Leave blank for everything"),
              F.text("name", "Show the value of", help="One exact variable name")])
def env_variables(v, ctx):
    if v["name"].strip():
        key = v["name"].strip()
        if key not in os.environ:
            raise ToolError(f"{key} is not set")
        return {key: os.environ[key]}
    needle = v["filter"].strip().lower()
    rows = [{"name": key, "value": value[:120]}
            for key, value in sorted(os.environ.items())
            if not needle or needle in key.lower()]
    ctx.log(report_table(rows))
    return f"{len(rows)} variable(s)"


@tool(id="path-audit", name="PATH Audit", category="System",
      summary="Check every PATH entry: which exist, which are duplicates and what is missing.",
      fields=[F.flag("duplicates_only", "Show only problems", False)])
def path_audit(v, ctx):
    entries = [p for p in os.environ.get("PATH", "").split(os.pathsep) if p.strip()]
    seen: dict[str, int] = {}
    rows = []
    for entry in entries:
        normalised = os.path.normcase(os.path.normpath(entry))
        seen[normalised] = seen.get(normalised, 0) + 1
        exists = os.path.isdir(entry)
        rows.append({"entry": entry, "exists": "yes" if exists else "MISSING",
                     "duplicate": "yes" if seen[normalised] > 1 else ""})
    if v["duplicates_only"]:
        rows = [r for r in rows if r["exists"] == "MISSING" or r["duplicate"]]
    ctx.log(report_table(rows[:120], ["entry", "exists", "duplicate"]))
    missing = sum(1 for r in rows if r["exists"] == "MISSING")
    return f"{len(entries)} PATH entries, {missing} missing, " \
           f"{len(entries) - len(seen)} duplicate(s)"


@tool(id="temp-path", name="Temp Folder Info", category="System",
      summary="Where temporary files live and how much space they are using.",
      fields=[])
def temp_path(v, ctx):
    import tempfile
    folder = Path(tempfile.gettempdir())
    total = 0
    count = 0
    for path in folder.rglob("*"):
        try:
            if path.is_file():
                total += path.stat().st_size
                count += 1
        except OSError:
            continue
    return {"temp_folder": str(folder), "files": count, "size": human_size(total)}


# --------------------------------------------------------------------------
# Processes
# --------------------------------------------------------------------------
@tool(id="process-list", name="Process List", category="System",
      summary="Running processes with PID, memory and CPU — sorted by what is heaviest.",
      fields=[F.text("filter", "Only names containing"),
              F.choice("sort", "Sort by", ["Memory", "Name", "PID", "CPU"], "Memory"),
              F.integer("limit", "Show", 40, minimum=1, maximum=500)])
def process_list(v, ctx):
    rows = []
    try:
        import psutil
        for process in psutil.process_iter(["pid", "name", "memory_info", "username"]):
            try:
                info = process.info
                rows.append({
                    "pid": info["pid"],
                    "name": info["name"] or "",
                    "memory_mb": round((info["memory_info"].rss if info["memory_info"] else 0) / 1_048_576, 1),
                    "user": (info["username"] or "")[:24],
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except ImportError:
        if IS_WINDOWS:
            data = _ps_json("Get-Process | Select-Object Id,ProcessName,"
                            "@{n='WS';e={[math]::Round($_.WS/1MB,1)}} | ConvertTo-Json")
            rows = [{"pid": item.get("Id"), "name": item.get("ProcessName", ""),
                     "memory_mb": item.get("WS", 0), "user": ""} for item in data]
        else:
            code, out, _ = run_command(["ps", "-eo", "pid,rss,comm"], timeout=30)
            for line in out.splitlines()[1:]:
                parts = line.split(None, 2)
                if len(parts) == 3:
                    rows.append({"pid": int(parts[0]), "name": parts[2][:40],
                                 "memory_mb": round(int(parts[1]) / 1024, 1), "user": ""})
    needle = v["filter"].strip().lower()
    if needle:
        rows = [row for row in rows if needle in str(row["name"]).lower()]
    key = {"Memory": "memory_mb", "Name": "name", "PID": "pid", "CPU": "memory_mb"}[v["sort"]]
    reverse = v["sort"] in ("Memory", "CPU")
    rows.sort(key=lambda row: (str(row[key]).lower() if key == "name" else row[key]), reverse=reverse)
    ctx.log(report_table(rows[:v["limit"]], ["pid", "name", "memory_mb", "user"]))
    total = sum(row["memory_mb"] for row in rows)
    return f"{len(rows)} process(es), {total:.0f} MB in view"


@tool(id="process-find", name="Find a Process", category="System",
      summary="Locate every process with a given name and show its executable path.",
      fields=[F.text("name", "Process name", "chrome", required=True)])
def process_find(v, ctx):
    needle = v["name"].strip().lower()
    hits = []
    try:
        import psutil
        for process in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
            try:
                if needle in (process.info["name"] or "").lower():
                    hits.append({"pid": process.info["pid"], "name": process.info["name"],
                                 "exe": process.info["exe"] or "",
                                 "started": time.strftime("%H:%M:%S",
                                                          time.localtime(process.create_time()))})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except ImportError:
        if IS_WINDOWS:
            data = _ps_json(f"Get-Process -Name '*{needle}*' | "
                            "Select-Object Id,ProcessName,Path | ConvertTo-Json")
            hits = [{"pid": item.get("Id"), "name": item.get("ProcessName"),
                     "exe": item.get("Path", ""), "started": ""} for item in data]
        else:
            code, out, _ = run_command(["ps", "-eo", "pid,comm,args"], timeout=30)
            for line in out.splitlines()[1:]:
                if needle in line.lower():
                    parts = line.split(None, 2)
                    hits.append({"pid": int(parts[0]), "name": parts[1],
                                 "exe": parts[2][:80] if len(parts) > 2 else "", "started": ""})
    if not hits:
        return f"No process matching {v['name']!r} is running."
    ctx.log(report_table(hits, ["pid", "name", "started", "exe"]))
    return f"{len(hits)} matching process(es)"


@tool(id="process-kill", name="End a Process", category="System",
      summary="Stop a process by PID or name — you are asked to confirm the exact target.",
      destructive=True,
      fields=[F.text("target", "PID or process name", required=True),
              F.flag("confirm", "Yes, end it", False)])
def process_kill(v, ctx):
    target = v["target"].strip()
    if not v["confirm"]:
        return f"Would end {target!r}. Tick the confirmation box to do it."
    if target.isdigit():
        if IS_WINDOWS:
            code, _, err = run_command(["taskkill", "/PID", target, "/F"], ctx=ctx, timeout=60)
        else:
            code, _, err = run_command(["kill", "-9", target], ctx=ctx, timeout=60)
        if code != 0:
            raise ToolError(f"Could not end PID {target}: {err.strip()[:150]}")
        return f"Ended process {target}"
    name = target if target.lower().endswith(".exe") or not IS_WINDOWS else target + ".exe"
    if IS_WINDOWS:
        code, _, err = run_command(["taskkill", "/IM", name, "/F"], ctx=ctx, timeout=60)
    else:
        code, _, err = run_command(["pkill", "-f", name], ctx=ctx, timeout=60)
    if code != 0:
        raise ToolError(f"Could not end {name}: {err.strip()[:150]}")
    return f"Ended every process named {name}"


# --------------------------------------------------------------------------
# Startup, services, tasks
# --------------------------------------------------------------------------
@tool(id="startup-items", name="Startup Programs", category="System",
      summary="Everything that launches at login — registry Run keys and the startup folder.",
      platforms=WIN,
      fields=[F.flag("details", "Include the command line", True)])
def startup_items(v, ctx):
    script = ("$paths='HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',"
              "'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',"
              "'HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Run';"
              "$out=@(); foreach($p in $paths){ if(Test-Path $p){ "
              "Get-ItemProperty $p | Get-Member -MemberType NoteProperty | "
              "Where-Object {$_.Name -notlike 'PS*'} | ForEach-Object { "
              "$out += [pscustomobject]@{Name=$_.Name; Command=(Get-ItemProperty $p).($_.Name); "
              "Source=$p} } } }; $out | ConvertTo-Json -Depth 3")
    data = _ps_json(script, ctx=ctx)
    rows = [{"name": item.get("Name", ""),
             "command": item.get("Command", "") if v["details"] else "",
             "source": "HKCU" if "HKCU" in str(item.get("Source", "")) else "HKLM"} for item in data]
    folder = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Startup"
    if folder.is_dir():
        for item in folder.iterdir():
            rows.append({"name": item.name, "command": str(item), "source": "Startup folder"})
    ctx.log(report_table(rows, ["name", "source", "command"]))
    return f"{len(rows)} startup item(s)"


@tool(id="services-list", name="Windows Services", category="System",
      summary="Installed services with their state and start mode, running ones first.",
      platforms=WIN,
      fields=[F.text("filter", "Only names containing"),
              F.choice("state", "Show", ["All", "Running", "Stopped"], "All")])
def services_list(v, ctx):
    data = _ps_json("Get-Service | Select-Object Name,DisplayName,Status,StartType | "
                    "ConvertTo-Json -Depth 2", ctx=ctx)
    needle = v["filter"].strip().lower()
    rows = []
    for item in data:
        name = item.get("Name", "")
        if needle and needle not in name.lower() and needle not in str(item.get("DisplayName", "")).lower():
            continue
        state = str(item.get("Status", ""))
        if v["state"] != "All" and state != v["state"]:
            continue
        rows.append({"name": name, "display": str(item.get("DisplayName", ""))[:40],
                     "state": state, "start": str(item.get("StartType", ""))})
    rows.sort(key=lambda row: (row["state"] != "Running", row["name"].lower()))
    ctx.log(report_table(rows[:150], ["name", "state", "start", "display"]))
    return f"{len(rows)} service(s)"


@tool(id="service-control", name="Start / Stop a Service", category="System",
      summary="Start, stop or restart a Windows service by name — administrator rights needed.",
      platforms=WIN, destructive=True,
      fields=[F.text("name", "Service name", "Spooler", required=True),
              F.choice("action", "Action", ["Start", "Stop", "Restart"], "Restart"),
              F.flag("confirm", "Yes, do it", False)])
def service_control(v, ctx):
    if not v["confirm"]:
        return f"Would {v['action'].lower()} {v['name']!r}. Tick the confirmation box."
    out = _powershell(f"{v['action']}-Service -Name '{v['name']}' -ErrorAction Stop; "
                      f"(Get-Service -Name '{v['name']}').Status", ctx=ctx, timeout=180)
    return f"{v['name']} → {out.strip().splitlines()[-1] if out.strip() else 'done'}"


@tool(id="scheduled-tasks", name="Scheduled Tasks", category="System",
      summary="Windows scheduled tasks with their state, trigger time and action.",
      platforms=WIN,
      fields=[F.text("filter", "Only names containing"),
              F.flag("ready_only", "Only enabled tasks", False)])
def scheduled_tasks(v, ctx):
    data = _ps_json("Get-ScheduledTask | Select-Object TaskName,TaskPath,State | "
                    "ConvertTo-Json -Depth 2", ctx=ctx)
    needle = v["filter"].strip().lower()
    rows = []
    for item in data:
        name = str(item.get("TaskName", ""))
        path = str(item.get("TaskPath", ""))
        if needle and needle not in name.lower() and needle not in path.lower():
            continue
        state = str(item.get("State", ""))
        if v["ready_only"] and state != "Ready":
            continue
        rows.append({"name": name[:50], "state": state, "folder": path[:40]})
    rows.sort(key=lambda row: row["name"].lower())
    ctx.log(report_table(rows[:150], ["name", "state", "folder"]))
    return f"{len(rows)} task(s)"


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------
HIVES = ["HKEY_CURRENT_USER", "HKEY_LOCAL_MACHINE", "HKEY_CLASSES_ROOT",
         "HKEY_USERS", "HKEY_CURRENT_CONFIG"]


@tool(id="registry-read", name="Read the Registry", category="System",
      summary="Show the values in a registry key, or one value if you name it.",
      platforms=WIN,
      fields=[F.choice("hive", "Hive", HIVES, "HKEY_CURRENT_USER"),
              F.text("path", "Key path", r"Software\Microsoft\Windows\CurrentVersion\Run",
                     required=True),
              F.text("value", "Value name", help="Leave blank for all values")])
def registry_read(v, ctx):
    key = f"{v['hive']}\\{v['path'].strip().strip(chr(92))}"
    script = (f"$p='Registry::{key}'; if(-not (Test-Path $p)){{ 'KEY NOT FOUND'; exit }}; "
              "$i=Get-ItemProperty $p; $i | Get-Member -MemberType NoteProperty | "
              "Where-Object {$_.Name -notlike 'PS*'} | ForEach-Object { "
              "'{0} = {1}' -f $_.Name, $i.($_.Name) }")
    out = _powershell(script, ctx=ctx, lenient=True)
    if "KEY NOT FOUND" in out:
        raise ToolError(f"The key {key} does not exist")
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    if v["value"].strip():
        wanted = v["value"].strip()
        match = [line for line in lines if line.lower().startswith(wanted.lower() + " =")]
        if not match:
            raise ToolError(f"No value {wanted!r} in {key}")
        return match[0]
    ctx.log("\n".join(lines))
    return f"{len(lines)} value(s) in {key}"


@tool(id="registry-write", name="Write a Registry Value", category="System",
      summary="Create or change one registry value. Export the key first — this is permanent.",
      platforms=WIN, destructive=True,
      fields=[F.choice("hive", "Hive", HIVES, "HKEY_CURRENT_USER"),
              F.text("path", "Key path", required=True),
              F.text("name", "Value name", required=True),
              F.text("data", "Data", required=True),
              F.choice("type", "Type", ["String", "DWord", "QWord", "ExpandString"], "String"),
              F.flag("confirm", "I have a backup — write it", False)])
def registry_write(v, ctx):
    if not v["confirm"]:
        return "Nothing written. Tick the confirmation box once you have a backup."
    key = f"{v['hive']}\\{v['path'].strip().strip(chr(92))}"
    kind = {"String": "String", "DWord": "DWord", "QWord": "QWord",
            "ExpandString": "ExpandString"}[v["type"]]
    script = (f"if(-not (Test-Path 'Registry::{key}')){{ New-Item -Path 'Registry::{key}' -Force | Out-Null }}; "
              f"New-ItemProperty -Path 'Registry::{key}' -Name '{v['name']}' "
              f"-Value '{v['data']}' -PropertyType {kind} -Force | Out-Null; 'OK'")
    out = _powershell(script, ctx=ctx)
    if "OK" not in out:
        raise ToolError(f"Write failed: {out.strip()[:200]}")
    return f"{v['name']} = {v['data']} written to {key}"


@tool(id="registry-delete", name="Delete a Registry Value", category="System",
      summary="Remove one registry value. Export the key first — this cannot be undone.",
      platforms=WIN, destructive=True,
      fields=[F.choice("hive", "Hive", HIVES, "HKEY_CURRENT_USER"),
              F.text("path", "Key path", required=True),
              F.text("name", "Value name", required=True),
              F.flag("confirm", "Yes, delete it", False)])
def registry_delete(v, ctx):
    if not v["confirm"]:
        return "Nothing deleted. Tick the confirmation box once you have a backup."
    key = f"{v['hive']}\\{v['path'].strip().strip(chr(92))}"
    script = (f"Remove-ItemProperty -Path 'Registry::{key}' -Name '{v['name']}' "
              "-ErrorAction Stop; 'OK'")
    out = _powershell(script, ctx=ctx)
    if "OK" not in out:
        raise ToolError(f"Delete failed: {out.strip()[:200]}")
    return f"{v['name']} removed from {key}"


@tool(id="registry-export", name="Export a Registry Key", category="System",
      summary="Save a registry key to a .reg file before you change anything.",
      platforms=WIN,
      fields=[F.choice("hive", "Hive", HIVES, "HKEY_CURRENT_USER"),
              F.text("path", "Key path", required=True),
              F.save("output", "Save .reg file as", required=True, filters="Registry (*.reg)")])
def registry_export(v, ctx):
    key = f"{v['hive']}\\{v['path'].strip().strip(chr(92))}"
    target = out_path(v["output"], "backup.reg")
    if target.suffix.lower() != ".reg":
        target = target.with_suffix(".reg")
    code, _, err = run_command(["reg", "export", key, str(target), "/y"], ctx=ctx, timeout=120)
    if code != 0:
        raise ToolError(f"Export failed: {err.strip()[:200]}")
    ctx.output(str(target))
    return f"Exported {key} → {target}"


@tool(id="registry-search", name="Search the Registry", category="System",
      summary="Find a word in registry key names under a hive — slow but thorough.",
      platforms=WIN,
      fields=[F.text("needle", "Search for", required=True),
              F.choice("hive", "Hive", ["HKEY_CURRENT_USER", "HKEY_LOCAL_MACHINE"],
                       "HKEY_CURRENT_USER"),
              F.integer("limit", "Stop after", 50, minimum=1, maximum=500)])
def registry_search(v, ctx):
    script = (f"Get-ChildItem -Path 'Registry::{v['hive']}' -Recurse -ErrorAction SilentlyContinue | "
              f"Where-Object {{ $_.Name -like '*{v['needle']}*' }} | "
              f"Select-Object -First {v['limit']} -ExpandProperty Name")
    out = _powershell(script, ctx=ctx, timeout=280)
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    if not lines:
        return f"Nothing matched {v['needle']!r}."
    ctx.log("\n".join(lines))
    return f"{len(lines)} key(s) matched"


# --------------------------------------------------------------------------
# Installed software, updates, drivers, events
# --------------------------------------------------------------------------
@tool(id="installed-programs", name="Installed Programs", category="System",
      summary="Everything installed, with versions and publishers, from the uninstall registry.",
      platforms=WIN,
      fields=[F.text("filter", "Only names containing"),
              F.save("report", "Save CSV to", required=False)])
def installed_programs(v, ctx):
    from ._util import write_csv
    script = ("$paths='HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
              "'HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
              "'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*';"
              "Get-ItemProperty $paths -ErrorAction SilentlyContinue | "
              "Where-Object {$_.DisplayName} | "
              "Select-Object DisplayName,DisplayVersion,Publisher,InstallDate | "
              "Sort-Object DisplayName | ConvertTo-Json -Depth 2")
    data = _ps_json(script, ctx=ctx)
    if isinstance(data, dict):
        data = [data]
    needle = v["filter"].strip().lower()
    rows = [{"name": str(item.get("DisplayName", ""))[:60],
             "version": str(item.get("DisplayVersion", "") or ""),
             "publisher": str(item.get("Publisher", "") or "")[:30],
             "installed": str(item.get("InstallDate", "") or "")}
            for item in data
            if not needle or needle in str(item.get("DisplayName", "")).lower()]
    ctx.log(report_table(rows[:150], ["name", "version", "publisher", "installed"]))
    if v["report"].strip():
        target = write_csv(out_path(v["report"], "installed-programs.csv"), rows)
        ctx.output(str(target))
    return f"{len(rows)} program(s)"


@tool(id="windows-updates", name="Installed Updates", category="System",
      summary="Windows hotfixes and updates installed on this machine.",
      platforms=WIN,
      fields=[F.integer("limit", "Show", 40, minimum=1, maximum=500)])
def windows_updates(v, ctx):
    data = _ps_json("Get-HotFix | Select-Object HotFixID,Description,InstalledOn | "
                    "Sort-Object InstalledOn -Descending | ConvertTo-Json -Depth 2",
                    ctx=ctx)
    rows = [{"hotfix": str(item.get("HotFixID", "")),
             "description": str(item.get("Description", "")),
             "installed": str(item.get("InstalledOn", ""))[:10]} for item in data[:v["limit"]]]
    ctx.log(report_table(rows, ["hotfix", "description", "installed"]))
    return f"{len(data)} update(s) installed"


@tool(id="drivers-list", name="Installed Drivers", category="System",
      summary="Kernel drivers with their state and whether they are signed.",
      platforms=WIN,
      fields=[F.text("filter", "Only names containing"),
              F.integer("limit", "Show", 60, minimum=1, maximum=500)])
def drivers_list(v, ctx):
    data = _ps_json("Get-CimInstance Win32_SystemDriver | "
                    "Select-Object Name,DisplayName,State,StartMode | "
                    "ConvertTo-Json -Depth 2", ctx=ctx)
    needle = v["filter"].strip().lower()
    rows = [{"name": str(item.get("Name", "")),
             "display": str(item.get("DisplayName", ""))[:40],
             "state": str(item.get("State", "")),
             "start": str(item.get("StartMode", ""))}
            for item in data if not needle or needle in str(item.get("Name", "")).lower()]
    rows.sort(key=lambda row: (row["state"] != "Running", row["name"].lower()))
    ctx.log(report_table(rows[:v["limit"]], ["name", "state", "start", "display"]))
    return f"{len(rows)} driver(s)"


@tool(id="event-log", name="Event Log", category="System",
      summary="Recent entries from a Windows event log — errors and warnings by default.",
      platforms=WIN,
      fields=[F.choice("log", "Log", ["System", "Application", "Security"], "System"),
              F.choice("level", "Level", ["Error and Warning", "Error only", "All"], "Error and Warning"),
              F.integer("count", "Entries", 20, minimum=1, maximum=200)])
def event_log(v, ctx):
    levels = {"Error and Warning": "@(1,2,3)", "Error only": "@(1,2)", "All": "@(0,1,2,3,4,5)"}
    data = _ps_json(f"Get-WinEvent -LogName {v['log']} -MaxEvents {v['count']} "
                      f"-ErrorAction SilentlyContinue | Where-Object {{ {levels[v['level']]} -contains $_.Level }} | "
                      "Select-Object TimeCreated,Id,LevelDisplayName,ProviderName,Message | "
                      "ConvertTo-Json -Depth 2", ctx=ctx, timeout=180)
    if isinstance(data, dict):
        data = [data]
    rows = [{"time": str(item.get("TimeCreated", ""))[:19],
             "id": item.get("Id", ""),
             "level": str(item.get("LevelDisplayName", "")),
             "source": str(item.get("ProviderName", ""))[:30]} for item in data]
    ctx.log(report_table(rows, ["time", "id", "level", "source"]))
    for item in data[:3]:
        message = str(item.get("Message", ""))[:300]
        if message:
            ctx.log(f"\n[{item.get('Id')}] {message}")
    return f"{len(rows)} event(s) from {v['log']}"


# --------------------------------------------------------------------------
# Security & power
# --------------------------------------------------------------------------
@tool(id="defender-status", name="Windows Defender Status", category="System",
      summary="Antivirus and firewall state, signature age and last scan time.",
      platforms=WIN,
      fields=[])
def defender_status(v, ctx):
    out = _powershell("try { $s=Get-MpComputerStatus; "
                      "'Real-time protection: ' + $s.RealTimeProtectionEnabled; "
                      "'Antivirus enabled: ' + $s.AntivirusEnabled; "
                      "'Signatures: ' + $s.AntivirusSignatureVersion + ' (' + "
                      "$s.AntivirusSignatureLastUpdated + ')'; "
                      "'Last quick scan: ' + $s.QuickScanEndTime; "
                      "'Last full scan: ' + $s.FullScanEndTime } catch { 'Defender is not available: ' + $_.Exception.Message }",
                      ctx=ctx, timeout=120)
    ctx.log(out.strip())
    return "Defender status reported above"


@tool(id="firewall-status", name="Firewall Status", category="System",
      summary="Whether the Windows firewall is on for each profile.",
      platforms=WIN,
      fields=[])
def firewall_status(v, ctx):
    out = _powershell("Get-NetFirewallProfile | Select-Object Name,Enabled,DefaultInboundAction,"
                      "DefaultOutboundAction | Format-Table -AutoSize | Out-String -Width 120",
                      ctx=ctx, timeout=120)
    ctx.log(out.strip())
    return "Firewall profiles listed above"


@tool(id="firewall-rules", name="Firewall Rules", category="System",
      summary="Enabled inbound and outbound firewall rules, with ports and programs.",
      platforms=WIN,
      fields=[F.text("filter", "Only names containing"),
              F.choice("direction", "Direction", ["Inbound", "Outbound", "Both"], "Inbound"),
              F.integer("limit", "Show", 40, minimum=1, maximum=300)])
def firewall_rules(v, ctx):
    direction = "" if v["direction"] == "Both" else f"-Direction {v['direction']}"
    data = _ps_json(f"Get-NetFirewallRule -Enabled True {direction} | "
                    "Select-Object DisplayName,Direction,Action,Profile | "
                    "ConvertTo-Json -Depth 2", ctx=ctx)
    needle = v["filter"].strip().lower()
    rows = [{"name": str(item.get("DisplayName", ""))[:50],
             "direction": str(item.get("Direction", "")),
             "action": str(item.get("Action", "")),
             "profile": str(item.get("Profile", ""))}
            for item in data if not needle or needle in str(item.get("DisplayName", "")).lower()]
    ctx.log(report_table(rows[:v["limit"]], ["name", "direction", "action", "profile"]))
    return f"{len(rows)} rule(s)"


@tool(id="bitlocker-status", name="BitLocker Status", category="System",
      summary="Drive encryption state for every volume, and whether a key protector exists.",
      platforms=WIN,
      fields=[])
def bitlocker_status(v, ctx):
    out = _powershell("try { Get-BitLockerVolume | Select-Object MountPoint,VolumeStatus,"
                      "ProtectionStatus,EncryptionPercentage | Format-Table -AutoSize | "
                      "Out-String -Width 120 } catch { 'BitLocker cmdlets unavailable: ' + "
                      "$_.Exception.Message }", ctx=ctx, timeout=120, lenient=True)
    ctx.log(out.strip())
    return "BitLocker volumes listed above"


@tool(id="users-list", name="Local User Accounts", category="System",
      summary="Accounts on this machine with their enabled state and last logon.",
      platforms=WIN,
      fields=[])
def users_list(v, ctx):
    data = _ps_json("Get-LocalUser | Select-Object Name,Enabled,LastLogon,Description | "
                    "ConvertTo-Json -Depth 2", ctx=ctx)
    rows = [{"name": item.get("Name", ""), "enabled": item.get("Enabled", ""),
             "last_logon": str(item.get("LastLogon", ""))[:19],
             "description": str(item.get("Description", ""))[:30]} for item in data]
    ctx.log(report_table(rows, ["name", "enabled", "last_logon", "description"]))
    return f"{len(rows)} account(s)"


@tool(id="wifi-networks", name="Wi-Fi Networks", category="System",
      summary="Saved Wi-Fi profiles and the networks currently in range.",
      platforms=WIN,
      fields=[F.choice("show", "Show", ["Saved profiles", "Networks in range", "Both"],
                       "Saved profiles")])
def wifi_networks(v, ctx):
    output = []
    if v["show"] in ("Saved profiles", "Both"):
        code, out, _ = run_command(["netsh", "wlan", "show", "profiles"], ctx=ctx, timeout=60)
        output.append(out.strip())
    if v["show"] in ("Networks in range", "Both"):
        code, out, _ = run_command(["netsh", "wlan", "show", "networks", "mode=bssid"],
                                   ctx=ctx, timeout=60)
        output.append(out.strip())
    text = "\n\n".join(part for part in output if part)
    if not text:
        raise ToolError("No Wi-Fi adapter reported anything — is Wi-Fi enabled?")
    ctx.log(text[:3000])
    return f"{text.count('SSID')} SSID line(s) reported"


@tool(id="power-plans", name="Power Plans", category="System",
      summary="Available power plans and which one is active.",
      platforms=WIN,
      fields=[])
def power_plans(v, ctx):
    code, out, err = run_command(["powercfg", "/list"], ctx=ctx, timeout=60)
    if code != 0:
        raise ToolError(f"powercfg failed: {err.strip()[:200]}")
    ctx.log(out.strip())
    return "Power plans listed above"


@tool(id="power-actions", name="Shut Down / Restart", category="System",
      summary="Lock, sleep, restart or shut down this machine after a delay you choose.",
      platforms=WIN, destructive=True,
      fields=[F.choice("action", "Action", ["Lock", "Sleep", "Restart", "Shut down"], "Lock"),
              F.integer("delay_seconds", "Delay (seconds)", 30, minimum=0, maximum=3600),
              F.flag("confirm", "Yes, do it", False)])
def power_actions(v, ctx):
    action = v["action"]
    if not v["confirm"]:
        return f"Would {action.lower()} in {v['delay_seconds']}s. Tick the confirmation box."
    if action == "Lock":
        code, _, err = run_command(["rundll32.exe", "user32.dll,LockWorkStation"], ctx=ctx)
    elif action == "Sleep":
        code, _, err = run_command(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], ctx=ctx)
    elif action == "Restart":
        code, _, err = run_command(["shutdown", "/r", "/t", str(v["delay_seconds"])], ctx=ctx)
    else:
        code, _, err = run_command(["shutdown", "/s", "/t", str(v["delay_seconds"])], ctx=ctx)
    if code != 0:
        raise ToolError(f"{action} failed: {err.strip()[:200]}")
    return f"{action} scheduled in {v['delay_seconds']}s"


@tool(id="hosts-file", name="Hosts File Editor", category="System",
      summary="Read the hosts file, or add and remove an entry with a backup kept.",
      fields=[F.choice("action", "Action", ["Show entries", "Add entry", "Remove entry"],
                       "Show entries"),
              F.text("ip", "IP address", "127.0.0.1"),
              F.text("hostname", "Hostname", "myapp.local"),
              F.flag("apply", "Write the change", False)])
def hosts_file(v, ctx):
    path = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32/drivers/etc/hosts" \
        if IS_WINDOWS else Path("/etc/hosts")
    if not path.exists():
        raise ToolError(f"No hosts file at {path}")
    raw = path.read_text(encoding="utf-8", errors="replace")
    entries = [line for line in raw.splitlines()
               if line.strip() and not line.strip().startswith("#")]
    if v["action"] == "Show entries":
        ctx.log("\n".join(entries) or "(no active entries)")
        return f"{len(entries)} active entr(ies) in {path}"
    ip, hostname = v["ip"].strip(), v["hostname"].strip()
    if not ip or not hostname:
        raise ToolError("Give both an IP address and a hostname")
    if v["action"] == "Add entry":
        if any(hostname in line.split() for line in entries):
            raise ToolError(f"{hostname} already has an entry — remove it first")
        new_text = raw.rstrip("\n") + f"\n{ip}\t{hostname}\n"
    else:
        kept = [line for line in raw.splitlines() if hostname not in line.split()[1:]]
        if len(kept) == len(raw.splitlines()):
            raise ToolError(f"No entry for {hostname}")
        new_text = "\n".join(kept) + "\n"
    if not v["apply"]:
        return "Preview only — tick 'Write the change' to save (a .bak backup is kept)"
    backup = path.with_suffix(".all4one.bak")
    backup.write_text(raw, encoding="utf-8")
    try:
        path.write_text(new_text, encoding="utf-8")
    except PermissionError as exc:
        raise ToolError("Editing the hosts file needs administrator rights") from exc
    return f"Saved. Backup at {backup}"


@tool(id="fonts-list", name="Installed Fonts", category="System",
      summary="Every font family installed on this machine.",
      fields=[F.text("filter", "Only names containing")])
def fonts_list(v, ctx):
    names: set[str] = set()
    if IS_WINDOWS:
        folder = Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts"
        for item in folder.glob("*.*"):
            names.add(item.stem)
    else:
        code, out, _ = run_command(["fc-list", "--format", "%{family}\n"], timeout=60)
        for line in out.splitlines():
            if line.strip():
                names.add(line.split(",")[0].strip())
    needle = v["filter"].strip().lower()
    rows = sorted(name for name in names if not needle or needle in name.lower())
    if not rows:
        return "No fonts matched."
    ctx.log("\n".join(rows[:200]))
    return f"{len(rows)} font(s)"


@tool(id="printers-list", name="Printers", category="System",
      summary="Installed printers with their driver, port and default status.",
      platforms=WIN,
      fields=[])
def printers_list(v, ctx):
    data = _ps_json("Get-Printer | Select-Object Name,DriverName,PortName,PrinterStatus | "
                      "ConvertTo-Json -Depth 2", ctx=ctx, timeout=120)
    if isinstance(data, dict):
        data = [data]
    rows = [{"name": str(item.get("Name", ""))[:40],
             "driver": str(item.get("DriverName", ""))[:30],
             "port": str(item.get("PortName", "")),
             "status": str(item.get("PrinterStatus", ""))} for item in data]
    ctx.log(report_table(rows, ["name", "status", "port", "driver"]))
    return f"{len(rows)} printer(s)"
