from __future__ import annotations

import argparse
import ftplib
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Basic FTP upload/download client.")
    p.add_argument("host")
    p.add_argument("--user", default="anonymous")
    p.add_argument("--password", default="")
    p.add_argument("--download")
    p.add_argument("--upload")
    p.add_argument("--remote")
    p.add_argument("--port", type=int, default=21)
    a = p.parse_args(args or [])
    if bool(a.download) == bool(a.upload):
        print("Specify exactly one of --download or --upload.")
        return 2
    with ftplib.FTP() as ftp:
        ftp.connect(a.host, a.port, timeout=30)
        ftp.login(a.user, a.password)
        if a.download:
            dest = Path(a.download)
            remote = a.remote or dest.name
            with dest.open("wb") as f:
                ftp.retrbinary("RETR " + remote, f.write)
            print(f"Downloaded {remote} -> {dest}")
        else:
            src = Path(a.upload)
            remote = a.remote or src.name
            with src.open("rb") as f:
                ftp.storbinary("STOR " + remote, f)
            print(f"Uploaded {src} -> {remote}")
    return 0
