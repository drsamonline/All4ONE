#!/usr/bin/env python3
"""All4one — one portable utility, every tool on its own page.

    python main.py                      open the desktop app
    python main.py list                 every tool, by category
    python main.py search pdf           find tools
    python main.py show hash-file       the options one tool takes
    python main.py run hash-file --file a.txt --algorithm sha256
    python main.py deps                 optional extras and their status

The same binary does both: with no arguments it opens the window, with a
command it behaves like a normal command-line tool.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main(argv: list[str] | None = None) -> int:
    from core.cli import main as cli_main

    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("gui", "--gui", "-g"):
        from ui.app import run
        return run([sys.argv[0]])
    if not argv:
        try:
            from ui.app import run
        except ImportError:
            return cli_main(argv)
        return run([sys.argv[0]])
    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
