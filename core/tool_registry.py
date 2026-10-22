"""Tool metadata registry and lazy execution engine.

Responsibilities
----------------
* Hold every tool's metadata (loaded from the embedded bundle, external
  ``plugins/`` overrides, or the source tree).
* Enforce the per-pack **enable/disable** preference: a disabled pack's tools
  are absent from :meth:`ToolRegistry.search` and :meth:`ToolRegistry.list_categories`
  and are refused by :meth:`ToolRegistry.get_tool` / :meth:`ToolRegistry.run_tool`
  with a clear message (never a crash).  The preference is durable — see
  :mod:`core.preferences`.
* Resolve handlers lazily (``<pack>.<module>.<func>``) and stream a tool's
  output line-by-line to a callback via :class:`_LineWriter`.
* Mark a tool unavailable when an external dependency is missing, using
  :class:`core.capability_checker.CapabilityChecker`.

Optional per-tool metadata
--------------------------
Tool entries may carry three optional fields that let the GUI show only the
controls that actually apply:

* ``accepts``   — ``"file" | "folder" | "text" | "none"`` (argument picker)
* ``produces``  — ``"file" | "text" | "none"`` (output actions)
* ``destructive`` — ``bool`` (confirm before running)

When a field is **absent** the GUI falls back to today's behaviour (it shows
every control), so a tool without metadata keeps working exactly as before.
The values in :data:`TOOL_METADATA` were derived from each handler's signature
and code path (argparse positionals for bespoke handlers; the ``extended_ops``
dispatch branch for the generated packs) and only where the analysis was
unambiguous — see the module docstring in ``tests/test_tool_metadata.py``.
"""

from __future__ import annotations

import contextlib
import importlib
import io
import logging
from collections.abc import Callable, Iterable
from typing import Any

from .capability_checker import CapabilityChecker
from .preferences import PackPreferences

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Optional per-tool metadata.  Absent -> the GUI shows every control.
# --------------------------------------------------------------------------- #

# A tool NOT listed here keeps today's behaviour: the GUI shows every control.
TOOL_METADATA: dict[str, dict[str, Any]] = {
    "ageactions": {"accepts": "folder", "produces": "file", "destructive": True},
    "always-on-top-toggle": {"accepts": "none", "produces": "text"},
    "angle-converter": {"accepts": "text", "produces": "text"},
    "area-converter": {"accepts": "text", "produces": "text"},
    "audio-duration": {"accepts": "file", "produces": "text"},
    "audio-metadata-reader": {"accepts": "file", "produces": "text"},
    "audio-mime-detector": {"accepts": "file", "produces": "text"},
    "audio-stream-inspector": {"accepts": "file", "produces": "text"},
    "automation-manifest": {"accepts": "text", "produces": "text"},
    "autostart-diff": {"accepts": "file", "produces": "file"},
    "b64-codec": {"accepts": "text", "produces": "text"},
    "b64-file": {"accepts": "file", "produces": "file"},
    "backup-log-analyzer": {"accepts": "file", "produces": "text"},
    "backup-schedule-generator": {"accepts": "folder", "produces": "file", "destructive": True},
    "base64-decoder": {"accepts": "none", "produces": "text"},
    "base64-encoder": {"accepts": "none", "produces": "text"},
    "batch-file-generator": {"accepts": "text", "produces": "text"},
    "battery-status": {"accepts": "folder", "produces": "text"},
    "bluetooth-device-inventory": {"accepts": "none", "produces": "text"},
    "bom-handler": {"accepts": "file", "produces": "file"},
    "broken-link-finder": {"accepts": "folder", "produces": "text"},
    "bytes-units": {"accepts": "text", "produces": "text"},
    "calendar-month": {"accepts": "text", "produces": "text"},
    "calendar-year": {"accepts": "text", "produces": "text"},
    "case-converter": {"accepts": "file", "produces": "text"},
    "charset-detect": {"accepts": "file", "produces": "text"},
    "checksum": {"accepts": "file", "produces": "text"},
    "checksum-verify": {"accepts": "file", "produces": "text"},
    "cleanmgr": {"accepts": "none", "produces": "text"},
    "clipboard-history-ring": {"accepts": "file", "produces": "file"},
    "command-history-guide": {"accepts": "none", "produces": "text"},
    "command-resolver": {"accepts": "text", "produces": "text"},
    "computer-name": {"accepts": "none", "produces": "text"},
    "count": {"accepts": "file", "produces": "text"},
    "countdown": {"accepts": "text", "produces": "text"},
    "crash-dump-inventory": {"accepts": "none", "produces": "text"},
    "cron-explainer": {"accepts": "none", "produces": "text"},
    "csv-query": {"accepts": "file", "produces": "text"},
    "data-rate-converter": {"accepts": "text", "produces": "text"},
    "date-difference": {"accepts": "text", "produces": "text"},
    "date-range-expander": {"accepts": "text", "produces": "text"},
    "day-of-year": {"accepts": "text", "produces": "text"},
    "decrypt": {"accepts": "file", "produces": "none"},
    "default-gateway": {"accepts": "none", "produces": "text"},
    "desktop-count-reader": {"accepts": "none", "produces": "text"},
    "desktop-hotkey-guide": {"accepts": "none", "produces": "text"},
    "desktop-launch-helper": {"accepts": "none", "produces": "text"},
    "desktop-process-summary": {"accepts": "none", "produces": "text"},
    "device-class-summary": {"accepts": "none", "produces": "text"},
    "dhcp-status": {"accepts": "none", "produces": "text"},
    "diff-text-files": {"accepts": "file", "produces": "text"},
    "dir-sync": {"accepts": "folder", "produces": "file", "destructive": True},
    "disk-benchmark-reader": {"accepts": "folder", "produces": "text"},
    "disk-cleanup-preview": {"accepts": "none", "produces": "text"},
    "disk-usage": {"accepts": "folder", "produces": "text"},
    "display-inventory": {"accepts": "none", "produces": "text"},
    "dns-cache-viewer": {"accepts": "none", "produces": "text"},
    "dns-server-list": {"accepts": "none", "produces": "text"},
    "download": {"accepts": "text", "produces": "text"},
    "driver-backup": {"accepts": "folder", "produces": "text"},
    "driver-class-report": {"accepts": "none", "produces": "text"},
    "driver-details": {"accepts": "none", "produces": "text"},
    "driver-device-status": {"accepts": "none", "produces": "text"},
    "driver-list": {"accepts": "none", "produces": "text"},
    "driver-package-inventory": {"accepts": "none", "produces": "text"},
    "driver-provider-report": {"accepts": "none", "produces": "text"},
    "driver-signature-check": {"accepts": "none", "produces": "text"},
    "driver-store-inventory": {"accepts": "none", "produces": "text"},
    "driver-update-reminder": {"accepts": "none", "produces": "text"},
    "driver-version-report": {"accepts": "none", "produces": "text"},
    "dupefinder": {"accepts": "folder", "produces": "text", "destructive": True},
    "empty-clean": {"accepts": "folder", "produces": "text", "destructive": True},
    "encoding": {"accepts": "file", "produces": "file"},
    "encoding-detector": {"accepts": "file", "produces": "text"},
    "encrypt": {"accepts": "file", "produces": "none"},
    "energy-converter": {"accepts": "text", "produces": "text"},
    "env": {"accepts": "text", "produces": "text"},
    "environment-report": {"accepts": "none", "produces": "text"},
    "environment-variable-diff": {"accepts": "text", "produces": "text"},
    "epoch-converter": {"accepts": "text", "produces": "text"},
    "event-log-export": {"accepts": "text", "produces": "text"},
    "event-log-keyword-filter": {"accepts": "text", "produces": "text"},
    "event-log-query": {"accepts": "text", "produces": "text"},
    "event-log-recent-errors": {"accepts": "text", "produces": "text"},
    "event-log-recent-warnings": {"accepts": "text", "produces": "text"},
    "event-log-source-search": {"accepts": "text", "produces": "text"},
    "event-log-statistics": {"accepts": "text", "produces": "text"},
    "event-log-time-filter": {"accepts": "text", "produces": "text"},
    "eventlog": {"accepts": "none", "produces": "text"},
    "executable-locator": {"accepts": "text", "produces": "text"},
    "executable-package-locator": {"accepts": "text", "produces": "text"},
    "exif-camera-reader": {"accepts": "file", "produces": "text"},
    "exif-date-reader": {"accepts": "file", "produces": "text"},
    "exit-code-decoder": {"accepts": "text", "produces": "text"},
    "file-age": {"accepts": "file", "produces": "text"},
    "file-age-histogram": {"accepts": "folder", "produces": "text"},
    "file-allocation-inspector": {"accepts": "folder", "produces": "text"},
    "file-size-histogram": {"accepts": "folder", "produces": "text"},
    "filetype": {"accepts": "file", "produces": "text"},
    "folder-backup": {"accepts": "folder", "produces": "file"},
    "folder-watch-snapshot": {"accepts": "folder", "produces": "text"},
    "frequency-converter": {"accepts": "text", "produces": "text"},
    "ftp": {"accepts": "text", "produces": "text"},
    "grep": {"accepts": "folder", "produces": "text"},
    "habit-streak": {"accepts": "file", "produces": "text"},
    "hardlink": {"accepts": "folder", "produces": "text"},
    "hash-calculator": {"accepts": "file", "produces": "text"},
    "hash-identify": {"accepts": "text", "produces": "text"},
    "hex-codec": {"accepts": "text", "produces": "text"},
    "hexview": {"accepts": "file", "produces": "text"},
    "hosts-file-audit": {"accepts": "file", "produces": "text"},
    "hosts-file-entry-checker": {"accepts": "file", "produces": "text"},
    "hosts-file-viewer": {"accepts": "file", "produces": "text"},
    "http-connectivity-test": {"accepts": "none", "produces": "text"},
    "http-serve": {"accepts": "folder", "produces": "text"},
    "https-connectivity-test": {"accepts": "none", "produces": "text"},
    "image-batch-dimensions": {"accepts": "folder", "produces": "text"},
    "image-batch-extension-convert": {"accepts": "folder", "produces": "text"},
    "image-batch-hash": {"accepts": "folder", "produces": "text"},
    "image-batch-rename-plan": {"accepts": "folder", "produces": "text"},
    "image-batch-renamer": {"accepts": "folder", "produces": "text"},
    "image-batch-resize-plan": {"accepts": "folder", "produces": "text"},
    "image-contact-sheet": {"accepts": "folder", "produces": "text"},
    "image-montage-builder": {"accepts": "folder", "produces": "text"},
    "import-package-test": {"accepts": "none", "produces": "text"},
    "indentation-analyzer": {"accepts": "file", "produces": "text"},
    "index": {"accepts": "folder", "produces": "text"},
    "ini-tool": {"accepts": "file", "produces": "file"},
    "installed-software-snapshot": {"accepts": "text", "produces": "text"},
    "integrity-baseline": {"accepts": "file", "produces": "file"},
    "integrity-baseline-plus": {"accepts": "file", "produces": "file"},
    "ip-calc": {"accepts": "text", "produces": "text"},
    "ipv4-configuration": {"accepts": "none", "produces": "text"},
    "ipv6-configuration": {"accepts": "none", "produces": "text"},
    "iso-time-formatter": {"accepts": "text", "produces": "text"},
    "joiner": {"accepts": "text", "produces": "text"},
    "json-format": {"accepts": "file", "produces": "file"},
    "json-schema": {"accepts": "text", "produces": "text"},
    "junction-finder": {"accepts": "folder", "produces": "text"},
    "junk-find": {"accepts": "folder", "produces": "text"},
    "length-converter": {"accepts": "text", "produces": "text"},
    "line-ending-detector": {"accepts": "file", "produces": "text"},
    "line-number-prefixer": {"accepts": "none", "produces": "text"},
    "log-rotate": {"accepts": "folder", "produces": "text", "destructive": True},
    "logon-task-report": {"accepts": "text", "produces": "text"},
    "long-running-procs": {"accepts": "text", "produces": "text"},
    "mac-address-viewer": {"accepts": "none", "produces": "text"},
    "mac-vendor": {"accepts": "text", "produces": "text"},
    "markdown-table-formatter": {"accepts": "none", "produces": "text"},
    "mass-converter": {"accepts": "text", "produces": "text"},
    "media-duplicate-finder": {"accepts": "folder", "produces": "text"},
    "media-duration-inventory": {"accepts": "folder", "produces": "text"},
    "media-file-scanner": {"accepts": "folder", "produces": "text"},
    "media-folder-report": {"accepts": "folder", "produces": "text"},
    "media-hash-inventory": {"accepts": "folder", "produces": "text"},
    "media-info": {"accepts": "file", "produces": "text"},
    "media-size-report": {"accepts": "folder", "produces": "text"},
    "mirror-backup": {"accepts": "folder", "produces": "file"},
    "monitor-threshold-calculator": {"accepts": "folder", "produces": "text"},
    "mount-point-viewer": {"accepts": "folder", "produces": "text"},
    "multi-hash": {"accepts": "file", "produces": "text"},
    "net-reset": {"accepts": "text", "produces": "text"},
    "network-adapter-details": {"accepts": "none", "produces": "text"},
    "network-adapter-list": {"accepts": "none", "produces": "text"},
    "network-adapter-snapshot": {"accepts": "folder", "produces": "text"},
    "network-diagnostics-bundle": {"accepts": "none", "produces": "text"},
    "open-file-guide": {"accepts": "none", "produces": "text"},
    "open-handles": {"accepts": "text", "produces": "text"},
    "open-share-guide": {"accepts": "file", "produces": "text"},
    "os-version": {"accepts": "none", "produces": "text"},
    "package-cache-guide": {"accepts": "none", "produces": "text"},
    "partition-information": {"accepts": "folder", "produces": "text"},
    "password-entropy": {"accepts": "none", "produces": "text"},
    "patch-preview": {"accepts": "file", "produces": "text"},
    "path-deduplication-report": {"accepts": "none", "produces": "text"},
    "path-length": {"accepts": "folder", "produces": "text"},
    "pdf-compress": {"accepts": "file", "produces": "text"},
    "pdf-metadata-reader": {"accepts": "file", "produces": "text"},
    "pdf-page-counter": {"accepts": "file", "produces": "text"},
    "pdf-rotate": {"accepts": "file", "produces": "text"},
    "pdf-text": {"accepts": "file", "produces": "text"},
    "pdf-text-search": {"accepts": "file", "produces": "text"},
    "permissions": {"accepts": "file", "produces": "text"},
    "pip-command-guide": {"accepts": "none", "produces": "text"},
    "pomodoro-timer": {"accepts": "text", "produces": "text"},
    "portable-scan": {"accepts": "folder", "produces": "text"},
    "power-converter": {"accepts": "text", "produces": "text"},
    "power-source-status": {"accepts": "folder", "produces": "text"},
    "powershell-script-generator": {"accepts": "text", "produces": "text"},
    "powershell-version": {"accepts": "none", "produces": "text"},
    "pressure-converter": {"accepts": "text", "produces": "text"},
    "printer-inventory": {"accepts": "none", "produces": "text"},
    "process-affinity-setter": {"accepts": "text", "produces": "text"},
    "process-cpu-snapshot": {"accepts": "text", "produces": "text"},
    "process-details": {"accepts": "text", "produces": "text"},
    "process-handle-summary": {"accepts": "text", "produces": "text"},
    "process-memory-snapshot": {"accepts": "text", "produces": "text"},
    "process-path-resolver": {"accepts": "text", "produces": "text"},
    "process-pipe-helper": {"accepts": "none", "produces": "text"},
    "process-priority-reader": {"accepts": "text", "produces": "text"},
    "process-priority-setter": {"accepts": "text", "produces": "text"},
    "process-search": {"accepts": "text", "produces": "text"},
    "process-start-time": {"accepts": "text", "produces": "text"},
    "process-terminate": {"accepts": "text", "produces": "text"},
    "process-tree": {"accepts": "text", "produces": "text"},
    "process-wait": {"accepts": "text", "produces": "text"},
    "proxy-configuration": {"accepts": "none", "produces": "text"},
    "python-environment": {"accepts": "none", "produces": "text"},
    "python-import-checker": {"accepts": "none", "produces": "text"},
    "python-package-list": {"accepts": "none", "produces": "text"},
    "python-package-versions": {"accepts": "none", "produces": "text"},
    "python-syntax-checker": {"accepts": "file", "produces": "text"},
    "rand-file": {"accepts": "text", "produces": "file"},
    "random-file": {"accepts": "folder", "produces": "text"},
    "recent-docs-report": {"accepts": "folder", "produces": "text"},
    "regedit": {"accepts": "none", "produces": "text"},
    "regex-replacer": {"accepts": "text", "produces": "text"},
    "registry-backup": {"accepts": "none", "produces": "text"},
    "registry-export": {"accepts": "text", "produces": "text"},
    "registry-import": {"accepts": "text", "produces": "text"},
    "registry-key-creator": {"accepts": "none", "produces": "text"},
    "registry-key-deleter": {"accepts": "none", "produces": "text"},
    "registry-path-validator": {"accepts": "text", "produces": "text"},
    "registry-query": {"accepts": "text", "produces": "text"},
    "registry-value-deleter": {"accepts": "none", "produces": "text"},
    "registry-value-enumerator": {"accepts": "text", "produces": "text"},
    "registry-value-setter": {"accepts": "none", "produces": "text"},
    "relative-time": {"accepts": "text", "produces": "text"},
    "renamer": {"accepts": "folder", "produces": "text"},
    "requirements-generator": {"accepts": "none", "produces": "text"},
    "resource-log-viewer": {"accepts": "folder", "produces": "text"},
    "resource-snapshot": {"accepts": "file", "produces": "file"},
    "resource-trend-csv": {"accepts": "folder", "produces": "text"},
    "restore-point": {"accepts": "none", "produces": "text"},
    "schedule": {"accepts": "text", "produces": "text"},
    "scheduled-task-details": {"accepts": "text", "produces": "text"},
    "scheduled-task-disable": {"accepts": "text", "produces": "text"},
    "scheduled-task-enable": {"accepts": "text", "produces": "text"},
    "scheduled-task-run": {"accepts": "text", "produces": "text"},
    "sdelete": {"accepts": "file", "produces": "text", "destructive": True},
    "search": {"accepts": "text", "produces": "text"},
    "seconds-converter": {"accepts": "text", "produces": "text"},
    "sentence-counter": {"accepts": "file", "produces": "text"},
    "service": {"accepts": "text", "produces": "text"},
    "shell-command-runner": {"accepts": "text", "produces": "text"},
    "slugify-converter": {"accepts": "none", "produces": "text"},
    "smart-status": {"accepts": "folder", "produces": "text"},
    "snapshot-inventory": {"accepts": "folder", "produces": "text"},
    "sorter": {"accepts": "folder", "produces": "file"},
    "sparse-file-inspector": {"accepts": "folder", "produces": "text"},
    "speed-converter": {"accepts": "text", "produces": "text"},
    "speed-probe": {"accepts": "text", "produces": "text"},
    "splitter": {"accepts": "file", "produces": "file"},
    "ssl-expiry": {"accepts": "text", "produces": "text"},
    "startup": {"accepts": "none", "produces": "text"},
    "startup-entry-inventory": {"accepts": "none", "produces": "text"},
    "startup-folder-cleaner": {"accepts": "none", "produces": "text"},
    "startup-folder-viewer": {"accepts": "none", "produces": "text"},
    "startup-report": {"accepts": "text", "produces": "text"},
    "startup-security-audit": {"accepts": "file", "produces": "text"},
    "stderr-capture": {"accepts": "text", "produces": "text"},
    "stdout-capture": {"accepts": "text", "produces": "text"},
    "subnet-calculator": {"accepts": "text", "produces": "text"},
    "symlink-finder": {"accepts": "folder", "produces": "text"},
    "system-directory-report": {"accepts": "none", "produces": "text"},
    "system-environment-export": {"accepts": "none", "produces": "text"},
    "system-information-json-export": {"accepts": "none", "produces": "text"},
    "system-information-text-export": {"accepts": "none", "produces": "text"},
    "system-summary": {"accepts": "none", "produces": "text"},
    "system-uptime": {"accepts": "none", "produces": "text"},
    "tar-create": {"accepts": "file", "produces": "text"},
    "tar-extract": {"accepts": "folder", "produces": "text"},
    "task-trigger-guide": {"accepts": "text", "produces": "text"},
    "task-xml-export": {"accepts": "text", "produces": "text"},
    "temp-aging-cleaner": {"accepts": "folder", "produces": "text", "destructive": True},
    "temp-clean": {"accepts": "none", "produces": "text", "destructive": True},
    "temperature-converter": {"accepts": "text", "produces": "text"},
    "text-diff": {"accepts": "text", "produces": "text"},
    "thumbnail": {"accepts": "file", "produces": "text"},
    "timestamp-converter": {"accepts": "text", "produces": "text"},
    "tls-certificate-inspector": {"accepts": "text", "produces": "text"},
    "transcode": {"accepts": "file", "produces": "text"},
    "tree-print": {"accepts": "file", "produces": "text"},
    "unicode-normalizer": {"accepts": "text", "produces": "text"},
    "url-decoder": {"accepts": "none", "produces": "text"},
    "url-encoder": {"accepts": "none", "produces": "text"},
    "usb-device-inventory": {"accepts": "none", "produces": "text"},
    "uuid-tool": {"accepts": "none", "produces": "text"},
    "venv-size": {"accepts": "none", "produces": "text"},
    "video-bitrate-inspector": {"accepts": "file", "produces": "text"},
    "video-duration": {"accepts": "file", "produces": "text"},
    "video-frame-rate-inspector": {"accepts": "file", "produces": "text"},
    "video-mime-detector": {"accepts": "file", "produces": "text"},
    "video-resolution-inspector": {"accepts": "file", "produces": "text"},
    "video-stream-inspector": {"accepts": "file", "produces": "text"},
    "virtual-desktop-settings": {"accepts": "none", "produces": "text"},
    "virtual-desktop-shortcut": {"accepts": "none", "produces": "text"},
    "virtual-environment-finder": {"accepts": "none", "produces": "text"},
    "virtual-environment-report": {"accepts": "none", "produces": "text"},
    "volume-converter": {"accepts": "text", "produces": "text"},
    "volume-serial-reader": {"accepts": "folder", "produces": "text"},
    "watch": {"accepts": "folder", "produces": "text"},
    "week-number": {"accepts": "text", "produces": "text"},
    "wheel-inspector": {"accepts": "none", "produces": "text"},
    "whois-lookup": {"accepts": "text", "produces": "text"},
    "window-desktop-mapper": {"accepts": "none", "produces": "text"},
    "window-list": {"accepts": "none", "produces": "text"},
    "window-minimize-all": {"accepts": "none", "produces": "text"},
    "window-restore-all": {"accepts": "none", "produces": "text"},
    "window-title-search": {"accepts": "none", "produces": "text"},
    "windows-features-snapshot": {"accepts": "text", "produces": "text"},
    "windows-hotfix-snapshot": {"accepts": "text", "produces": "text"},
    "windows-version-report": {"accepts": "none", "produces": "text"},
    "yaml-structure-checker": {"accepts": "file", "produces": "text"},
    "zip-create": {"accepts": "file", "produces": "file"},
    "zip-extract": {"accepts": "folder", "produces": "text"},
}

_VALID_ACCEPTS = {"file", "folder", "text", "none"}
_VALID_PRODUCES = {"file", "text", "none"}


def apply_tool_metadata(tool: dict[str, Any]) -> dict[str, Any]:
    """Fill in optional ``accepts`` / ``produces`` / ``destructive`` fields.

    A value already present on the tool entry wins (packs may declare their own
    metadata); otherwise the curated table is consulted.  Fields that remain
    unset are left absent on purpose so the GUI keeps today's behaviour.
    """
    cmd = str(tool.get("cli_command", "")).strip()
    meta = TOOL_METADATA.get(cmd)
    if not meta:
        return tool
    if "accepts" in meta and tool.get("accepts") not in _VALID_ACCEPTS:
        tool["accepts"] = meta["accepts"]
    if "produces" in meta and tool.get("produces") not in _VALID_PRODUCES:
        tool["produces"] = meta["produces"]
    if meta.get("destructive") and "destructive" not in tool:
        tool["destructive"] = True
    return tool


class _LineWriter(io.TextIOBase):
    """Stream complete lines to a callback as they are written.

    Used to redirect a tool's stdout/stderr to a live consumer (the GUI) so
    long-running tools show output as it happens instead of buffering the whole
    run in memory until the handler returns.
    """

    def __init__(self, emit: Callable[[str], None]) -> None:
        self._emit = emit
        self._buf = ""

    def write(self, text: str) -> int:
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self._emit(line)
        return len(text)

    def flush(self) -> None:
        if self._buf:
            self._emit(self._buf)
            self._buf = ""

    def writable(self) -> bool:
        return True

    def isatty(self) -> bool:
        return False


class ToolRegistry:
    def __init__(self, tools: list[dict[str, Any]], *, preferences: PackPreferences | None = None) -> None:
        self.tools: dict[str, dict[str, Any]] = {}
        self.capability_checker = CapabilityChecker()
        # A fresh PackPreferences re-reads the durable file, so a rebuild (the
        # GUI's on_refresh) always reflects the latest enable/disable choices.
        self.preferences = preferences if preferences is not None else PackPreferences()
        for tool in tools:
            self.register_tool(tool)
        self.check_availability()

    # ------------------------------------------------------------- registration
    def register_tool(self, tool: dict[str, Any]) -> None:
        cmd = str(tool.get("cli_command", "")).strip()
        handler = str(tool.get("handler", "")).strip()
        if not cmd or not handler:
            logger.warning("Ignoring malformed tool metadata: %s", tool)
            return
        if cmd in self.tools:
            logger.warning("Duplicate CLI command %s; keeping first registration", cmd)
            return
        normalized = dict(tool)
        normalized["cli_command"] = cmd
        normalized["dependencies"] = list(normalized.get("dependencies") or [])
        normalized["pack"] = str(normalized.get("pack", ""))
        normalized["available"] = False
        normalized["missing_dependencies"] = []
        apply_tool_metadata(normalized)
        self.tools[cmd] = normalized

    # ------------------------------------------------------------------- packs
    def is_pack_enabled(self, name: str) -> bool:
        """True when ``name`` is not in the user's opt-out list."""
        return self.preferences.is_enabled(str(name))

    def all_packs(self) -> list[str]:
        """Every pack that contributes a tool, sorted."""
        return sorted({t["pack"] for t in self.tools.values() if t.get("pack")})

    def enabled_packs(self) -> list[str]:
        """Packs that are present *and* enabled, sorted."""
        return [p for p in self.all_packs() if self.is_pack_enabled(p)]

    def disabled_packs(self) -> list[str]:
        return [p for p in self.all_packs() if not self.is_pack_enabled(p)]

    def set_pack_enabled(self, name: str, enabled: bool) -> bool:
        """Persist a pack's enabled state; returns the resulting state.

        The change is durable immediately.  Callers rebuild the registry (the
        GUI's ``on_refresh``) to make it take effect without a restart.
        """
        self.preferences.set_enabled(name, enabled)
        return self.is_pack_enabled(name)

    def _tool_enabled(self, tool: dict[str, Any]) -> bool:
        return self.is_pack_enabled(tool.get("pack", ""))

    @staticmethod
    def _pack_title(pack: str, tools: Iterable[dict[str, Any]]) -> str:
        """Display title for a pack: its most common tool category."""
        counts: dict[str, int] = {}
        for tool in tools:
            cat = str(tool.get("category", "")).strip()
            if cat:
                counts[cat] = counts.get(cat, 0) + 1
        if counts:
            return max(counts.items(), key=lambda kv: kv[1])[0]
        return pack.replace("_", " ").title()

    def pack_summaries(self) -> list[dict[str, Any]]:
        """Per-pack facts for the Packs view.

        Each entry: ``name``, ``title``, ``tool_count``, ``enabled`` and
        ``runnable`` (how many of its tools have every dependency installed
        right now).
        """
        grouped: dict[str, list[dict[str, Any]]] = {}
        for tool in self.tools.values():
            pack = tool.get("pack", "")
            if pack:
                grouped.setdefault(pack, []).append(tool)
        summaries = []
        for pack, pack_tools in grouped.items():
            summaries.append(
                {
                    "name": pack,
                    "title": self._pack_title(pack, pack_tools),
                    "tool_count": len(pack_tools),
                    "enabled": self.is_pack_enabled(pack),
                    "runnable": sum(1 for t in pack_tools if t.get("available")),
                }
            )
        return sorted(summaries, key=lambda s: (not s["enabled"], s["title"].lower()))

    # ------------------------------------------------------------------ lookup
    def _raw_tool(self, cli_command: str) -> dict[str, Any] | None:
        return self.tools.get(cli_command)

    def get_tool(self, cli_command: str) -> dict[str, Any] | None:
        """Return a tool, or ``None`` when it is missing *or* its pack is disabled."""
        tool = self.tools.get(cli_command)
        if tool is None or not self._tool_enabled(tool):
            return None
        return tool

    def enabled_tools(self) -> list[dict[str, Any]]:
        return [t for t in self.tools.values() if self._tool_enabled(t)]

    def search(self, query: str) -> list[dict[str, Any]]:
        q = query.strip().lower()
        tools = self.enabled_tools()
        if not q:
            return tools
        return [
            t
            for t in tools
            if any(q in str(t.get(k, "")).lower() for k in ("name", "description", "category", "cli_command"))
        ]

    def list_categories(self) -> dict[str, list[dict[str, Any]]]:
        categories: dict[str, list[dict[str, Any]]] = {}
        for tool in self.enabled_tools():
            categories.setdefault(str(tool.get("category", "Uncategorized")), []).append(tool)
        for items in categories.values():
            items.sort(key=lambda t: str(t.get("name", "")).lower())
        return dict(sorted(categories.items(), key=lambda kv: kv[0].lower()))

    def check_availability(self) -> None:
        for tool in self.tools.values():
            missing = self.capability_checker.get_missing(tool.get("dependencies", []))
            tool["missing_dependencies"] = missing
            tool["available"] = not missing

    @staticmethod
    def _resolve_handler(tool: dict[str, Any]) -> Callable[..., Any]:
        handler_path = str(tool["handler"])
        module_name, func_name = handler_path.rsplit(".", 1)
        module = importlib.import_module(f"{tool['pack']}.{module_name}")
        return getattr(module, func_name)

    def run_tool(
        self, cli_command: str, args: list[str] | None = None, *, output: Callable[[str], None] | None = None
    ) -> int:
        emit = output or print
        tool = self._raw_tool(cli_command)
        if not tool:
            emit(f"Tool '{cli_command}' not found.")
            return 2
        if not self._tool_enabled(tool):
            pack = tool.get("pack", "")
            emit(
                f"Tool '{tool.get('name', cli_command)}' is disabled: its pack '{pack}' is turned off.\n"
                f"Enable the '{pack}' pack in the Packs view (or run: utility_suite packs enable {pack}) to use it."
            )
            return 4
        if not tool.get("available", False):
            missing = tool.get("missing_dependencies", []) or []
            from .capability_checker import download_hint

            lines = [f"Tool '{tool['name']}' is unavailable. Missing: {', '.join(missing) or 'unknown dependency'}"]
            for dep in missing:
                lines.append(f"  - {dep}: {download_hint(dep)}")
            emit("\n".join(lines))
            return 3
        try:
            handler = self._resolve_handler(tool)
        except Exception as exc:
            logger.exception("Handler import failed for %s", cli_command)
            emit(f"Error loading tool: {exc}")
            return 1
        try:
            if output is None:
                result = handler(args or [])
            else:
                writer = _LineWriter(output)
                with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                    result = handler(args or [])
                writer.flush()
            return int(result or 0)
        except SystemExit as exc:
            return int(exc.code or 0)
        except Exception as exc:
            logger.exception("Tool failed: %s", tool.get("name"))
            emit(f"Tool execution failed: {exc}")
            return 1
