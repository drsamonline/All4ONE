"""Executing a tool: values in, streamed lines out.

One code path serves the desktop UI and the CLI, so a tool behaves identically
in both. Everything runs off the GUI thread when the UI calls it.
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable

from .tool import Context, Tool, ToolCancelled, ToolError


@dataclass
class RunResult:
    ok: bool
    text: str = ""
    outputs: list[str] = field(default_factory=list)
    error: str = ""
    seconds: float = 0.0
    cancelled: bool = False

    def summary(self) -> str:
        if self.cancelled:
            return f"Stopped after {self.seconds:.1f}s"
        if not self.ok:
            return "Failed"
        return f"Done in {self.seconds:.2f}s"


def render(value: Any) -> str:
    """How a tool's return value appears in the console."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, indent=2, ensure_ascii=False, default=str)
    return str(value)


def execute(tool: Tool, values: dict[str, Any],
            sink: Callable[[str], None] | None = None,
            cancelled: Callable[[], bool] | None = None) -> RunResult:
    """Run one tool. Never raises: failures come back as ``RunResult``."""
    lines: list[str] = []

    def capture(line: str) -> None:
        lines.append(line)
        if sink is not None:
            sink(line)

    ctx = Context(sink=capture, cancelled=cancelled)
    payload = tool.normalise(values)

    problems = tool.validate(payload)
    if problems:
        return RunResult(ok=False, text="\n".join(lines), error="; ".join(problems))

    started = time.perf_counter()
    try:
        result = tool.run(payload, ctx)
        rendered = render(result)
        if rendered:
            ctx.log(rendered)
        return RunResult(ok=True, text="\n".join(lines), outputs=list(ctx.outputs),
                         seconds=time.perf_counter() - started)
    except ToolCancelled:
        return RunResult(ok=False, text="\n".join(lines), cancelled=True,
                         seconds=time.perf_counter() - started)
    except ToolError as exc:
        ctx.log(f"✕ {exc}")
        return RunResult(ok=False, text="\n".join(lines), error=str(exc),
                         seconds=time.perf_counter() - started)
    except Exception as exc:  # noqa: BLE001 - a tool must never crash the app
        ctx.log(f"✕ {type(exc).__name__}: {exc}")
        for line in traceback.format_exc().splitlines()[-6:]:
            ctx.log(f"  {line}")
        return RunResult(ok=False, text="\n".join(lines), error=f"{type(exc).__name__}: {exc}",
                         seconds=time.perf_counter() - started)
