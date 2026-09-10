from __future__ import annotations
import argparse, json, shutil, subprocess


def run(args=None):
    p = argparse.ArgumentParser(description="Extract media metadata with ffprobe.")
    p.add_argument("file")
    a = p.parse_args(args or [])
    exe = shutil.which("ffprobe")
    if not exe:
        print("ffprobe not found.")
        return 3
    r = subprocess.run(
        [exe, "-v", "error", "-show_format", "-show_streams", "-of", "json", a.file],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode:
        print(r.stderr.strip() or "ffprobe failed")
        return r.returncode
    print(json.dumps(json.loads(r.stdout), indent=2))
    return 0
