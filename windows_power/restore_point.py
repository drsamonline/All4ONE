from __future__ import annotations
import argparse, shutil, subprocess, sys


def run(args=None):
    p = argparse.ArgumentParser(description="Create a Windows system restore point.")
    p.add_argument("--description", default="Utility Suite Restore Point")
    a = p.parse_args(args or [])
    if sys.platform != "win32":
        print("Windows-only tool.")
        return 3
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if not ps:
        print("PowerShell not found.")
        return 3
    desc = a.description.replace(chr(39), chr(39) * 2)
    cmd = f"Checkpoint-Computer -Description '{desc}' -RestorePointType MODIFY_SETTINGS"
    return subprocess.run([ps, "-NoProfile", "-Command", cmd], check=False).returncode
