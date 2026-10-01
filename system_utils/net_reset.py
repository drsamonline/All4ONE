from __future__ import annotations

import argparse
import shutil
import subprocess
import sys


def run(args=None):
    p = argparse.ArgumentParser(description="Reset a Windows network adapter.")
    p.add_argument("adapter", help="Adapter name")
    p.add_argument("--yes", action="store_true")
    a = p.parse_args(args or [])
    if sys.platform != "win32":
        print("Windows-only tool.")
        return 3
    if not a.yes:
        print("Destructive network action blocked. Rerun with --yes.")
        return 2
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if not ps:
        print("PowerShell not found.")
        return 3
    cmd = f"Start-Process powershell -Verb RunAs -ArgumentList \"-NoProfile -Command \"Disable-NetAdapter -Name '{a.adapter}' -Confirm:$false; Start-Sleep -Seconds 2; Enable-NetAdapter -Name '{a.adapter}' -Confirm:$false\"\""
    try:
        return subprocess.run([ps, "-NoProfile", "-Command", cmd], check=False, timeout=30).returncode
    except subprocess.TimeoutExpired:
        print("Network reset timed out (likely waiting on a UAC elevation prompt).")
        return 1
