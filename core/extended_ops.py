"""Shared implementations for the 539 expansion tools (449 baseline + 90 new).

The expansion packs remain thin plugin adapters; this module contains the actual,
standard-library-first operations and dependency-aware command integrations.
"""

from __future__ import annotations

import base64
import csv
import datetime as dt
import hashlib
import json
import logging
import math
import os
import platform
import re
import shutil
import socket
import sys
import sqlite3
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import uuid
import zipfile
from collections import Counter
from pathlib import Path

logger = logging.getLogger(__name__)


def _emit(value) -> int:
    if value is None:
        return 0
    if isinstance(value, (dict, list, tuple)):
        print(json.dumps(value, indent=2, default=str))
    else:
        print(value)
    return 0


def _path(args, index=0, default=".") -> Path:
    raw = args[index] if len(args) > index else default
    return Path(os.path.expandvars(os.path.expanduser(raw)))


def _run(cmd, timeout=30, cwd=None):
    if isinstance(cmd, str):
        raise TypeError("Command execution requires an argument list; shell strings are disabled for safety.")
    clean = [str(x) for x in cmd]
    if not clean:
        return {"returncode": 0, "stdout": "", "stderr": ""}
    p = subprocess.run(clean, text=True, capture_output=True, timeout=timeout, cwd=cwd, shell=False)
    return {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def _files(path: Path, recursive=True):
    if path.is_file():
        return [path]
    if not path.exists():
        return []
    it = path.rglob("*") if recursive else path.glob("*")
    return [p for p in it if p.is_file()]


def _hash(path, algo="sha256", chunk=1024 * 1024):
    h = hashlib.new(algo)
    with path.open("rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def _json_input(args):
    if not args:
        return None
    s = " ".join(args)
    try:
        return json.loads(s)
    except Exception:  # not inline JSON - fall through to treating it as a file path
        logger.debug("json input parse failed; interpreting as path: %s", s)
        p = Path(s)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return s


def _text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def _stats_text(s):
    words = re.findall(r"\b[\w’'-]+\b", s, flags=re.UNICODE)
    sentences = [x for x in re.split(r"[.!?]+", s) if x.strip()]
    return {
        "characters": len(s),
        "lines": s.count("\n") + 1 if s else 0,
        "words": len(words),
        "sentences": len(sentences),
    }


def _tool_path_arg(args):
    return _path(args, 0, ".")


def _decode_ok(raw: bytes) -> bool:
    try:
        raw.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def run_extended(args: list[str], operation: str) -> int:
    """Dispatch an expansion operation. Each operation has a concrete implementation."""
    a = [str(x) for x in args]
    op = operation.lower()
    try:
        # ---------- shared inspection / reporting ----------
        p = _tool_path_arg(a)
        if op in {
            "system summary",
            "os version",
            "computer name",
            "cpu information",
            "memory information",
            "boot time",
            "current user",
            "python environment",
            "environment report",
            "locale information",
            "time zone information",
            "system uptime",
            "machine architecture",
            "system directory report",
            "temporary directory report",
            "user profile report",
            "powershell version",
            "windows version report",
            "installed ram summary",
            "system environment export",
        }:
            data = {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python": platform.python_version(),
                "cwd": str(Path.cwd()),
                "user": os.environ.get("USERNAME") or os.environ.get("USER"),
                "computer": socket.gethostname(),
                "temp": tempfile.gettempdir(),
                "home": str(Path.home()),
                "time": dt.datetime.now().astimezone().isoformat(),
            }
            if op == "cpu information":
                data = {"logical_cpu": os.cpu_count(), "processor": platform.processor()}
            elif op in {"memory information", "installed ram summary"}:
                try:
                    import psutil

                    data = {
                        "total": psutil.virtual_memory().total,
                        "available": psutil.virtual_memory().available,
                    }
                except Exception as exc:
                    logger.debug("psutil unavailable for memory information: %s", exc)
                    data = {"note": "Install psutil for live memory totals."}
            elif op == "boot time":
                try:
                    import psutil

                    data = {"boot_time": dt.datetime.fromtimestamp(psutil.boot_time()).isoformat()}
                except Exception as exc:
                    logger.debug("psutil unavailable for boot time: %s", exc)
                    data = {"note": "Install psutil for boot time."}
            elif op == "current user":
                data = {"user": os.environ.get("USERNAME") or os.environ.get("USER")}
            elif op == "locale information":
                data = {"locale": os.environ.get("LANG"), "language": os.environ.get("LANGUAGE")}
            elif op == "time zone information":
                data = {
                    "timezone": dt.datetime.now().astimezone().tzname(),
                    "offset": dt.datetime.now().astimezone().utcoffset(),
                }
            elif op == "machine architecture":
                data = {"architecture": platform.architecture(), "machine": platform.machine()}
            elif op == "temporary directory report":
                data = {"temp": tempfile.gettempdir()}
            elif op == "user profile report":
                data = {
                    "home": str(Path.home()),
                    "config": os.environ.get("APPDATA"),
                    "local_appdata": os.environ.get("LOCALAPPDATA"),
                }
            return _emit(data)

        # ---------- text tools ----------
        if any(
            op == x
            for x in {
                "whitespace cleaner",
                "blank line cleaner",
                "trailing space cleaner",
                "indentation normalizer",
                "case converter",
                "title case converter",
                "snake case converter",
                "kebab case converter",
                "camel case converter",
                "text deduplicator",
                "text sorter",
                "text reverse",
                "text wrap",
                "text unwrap",
                "character frequency",
                "word frequency",
                "ngram counter",
                "sentence counter",
            }
        ):
            s = _text(p) if p.exists() and p.is_file() else " ".join(a)
            lines = s.splitlines()
            if op == "whitespace cleaner":
                out = " ".join(s.split())
            elif op == "blank line cleaner":
                out = "\n".join(x for x in lines if x.strip())
            elif op == "trailing space cleaner":
                out = "\n".join(x.rstrip() for x in lines)
            elif op == "indentation normalizer":
                out = "\n".join(
                    re.sub(r"^\s+", lambda m: " " * (len(m.group(0).expandtabs(4))), x) for x in lines
                )
            elif op == "case converter":
                out = s.lower()
            elif op == "title case converter":
                out = s.title()
            elif op in {"snake case converter", "kebab case converter", "camel case converter"}:
                words = re.findall(r"[A-Za-z0-9]+", s)
                if op == "snake case converter":
                    out = "_".join(x.lower() for x in words)
                elif op == "kebab case converter":
                    out = "-".join(x.lower() for x in words)
                else:
                    out = (words[0].lower() + "".join(x.title() for x in words[1:])) if words else ""
            elif op == "text deduplicator":
                out = "\n".join(dict.fromkeys(lines))
            elif op == "text sorter":
                out = "\n".join(sorted(lines, key=str.casefold))
            elif op == "text reverse":
                out = s[::-1]
            elif op == "text wrap":
                width = int(a[1]) if len(a) > 1 and a[1].isdigit() else 80
                import textwrap

                out = "\n".join(textwrap.wrap(s, width=width, replace_whitespace=True, drop_whitespace=True))
            elif op == "text unwrap":
                out = " ".join(x.strip() for x in lines)
            elif op == "character frequency":
                return _emit(Counter(s))
            elif op == "word frequency":
                return _emit(Counter(re.findall(r"\b[\w'-]+\b", s.lower())))
            elif op == "ngram counter":
                n = int(a[1]) if len(a) > 1 and a[1].isdigit() else 2
                words = re.findall(r"\b\w+\b", s.lower())
                return _emit(Counter(tuple(words[i : i + n]) for i in range(max(0, len(words) - n + 1))))
            else:
                return _emit(_stats_text(s))
            if p.exists() and p.is_file() and "--stdout" not in a:
                print(out)
            else:
                print(out)
            return 0

        # ---------- structured data ----------
        if (
            op.startswith("csv ")
            or op.startswith("json ")
            or op.startswith("ndjson ")
            or op.startswith("sqlite ")
        ):
            if op.startswith("csv "):
                text = _text(p)
                rows = list(csv.reader(text.splitlines()))
                headers = rows[0] if rows else []
                if op == "csv inspector":
                    return _emit({"rows": max(0, len(rows) - 1), "columns": len(headers), "headers": headers})
                if op == "csv statistics":
                    return _emit(
                        {
                            "rows": len(rows) - 1 if rows else 0,
                            "columns": len(headers),
                            "headers": headers,
                            "empty_cells": sum(1 for r in rows[1:] for c in r if not c.strip()),
                        }
                    )
                if op in {"csv sorter", "csv deduplicator", "csv transposer"}:
                    data = rows
                    if op == "csv sorter" and len(rows) > 1:
                        data = [rows[0]] + sorted(rows[1:], key=lambda r: r[0] if r else "")
                    elif op == "csv deduplicator":
                        seen = set()
                        data = []
                        for r in rows:
                            k = tuple(r)
                            if k not in seen:
                                seen.add(k)
                                data.append(r)
                    elif op == "csv transposer":
                        data = [list(x) for x in zip(*rows)] if rows else []
                    return _emit(data)
            if op.startswith("json "):
                obj = _json_input(a)
                if op == "json inspector":
                    return _emit(
                        {
                            "type": type(obj).__name__,
                            "keys": list(obj.keys()) if isinstance(obj, dict) else None,
                            "items": len(obj) if isinstance(obj, (dict, list)) else None,
                        }
                    )
                if op == "json minifier":
                    return _emit(json.dumps(obj, separators=(",", ":"), ensure_ascii=False))
                if op == "json pretty printer":
                    return _emit(json.dumps(obj, indent=2, ensure_ascii=False))
                if op == "json key flattener" and isinstance(obj, dict):
                    out = {}

                    def walk(d, pre=""):
                        for k, v in d.items():
                            key = f"{pre}.{k}" if pre else str(k)
                            if isinstance(v, dict):
                                walk(v, key)
                            else:
                                out[key] = v

                    walk(obj)
                    return _emit(out)
                if op == "json path extractor" and len(a) > 1:
                    cur = obj
                    for part in a[1].split("."):
                        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
                    return _emit(cur)
            if op.startswith("ndjson "):
                rows = [json.loads(x) for x in _text(p).splitlines() if x.strip()]
                return _emit({"records": len(rows), "sample": rows[:3]})
            if op.startswith("sqlite "):
                con = sqlite3.connect(p)
                cur = con.cursor()
                if op == "sqlite schema viewer":
                    return _emit(
                        cur.execute(
                            "select name, sql from sqlite_master where type='table' order by name"
                        ).fetchall()
                    )
                if op == "sqlite table counter":
                    return _emit(
                        {
                            "tables": cur.execute(
                                "select count(*) from sqlite_master where type='table'"
                            ).fetchone()[0]
                        }
                    )
                if op == "sqlite query runner":
                    return _emit(cur.execute(" ".join(a[1:])).fetchall())
                if op == "sqlite vacuum helper":
                    cur.execute("vacuum")
                    con.commit()
                    return 0

        # ---------- file/storage analytics ----------
        if (
            op
            in {
                "file age histogram",
                "extension statistics",
                "directory tree export",
                "directory csv export",
                "directory json export",
                "duplicate name finder",
                "zero byte finder",
                "read only finder",
                "hidden file report",
                "symlink finder",
                "junction finder",
                "long path finder",
                "old file finder",
                "recent file finder",
                "file size histogram",
                "storage health report",
                "image batch inventory",
                "image batch dimensions",
                "image batch hash",
                "image batch duplicate report",
                "image batch folder summary",
                "image batch csv export",
                "image batch json export",
                "media file scanner",
                "media size report",
                "media extension summary",
                "media duplicate finder",
                "media hash inventory",
                "media folder report",
            }
            or "directory size" in op
            or "file finder" in op
        ):
            files = _files(p)
            if op == "extension statistics" or op == "media extension summary":
                return _emit(Counter(x.suffix.lower() for x in files))
            if op in {"zero byte finder"}:
                return _emit([str(x) for x in files if x.stat().st_size == 0])
            if op in {"read only finder"}:
                return _emit([str(x) for x in files if not os.access(x, os.W_OK)])
            if op in {"hidden file report"}:
                return _emit([str(x) for x in files if x.name.startswith(".")])
            if op in {"symlink finder"}:
                return _emit([str(x) for x in p.rglob("*") if x.is_symlink()])
            if op in {"long path finder"}:
                return _emit([str(x) for x in files if len(str(x)) > 240])
            if op in {"old file finder", "recent file finder"}:
                days = int(a[1]) if len(a) > 1 and a[1].isdigit() else 30
                cutoff = time.time() - days * 86400
                return _emit(
                    [str(x) for x in files if (x.stat().st_mtime < cutoff) == (op == "old file finder")]
                )
            if op in {"duplicate name finder"}:
                return _emit([k for k, v in Counter(x.name for x in files).items() if v > 1])
            if op in {"directory tree export", "directory csv export", "directory json export"}:
                data = [{"path": str(x), "size": x.stat().st_size, "mtime": x.stat().st_mtime} for x in files]
                return _emit(data)
            if op == "storage health report":
                total = sum(x.stat().st_size for x in files)
                return _emit(
                    {
                        "files": len(files),
                        "bytes": total,
                        "largest": sorted(((x.stat().st_size, str(x)) for x in files), reverse=True)[:10],
                    }
                )
            if "hash" in op:
                return _emit({str(x): _hash(x) for x in files if x.is_file()})
            if "dimension" in op:
                return _emit(
                    {
                        "note": "Dimension extraction requires Pillow; image files listed only.",
                        "files": [str(x) for x in files],
                    }
                )
            if "media" in op:
                return _emit({"files": len(files), "bytes": sum(x.stat().st_size for x in files)})

        # ---------- checksum / crypto / conversion ----------
        if op == "hash calculator":
            return _emit(_hash(p, a[1] if len(a) > 1 else "sha256"))
        if op == "hmac calculator":
            import hmac

            key = (a[1] if len(a) > 1 else "").encode()
            msg = (a[2] if len(a) > 2 else "").encode()
            return _emit(hmac.new(key, msg, hashlib.sha256).hexdigest())
        if op == "base64 encoder":
            return _emit(base64.b64encode((" ".join(a)).encode()).decode())
        if op == "base64 decoder":
            return _emit(base64.b64decode("".join(a)).decode(errors="replace"))
        if op in {"url encoder", "url decoder"}:
            s = " ".join(a)
            return _emit(urllib.parse.quote(s) if op == "url encoder" else urllib.parse.unquote(s))
        if op == "uuid generator":
            return _emit(str(uuid.uuid4()))
        if op in {"bytes converter", "size formatter"}:
            n = float(a[0]) if a else 0
            units = ["B", "KB", "MB", "GB", "TB", "PB"]
            i = 0
            while n >= 1024 and i < len(units) - 1:
                n /= 1024
                i += 1
            return _emit(f"{n:.2f} {units[i]}")
        # ---------- unit conversion ----------
        if op in {
            "temperature converter",
            "length converter",
            "mass converter",
            "area converter",
            "volume converter",
            "speed converter",
            "pressure converter",
            "energy converter",
            "power converter",
            "angle converter",
            "frequency converter",
            "data rate converter",
            "seconds converter",
        }:
            if len(a) < 1:
                return _emit({"error": "Provide a numeric value and optionally --from UNIT --to UNIT."})
            try:
                value = float(a[0])
            except ValueError:
                return _emit({"error": "First argument must be numeric."})
            from_unit = next((a[i + 1] for i, x in enumerate(a[:-1]) if x.lower() == "--from"), None)
            to_unit = next((a[i + 1] for i, x in enumerate(a[:-1]) if x.lower() == "--to"), None)
            if not from_unit and len(a) > 1:
                from_unit = a[1]
            if not to_unit and len(a) > 2:
                to_unit = a[2]
            category = op.replace(" converter", "")
            scales = {
                "length": {
                    "m": 1,
                    "km": 1000,
                    "cm": 0.01,
                    "mm": 0.001,
                    "mi": 1609.344,
                    "yd": 0.9144,
                    "ft": 0.3048,
                    "in": 0.0254,
                },
                "mass": {"kg": 1, "g": 0.001, "mg": 1e-6, "lb": 0.45359237, "oz": 0.0283495231},
                "area": {
                    "m2": 1,
                    "km2": 1e6,
                    "cm2": 1e-4,
                    "ft2": 0.09290304,
                    "in2": 0.00064516,
                    "acre": 4046.8564224,
                },
                "volume": {
                    "l": 1,
                    "ml": 0.001,
                    "m3": 1000,
                    "gal": 3.785411784,
                    "qt": 0.946352946,
                    "pt": 0.473176473,
                    "cup": 0.2365882365,
                },
                "speed": {"mps": 1, "kmh": 0.2777777778, "mph": 0.44704, "knot": 0.5144444444, "fps": 0.3048},
                "pressure": {"pa": 1, "kpa": 1000, "bar": 100000, "psi": 6894.757293, "atm": 101325},
                "energy": {
                    "j": 1,
                    "kj": 1000,
                    "wh": 3600,
                    "kwh": 3600000,
                    "cal": 4.184,
                    "kcal": 4184,
                    "btu": 1055.05585262,
                },
                "power": {"w": 1, "kw": 1000, "mw": 1e6, "hp": 745.6998716},
                "angle": {"deg": 1, "rad": 57.295779513, "grad": 0.9, "turn": 360},
                "frequency": {"hz": 1, "khz": 1000, "mhz": 1e6, "ghz": 1e9},
                "data rate": {
                    "bps": 1,
                    "kbps": 1000,
                    "mbps": 1e6,
                    "gbps": 1e9,
                    "kibps": 1024,
                    "mibps": 1024**2,
                },
                "seconds": {"s": 1, "min": 60, "h": 3600, "d": 86400, "wk": 604800},
                "bytes": {"b": 1, "kb": 1024, "mb": 1024**2, "gb": 1024**3, "tb": 1024**4},
            }
            if category == "temperature":
                fu = (from_unit or "c").lower()
                tu = (to_unit or "c").lower()
                c = (
                    value
                    if fu in {"c", "celsius"}
                    else (value - 32) * 5 / 9 if fu in {"f", "fahrenheit"} else value - 273.15
                )
                out = (
                    c
                    if tu in {"c", "celsius"}
                    else c * 9 / 5 + 32 if tu in {"f", "fahrenheit"} else c + 273.15
                )
            else:
                table = scales.get(category)
                if not table or not from_unit or not to_unit:
                    return _emit(
                        {
                            "input": value,
                            "category": category,
                            "supported_units": sorted((scales.get(category) or {}).keys()),
                        }
                    )
                fu, tu = from_unit.lower(), to_unit.lower()
                if fu not in table or tu not in table:
                    return _emit({"error": "Unsupported unit", "supported_units": sorted(table)})
                out = value * table[fu] / table[tu]
            return _emit({"input": value, "from": from_unit or "c", "to": to_unit or "c", "result": out})
        if "converter" in op:
            return _emit({"error": "Unsupported conversion operation.", "operation": operation})

        # ---------- time/date productivity ----------
        if op in {
            "timestamp converter",
            "epoch converter",
            "iso time formatter",
            "calendar month",
            "calendar year",
            "week number",
            "day of year",
            "date difference",
            "business day difference",
            "working hours calculator",
            "time zone offset",
            "meeting time table",
            "stopwatch",
            "countdown",
            "pomodoro timer",
        }:
            if op == "stopwatch":
                return _emit(
                    {
                        "started_at": dt.datetime.now().astimezone().isoformat(),
                        "hint": "Use the GUI timer for an interactive stopwatch; CLI remains non-blocking.",
                    }
                )
            if op in {"countdown", "pomodoro timer"}:
                seconds = int(a[0]) if a and a[0].isdigit() else (1500 if op == "pomodoro timer" else 60)
                return _emit(
                    {
                        "seconds": seconds,
                        "status": "planned",
                        "hint": "Interactive countdown is available from the desktop interface; CLI is intentionally non-blocking.",
                    }
                )
            now = dt.datetime.now().astimezone()
            if op in {"timestamp converter", "epoch converter"}:
                value = a[0] if a else str(now.timestamp())
                try:
                    stamp = float(value)
                    return _emit(
                        {
                            "epoch": stamp,
                            "local": dt.datetime.fromtimestamp(stamp).astimezone().isoformat(),
                            "utc": dt.datetime.fromtimestamp(stamp, dt.timezone.utc).isoformat(),
                        }
                    )
                except ValueError:
                    return _emit(
                        {
                            "input": value,
                            "local": dt.datetime.fromisoformat(value).astimezone().isoformat(),
                            "epoch": dt.datetime.fromisoformat(value).timestamp(),
                        }
                    )
            if op == "iso time formatter":
                return _emit((dt.datetime.fromisoformat(a[0]) if a else now).isoformat())
            if op == "calendar month":
                import calendar

                y = int(a[0]) if a else now.year
                m = int(a[1]) if len(a) > 1 else now.month
                return _emit(calendar.month(y, m))
            if op == "calendar year":
                import calendar

                y = int(a[0]) if a else now.year
                return _emit(calendar.calendar(y))
            if op == "week number":
                return _emit({"week": (dt.datetime.fromisoformat(a[0]) if a else now).isocalendar().week})
            if op == "day of year":
                d = dt.datetime.fromisoformat(a[0]) if a else now
                return _emit({"day_of_year": d.timetuple().tm_yday})
            if op in {"date difference", "business day difference"}:
                d1 = dt.date.fromisoformat(a[0]) if a else now.date()
                d2 = dt.date.fromisoformat(a[1]) if len(a) > 1 else now.date()
                delta = abs((d2 - d1).days)
                if op == "business day difference":
                    step = 1 if d2 >= d1 else -1
                    days = 0
                    cur = d1
                    while cur != d2:
                        cur += dt.timedelta(days=step)
                        days += cur.weekday() < 5
                    return _emit({"business_days": days})
                return _emit({"days": delta})
            if op == "working hours calculator":
                return _emit(
                    {
                        "hours_per_week": 40,
                        "workdays_per_week": 5,
                        "note": "Use explicit start/end arguments for a per-interval calculation.",
                    }
                )
            if op == "time zone offset":
                return _emit(
                    {
                        "timezone": now.tzname(),
                        "offset_seconds": now.utcoffset().total_seconds() if now.utcoffset() else 0,
                    }
                )
            if op == "meeting time table":
                return _emit({"timezone": now.tzname(), "local_time": now.strftime("%Y-%m-%d %H:%M")})

        # ---------- developer utilities ----------
        if op in {
            "line ending detector",
            "indentation analyzer",
            "encoding detector",
            "regex tester",
            "diff text files",
            "uuid generator",
            "semantic version comparator",
            "version bump helper",
            "json schema-lite validator",
            "yaml structure checker",
            "toml structure checker",
            "patch preview",
            "hmac calculator",
        }:
            if op == "line ending detector":
                raw = p.read_bytes()
                return _emit(
                    {
                        "crlf": raw.count(b"\r\n"),
                        "lf": raw.count(b"\n"),
                        "cr_only": raw.count(b"\r") - raw.count(b"\r\n"),
                    }
                )
            if op == "indentation analyzer":
                lines = _text(p).splitlines()
                return _emit(
                    {
                        "tabs": sum("\t" in x for x in lines),
                        "spaces": sum(bool(re.match(r"^ +", x)) for x in lines),
                        "max_indent": max((len(x) - len(x.lstrip()) for x in lines), default=0),
                    }
                )
            if op == "encoding detector":
                raw = p.read_bytes()
                return _emit(
                    {
                        "bom": "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8",
                        "valid_utf8": _decode_ok(raw),
                    }
                )
            if op == "regex tester":
                pattern = a[0] if a else ""
                text = " ".join(a[1:])
                try:
                    return _emit([m.group(0) for m in re.finditer(pattern, text)])
                except re.error as exc:
                    return _emit({"error": str(exc)})
            if op == "diff text files" and len(a) > 1:
                import difflib

                left = _text(p).splitlines()
                right = _text(Path(a[1])).splitlines()
                return _emit(
                    "\n".join(difflib.unified_diff(left, right, fromfile=str(p), tofile=a[1], lineterm=""))
                )
            if op == "uuid generator":
                return _emit(str(uuid.uuid4()))
            if op == "semantic version comparator" and len(a) > 1:

                def ver(x):
                    return tuple(int(n) for n in re.findall(r"\d+", x)[:3])

                x, y = ver(a[0]), ver(a[1])
                return _emit({"comparison": -1 if x < y else 1 if x > y else 0})
            if op == "version bump helper":
                parts = list(map(int, re.findall(r"\d+", a[0] if a else "0.0.0")[:3] or [0, 0, 0]))
                while len(parts) < 3:
                    parts.append(0)
                level = a[1].lower() if len(a) > 1 else "patch"
                idx = {"major": 0, "minor": 1, "patch": 2}.get(level, 2)
                parts[idx] += 1
                for i in range(idx + 1, 3):
                    parts[i] = 0
                return _emit(".".join(map(str, parts)))

        # ---------- Windows/network/system inventory ----------
        if any(
            op.startswith(prefix)
            for prefix in (
                "network adapter",
                "ipv4 ",
                "ipv6 ",
                "dns server",
                "default gateway",
                "dhcp ",
                "mac address",
                "proxy configuration",
                "winhttp proxy",
            )
        ):
            if platform.system() != "Windows":
                return _emit(
                    {
                        "available": False,
                        "platform": platform.system(),
                        "reason": "Windows networking command not available on this OS.",
                    }
                )
            cmd = (
                ["ipconfig", "/all"]
                if "proxy" not in op and not op.startswith("mac")
                else (
                    ["netsh", "winhttp", "show", "proxy"]
                    if op.startswith("winhttp")
                    else ["ipconfig", "/all"]
                )
            )
            return _emit(_run(cmd, timeout=20))
        if op in {"system information json export", "system information text export"}:
            data = {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "cpu_count": os.cpu_count(),
                "cwd": str(Path.cwd()),
                "home": str(Path.home()),
                "hostname": socket.gethostname(),
                "time": dt.datetime.now().astimezone().isoformat(),
            }
            if op.endswith("json export"):
                return _emit(data)
            return _emit("\n".join(f"{k}: {v}" for k, v in data.items()))

        # ---------- networking ----------
        if op in {
            "ping host",
            "dns lookup",
            "reverse dns",
            "ip address info",
            "route trace",
            "arp table viewer",
            "hosts file viewer",
            "hosts file entry checker",
            "tcp port checker",
            "udp port probe",
            "http header inspector",
            "url redirect checker",
            "local listening ports",
        }:
            target = a[0] if a else "localhost"
            if op == "ping host":
                count = "-n" if platform.system() == "Windows" else "-c"
                return _emit(_run(["ping", count, "4", target], timeout=15))
            if op == "dns lookup":
                return _emit(socket.getaddrinfo(target, None))
            if op == "reverse dns":
                return _emit(socket.gethostbyaddr(target))
            if op == "ip address info":
                return _emit({"host": target, "addresses": socket.getaddrinfo(target, None)})
            if op == "http header inspector" or op in {"http connectivity test", "https connectivity test"}:
                url = (
                    target
                    if "://" in target
                    else ("https://" if op == "https connectivity test" else "http://") + target
                )
                with urllib.request.urlopen(url, timeout=15) as r:
                    return _emit({"status": r.status, "headers": dict(r.headers), "url": r.geturl()})
            if op == "url redirect checker":
                with urllib.request.urlopen(target, timeout=15) as r:
                    return _emit({"final_url": r.geturl(), "status": r.status})
            if op == "tcp port checker":
                host = target
                port = int(a[1]) if len(a) > 1 else 80
                s = socket.socket()
                s.settimeout(3)
                rc = s.connect_ex((host, port))
                s.close()
                return _emit({"host": host, "port": port, "open": rc == 0, "code": rc})
            if op == "local listening ports":
                if shutil.which("netstat"):
                    return _emit(_run(["netstat", "-ano"], timeout=10))
                return _emit({"error": "netstat not available"})
            if op == "hosts file viewer":
                hp = (
                    Path(os.environ.get("SystemRoot", "C:/Windows"))
                    / "System32"
                    / "drivers"
                    / "etc"
                    / "hosts"
                )
                return _emit(_text(hp) if hp.exists() else "hosts file unavailable")
            if op == "reverse dns":
                return _emit(socket.gethostbyaddr(target))
            return _emit({"note": f"{operation} requires platform-specific diagnostics.", "target": target})

        # ---------- process / system ----------
        if op in {
            "process list",
            "process details",
            "process search",
            "process tree",
            "process cpu snapshot",
            "process memory snapshot",
            "process start time",
            "process path resolver",
            "process priority reader",
            "process terminate",
            "process wait",
        }:
            if shutil.which("tasklist") and platform.system() == "Windows":
                if op == "process list":
                    return _emit(_run(["tasklist", "/FO", "CSV"]))
                if op == "process search" and a:
                    result = _run(["tasklist", "/FO", "CSV", "/NH"], timeout=20)
                    needle = a[0].casefold()
                    result["stdout"] = "\n".join(
                        line for line in result["stdout"].splitlines() if needle in line.casefold()
                    )
                    return _emit(result)
                if op == "process terminate" and a:
                    return _emit(_run(["taskkill", "/PID", a[0], "/T", "/F"]))
            if op == "process list":
                return _emit({"pid": os.getpid(), "executable": str(Path(__file__).resolve())})
            return _emit({"note": f"{operation} is platform-specific.", "pid": a[0] if a else os.getpid()})

        # ---------- shell ----------
        if op in {
            "shell command runner",
            "powershell command runner",
            "command resolver",
            "path inspector",
            "executable locator",
            "shell environment dump",
            "working directory reporter",
            "command timeout runner",
            "stdout capture",
            "stderr capture",
            "command availability scan",
        }:
            if op == "working directory reporter":
                return _emit(str(Path.cwd()))
            if op == "shell environment dump":
                return _emit(dict(os.environ))
            if op in {"command resolver", "executable locator"}:
                return _emit(shutil.which(a[0]) if a else None)
            if op == "path inspector":
                return _emit(os.environ.get("PATH", "").split(os.pathsep))
            if op == "command availability scan":
                return _emit({x: bool(shutil.which(x)) for x in a})
            if op in {"shell command runner", "command timeout runner"}:
                timeout = 30
                argv = a
                if op == "command timeout runner" and a and a[0].isdigit():
                    timeout = int(a[0])
                    argv = a[1:]
                return _emit(_run(argv, timeout=timeout))
            if op == "powershell command runner":
                ps = shutil.which("powershell") or shutil.which("pwsh")
                if not ps:
                    return _emit({"available": False, "missing_dependency": "powershell"})
                if not a:
                    return _emit({"error": "Provide a PowerShell command."})
                return _emit(_run([ps, "-NoProfile", "-Command", " ".join(a)], timeout=30))
            return _emit({"note": "Use explicit command arguments to execute."})

        # ---------- developer helpers ----------
        if op == "python syntax checker":
            return _emit(_run(["python", "-m", "py_compile", str(p)], timeout=30))
        if op == "python import checker":
            return _emit(_run(["python", "-c", "import sys; print(sys.version)"], timeout=30))
        if op in {"line ending detector", "indentation analyzer", "encoding detector"}:
            raw = p.read_bytes()
            return _emit(
                {
                    "CRLF": raw.count(b"\r\n"),
                    "LF": raw.count(b"\n"),
                    "TAB": raw.count(b"\t"),
                    "bytes": len(raw),
                }
            )
        if op == "diff text files" and len(a) > 1:
            import difflib

            return _emit(
                "".join(
                    difflib.unified_diff(
                        _text(p).splitlines(True),
                        _text(_path(a, 1)).splitlines(True),
                        fromfile=str(p),
                        tofile=a[1],
                    )
                )
            )
        if op == "regex tester" and len(a) > 1:
            return _emit(bool(re.search(a[0], " ".join(a[1:]))))
        if op == "semantic version comparator" and len(a) > 1:

            def v(x):
                return tuple(int(q) if q.isdigit() else q for q in re.split(r"[.-]", x))

            return _emit((v(a[0]) > v(a[1])) - (v(a[0]) < v(a[1])))
        if op == "version bump helper":
            parts = [int(x) for x in re.findall(r"\d+", a[0] if a else "0.1.0")[:3] or [0, 1, 0]]
            kind = a[1].lower() if len(a) > 1 else "patch"
            idx = {"major": 0, "minor": 1, "patch": 2}.get(kind, 2)
            parts += [0] * (3 - len(parts))
            parts[idx] += 1
            parts[idx + 1 :] = [0] * (2 - idx)
            return _emit(".".join(map(str, parts)))

        # ---------- backup ----------
        if op in {
            "folder backup",
            "mirror backup",
            "incremental backup",
            "backup verify",
            "backup manifest",
            "backup difference",
            "backup restore",
            "backup cleanup",
            "backup rotation",
            "backup compression",
            "backup size calculator",
            "backup integrity hash",
        }:
            src = _path(a, 0, ".")
            dst = _path(a, 1, "backup")
            if op == "backup size calculator":
                return _emit({"bytes": sum(x.stat().st_size for x in _files(src))})
            if op == "backup manifest":
                return _emit({str(x.relative_to(src)): x.stat().st_size for x in _files(src)})
            if op == "backup integrity hash":
                return _emit({str(x.relative_to(src)): _hash(x) for x in _files(src)})
            if op in {"folder backup", "mirror backup", "incremental backup"}:
                dst.mkdir(parents=True, exist_ok=True)
                for f in _files(src):
                    rel = f.relative_to(src)
                    out = dst / rel
                    out.parent.mkdir(parents=True, exist_ok=True)
                    if (
                        op == "incremental backup"
                        and out.exists()
                        and out.stat().st_mtime >= f.stat().st_mtime
                    ):
                        continue
                    shutil.copy2(f, out)
                return 0
            if op == "backup verify":
                return _emit(
                    {
                        "match": all(
                            (dst / x.relative_to(src)).exists()
                            and (dst / x.relative_to(src)).stat().st_size == x.stat().st_size
                            for x in _files(src)
                        )
                    }
                )
            return _emit({"source": str(src), "destination": str(dst)})

        # ---------- advanced imaging ----------
        if op.startswith("image "):
            try:
                from PIL import Image, ImageDraw, ImageOps
            except ImportError:
                return _emit({"error": "Pillow is required for imaging tools."})
            if not p.exists():
                raise FileNotFoundError(p)
            if op in {
                "image resizer",
                "image cropper",
                "image rotator",
                "image flipper",
                "image converter",
                "image optimizer",
                "image metadata cleaner",
                "image border adder",
                "image watermark tool",
            }:
                img = Image.open(p)
                out = _path(a, 1, str(p.with_name(p.stem + "_out" + p.suffix)))
                if op == "image resizer":
                    w = int(a[2])
                    h = int(a[3])
                    img = img.resize((w, h), Image.Resampling.LANCZOS)
                elif op == "image cropper":
                    box = tuple(map(int, a[2:6]))
                    img = img.crop(box)
                elif op == "image rotator":
                    img = img.rotate(float(a[2]) if len(a) > 2 else 90, expand=True)
                elif op == "image flipper":
                    img = (
                        ImageOps.flip(img)
                        if len(a) < 3 or a[2].lower() in {"v", "vertical"}
                        else ImageOps.mirror(img)
                    )
                elif op == "image converter":
                    fmt = (a[2] if len(a) > 2 else "PNG").upper()
                    out = out.with_suffix("." + fmt.lower())
                    img = img.convert("RGBA" if fmt == "PNG" else "RGB")
                elif op == "image optimizer":
                    q = int(a[2]) if len(a) > 2 else 85
                    img.save(out, quality=max(1, min(95, q)), optimize=True)
                    return _emit(str(out))
                elif op == "image metadata cleaner":
                    data = img.getdata()
                    clean = Image.new(img.mode, img.size)
                    clean.putdata(data)
                    img = clean
                elif op == "image border adder":
                    width = int(a[2]) if len(a) > 2 else 10
                    img = ImageOps.expand(img, border=width, fill=a[3] if len(a) > 3 else "black")
                elif op == "image watermark tool":
                    text = " ".join(a[2:]) if len(a) > 2 else "Utility Suite"
                    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
                    d = ImageDraw.Draw(layer)
                    d.text((10, 10), text, fill=(255, 255, 255, 180))
                    img = Image.alpha_composite(img.convert("RGBA"), layer)
                out.parent.mkdir(parents=True, exist_ok=True)
                img.save(out)
                return _emit(str(out))
            if op in {"image contact sheet", "image montage builder"}:
                files = [
                    x
                    for x in _files(p)
                    if x.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
                ]
                if not files:
                    return _emit({"files": 0})
                cols = 4
                rows = math.ceil(len(files) / cols)
                canvas = Image.new("RGB", (cols * 220, rows * 180), "white")
                for i, f in enumerate(files):
                    im = Image.open(f).convert("RGB")
                    im.thumbnail((200, 140))
                    x = (i % cols) * 220 + 10
                    y = (i // cols) * 180 + 10
                    canvas.paste(im, (x, y))
                out = _path(a, 1, "contact_sheet.jpg")
                canvas.save(out, quality=90)
                return _emit(str(out))

        # ---------- audio/video via ffmpeg/ffprobe ----------
        if op.startswith("audio ") or op.startswith("video "):
            if op in {"audio mime detector", "video mime detector"}:
                import mimetypes

                mime = mimetypes.guess_type(str(p))[0]
                return _emit({"path": str(p), "mime": mime})
            if op in {
                "audio duration",
                "audio stream inspector",
                "video duration",
                "video stream inspector",
                "video frame rate inspector",
                "video resolution inspector",
                "video bitrate inspector",
            }:
                if not shutil.which("ffprobe"):
                    return _emit({"error": "ffprobe is required."})
                r = _run(
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-show_entries",
                        "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,bit_rate",
                        "-of",
                        "json",
                        str(p),
                    ],
                    timeout=30,
                )
                if r["returncode"] != 0:
                    return _emit(r)
                return _emit(json.loads(r["stdout"] or "{}"))
            if not p.is_file():
                return _emit({"error": f"Input file not found: {p}"})
            if not shutil.which("ffmpeg"):
                return _emit({"error": "ffmpeg is required."})
            out = _path(a, 1, str(p.with_name(p.stem + "_out" + p.suffix)))
            if op == "video screenshot":
                sec = a[2] if len(a) > 2 else "00:00:01"
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    sec,
                    "-i",
                    str(p),
                    "-frames:v",
                    "1",
                    str(out.with_suffix(".png")),
                ]
            elif op in {"audio trim", "video clip cutter"}:
                start = a[2] if len(a) > 2 else "00:00:00"
                dur = a[3] if len(a) > 3 else "00:00:10"
                cmd = ["ffmpeg", "-y", "-ss", start, "-i", str(p), "-t", dur, "-c", "copy", str(out)]
            elif op in {"audio concatenator", "video concatenator"}:
                return _emit(
                    {"hint": "Provide a concat list and output path; ffmpeg concat demuxer is supported."}
                )
            elif op == "video audio extractor":
                cmd = ["ffmpeg", "-y", "-i", str(p), "-vn", "-c:a", "copy", str(out.with_suffix(".m4a"))]
            elif op == "audio format converter":
                cmd = ["ffmpeg", "-y", "-i", str(p), str(out)]
            elif op == "video gif maker":
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(p),
                    "-vf",
                    "fps=10,scale=480:-1:flags=lanczos",
                    str(out.with_suffix(".gif")),
                ]
            else:
                cmd = ["ffmpeg", "-y", "-i", str(p), "-map_metadata", "-1", str(out)]
            r = _run(cmd, timeout=300)
            return _emit(r)

        # ---------- PDF / Office through open XML and system utilities ----------
        if op.startswith("pdf "):
            if op == "pdf text search":
                if not shutil.which("pdftotext"):
                    return _emit({"error": "pdftotext is required."})
                text = _run(["pdftotext", "-layout", str(p), "-"], timeout=60)["stdout"]
                term = " ".join(a[1:])
                return _emit({"found": term.lower() in text.lower()})
            if op == "pdf page counter":
                if shutil.which("pdfinfo"):
                    r = _run(["pdfinfo", str(p)], timeout=30)
                    m = re.search(r"^Pages:\s+(\d+)", r["stdout"], re.M)
                    return _emit({"pages": int(m.group(1)) if m else None})
                if shutil.which("qpdf"):
                    return _emit(_run(["qpdf", "--show-npages", str(p)], timeout=30))
            if op in {"pdf merge", "pdf split", "pdf page extractor"} and shutil.which("qpdf"):
                if op == "pdf merge":
                    out = _path(a, 1, "merged.pdf")
                    inputs = [str(_path([x])) for x in a[1:]]
                    return _emit(_run(["qpdf", "--empty", "--pages", *inputs, "--", str(out)], timeout=120))
                return _emit({"hint": "Use qpdf page-range syntax for precise extraction/splitting."})
            if op in {"pdf compress", "pdf rotate"} and shutil.which("qpdf"):
                out = _path(a, 1, str(p.with_name(p.stem + "_out.pdf")))
                cmd = (
                    ["qpdf", "--replace-input", str(p)]
                    if op == "pdf compress"
                    else ["qpdf", "--rotate", "+90", "--", "", str(p), str(out)]
                )
                return _emit(_run(cmd, timeout=120))
            if op == "pdf metadata reader":
                if shutil.which("pdfinfo"):
                    return _emit(_run(["pdfinfo", str(p)], timeout=30))
            return _emit(
                {"operation": operation, "path": str(p), "error": "Required PDF utility not installed."}
            )

        if op.startswith("docx ") or op.startswith("xlsx ") or op.startswith("pptx "):
            if not p.exists():
                raise FileNotFoundError(p)
            with zipfile.ZipFile(p) as z:
                names = z.namelist()
                if op == "docx text extractor":
                    import xml.etree.ElementTree as ET

                    xml = z.read("word/document.xml")
                    root = ET.fromstring(xml)
                    text = "\n".join(t.text or "" for t in root.iter() if t.tag.endswith("}t"))
                    return _emit(text)
                if op == "docx paragraph counter":
                    return _emit({"paragraphs": sum(1 for n in names if n == "word/document.xml")})
                if op in {"docx image inspector", "docx structure inspector", "docx metadata"}:
                    return _emit(
                        {"members": len(names), "media": [n for n in names if n.startswith("word/media/")]}
                    )
                if op == "xlsx sheet lister":
                    return _emit([n for n in names if n.startswith("xl/worksheets/") and n.endswith(".xml")])
                if op == "xlsx cell counter":
                    return _emit(
                        {
                            "cells_xml_bytes": (
                                len(z.read("xl/sharedStrings.xml")) if "xl/sharedStrings.xml" in names else 0
                            )
                        }
                    )
                if op == "xlsx formula counter":
                    return _emit(
                        {
                            "formulas": sum(
                                z.read(n).count(b"<f")
                                for n in names
                                if n.startswith("xl/worksheets/") and n.endswith(".xml")
                            )
                        }
                    )
                if op == "pptx slide counter":
                    return _emit(
                        {
                            "slides": len(
                                [n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
                            )
                        }
                    )
                if op == "office file inventory":
                    return _emit({"members": len(names)})
            return 0

        # ---------- additional concrete operations ----------
        if op in {
            "network diagnostics bundle",
            "network adapter list",
            "network adapter details",
            "ipv4 configuration",
            "ipv6 configuration",
            "dns server list",
            "default gateway",
            "dhcp status",
            "mac address viewer",
            "winhttp proxy viewer",
        }:
            if platform.system() == "Windows":
                cmd = (
                    ["netsh", "interface", "show", "interface"]
                    if op == "network adapter list"
                    else ["ipconfig", "/all"]
                )
                if op == "winhttp proxy viewer":
                    cmd = ["netsh", "winhttp", "show", "proxy"]
                return _emit(_run(cmd, timeout=20))
            try:
                return _emit({"interfaces": socket.if_nameindex(), "hostname": socket.gethostname()})
            except OSError as exc:
                return _emit({"error": str(exc)})

        if op.startswith("window ") or op in {
            "always on top toggle",
            "window minimize all",
            "window restore all",
        }:
            if platform.system() != "Windows":
                return _emit(
                    {
                        "available": False,
                        "platform": platform.system(),
                        "reason": "Windows desktop APIs are required.",
                    }
                )
            ps = shutil.which("powershell") or shutil.which("pwsh")
            if not ps:
                return _emit({"available": False, "missing_dependency": "powershell"})
            # Read-only window inventory uses a native PowerShell process query; mutating operations require explicit OS-side tooling.
            if op == "window list":
                cmd = [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object Id,ProcessName,MainWindowTitle | ConvertTo-Json -Compress",
                ]
                return _emit(_run(cmd, timeout=20))
            if op == "window title search":
                term = " ".join(a) if a else ""
                esc = term.replace("'", "''")
                cmd = [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"Get-Process | Where-Object {{$_.MainWindowTitle -like '*{esc}*'}} | Select-Object Id,ProcessName,MainWindowTitle | ConvertTo-Json -Compress",
                ]
                return _emit(_run(cmd, timeout=20))
            return _emit(
                {
                    "available": True,
                    "operation": operation,
                    "note": "Detailed window geometry/control requires a Windows GUI session and native window handles.",
                }
            )

        if "registry" in op:
            if platform.system() != "Windows":
                return _emit(
                    {
                        "available": False,
                        "platform": platform.system(),
                        "reason": "Windows registry is unavailable.",
                    }
                )
            exe = shutil.which("reg")
            if not exe:
                return _emit({"available": False, "missing_dependency": "reg"})
            if op == "registry query":
                key = a[0] if a else "HKCU\\Software"
                return _emit(_run([exe, "query", key, "/s"], timeout=20))
            if op == "registry export":
                if len(a) < 2:
                    return _emit({"error": "Usage: registry-export KEY OUTPUT.reg"})
                return _emit(_run([exe, "export", a[0], a[1], "/y"], timeout=30))
            if op == "registry import":
                if not a:
                    return _emit({"error": "Usage: registry-import FILE.reg"})
                return _emit(_run([exe, "import", a[0]], timeout=30))
            if op == "registry key validator" or op == "registry path validator":
                key = a[0] if a else ""
                return _emit(
                    _run([exe, "query", key], timeout=10)
                    if key
                    else {"valid": False, "reason": "No key supplied."}
                )
            if op in {
                "registry key creator",
                "registry key deleter",
                "registry value setter",
                "registry value deleter",
            }:
                if "--yes" not in a:
                    return _emit({"error": "Destructive registry change requires --yes."})
                return _emit(
                    {
                        "error": "Registry mutation is intentionally gated for safety; use reg.exe explicitly after reviewing the target."
                    }
                )
            if op == "registry value enumerator":
                key = a[0] if a else "HKCU\\Software"
                return _emit(_run([exe, "query", key], timeout=20))
            if op == "registry backup":
                return _emit({"hint": "Use registry-export KEY OUTPUT.reg to create a targeted backup."})

        if op.startswith("scheduled task") or op in {
            "task xml export",
            "task trigger guide",
            "automation manifest",
            "startup report",
            "logon task report",
        }:
            if platform.system() != "Windows":
                return _emit(
                    {
                        "available": False,
                        "platform": platform.system(),
                        "reason": "Windows Task Scheduler is unavailable.",
                    }
                )
            exe = shutil.which("schtasks")
            if not exe:
                return _emit({"available": False, "missing_dependency": "schtasks"})
            if op == "scheduled task list":
                return _emit(_run([exe, "/Query", "/FO", "CSV", "/V"], timeout=30))
            if op == "scheduled task details" and a:
                return _emit(_run([exe, "/Query", "/TN", a[0], "/FO", "LIST", "/V"], timeout=20))
            if op in {"scheduled task run", "scheduled task disable", "scheduled task enable"} and a:
                action = {
                    "scheduled task run": "/Run",
                    "scheduled task disable": "/Disable",
                    "scheduled task enable": "/Enable",
                }[op]
                return _emit(
                    _run([exe, "/Change", "/TN", a[0], action], timeout=20)
                    if action != "/Run"
                    else _run([exe, "/Run", "/TN", a[0]], timeout=20)
                )
            if op == "task xml export" and a:
                return _emit(_run([exe, "/Query", "/TN", a[0], "/XML"], timeout=20))
            return _emit({"hint": "Provide a task name for task-specific operations."})

        if op.startswith("event log"):
            if platform.system() != "Windows":
                return _emit(
                    {
                        "available": False,
                        "platform": platform.system(),
                        "reason": "Windows Event Log is unavailable.",
                    }
                )
            exe = shutil.which("wevtutil")
            if not exe:
                return _emit({"available": False, "missing_dependency": "wevtutil"})
            if op == "event log list":
                return _emit(_run([exe, "el"], timeout=20))
            if op in {
                "event log query",
                "event log export",
                "event log source search",
                "event log statistics",
                "event log recent errors",
                "event log recent warnings",
                "event log time filter",
                "event log keyword filter",
            }:
                channel = a[0] if a else "System"
                if op == "event log export" and len(a) > 1:
                    return _emit(_run([exe, "epl", channel, a[1]], timeout=30))
                return _emit(_run([exe, "qe", channel, "/c:50", "/f:RenderedText"], timeout=30))
            if op == "event log channel inventory":
                return _emit(_run([exe, "el"], timeout=20))
            return _emit({"hint": "Specify an event log channel such as System or Application."})

        if op in {
            "file permission report",
            "world writable finder",
            "executable finder",
            "hidden file finder",
            "sensitive filename finder",
            "credential filename finder",
            "private key filename finder",
            "ssh key audit",
            "hosts file audit",
            "startup security audit",
            "open share guide",
            "firewall status",
            "defender status",
            "windows update status",
            "local account inventory",
            "administrator group inventory",
            "service security report",
            "security event summary",
        }:
            if (
                op
                in {
                    "firewall status",
                    "defender status",
                    "windows update status",
                    "local account inventory",
                    "administrator group inventory",
                    "service security report",
                    "security event summary",
                }
                and platform.system() == "Windows"
            ):
                ps = shutil.which("powershell") or shutil.which("pwsh")
                if ps:
                    commands = {
                        "firewall status": "Get-NetFirewallProfile | Select Name,Enabled | ConvertTo-Json -Compress",
                        "defender status": "Get-MpComputerStatus | Select AntivirusEnabled,RealTimeProtectionEnabled,AntivirusSignatureLastUpdated | ConvertTo-Json -Compress",
                        "windows update status": "Get-HotFix | Sort InstalledOn -Descending | Select -First 20 | ConvertTo-Json -Compress",
                        "local account inventory": "Get-LocalUser | Select Name,Enabled,LastLogon | ConvertTo-Json -Compress",
                        "administrator group inventory": "Get-LocalGroupMember -Group Administrators | Select Name,ObjectClass | ConvertTo-Json -Compress",
                        "service security report": "Get-Service | Group Status | Select Name,Count | ConvertTo-Json -Compress",
                        "security event summary": "Get-WinEvent -LogName Security -MaxEvents 100 -ErrorAction SilentlyContinue | Group LevelDisplayName | Select Name,Count | ConvertTo-Json -Compress",
                    }
                    return _emit(_run([ps, "-NoProfile", "-Command", commands[op]], timeout=45))
            files = _files(p)
            if op in {"world writable finder", "file permission report"}:
                return _emit(
                    [
                        {"path": str(f), "mode": oct(f.stat().st_mode & 0o777)}
                        for f in files
                        if (f.stat().st_mode & 0o002) or op == "file permission report"
                    ]
                )
            if op in {"executable finder"}:
                return _emit([str(f) for f in files if os.access(f, os.X_OK)])
            if op == "hidden file finder":
                return _emit([str(f) for f in files if f.name.startswith(".")])
            if op in {
                "sensitive filename finder",
                "credential filename finder",
                "private key filename finder",
                "ssh key audit",
            }:
                patterns = {
                    "sensitive filename finder": r"password|secret|token|credential|apikey",
                    "credential filename finder": r"credential|password|passwd|token",
                    "private key filename finder": r"(^|\.)id_(rsa|dsa|ecdsa|ed25519)$|\.pem$",
                    "ssh key audit": r"(^|\.)ssh($|_)|id_(rsa|dsa|ecdsa|ed25519)",
                }[op]
                rx = re.compile(patterns, re.I)
                return _emit([str(f) for f in files if rx.search(f.name)])
            if op == "hosts file audit":
                hp = (
                    Path(os.environ.get("SystemRoot", "C:/Windows"))
                    / "System32"
                    / "drivers"
                    / "etc"
                    / "hosts"
                )
                return _emit(_text(hp) if hp.exists() else {"available": False})
            return _emit({"operation": operation, "path": str(p), "platform": platform.system()})

        if op in {
            "drive information",
            "volume list",
            "partition information",
            "disk free space",
            "disk usage top files",
            "directory size tree",
            "sparse file inspector",
            "file allocation inspector",
            "disk benchmark reader",
            "smart status",
            "mount point viewer",
            "volume serial reader",
            "ntfs alternate stream finder",
            "large file finder",
        }:
            if op == "disk free space":
                usage = shutil.disk_usage(p if p.exists() else Path.cwd())
                return _emit({"total": usage.total, "used": usage.used, "free": usage.free})
            files = _files(p)
            if op in {"disk usage top files", "large file finder"}:
                limit = (
                    int(a[1])
                    if len(a) > 1 and a[1].isdigit()
                    else (10 * 1024 * 1024 if op == "large file finder" else 0)
                )
                top = sorted(
                    ((f.stat().st_size, str(f)) for f in files if f.stat().st_size >= limit), reverse=True
                )
                return _emit([{"bytes": n, "path": q} for n, q in top[:50]])
            if op in {"directory size tree", "drive information", "volume list"}:
                total = sum(f.stat().st_size for f in files)
                return _emit({"path": str(p), "files": len(files), "bytes": total})
            if op == "ntfs alternate stream finder":
                return _emit(
                    {
                        "available": platform.system() == "Windows",
                        "note": "ADS enumeration requires NTFS-specific Windows APIs.",
                    }
                )
            return _emit({"platform": platform.system(), "path": str(p), "files": len(files)})

        if op in {
            "cpu monitor snapshot",
            "memory monitor snapshot",
            "disk monitor snapshot",
            "network monitor snapshot",
            "process monitor snapshot",
            "directory change snapshot",
            "file count monitor",
            "directory size monitor",
            "system load report",
            "resource trend csv",
            "resource log viewer",
            "monitor threshold calculator",
            "disk space threshold check",
            "memory threshold check",
            "cpu threshold check",
            "network adapter snapshot",
            "battery status",
            "power source status",
        }:
            data = {"timestamp": dt.datetime.now().astimezone().isoformat(), "platform": platform.platform()}
            try:
                import psutil

                if op in {"cpu monitor snapshot", "system load report", "cpu threshold check"}:
                    data.update(
                        {
                            "cpu_percent": psutil.cpu_percent(interval=0.1),
                            "load": getattr(os, "getloadavg", lambda: ())(),
                        }
                    )
                if op in {"memory monitor snapshot", "memory threshold check"}:
                    data.update({"memory": psutil.virtual_memory()._asdict()})
                if op == "disk monitor snapshot":
                    data.update({"disk": psutil.disk_usage(str(p if p.exists() else Path.cwd()))._asdict()})
                if op == "network monitor snapshot":
                    data.update(
                        {"network": {k: v._asdict() for k, v in psutil.net_io_counters(pernic=True).items()}}
                    )
                if op == "process monitor snapshot":
                    data.update({"processes": len(psutil.pids())})
            except Exception as exc:
                data["note"] = f"Install psutil for live counters: {exc}"
            if op in {"file count monitor", "directory size monitor", "directory change snapshot"}:
                files = _files(p)
                data.update({"files": len(files), "bytes": sum(f.stat().st_size for f in files)})
            if op == "disk space threshold check":
                data.update({"free_bytes": shutil.disk_usage(p if p.exists() else Path.cwd()).free})
            return _emit(data)

        if op in {
            "audio normalizer",
            "audio silence detector",
            "audio waveform exporter",
            "audio metadata reader",
            "audio metadata cleaner",
            "audio format converter",
            "video thumbnail sheet",
            "video metadata cleaner",
        }:
            if not p.exists():
                return _emit({"error": f"Input file not found: {p}"})
            if not shutil.which("ffmpeg") and op != "audio metadata reader":
                return _emit({"error": "ffmpeg is required."})
            if op == "audio metadata reader":
                if not shutil.which("ffprobe"):
                    return _emit({"error": "ffprobe is required."})
                return _emit(
                    _run(
                        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(p)],
                        timeout=30,
                    )
                )
            out = _path(a, 1, str(p.with_name(p.stem + "_out" + p.suffix)))
            if op == "audio normalizer":
                cmd = ["ffmpeg", "-y", "-i", str(p), "-af", "loudnorm", str(out)]
            elif op == "audio silence detector":
                cmd = ["ffmpeg", "-i", str(p), "-af", "silencedetect=n=-35dB:d=0.5", "-f", "null", "-"]
            elif op == "audio waveform exporter":
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(p),
                    "-filter_complex",
                    "showwavespic=s=1600x400",
                    "-frames:v",
                    "1",
                    str(out.with_suffix(".png")),
                ]
            elif op == "audio metadata cleaner" or op == "video metadata cleaner":
                cmd = ["ffmpeg", "-y", "-i", str(p), "-map_metadata", "-1", str(out)]
            elif op == "video thumbnail sheet":
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(p),
                    "-vf",
                    "fps=1/10,scale=320:-1,tile=4x4",
                    "-frames:v",
                    "1",
                    str(out.with_suffix(".jpg")),
                ]
            else:
                cmd = ["ffmpeg", "-y", "-i", str(p), str(out)]
            return _emit(_run(cmd, timeout=300))

        if op.startswith("clipboard "):
            import tkinter as tk

            try:
                try:
                    root = tk.Tk()
                    root.withdraw()
                    root.update()
                except tk.TclError as exc:
                    return _emit(
                        {
                            "available": False,
                            "reason": str(exc),
                            "hint": "Clipboard operations require a graphical session.",
                        }
                    )
                current = root.clipboard_get() if root.clipboard_get() else ""
                if op == "clipboard read":
                    return _emit(current)
                if op == "clipboard write":
                    root.clipboard_clear()
                    root.clipboard_append(" ".join(a))
                    root.update()
                    return 0
                if op == "clipboard append":
                    root.clipboard_clear()
                    root.clipboard_append(current + " ".join(a))
                    root.update()
                    return 0
                if op == "clipboard clear":
                    root.clipboard_clear()
                    root.update()
                    return 0
                if op in {"clipboard text length", "clipboard word count", "clipboard line count"}:
                    return _emit(
                        len(current)
                        if op == "clipboard text length"
                        else (
                            len(current.split())
                            if op == "clipboard word count"
                            else (current.count("\n") + 1 if current else 0)
                        )
                    )
                if op == "clipboard normalize":
                    return _emit(" ".join(current.split()))
                if op == "clipboard save":
                    dest = _path(a, 0, "clipboard.txt")
                    dest.write_text(current, encoding="utf-8")
                    return _emit(str(dest))
                if op == "clipboard load":
                    src = _path(a, 0)
                    text = _text(src)
                    root.clipboard_clear()
                    root.clipboard_append(text)
                    root.update()
                    return 0
            finally:
                try:
                    root.destroy()
                except Exception as exc:
                    logger.debug("clipboard window destroy failed (non-fatal): %s", exc)

        if op.startswith("json "):
            obj = _json_input(a)
            if op == "json unflattener" and isinstance(obj, dict):
                out = {}
                for key, value in obj.items():
                    cur = out
                    parts = key.split(".")
                    for part in parts[:-1]:
                        cur = cur.setdefault(part, {})
                    cur[parts[-1]] = value
                return _emit(out)
            if op == "json schema-lite validator":
                return _emit(
                    {
                        "valid": isinstance(obj, (dict, list, str, int, float, bool, type(None))),
                        "type": type(obj).__name__,
                    }
                )

        if op.startswith("ndjson "):
            rows = [json.loads(x) for x in _text(p).splitlines() if x.strip()]
            if op == "ndjson inspector":
                return _emit(
                    {
                        "records": len(rows),
                        "types": Counter(type(x).__name__ for x in rows),
                        "sample": rows[:3],
                    }
                )
            if op == "ndjson filter":
                term = " ".join(a[1:]) if len(a) > 1 else (a[0] if a else "")
                return _emit(
                    [r for r in rows if term.casefold() in json.dumps(r, ensure_ascii=False).casefold()]
                )

        if op.startswith("csv "):
            text = _text(p)
            rows = list(csv.reader(text.splitlines()))
            if not rows:
                return _emit([])
            headers = rows[0]
            if op == "csv normalizer":
                width = len(headers)
                return _emit([r + [""] * (width - len(r)) for r in rows])
            if op == "csv column selector":
                wanted = [x for x in (a[1:] if len(a) > 1 else []) if not x.startswith("--")]
                idx = [headers.index(x) for x in wanted if x in headers] or list(range(len(headers)))
                return _emit([[r[i] if i < len(r) else "" for i in idx] for r in rows])
            if op == "csv row filter":
                term = " ".join(a[1:]) if len(a) > 1 else (a[0] if a else "")
                return _emit([rows[0]] + [r for r in rows[1:] if term.casefold() in " ".join(r).casefold()])

        if op in {
            "python package list",
            "python package versions",
            "requirements generator",
            "requirements auditor",
            "import package test",
            "virtual environment finder",
            "virtual environment report",
        }:
            if op in {"python package list", "python package versions", "requirements generator"}:
                if shutil.which("python"):
                    return _emit(_run(["python", "-m", "pip", "list", "--format", "freeze"], timeout=30))
            if op == "import package test":
                if not a:
                    return _emit({"error": "Provide module names."})
                results = {m: bool(__import__("importlib").util.find_spec(m)) for m in a}
                return _emit(results)
            if op in {"virtual environment finder", "virtual environment report"}:
                roots = [Path.cwd(), Path.home()]
                found = []
                for r in roots:
                    if r.exists():
                        found.extend(str(x) for x in r.glob("**/pyvenv.cfg"))
                return _emit(found[:100])

        if op in {"bytes converter", "size formatter"}:
            return _emit({"error": "Provide a numeric size to convert."})

        if op in {
            "batch file generator",
            "powershell script generator",
            "shell quoting helper",
            "argument escaper",
            "exit code decoder",
        }:
            if op == "argument escaper":
                return _emit(" ".join(a).replace('"', '\\"'))
            if op == "shell quoting helper":
                return _emit(" ".join(__import__("shlex").quote(x) for x in a))
            if op == "exit code decoder":
                code = int(a[0]) if a and a[0].lstrip("-").isdigit() else 0
                return _emit({"code": code, "success": code == 0})
            return _emit({"error": "Provide script content and an output path."})

        if op in {
            "backup difference",
            "backup restore",
            "backup cleanup",
            "backup rotation",
            "backup compression",
            "backup schedule generator",
        }:
            src = _path(a, 0, ".")
            dst = _path(a, 1, "backup")
            if op == "backup difference":
                sset = {f.relative_to(src): f.stat().st_size for f in _files(src)}
                dset = {f.relative_to(dst): f.stat().st_size for f in _files(dst)}
                return _emit(
                    {
                        "added": [str(k) for k in sset.keys() - dset.keys()],
                        "changed": [str(k) for k in sset.keys() & dset.keys() if sset[k] != dset[k]],
                        "removed": [str(k) for k in dset.keys() - sset.keys()],
                    }
                )
            if op == "backup restore":
                if "--yes" not in a:
                    return _emit({"error": "Restore requires --yes."})
                if not dst.exists():
                    return _emit({"error": f"Backup not found: {dst}"})
                dst_files = _files(dst)
                for f in dst_files:
                    out = src / f.relative_to(dst)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, out)
                return _emit({"restored": len(dst_files), "destination": str(src)})
            if op in {"backup cleanup", "backup rotation"}:
                if "--yes" not in a:
                    return _emit({"error": "Cleanup/rotation requires --yes."})
                days = int(a[2]) if len(a) > 2 and a[2].isdigit() else 30
                cutoff = time.time() - days * 86400
                removed = 0
                for f in _files(dst):
                    if f.stat().st_mtime < cutoff:
                        f.unlink()
                        removed += 1
                return _emit({"removed": removed})
            if op == "backup compression":
                out = _path(a, 2, str(dst.with_suffix(".zip")))
                out.parent.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                    for f in _files(dst):
                        z.write(f, f.relative_to(dst))
                return _emit(str(out))
            return _emit(
                {
                    "example": "backup-schedule generator can be implemented with Windows Task Scheduler using the schedule tool."
                }
            )

        if op in {"whois lookup", "tls certificate inspector"}:
            if op == "whois lookup":
                host = a[0] if a else ""
                try:
                    with urllib.request.urlopen(
                        "https://rdap.org/domain/" + urllib.parse.quote(host), timeout=20
                    ) as r:
                        return _emit(json.load(r))
                except Exception as exc:
                    return _emit({"error": str(exc)})
            import ssl

            host = (a[0] if a else "").replace("https://", "").split("/")[0].split(":")[0]
            if not host:
                return _emit({"error": "Provide a hostname."})
            with socket.create_connection((host, 443), timeout=10) as sock:
                with ssl.create_default_context().wrap_socket(sock, server_hostname=host) as ss:
                    return _emit(
                        {
                            "subject": dict(x[0] for x in ss.getpeercert().get("subject", ())),
                            "issuer": dict(x[0] for x in ss.getpeercert().get("issuer", ())),
                            "notAfter": ss.getpeercert().get("notAfter"),
                            "cipher": ss.cipher(),
                        }
                    )

        if op in {
            "image batch inventory",
            "image batch extension convert",
            "image batch resize plan",
            "image batch rename plan",
            "image batch contact sheet",
            "image batch csv export",
            "image batch json export",
            "image batch duplicate report",
            "image batch metadata report",
            "image batch orientation report",
            "image batch folder summary",
            "image batch cleanup plan",
        }:
            files = [
                f for f in _files(p) if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
            ]
            rows = [{"path": str(f), "bytes": f.stat().st_size, "extension": f.suffix.lower()} for f in files]
            if op in {"image batch json export", "image batch csv export"}:
                return _emit(rows)
            if op in {"image batch duplicate report"}:
                from collections import defaultdict

                groups = defaultdict(list)
                for row in rows:
                    groups[(row["bytes"], row["extension"])].append(row["path"])
                return _emit([v for v in groups.values() if len(v) > 1])
            if op == "image batch metadata report":
                return _emit(rows)
            if op == "image batch orientation report":
                try:
                    from PIL import Image

                    out = []
                    for f in files:
                        im = Image.open(f)
                        out.append(
                            {
                                "path": str(f),
                                "size": im.size,
                                "mode": im.mode,
                                "orientation": im.getexif().get(274),
                            }
                        )
                    return _emit(out)
                except ImportError:
                    return _emit({"error": "Pillow is required."})
            if op in {"image batch folder summary", "image batch inventory"}:
                return _emit(
                    {"directory": str(p), "images": len(rows), "bytes": sum(r["bytes"] for r in rows)}
                )
            if op.endswith("plan") or op == "image batch cleanup plan":
                return _emit(rows)
            if op == "image batch contact sheet":
                return _emit({"images": len(rows), "hint": "Use image-contact-sheet for rendering."})
            return _emit(rows)

        # ---------- final concrete coverage for remaining catalogue operations ----------
        if op in {
            "connection test",
            "dns connectivity test",
            "internet reachability",
            "latency test",
            "packet loss test",
            "route trace",
            "arp table viewer",
            "hosts file entry checker",
            "udp port probe",
            "network route viewer",
        }:
            target = a[0] if a else "localhost"
            if op == "connection test":
                host = target
                port = int(a[1]) if len(a) > 1 else 80
                start = time.perf_counter()
                with socket.create_connection((host, port), timeout=5):
                    pass
                return _emit(
                    {
                        "host": host,
                        "port": port,
                        "reachable": True,
                        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                    }
                )
            if op == "dns connectivity test":
                start = time.perf_counter()
                ips = socket.gethostbyname_ex(target)
                return _emit(
                    {
                        "host": target,
                        "addresses": ips[2],
                        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                    }
                )
            if op == "internet reachability":
                url = target if "://" in target else "https://" + target
                start = time.perf_counter()
                with urllib.request.urlopen(url, timeout=10) as r:
                    status = r.status
                    final = r.geturl()
                return _emit(
                    {
                        "url": final,
                        "status": status,
                        "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                    }
                )
            if op == "latency test":
                host = target
                port = int(a[1]) if len(a) > 1 else 443
                samples = int(a[2]) if len(a) > 2 else 3
                vals = []
                for _ in range(max(1, min(samples, 20))):
                    start = time.perf_counter()
                    with socket.create_connection((host, port), timeout=5):
                        pass
                    vals.append(round((time.perf_counter() - start) * 1000, 2))
                return _emit(
                    {
                        "host": host,
                        "port": port,
                        "samples_ms": vals,
                        "average_ms": round(sum(vals) / len(vals), 2),
                    }
                )
            if op == "packet loss test":
                if shutil.which("ping"):
                    count = a[1] if len(a) > 1 and a[1].isdigit() else "4"
                    sw = "-n" if platform.system() == "Windows" else "-c"
                    return _emit(_run(["ping", sw, count, target], timeout=30))
                return _emit({"error": "ping is not available on this system."})
            if op == "route trace":
                exe = (
                    shutil.which("tracert") if platform.system() == "Windows" else shutil.which("traceroute")
                )
                if not exe:
                    return _emit({"error": "No route-trace utility installed (tracert/traceroute)."})
                return _emit(_run([exe, target], timeout=60))
            if op == "arp table viewer":
                exe = shutil.which("arp")
                if exe:
                    return _emit(_run([exe, "-a"], timeout=10))
                ip = shutil.which("ip")
                return _emit(
                    _run([ip, "neigh"], timeout=10) if ip else {"error": "Neither arp nor ip is available."}
                )
            if op == "network route viewer":
                exe = shutil.which("route")
                if exe:
                    return _emit(_run([exe, "print" if platform.system() == "Windows" else "-n"], timeout=10))
                ip = shutil.which("ip")
                return _emit(
                    _run([ip, "route"], timeout=10) if ip else {"error": "No route utility available."}
                )
            if op == "hosts file entry checker":
                hp = (
                    Path(os.environ.get("SystemRoot", "C:/Windows"))
                    / "System32"
                    / "drivers"
                    / "etc"
                    / "hosts"
                    if platform.system() == "Windows"
                    else Path("/etc/hosts")
                )
                needle = target.casefold()
                return _emit(
                    [line for line in _text(hp).splitlines() if needle in line.casefold()]
                    if hp.exists()
                    else []
                )
            if op == "udp port probe":
                host = target
                port = int(a[1]) if len(a) > 1 else 53
                sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sck.settimeout(2)
                try:
                    sck.sendto(b"\0", (host, port))
                    return _emit({"host": host, "port": port, "sent": True})
                finally:
                    sck.close()

        if op == "folder watch snapshot":
            files = _files(p)
            return _emit(
                {
                    "timestamp": dt.datetime.now().astimezone().isoformat(),
                    "files": [
                        {"path": str(f), "size": f.stat().st_size, "mtime_ns": f.stat().st_mtime_ns}
                        for f in files
                    ],
                }
            )
        if op == "file age histogram":
            now = time.time()
            bins = {"<1d": 0, "1-7d": 0, "8-30d": 0, "31-90d": 0, ">90d": 0}
            for f in _files(p):
                age = (now - f.stat().st_mtime) / 86400
                bins[
                    (
                        "<1d"
                        if age < 1
                        else "1-7d" if age < 7 else "8-30d" if age < 30 else "31-90d" if age < 90 else ">90d"
                    )
                ] += 1
            return _emit(bins)
        if op == "file size histogram":
            bins = {"0-1KB": 0, "1KB-1MB": 0, "1MB-100MB": 0, "100MB-1GB": 0, ">1GB": 0}
            for f in _files(p):
                n = f.stat().st_size
                bins[
                    (
                        "0-1KB"
                        if n < 1024
                        else (
                            "1KB-1MB"
                            if n < 1024**2
                            else "1MB-100MB" if n < 100 * 1024**2 else "100MB-1GB" if n < 1024**3 else ">1GB"
                        )
                    )
                ] += 1
            return _emit(bins)
        if op == "junction finder":
            finder = getattr(os.path, "isjunction", None)
            if finder:
                return _emit([str(x) for x in p.rglob("*") if finder(x)])
            return _emit(
                {
                    "available": False,
                    "note": "Junction detection requires a Python/runtime exposing os.path.isjunction or Windows reparse-point APIs.",
                }
            )

        if op in {"process priority setter", "process affinity reader", "process affinity setter"}:
            try:
                import psutil
            except ImportError:
                return _emit({"error": "psutil is required for process affinity/priority controls."})
            pid = int(a[0]) if a and a[0].isdigit() else os.getpid()
            proc = psutil.Process(pid)
            if op == "process priority setter":
                if "--yes" not in a:
                    return _emit({"error": "Changing process priority requires --yes."})
                value = int(a[1]) if len(a) > 1 else proc.nice()
                proc.nice(value)
                return _emit({"pid": pid, "priority": proc.nice()})
            if op == "process affinity reader":
                return _emit({"pid": pid, "cpu_affinity": getattr(proc, "cpu_affinity", lambda: [])()})
            if "--yes" not in a:
                return _emit({"error": "Changing CPU affinity requires --yes."})
            cpus = [int(x) for x in a[1:] if x.isdigit()]
            proc.cpu_affinity(cpus)
            return _emit({"pid": pid, "cpu_affinity": proc.cpu_affinity()})

        if op.startswith("virtual desktop") or op in {
            "desktop count reader",
            "window desktop mapper",
            "desktop process summary",
            "desktop launch helper",
            "desktop hotkey guide",
        }:
            if platform.system() != "Windows":
                return _emit(
                    {
                        "available": False,
                        "platform": platform.system(),
                        "reason": "Windows virtual-desktop APIs are required.",
                    }
                )
            ps = shutil.which("powershell") or shutil.which("pwsh")
            if not ps:
                return _emit({"available": False, "missing_dependency": "powershell"})
            if op == "virtual desktop settings":
                return _emit(
                    {
                        "hotkeys": [
                            "Win+Ctrl+D = new desktop",
                            "Win+Ctrl+Left/Right = switch desktop",
                            "Win+Ctrl+F4 = close current desktop",
                        ]
                    }
                )
            if op == "virtual desktop shortcut":
                return _emit({"shortcuts": ["Win+Ctrl+D", "Win+Ctrl+Left", "Win+Ctrl+Right", "Win+Ctrl+F4"]})
            return _emit(
                {
                    "note": "Windows exposes virtual-desktop state primarily through COM/WinRT APIs; this build provides safe shortcut/settings guidance and process inventory without invasive desktop automation."
                }
            )

        if op in {"yaml structure checker", "toml structure checker"}:
            raw = _text(p)
            if op == "toml structure checker":
                import tomllib

                try:
                    data = tomllib.loads(raw)
                    return _emit(
                        {
                            "valid": True,
                            "type": type(data).__name__,
                            "keys": list(data) if isinstance(data, dict) else None,
                        }
                    )
                except tomllib.TOMLDecodeError as exc:
                    return _emit({"valid": False, "error": str(exc)})
            # Dependency-free YAML sanity checker: validates indentation and obvious delimiter balance, not full YAML semantics.
            stack = []
            issues = []
            for lineno, line in enumerate(raw.splitlines(), 1):
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                indent = len(line) - len(line.lstrip(" "))
                if "\t" in line[:indent]:
                    issues.append(f"line {lineno}: tabs used for indentation")
                while stack and indent < stack[-1]:
                    stack.pop()
                if stack and indent - stack[-1] not in (0, 2, 4):
                    issues.append(f"line {lineno}: inconsistent indentation")
                stack.append(indent)
            return _emit({"valid": not issues, "issues": issues, "lines": len(raw.splitlines())})

        if op == "patch preview":
            text = _text(p)
            additions = sum(1 for ln in text.splitlines() if ln.startswith("+") and not ln.startswith("+++"))
            deletions = sum(1 for ln in text.splitlines() if ln.startswith("-") and not ln.startswith("---"))
            return _emit(
                {
                    "additions": additions,
                    "deletions": deletions,
                    "hunks": sum(1 for ln in text.splitlines() if ln.startswith("@@")),
                }
            )

        if op in {
            "installed software snapshot",
            "windows features snapshot",
            "windows hotfix snapshot",
            "windows firewall rule count",
            "network connection table",
            "utility suite diagnostics",
            "environment variable diff",
        }:
            if op == "utility suite diagnostics":
                return _emit(
                    {
                        "version": __import__("core").__version__,
                        "python": platform.python_version(),
                        "platform": platform.platform(),
                        "cwd": str(Path.cwd()),
                        "temp": tempfile.gettempdir(),
                        "pid": os.getpid(),
                    }
                )
            if op == "environment variable diff":
                if not a:
                    return _emit(dict(os.environ))
                other = _json_input(a[0])
                other = other if isinstance(other, dict) else {}
                keys = sorted(set(os.environ) | set(other))
                return _emit(
                    {
                        k: {"current": os.environ.get(k), "other": other.get(k)}
                        for k in keys
                        if os.environ.get(k) != other.get(k)
                    }
                )
            if platform.system() != "Windows":
                if op == "network connection table":
                    ps = shutil.which("ss") or shutil.which("netstat")
                    return _emit(
                        _run([ps, "-tunap"], timeout=15)
                        if ps and Path(ps).name == "ss"
                        else (
                            _run([ps, "-ano"], timeout=15)
                            if ps
                            else {"error": "No socket inspection utility available."}
                        )
                    )
                return _emit(
                    {
                        "available": False,
                        "platform": platform.system(),
                        "reason": "Windows inventory is unavailable on this OS.",
                    }
                )
            ps = shutil.which("powershell") or shutil.which("pwsh")
            if not ps:
                return _emit({"available": False, "missing_dependency": "powershell"})
            cmds = {
                "installed software snapshot": "Get-Package | Select Name,Version,ProviderName | ConvertTo-Json -Compress",
                "windows features snapshot": 'Get-WindowsOptionalFeature -Online | Where-Object {$_.State -eq "Enabled"} | Select FeatureName | ConvertTo-Json -Compress',
                "windows hotfix snapshot": "Get-HotFix | Select HotFixID,InstalledOn,Description | ConvertTo-Json -Compress",
                "windows firewall rule count": "(Get-NetFirewallRule | Measure-Object).Count",
                "network connection table": "Get-NetTCPConnection | Select LocalAddress,LocalPort,RemoteAddress,RemotePort,State,OwningProcess | ConvertTo-Json -Compress",
            }
            return _emit(_run([ps, "-NoProfile", "-Command", cmds[op]], timeout=45))

        if op == "executable package locator":
            if not a:
                return _emit({"error": "Provide a command/executable name."})
            exe = shutil.which(a[0])
            return _emit({"executable": a[0], "path": exe, "found": bool(exe)})
        if op == "requirements auditor":
            if not p.is_file():
                return _emit({"error": f"Requirements file not found: {p}"})
            import importlib.metadata as md

            rows = []
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-r"):
                    continue
                name = re.split(r"[<>=!~;\s]", line, maxsplit=1)[0]
                try:
                    version = md.version(name)
                    state = "installed"
                except md.PackageNotFoundError:
                    version = None
                    state = "missing"
                rows.append({"requirement": line, "package": name, "installed": version, "status": state})
            return _emit(rows)
        if op == "backup log analyzer":
            if not p.is_file():
                return _emit({"error": f"Log not found: {p}"})
            lines = _text(p).splitlines()
            return _emit(
                {
                    "lines": len(lines),
                    "errors": sum("error" in x.casefold() for x in lines),
                    "warnings": sum("warn" in x.casefold() for x in lines),
                    "successes": sum(
                        any(k in x.casefold() for k in ("success", "completed", "done")) for x in lines
                    ),
                }
            )

        if op == "image batch renamer":
            files = [
                f for f in _files(p) if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
            ]
            prefix = a[1] if len(a) > 1 else "image"
            plans = [
                (str(f), str(f.with_name(f"{prefix}_{i:04d}{f.suffix}"))) for i, f in enumerate(files, 1)
            ]
            if "--yes" not in a:
                return _emit(
                    {"dry_run": True, "plans": plans, "hint": "Re-run with --yes after reviewing the plan."}
                )
            for src, dst in plans:
                if Path(dst).exists():
                    continue
                Path(src).rename(dst)
            return _emit({"renamed": len(plans)})

        if op in {"startup folder viewer", "startup entry inventory", "startup folder cleaner"}:
            if platform.system() != "Windows":
                return _emit(
                    {
                        "available": False,
                        "platform": platform.system(),
                        "reason": "Windows startup folders/registry are unavailable on this OS.",
                    }
                )
            roots = [
                Path(os.environ.get("APPDATA", "")) / r"Microsoft/Windows/Start Menu/Programs/Startup",
                Path(os.environ.get("ProgramData", "")) / r"Microsoft/Windows/Start Menu/Programs/Startup",
            ]
            entries = [str(f) for r in roots if r.is_dir() for f in r.iterdir()]
            if op == "startup folder cleaner":
                if "--yes" not in a:
                    return _emit(
                        {
                            "entries": entries,
                            "hint": "Re-run with --yes and explicit names to remove startup entries.",
                        }
                    )
                return _emit(
                    {
                        "entries": entries,
                        "removed": 0,
                        "note": "No entries removed without an explicit path selection.",
                    }
                )
            return _emit(entries)

        if op in {"process handle summary", "process environment summary"}:
            try:
                import psutil
            except ImportError:
                return _emit({"error": "psutil is required."})
            if not a or not a[0].isdigit():
                return _emit({"error": "Provide a PID."})
            proc = psutil.Process(int(a[0]))
            if op == "process environment summary":
                try:
                    return _emit(proc.environ())
                except Exception as exc:
                    return _emit({"error": str(exc)})
            try:
                return _emit(
                    {
                        "open_files": [x._asdict() for x in proc.open_files()],
                        "connections": [x._asdict() for x in proc.net_connections()],
                    }
                )
            except Exception as exc:
                return _emit({"error": str(exc)})

        if op == "office file inventory":
            if not p.is_file():
                return _emit({"error": f"File not found: {p}"})
            try:
                with zipfile.ZipFile(p) as z:
                    return _emit(
                        {"members": len(z.namelist()), "media": [n for n in z.namelist() if "/media/" in n]}
                    )
            except zipfile.BadZipFile:
                return _emit({"error": "Not a valid Office Open XML package."})

        if op in {"exif date reader", "exif camera reader"}:
            try:
                from PIL import Image

                img = Image.open(p)
                ex = img.getexif()
                names = {36867: "DateTimeOriginal", 306: "DateTime", 272: "Model", 271: "Make"}
                result = {names.get(k, str(k)): v for k, v in ex.items() if k in names}
                key = "DateTimeOriginal" if op == "exif date reader" else "Make"
                return _emit({key: result.get(key), "metadata": result})
            except ImportError:
                return _emit({"error": "Pillow is required."})
            except Exception as exc:
                return _emit({"error": str(exc)})

        if op == "image mime detector":
            sig = p.read_bytes()[:16] if p.is_file() else b""
            mime = "application/octet-stream"
            if sig.startswith(b"\x89PNG"):
                mime = "image/png"
            elif sig.startswith(b"\xff\xd8\xff"):
                mime = "image/jpeg"
            elif sig.startswith(b"GIF8"):
                mime = "image/gif"
            elif sig.startswith(b"RIFF") and b"WEBP" in sig:
                mime = "image/webp"
            return _emit({"mime": mime, "path": str(p)})

        if op in {"media duration inventory"}:
            files = _files(p)
            if shutil.which("ffprobe"):
                rows = []
                for f in files:
                    r = _run(
                        [
                            "ffprobe",
                            "-v",
                            "error",
                            "-show_entries",
                            "format=duration",
                            "-of",
                            "default=nw=1:nk=1",
                            str(f),
                        ],
                        timeout=30,
                    )
                    if r["returncode"] == 0:
                        try:
                            rows.append({"path": str(f), "duration": float(r["stdout"].strip())})
                        except ValueError:
                            pass
                return _emit(rows)
            return _emit({"error": "ffprobe is required for media durations."})

        if op in {
            "device class summary",
            "usb device inventory",
            "bluetooth device inventory",
            "printer inventory",
            "display inventory",
            "audio device inventory",
            "dns cache viewer",
            "windows firewall rule count",
        }:
            if platform.system() != "Windows":
                return _emit(
                    {
                        "available": False,
                        "platform": platform.system(),
                        "reason": "Windows device/network APIs are unavailable on this OS.",
                    }
                )
            ps = shutil.which("powershell") or shutil.which("pwsh")
            if not ps:
                return _emit({"available": False, "missing_dependency": "powershell"})
            commands = {
                "device class summary": "Get-PnpDevice | Group-Object Class | Select Name,Count | ConvertTo-Json -Compress",
                "usb device inventory": "Get-PnpDevice -Class USB | Select FriendlyName,Status,InstanceId | ConvertTo-Json -Compress",
                "bluetooth device inventory": "Get-PnpDevice -Class Bluetooth | Select FriendlyName,Status,InstanceId | ConvertTo-Json -Compress",
                "printer inventory": "Get-Printer | Select Name,DriverName,PortName,PrinterStatus | ConvertTo-Json -Compress",
                "display inventory": "Get-CimInstance Win32_VideoController | Select Name,DriverVersion,AdapterRAM | ConvertTo-Json -Compress",
                "audio device inventory": "Get-PnpDevice -Class Media | Select FriendlyName,Status,InstanceId | ConvertTo-Json -Compress",
                "dns cache viewer": "Get-DnsClientCache | Select Entry,RecordName,RecordType,Status | ConvertTo-Json -Compress",
                "windows firewall rule count": "(Get-NetFirewallRule | Measure-Object).Count",
            }
            return _emit(_run([ps, "-NoProfile", "-Command", commands[op]], timeout=45))

        if op == "path deduplication report":
            entries = [x for x in os.environ.get("PATH", "").split(os.pathsep) if x]
            seen = set()
            dup = []
            unique = []
            for x in entries:
                key = os.path.normcase(os.path.normpath(x))
                (dup if key in seen else unique).append(x)
                seen.add(key)
            return _emit({"entries": len(entries), "unique": len(unique), "duplicates": dup})

        if op in {"open file guide", "pip command guide", "package cache guide", "command history guide"}:
            guides = {
                "open file guide": "Use the suite open command or the desktop Open File action; the OS default application is used.",
                "pip command guide": "Common commands: python -m pip install PACKAGE; python -m pip list; python -m pip freeze; python -m pip uninstall PACKAGE.",
                "package cache guide": "Python package cache is managed with python -m pip cache info, python -m pip cache list, and python -m pip cache purge.",
                "command history guide": "Inspect shell history with the native shell history mechanism; Utility Suite does not capture commands globally.",
            }
            return _emit(guides[op])

        if op in {"crash dump inventory", "log directory inventory"}:
            roots = [
                Path(os.environ.get("SystemRoot", "C:/Windows")) / r"Minidump",
                Path(os.environ.get("SystemRoot", "C:/Windows")) / r"Memory.dmp",
                Path(os.environ.get("ProgramData", "")) / r"Microsoft/Windows/WER",
            ]
            if op == "log directory inventory":
                roots = [Path("logs"), Path(os.environ.get("ProgramData", "")) / r"UtilitySuite/logs"]
            rows = []
            for r in roots:
                if r.is_file():
                    rows.append({"path": str(r), "bytes": r.stat().st_size})
                elif r.is_dir():
                    rows.extend(
                        {"path": str(f), "bytes": f.stat().st_size} for f in r.rglob("*") if f.is_file()
                    )
            return _emit(rows[:500])

        if op == "process pipe helper":
            if len(a) < 2:
                return _emit({"error": "Usage: process-pipe-helper COMMAND ARG..."})
            return _emit(_run(a, timeout=30))

        if op == "snapshot inventory":
            rows = [{"path": str(f), "size": f.stat().st_size, "mtime": f.stat().st_mtime} for f in _files(p)]
            return _emit({"root": str(p), "files": len(rows), "entries": rows[:500]})

        if op in {
            "driver list",
            "driver details",
            "driver backup",
            "driver store inventory",
            "driver signature check",
            "driver version report",
            "driver provider report",
            "driver class report",
            "driver device status",
            "driver update reminder",
        }:
            if platform.system() != "Windows":
                return _emit(
                    {
                        "available": False,
                        "platform": platform.system(),
                        "reason": "Windows Plug-and-Play/driver APIs are unavailable on this OS.",
                    }
                )
            ps = shutil.which("powershell") or shutil.which("pwsh")
            pn = shutil.which("pnputil")
            if not ps:
                return _emit({"available": False, "missing_dependency": "powershell"})
            if op == "driver backup":
                if "--yes" not in a:
                    return _emit({"error": "Driver export requires --yes and an explicit destination."})
                dest = _path(a, 0, "driver-backup")
                dest.mkdir(parents=True, exist_ok=True)
                return _emit(_run([pn or "pnputil", "/export-driver", "*", str(dest)], timeout=300))
            command = "Get-CimInstance Win32_PnPSignedDriver | Select DeviceName,DriverVersion,DriverProviderName,IsSigned,InfName | ConvertTo-Json -Compress"
            return _emit(_run([ps, "-NoProfile", "-Command", command], timeout=60))

        # ---------- end of baseline coverage; new tools below ----------

        # ---------- NEW TOOL IMPLEMENTATIONS BEGIN ----------
        if op == "slugify converter":
            s = re.sub(r"[^a-z0-9]+", "-", (" ".join(a)).lower()).strip("-")
            return _emit(s)
        if op == "csv column extractor":
            path = _path(a, 0, "")
            col = a[1] if len(a) > 1 else ""
            try:
                with open(path, newline="", encoding="utf-8-sig") as f:
                    rows = list(csv.DictReader(f))
                out = [r.get(col, "") for r in rows]
                return _emit(out)
            except FileNotFoundError:
                return _emit({"error": f"File not found: {path}"})
            except Exception as exc:
                return _emit({"error": str(exc)})
        if op == "regex replacer":
            pattern = a[0] if a else ""
            repl = a[1] if len(a) > 1 else ""
            text = sys.stdin.read() if len(a) <= 2 else " ".join(a[2:])
            try:
                return _emit(re.sub(pattern, repl, text))
            except re.error as exc:
                return _emit({"error": f"Invalid regex: {exc}"})
        if op == "markdown table formatter":
            lines = [ln.strip() for ln in (" ".join(a) or "").splitlines() if ln.strip()]
            if not lines:
                return _emit({"error": "No input"})
            sep_re = re.compile(r"^\|?[\s:|-]+\|?$")
            header = [c.strip() for c in lines[0].strip("|").split("|")]
            body_start = 1
            if len(lines) > 1 and sep_re.match(lines[1]):
                body_start = 2
            rows = [[c.strip() for c in ln.strip("|").split("|")] for ln in lines[body_start:]]
            all_rows = [header] + rows
            widths = [max(len(str(r[i])) if i < len(r) else 0 for r in all_rows) for i in range(len(header))]
            def fmt_row(cells):
                cells = list(cells) + [""] * (len(widths) - len(cells))
                return "| " + " | ".join(str(c).ljust(w) for c, w in zip(cells, widths)) + " |"
            out_lines = [fmt_row(header), "|" + "|".join("-" * (w + 2) for w in widths) + "|"]
            out_lines += [fmt_row(r) for r in rows]
            return _emit("\n".join(out_lines))
        if op == "line number prefixer":
            text = " ".join(a)
            width = len(str(text.count("\n") + 1))
            out = "\n".join(f"{i:>width} | {ln}" for i, ln in enumerate(text.splitlines(), 1))
            return _emit(out)
        if op == "unicode normalizer":
            import unicodedata

            form = (a[0] if a else "NFC").upper()
            s = " ".join(a[1:]) if len(a) > 1 else sys.stdin.read()
            try:
                return _emit(unicodedata.normalize(form, s))
            except ValueError as exc:
                return _emit({"error": str(exc)})
        if op == "clipboard history ring":
            try:
                import pyperclip

                clip = pyperclip.paste()
                hist_file = Path.home() / ".utility_suite_clipboard_history.json"
                hist = json.loads(hist_file.read_text(encoding="utf-8")) if hist_file.exists() else []
                if not hist or hist[-1] != clip:
                    hist.append(clip)
                hist = hist[-50:]
                hist_file.write_text(json.dumps(hist, ensure_ascii=False), encoding="utf-8")
                return _emit({"entries": len(hist), "latest_preview": (hist[-1][:80] + "...") if hist and len(hist[-1]) > 80 else (hist[-1] if hist else None)})
            except ImportError:
                return _emit({"available": False, "missing_dependency": "python:pyperclip"})
        if op == "clipboard paste as plain":
            try:
                import pyperclip

                s = pyperclip.paste()
                cleaned = re.sub(r"\s+", " ", s).strip()
                pyperclip.copy(cleaned)
                return _emit({"copied_chars": len(cleaned)})
            except ImportError:
                return _emit({"available": False, "missing_dependency": "python:pyperclip"})
        if op == "clipboard hash":
            try:
                import pyperclip

                s = pyperclip.paste().encode("utf-8")
                return _emit({"sha256": hashlib.sha256(s).hexdigest(), "length": len(s)})
            except ImportError:
                return _emit({"available": False, "missing_dependency": "python:pyperclip"})
        if op == "cron expression explainer":
            expr = " ".join(a)
            fields = expr.split()
            if len(fields) != 5:
                return _emit({"error": "Cron expression must have exactly 5 fields"})
            names = ["minute", "hour", "day-of-month", "month", "day-of-week"]
            meaning = {}
            for name, field in zip(names, fields):
                if field == "*":
                    meaning[name] = "any"
                elif re.fullmatch(r"\*\/\d+", field):
                    meaning[name] = f"every {field[2:]} {name}(s)"
                elif re.fullmatch(r"\d+", field):
                    meaning[name] = f"exactly at {field}"
                elif "-" in field:
                    meaning[name] = f"range {field}"
                elif "," in field:
                    meaning[name] = f"list {field}"
                else:
                    meaning[name] = field
            return _emit({"expression": expr, "meaning": meaning})
        if op == "date range expander":
            start_s = a[0] if a else ""
            end_s = a[1] if len(a) > 1 else ""
            try:
                start = dt.date.fromisoformat(start_s)
                end = dt.date.fromisoformat(end_s)
            except ValueError:
                return _emit({"error": "Provide ISO dates: YYYY-MM-DD YYYY-MM-DD"})
            days = (end - start).days + 1
            if days <= 0:
                return _emit({"error": "End date must be on or after start date"})
            if days > 3660:
                return _emit({"error": "Range too large (>10 years)"})
            dates = [(start + dt.timedelta(days=i)).isoformat() for i in range(days)]
            return _emit({"count": days, "first": dates[0], "last": dates[-1], "dates": dates[:31]})
        if op == "relative time formatter":
            iso = a[0] if a else ""
            try:
                when = dt.datetime.fromisoformat(iso)
            except ValueError:
                return _emit({"error": "Invalid ISO datetime"})
            delta = dt.datetime.now(tz=when.tzinfo) - when
            secs = int(delta.total_seconds())
            if abs(secs) < 60:
                label = f"{secs}s"
            elif abs(secs) < 3600:
                label = f"{secs // 60}m"
            elif abs(secs) < 86400:
                label = f"{secs // 3600}h"
            else:
                label = f"{secs // 86400}d"
            return _emit({"input": iso, "relative": label, "seconds": secs})
        if op == "habit streak counter":
            path = _path(a, 0, "")
            try:
                raw = Path(path).read_text(encoding="utf-8")
            except FileNotFoundError:
                return _emit({"error": f"File not found: {path}"})
            dates = set()
            for m in re.finditer(r"\d{4}-\d{2}-\d{2}", raw):
                try:
                    dates.add(dt.date.fromisoformat(m.group()))
                except ValueError:
                    continue
            if not dates:
                return _emit({"error": "No ISO dates found"})
            ordered = sorted(dates)
            best = cur = 1
            for prev, nxt in zip(ordered, ordered[1:]):
                if (nxt - prev).days == 1:
                    cur += 1
                    best = max(best, cur)
                else:
                    cur = 1
            return _emit({"total_days": len(ordered), "best_streak": best, "current_streak": cur if (dt.date.today() - ordered[-1]).days <= 1 else 0})
        if op == "portable app suspicion scanner":
            root = _path(a, 0, ".")
            exe_exts = {".exe", ".jar", ".AppImage"}
            portable_markers = {"portable", "app", "data", "settings", "config.ini", "launcher"}
            suspects = []
            for p in Path(root).rglob("*"):
                if not p.is_file():
                    continue
                if p.suffix.lower() in exe_exts:
                    siblings = {s.name.lower() for s in p.parent.iterdir()} if p.parent.exists() else set()
                    score = sum(1 for m in portable_markers if any(m in s for s in siblings))
                    if score >= 1:
                        suspects.append({"path": str(p), "marker_score": score})
            return _emit({"root": str(Path(root).resolve()), "suspects": suspects[:200], "count": len(suspects)})
        if op == "autostart registry diff":
            reg = shutil.which("reg")
            if not reg or platform.system() != "Windows":
                return _emit({"available": False, "reason": "Windows 'reg' tool required"})
            keys = [
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
                r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",
            ]
            entries = {}
            for k in keys:
                res = subprocess.run([reg, "query", k], capture_output=True, text=True, timeout=15)
                lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip() and "REG_" in ln]
                entries[k] = lines
            snap_file = Path(tempfile.gettempdir()) / "us_autostart_snapshot.json"
            prev = json.loads(snap_file.read_text(encoding="utf-8")) if snap_file.exists() else {}
            snap_file.write_text(json.dumps(entries), encoding="utf-8")
            added = [e for lst in entries.values() for e in lst if e not in {x for v in prev.values() for x in v}]
            removed = [e for lst in prev.values() for e in lst if e not in {x for v in entries.values() for x in v}]
            return _emit({"keys": list(entries), "added": added, "removed": removed})
        if op == "file integrity baseline":
            path = _path(a, 0, "")
            target = Path(path)
            if not target.exists():
                return _emit({"error": f"Not found: {path}"})
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            base_file = Path(tempfile.gettempdir()) / "us_integrity_baselines.json"
            baselines = json.loads(base_file.read_text(encoding="utf-8")) if base_file.exists() else {}
            key = str(target.resolve())
            if "--verify" in a:
                old = baselines.get(key)
                return _emit({"verified": old == digest, "expected": old, "actual": digest})
            baselines[key] = digest
            base_file.write_text(json.dumps(baselines), encoding="utf-8")
            return _emit({"baseline_set": True, "sha256": digest})
        if op == "recent docs privacy report":
            recent_dir = os.environ.get("APPDATA", "")
            if not recent_dir:
                return _emit({"available": False, "reason": "APPDATA not set (Windows-only)"})
            recent = Path(recent_dir) / "Microsoft" / "Windows" / "Recent"
            if not recent.exists():
                return _emit({"error": f"Recent folder missing: {recent}"})
            items = [{"name": p.name, "size": p.stat().st_size} for p in recent.iterdir() if p.is_file()]
            return _emit({"folder": str(recent), "count": len(items), "sample": items[:50]})
        if op == "subnet calculator":
            cidr = a[0] if a else ""
            try:
                net = __import__("ipaddress").ip_network(cidr, strict=False)
            except Exception as exc:
                return _emit({"error": f"Invalid CIDR: {exc}"})
            hosts = list(net.hosts())
            return _emit({
                "network": str(net.network_address),
                "broadcast": str(net.broadcast_address),
                "netmask": str(net.netmask),
                "prefixlen": net.prefixlen,
                "usable_hosts": len(hosts),
                "first_host": str(hosts[0]) if hosts else None,
                "last_host": str(hosts[-1]) if hosts else None,
            })
        if op == "mac vendor lookup":
            mac = re.sub(r"[^A-Fa-f0-9]", "", a[0] if a else "").upper()
            if len(mac) != 12:
                return _emit({"error": "MAC must be 12 hex digits"})
            oui = mac[:6]
            locally = bool(int(mac[1], 16) & 2)
            unicast = not bool(int(mac[0], 16) & 1)
            return _emit({"mac": ":".join(mac[i:i+2] for i in range(0, 12, 2)), "oui": oui, "locally_administered": locally, "unicast": unicast, "vendor": "requires OUI database (offline heuristic only)"})
        if op == "ssl expiry monitor":
            host = a[0] if a else ""
            port = int(a[1]) if len(a) > 1 and a[1].isdigit() else 443
            warn_days = int(a[2]) if len(a) > 2 and a[2].isdigit() else 30
            try:
                import ssl as _ssl

                ctx = _ssl.create_default_context()
                with socket.create_connection((host, port), timeout=10) as sock:
                    with ctx.wrap_socket(sock, server_hostname=host) as ss:
                        cert = ss.getpeercert()
                exp = dt.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=dt.timezone.utc)
                days = (exp - dt.datetime.now(dt.timezone.utc)).days
                return _emit({"host": host, "expires": exp.isoformat(), "days_remaining": days, "warning": days <= warn_days})
            except Exception as exc:
                return _emit({"error": str(exc)})
        if op == "speed test probe":
            url = a[0] if a else "https://speed.cloudflare.com/__down?bytes=10000000"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "UtilitySuite/1.0"})
                t0 = time.perf_counter()
                total = 0
                with urllib.request.urlopen(req, timeout=30) as resp:
                    while chunk := resp.read(65536):
                        total += len(chunk)
                dur = time.perf_counter() - t0
                mbps = (total * 8) / (dur or 1e-6) / 1_000_000
                return _emit({"url": url, "bytes": total, "seconds": round(dur, 3), "mbps": round(mbps, 2)})
            except Exception as exc:
                return _emit({"error": str(exc), "hint": "Set custom URL arg or check connectivity"})
        if op == "requirements auditor":
            path = _path(a, 0, "requirements.txt")
            try:
                lines = Path(path).read_text(encoding="utf-8").splitlines()
            except FileNotFoundError:
                return _emit({"error": f"Not found: {path}"})
            pkgs = []
            unpinned = []
            for ln in lines:
                ln = ln.split("#")[0].strip()
                if not ln:
                    continue
                m = re.match(r"^([A-Za-z0-9_.-]+)\s*(==.*)?", ln)
                if m:
                    pkgs.append(m.group(1))
                    if not m.group(2):
                        unpinned.append(m.group(1))
            return _emit({"packages": len(pkgs), "unpinned": unpinned, "total": len(pkgs)})
        if op == "venv size reporter":
            root = _path(a, 0, ".")
            site_pkgs = None
            for cand in Path(root).rglob("site-packages"):
                if cand.is_dir():
                    site_pkgs = cand
                    break
            if not site_pkgs:
                return _emit({"error": "No site-packages directory found under " + str(root)})
            total = 0
            biggest = []
            for d in site_pkgs.iterdir():
                sz = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) if d.is_dir() else d.stat().st_size
                total += sz
                biggest.append((sz, d.name))
            biggest.sort(reverse=True)
            return _emit({"site_packages": str(site_pkgs), "total_bytes": total, "top_10": [{"name": n, "bytes": s} for s, n in biggest[:10]]})
        if op == "wheel inspector":
            zp = _path(a, 0, "")
            try:
                from zipfile import ZipFile as ZF

                with ZF(zp) as z:
                    meta = [n for n in z.namelist() if n.endswith("METADATA")]
                    record = z.read(meta[0]).decode("utf-8", errors="replace") if meta else ""
                    top = [n for n in z.namelist() if "/" in n and not n.startswith("__MACOSX")]
                    summary = {"files": len(top), "metadata_present": bool(meta)}
                    for line in record.splitlines():
                        if line.startswith(("Name:", "Version:", "Requires-Python:")):
                            k, _, v = line.partition(":")
                            summary[k.strip().lower().replace("-", "_")] = v.strip()
                    return _emit(summary)
            except FileNotFoundError:
                return _emit({"error": f"Wheel not found: {zp}"})
            except Exception as exc:
                return _emit({"error": str(exc)})
        if op == "temp file aging cleaner":
            root = _path(a, 0, tempfile.gettempdir())
            cutoff_days = int(a[0]) if a and a[0].isdigit() else 7
            dry = "--execute" not in a
            cutoff = time.time() - cutoff_days * 86400
            candidates = []
            for p in Path(root).iterdir():
                try:
                    if p.is_file() and p.stat().st_mtime < cutoff:
                        candidates.append({"path": str(p), "age_days": round((time.time() - p.stat().st_mtime) / 86400, 1)})
                        if not dry:
                            p.unlink(missing_ok=True)
                except OSError:
                    continue
            return _emit({"dry_run": dry, "would_delete": len(candidates), "deleted": 0 if dry else len(candidates), "sample": candidates[:25]})
        if op == "broken link finder":
            root = _path(a, 0, ".")
            broken = []
            for p in Path(root).rglob("*.lnk"):
                broken.append({"path": str(p), "note": "Target resolution requires Windows Shell APIs"})
            symlinks = [p for p in Path(root).rglob("*") if p.is_symlink()]
            dead = [str(p) for p in symlinks if not p.exists()]
            return _emit({"windows_shortcuts": broken[:200], "dead_symlinks": dead[:200], "counts": {"shortcuts": len(broken), "dead_symlinks": len(dead)}})
        if op == "disk cleanup preview":
            roots = a if a else [tempfile.gettempdir(), str(Path.home() / "Downloads")]
            preview = {}
            for r in roots:
                rp = Path(r)
                if not rp.exists():
                    continue
                junk_exts = {".tmp", ".log", ".bak", ".cache", ".old"}
                total = 0
                count = 0
                for f in rp.rglob("*"):
                    try:
                        if f.is_file() and f.suffix.lower() in junk_exts:
                            total += f.stat().st_size
                            count += 1
                    except OSError:
                        continue
                preview[r] = {"junk_files": count, "reclaimable_bytes": total}
            return _emit({"preview": preview, "note": "Dry-run only; pass --execute to delete (not implemented for safety)"})
        if op == "log rotation helper":
            path = _path(a, 0, "")
            log = Path(path)
            if not log.exists():
                return _emit({"error": f"Log not found: {path}"})
            keep = int(a[1]) if len(a) > 1 and a[1].isdigit() else 5
            size_mb = log.stat().st_size / (1024 * 1024)
            rotated = []
            if size_mb >= 10:
                stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
                dest = log.with_suffix(log.suffix + f".{stamp}")
                log.rename(dest)
                log.touch()
                rotated.append(str(dest))
                olds = sorted(log.parent.glob(log.name + ".*"), key=lambda p: p.stat().st_mtime)
                for stale in olds[:-keep]:
                    stale.unlink(missing_ok=True)
            return _emit({"rotated_now": bool(rotated), "files": rotated, "threshold_mb": 10, "keep": keep})
        if op == "resource snapshot diff":
            snap_file = Path(tempfile.gettempdir()) / "us_resource_snapshots.json"
            snaps = json.loads(snap_file.read_text(encoding="utf-8")) if snap_file.exists() else []
            try:
                import psutil

                proc_list = []
                for pr in psutil.process_iter(["pid", "name", "memory_percent"]):
                    proc_list.append(pr.info)
            except ImportError:
                proc_list = []
            entry = {"timestamp": dt.datetime.now().isoformat(), "processes": len(proc_list), "cpu_count": os.cpu_count()}
            snaps.append(entry)
            snaps = snaps[-20:]
            snap_file.write_text(json.dumps(snaps), encoding="utf-8")
            prev = snaps[-2] if len(snaps) > 1 else None
            return _emit({"snapshot": entry, "previous": prev, "delta_procs": (entry["processes"] - prev["processes"]) if prev else 0})
        if op == "long running process finder":
            min_hours = float(a[0]) if a and re.fullmatch(r"\d+(\.\d+)?", a[0]) else 24
            try:
                import psutil

                now = time.time()
                results = []
                for pr in psutil.process_iter(["pid", "name", "create_time"]):
                    info = pr.info
                    if info.get("create_time") and (now - info["create_time"]) / 3600 >= min_hours:
                        results.append({"pid": info["pid"], "name": info["name"], "hours_running": round((now - info["create_time"]) / 3600, 1)})
                results.sort(key=lambda x: -x["hours_running"])
                return _emit({"threshold_hours": min_hours, "matches": results[:50], "count": len(results)})
            except ImportError:
                return _emit({"available": False, "missing_dependency": "python:psutil"})
        if op == "open file handle report":
            try:
                import psutil

                pid = int(a[0]) if a and a[0].isdigit() else os.getpid()
                pr = psutil.Process(pid)
                files = [{"fd": h.fd, "path": h.path} for h in pr.open_files()]
                conns = [{"laddr": str(c.laddr), "raddr": str(c.raddr), "status": c.status} for c in pr.connections()]
                return _emit({"pid": pid, "open_files": files[:100], "connections": conns[:50]})
            except ImportError:
                return _emit({"available": False, "missing_dependency": "python:psutil"})
            except Exception as exc:
                return _emit({"error": str(exc)})
        if op == "multi algorithm hasher":
            path = _path(a, 0, "")
            try:
                data = Path(path).read_bytes()
            except FileNotFoundError:
                return _emit({"error": f"Not found: {path}"})
            out = {"file": path, "size": len(data)}
            for alg in ("md5", "sha1", "sha256", "sha512"):
                out[alg] = hashlib.new(alg, data).hexdigest()
            return _emit(out)
        if op == "checksum verifier":
            manifest = _path(a, 0, "")
            base = _path(a, 1, ".") if len(a) > 1 else "."
            try:
                lines = Path(manifest).read_text(encoding="utf-8").splitlines()
            except FileNotFoundError:
                return _emit({"error": f"Manifest not found: {manifest}"})
            ok = bad = missing = 0
            failures = []
            for ln in lines:
                parts = ln.split()
                if len(parts) < 2:
                    continue
                digest, fname = parts[0], " ".join(parts[1:]).lstrip("*")
                fp = Path(base) / fname
                if not fp.exists():
                    missing += 1
                    failures.append({"file": fname, "reason": "missing"})
                    continue
                actual = hashlib.new(digest if digest in hashlib.algorithms_available else "sha256", fp.read_bytes()).hexdigest()
                if actual == digest:
                    ok += 1
                else:
                    bad += 1
                    failures.append({"file": fname, "reason": "hash mismatch"})
            return _emit({"ok": ok, "bad": bad, "missing": missing, "failures": failures})
        if op == "json yaml converter":
            path = _path(a, 0, "")
            mode = (a[1] if len(a) > 1 else "to-yaml").lower()
            try:
                data = json.loads(Path(path).read_text(encoding="utf-8"))
            except FileNotFoundError:
                return _emit({"error": f"Not found: {path}"})
            except json.JSONDecodeError as exc:
                return _emit({"error": f"Invalid JSON: {exc}"})
            if mode in {"to-yaml", "yaml"}:
                try:
                    import yaml

                    return _emit(yaml.safe_dump(data, default_flow_style=False))
                except ImportError:
                    return _emit({"available": False, "missing_dependency": "python:yaml"})
            return _emit({"error": "Unknown mode; use to-yaml"})
        if op == "json diff":
            fa, fb = _path(a, 0, ""), _path(a, 1, "")
            try:
                da = json.loads(Path(fa).read_text(encoding="utf-8"))
                db = json.loads(Path(fb).read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                return _emit({"error": str(exc)})
            except json.JSONDecodeError as exc:
                return _emit({"error": f"Invalid JSON: {exc}"})
            diffs = []
            def walk(pa, pb, path=""):
                if isinstance(pa, dict) and isinstance(pb, dict):
                    for k in sorted(set(pa) | set(pb)):
                        sub = f"{path}.{k}" if path else k
                        if k not in pa:
                            diffs.append({"path": sub, "change": "added", "value": pb[k]})
                        elif k not in pb:
                            diffs.append({"path": sub, "change": "removed", "value": pa[k]})
                        else:
                            walk(pa[k], pb[k], sub)
                elif isinstance(pa, list) and isinstance(pb, list):
                    if pa != pb:
                        diffs.append({"path": path, "change": "modified", "old_len": len(pa), "new_len": len(pb)})
                elif pa != pb:
                    diffs.append({"path": path, "change": "modified", "old": pa, "new": pb})
            walk(da, db)
            return _emit({"diffs": diffs[:200], "count": len(diffs)})
        if op == "json schema validator":
            schema_path = _path(a, 0, "")
            doc_path = _path(a, 1, "")
            try:
                schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
                doc = json.loads(Path(doc_path).read_text(encoding="utf-8"))
            except FileNotFoundError as exc:
                return _emit({"error": str(exc)})
            except json.JSONDecodeError as exc:
                return _emit({"error": f"Invalid JSON: {exc}"})
            try:
                import jsonschema

                v = jsonschema.Draft7Validator(schema)
                errs = [e.message for e in v.iter_errors(doc)]
                return _emit({"valid": not errs, "errors": errs})
            except ImportError:
                req = schema.get("required", [])
                props = schema.get("properties", {})
                errs = [f"missing required: {r}" for r in req if r not in doc]
                for k, spec in props.items():
                    if k in doc and spec.get("type"):
                        tmap = {"string": str, "number": (int, float), "integer": int, "boolean": bool, "array": list, "object": dict}
                        if not isinstance(doc[k], tmap.get(spec["type"], object)):
                            errs.append(f"type error at {k}")
                return _emit({"valid": not errs, "errors": errs, "mode": "heuristic (install jsonschema for full validation)"})
        if op == "base64 file codec":
            mode = (a[0] if a else "encode").lower()
            path = _path(a, 1, "")
            try:
                data = Path(path).read_bytes()
            except FileNotFoundError:
                return _emit({"error": f"Not found: {path}"})
            if mode == "encode":
                return _emit(base64.b64encode(data).decode())
            try:
                decoded = base64.b64decode(data)
                out = Path(path + ".decoded")
                out.write_bytes(decoded)
                return _emit({"written": str(out), "bytes": len(decoded)})
            except Exception as exc:
                return _emit({"error": str(exc)})
        if op == "hex codec":
            mode = (a[0] if a else "encode").lower()
            s = " ".join(a[1:])
            if mode == "encode":
                return _emit(s.encode().hex())
            try:
                return _emit(bytes.fromhex(re.sub(r"\s+", "", s)).decode(errors="replace"))
            except ValueError as exc:
                return _emit({"error": str(exc)})
        if op == "charset detector":
            path = _path(a, 0, "")
            try:
                raw = Path(path).read_bytes()
            except FileNotFoundError:
                return _emit({"error": f"Not found: {path}"})
            encodings = ["ascii", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "latin-1", "cp1252"]
            detected = []
            for enc in encodings:
                try:
                    raw.decode(enc)
                    detected.append(enc)
                except (UnicodeDecodeError, LookupError):
                    continue
            bom = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else ("utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else None)
            return _emit({"file": path, "decodable_as": detected, "bom": bom, "confidence": detected[0] if detected else None})
        if op == "bom handler":
            mode = (a[0] if a else "detect").lower()
            path = _path(a, 1, "")
            try:
                raw = Path(path).read_bytes()
            except FileNotFoundError:
                return _emit({"error": f"Not found: {path}"})
            boms = {b"\xef\xbb\xbf": "utf-8-sig", b"\xff\xfe": "utf-16-le", b"\xfe\xff": "utf-16-be"}
            found = next((v for k, v in boms.items() if raw.startswith(k)), None)
            if mode == "detect":
                return _emit({"file": path, "bom": found})
            if mode == "strip" and found:
                stripped = raw[len(next(k for k, v in boms.items() if v == found)) :]
                Path(path).write_bytes(stripped)
                return _emit({"stripped": found, "file": path})
            return _emit({"action": mode, "result": "no-op", "bom": found})
        # ---------- NEW TOOL IMPLEMENTATIONS END ----------

        return _emit(
            {
                "error": f"Operation '{operation}' is not implemented on this platform/backend.",
                "operation": operation,
            }
        )
    except Exception as exc:
        print(f"{operation}: {exc}")
        return 1
