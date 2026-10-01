from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

SCHEMA = "CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY,size INTEGER,mtime REAL,extension TEXT,name TEXT); CREATE INDEX IF NOT EXISTS idx_files_name ON files(name); CREATE INDEX IF NOT EXISTS idx_files_ext ON files(extension); CREATE INDEX IF NOT EXISTS idx_files_size ON files(size);"


def run(args=None):
    p = argparse.ArgumentParser(description="Build or update the SQLite file index.")
    p.add_argument("directory")
    p.add_argument("--db", default="~/.utility_suite/index.db")
    p.add_argument("--clear", action="store_true")
    a = p.parse_args(args or [])
    root = Path(a.directory)
    if not root.is_dir():
        print("Directory not found.")
        return 1
    db = Path(a.db).expanduser()
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    con.executescript("PRAGMA journal_mode=WAL;" + SCHEMA)
    if a.clear:
        con.execute("DELETE FROM files")
    count = 0
    with con:
        for f in root.rglob("*"):
            if not f.is_file():
                continue
            try:
                st = f.stat()
                con.execute(
                    "INSERT OR REPLACE INTO files VALUES (?,?,?,?,?)",
                    (str(f.resolve()), st.st_size, st.st_mtime, f.suffix.lower(), f.name),
                )
                count += 1
            except OSError:
                pass
    con.close()
    print(f"Indexed {count} files into {db}")
    return 0
