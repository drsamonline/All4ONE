"""Central logging configuration.

Console output stays short and user-friendly - a tool's own print()
already explains what happened, so the console handler intentionally
drops exception tracebacks (ConsoleFormatter below). The rotating file
log keeps the full traceback for every ERROR so a developer can still
diagnose the root cause later.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from .config import get_config_path, get_setting

_CONFIGURED = False


class ConsoleFormatter(logging.Formatter):
    """Formats console records without a stack trace, even when the
    LogRecord carries exc_info (e.g. from logger.exception())."""

    def formatException(self, exc_info):
        return ""

    def format(self, record):
        # Temporarily hide exc_info from the base formatter so it doesn't
        # append "NoneType: None" after our blanked-out formatException().
        exc_info, record.exc_info = record.exc_info, None
        try:
            text = super().format(record)
        finally:
            record.exc_info = exc_info
        return text


def setup_logging() -> logging.Logger:
    global _CONFIGURED
    root = logging.getLogger()
    if _CONFIGURED:
        return root
    level = getattr(logging, str(get_setting("log_level", "INFO")).upper(), logging.INFO)
    root.setLevel(level)

    console_formatter = ConsoleFormatter("%(levelname)s: %(message)s")
    file_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    if not any(getattr(h, "_us_console", False) for h in root.handlers):
        console = logging.StreamHandler()
        console.setFormatter(console_formatter)
        console.setLevel(logging.WARNING)  # routine INFO/DEBUG noise stays out of the console
        console._us_console = True
        root.addHandler(console)

    log_file = get_setting("log_file", "logs/utility_suite.log")
    if log_file:
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = get_config_path().parent / log_path
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if not any(
                isinstance(h, logging.handlers.RotatingFileHandler)
                and Path(getattr(h, "baseFilename", "")).resolve() == log_path.resolve()
                for h in root.handlers
            ):
                handler = logging.handlers.RotatingFileHandler(
                    log_path,
                    maxBytes=int(get_setting("max_log_size_mb", 5)) * 1024 * 1024,
                    backupCount=int(get_setting("backup_count", 3)),
                    encoding="utf-8",
                )
                handler.setFormatter(file_formatter)
                root.addHandler(handler)
        except OSError:
            pass  # read-only install location - console-only logging is an acceptable fallback

    _CONFIGURED = True
    return root
