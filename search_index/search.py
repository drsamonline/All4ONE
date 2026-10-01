from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Search the SQLite file index.")
    p.add_argument("query")
    p.add_argument("--db", default="~/.utility_suite/index.db")
    p.add_argument("--ext")
    p.add_argument("--min-size", type=int)
    p.add_argument("--limit", type=int, default=100)
    a = p.parse_args(args or [])
    db = Path(a.db).expanduser()
    if not db.exists():
        print("Index database not found. Run index first.")
        return 1
    clauses = ["name LIKE ?"]
    params = [f"%{a.query}%"]
    if a.ext:
        clauses.append("extension=?")
        params.append(a.ext if a.ext.startswith(".") else "." + a.ext)
    if a.min_size is not None:
        clauses.append("size>=?")
        params.append(a.min_size)
    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT path,size,mtime FROM files WHERE " + " AND ".join(clauses) + " ORDER BY name LIMIT ?",
        params + [a.limit],
    ).fetchall()
    con.close()
    for path, size, _mtime in rows:
        print(f"{size:>12,}  {path}")
    print(f"Found {len(rows)} matches.")
    return 0
