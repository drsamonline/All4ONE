from __future__ import annotations
import argparse, shutil, subprocess


def _run_gpg(args):
    exe = shutil.which("gpg")
    if not exe:
        print("gpg not found. Install GnuPG and retry.")
        return 3
    r = subprocess.run([exe, *args], check=False)
    return r.returncode


def run(args=None):
    p = argparse.ArgumentParser(description="Encrypt a file using GnuPG.")
    p.add_argument("file")
    p.add_argument("-o", "--output")
    p.add_argument("--recipient", "-r", required=True)
    a = p.parse_args(args or [])
    out = a.output or a.file + ".gpg"
    return _run_gpg(["--batch", "--yes", "--output", out, "--encrypt", "--recipient", a.recipient, a.file])


def decrypt(args=None):
    p = argparse.ArgumentParser(description="Decrypt a GnuPG file.")
    p.add_argument("file")
    p.add_argument("-o", "--output")
    a = p.parse_args(args or [])
    out = a.output or (a.file[:-4] if a.file.endswith(".gpg") else a.file + ".decrypted")
    return _run_gpg(["--batch", "--yes", "--output", out, "--decrypt", a.file])
