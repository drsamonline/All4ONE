from __future__ import annotations

import sys

from .cli import main as cli_main
from .logging_utils import setup_logging


def main() -> int:
    setup_logging()
    return cli_main()


if __name__ == "__main__":
    sys.exit(main())
