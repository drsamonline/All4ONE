from __future__ import annotations
import argparse, shutil, subprocess, sys


def run(args=None):
    p = argparse.ArgumentParser(description="Create a Windows Task Scheduler task.")
    p.add_argument("task_name")
    p.add_argument("command")
    p.add_argument("--time", help="HH:mm")
    p.add_argument("--daily", action="store_true")
    p.add_argument("--once", action="store_true")
    p.add_argument("--run-as-system", action="store_true")
    a = p.parse_args(args or [])
    if sys.platform != "win32":
        print("Windows-only tool.")
        return 3
    exe = shutil.which("schtasks")
    if not exe:
        print("schtasks not found.")
        return 3
    schedule = "DAILY" if a.daily or a.time else "ONCE"
    cmd = [exe, "/Create", "/TN", a.task_name, "/TR", a.command, "/SC", schedule, "/F"]
    if schedule in {"DAILY", "ONCE"}:
        cmd += ["/ST", a.time or "00:00"]
    if a.run_as_system:
        cmd += ["/RU", "SYSTEM"]
    return subprocess.run(cmd, check=False).returncode
