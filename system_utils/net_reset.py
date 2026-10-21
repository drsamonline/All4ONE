from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys

# Adapter names are passed into a PowerShell -Command string, so they must be
# restricted to characters that cannot break out of the single-quoted literal
# (no quotes, backticks, '$', ';', '|' or '&'). The regex is the primary
# defence; the quote-doubling below is belt-and-braces.
_SAFE_ADAPTER = re.compile(r"^[A-Za-z0-9 ._\-()]{1,128}$")


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
    if not _SAFE_ADAPTER.match(a.adapter):
        print(f"Refusing adapter name with unsupported characters: {a.adapter!r}")
        print("Allowed: letters, digits, spaces and . _ - ( )")
        return 2
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if not ps:
        print("PowerShell not found.")
        return 3
    safe = a.adapter.replace("'", "''")
    cmd = (
        "Start-Process powershell -Verb RunAs -ArgumentList "
        f"\"-NoProfile -Command \"Disable-NetAdapter -Name '{safe}' -Confirm:$false; "
        f"Start-Sleep -Seconds 2; Enable-NetAdapter -Name '{safe}' -Confirm:$false\"\""
    )
    try:
        return subprocess.run([ps, "-NoProfile", "-Command", cmd], check=False, timeout=30).returncode
    except subprocess.TimeoutExpired:
        print("Network reset timed out (likely waiting on a UAC elevation prompt).")
        return 1
