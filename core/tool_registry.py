"""Tool metadata registry and lazy execution engine."""

from __future__ import annotations

import contextlib
import importlib
import io
import logging
from typing import Any, Callable

from .capability_checker import CapabilityChecker

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self, tools: list[dict[str, Any]]) -> None:
        self.tools: dict[str, dict[str, Any]] = {}
        self.capability_checker = CapabilityChecker()
        for tool in tools:
            self.register_tool(tool)
        self.check_availability()

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
        normalized["available"] = False
        normalized["missing_dependencies"] = []
        self.tools[cmd] = normalized

    def get_tool(self, cli_command: str) -> dict[str, Any] | None:
        return self.tools.get(cli_command)

    def search(self, query: str) -> list[dict[str, Any]]:
        q = query.strip().lower()
        if not q:
            return list(self.tools.values())
        return [
            t
            for t in self.tools.values()
            if any(q in str(t.get(k, "")).lower() for k in ("name", "description", "category", "cli_command"))
        ]

    def list_categories(self) -> dict[str, list[dict[str, Any]]]:
        categories: dict[str, list[dict[str, Any]]] = {}
        for tool in self.tools.values():
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
        tool = self.get_tool(cli_command)
        if not tool:
            emit(f"Tool '{cli_command}' not found.")
            return 2
        if not tool.get("available", False):
            missing = ", ".join(tool.get("missing_dependencies", [])) or "unknown dependency"
            emit(f"Tool '{tool['name']}' is unavailable. Missing: {missing}")
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
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                    result = handler(args or [])
                for line in buffer.getvalue().splitlines():
                    output(line)
            return int(result or 0)
        except SystemExit as exc:
            return int(exc.code or 0)
        except Exception as exc:
            logger.exception("Tool failed: %s", tool.get("name"))
            emit(f"Tool execution failed: {exc}")
            return 1
