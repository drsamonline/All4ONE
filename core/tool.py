"""Tool contract for All4one.

A tool is a plain function plus a declarative description of its options.
The description is the single source of truth for three frontends:

* the desktop UI renders one page per tool straight from ``Tool.fields``,
* the CLI turns the same fields into ``--flags``,
* the catalogue is generated from the same metadata.

Nothing here imports a GUI toolkit, so the engine stays usable headless.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence

# --------------------------------------------------------------------------
# Field kinds understood by the UI and the CLI
# --------------------------------------------------------------------------
TEXT = "text"
PASSWORD = "password"
MULTILINE = "multiline"
INT = "int"
FLOAT = "float"
CHOICE = "choice"
MULTI = "multi"
BOOL = "bool"
FILE = "file"
FILES = "files"
DIR = "dir"
SAVE = "save"
COLOR = "color"
SLIDER = "slider"

KINDS = {TEXT, PASSWORD, MULTILINE, INT, FLOAT, CHOICE, MULTI, BOOL,
         FILE, FILES, DIR, SAVE, COLOR, SLIDER}


@dataclass(frozen=True)
class Field:
    """One option on a tool page."""

    key: str
    label: str
    kind: str = TEXT
    default: Any = ""
    choices: tuple[str, ...] = ()
    help: str = ""
    required: bool = False
    placeholder: str = ""
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    suffix: str = ""
    filters: str = "All files (*)"
    show_if: str = ""          # key of a bool field that must be on
    rows: int = 8              # multiline height
    secret: bool = False

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"{self.key}: unknown field kind {self.kind!r}")
        if self.kind in (CHOICE, MULTI) and not self.choices:
            raise ValueError(f"{self.key}: {self.kind} needs choices")

    # -- conversions -------------------------------------------------------
    def coerce(self, raw: Any) -> Any:
        """Turn a raw UI/CLI value into the type the tool expects."""
        if raw is None:
            return None
        if self.kind == BOOL:
            if isinstance(raw, str):
                return raw.strip().lower() in {"1", "true", "yes", "on", "y"}
            return bool(raw)
        if self.kind == INT:
            text = str(raw).strip()
            return int(float(text)) if text else (self.default or 0)
        if self.kind == FLOAT:
            text = str(raw).strip()
            return float(text) if text else (self.default or 0.0)
        if self.kind == MULTI:
            if isinstance(raw, (list, tuple)):
                return list(raw)
            text = str(raw).strip()
            return [p.strip() for p in text.split(",") if p.strip()]
        if self.kind == SLIDER:
            try:
                return float(raw)
            except (TypeError, ValueError):
                return float(self.default or 0)
        return "" if raw is None else str(raw)

    def default_value(self) -> Any:
        if self.kind == BOOL:
            return bool(self.default)
        if self.kind in (INT,):
            return self.default if self.default != "" else 0
        if self.kind in (FLOAT, SLIDER):
            return self.default if self.default != "" else 0.0
        if self.kind == MULTI:
            return list(self.default or [])
        return self.default


# --------------------------------------------------------------------------
# Shorthand constructors used by the tool modules
# --------------------------------------------------------------------------
class F:
    """Field factories: ``F.file("path", "Input file")``."""

    @staticmethod
    def text(key, label, default="", help="", required=False, placeholder="", show_if=""):
        return Field(key, label, TEXT, default, help=help, required=required,
                     placeholder=placeholder, show_if=show_if)

    @staticmethod
    def secret(key, label, default="", help="", required=False, placeholder=""):
        return Field(key, label, PASSWORD, default, help=help, required=required,
                     placeholder=placeholder, secret=True)

    @staticmethod
    def multi(key, label, default="", help="", required=False, placeholder="", rows=8):
        return Field(key, label, MULTILINE, default, help=help, required=required,
                     placeholder=placeholder, rows=rows)

    @staticmethod
    def integer(key, label, default=0, help="", minimum=None, maximum=None,
                suffix="", show_if=""):
        return Field(key, label, INT, default, help=help, minimum=minimum,
                     maximum=maximum, suffix=suffix, show_if=show_if)

    @staticmethod
    def number(key, label, default=0.0, help="", minimum=None, maximum=None,
               suffix="", step=None, show_if=""):
        return Field(key, label, FLOAT, default, help=help, minimum=minimum,
                     maximum=maximum, suffix=suffix, step=step, show_if=show_if)

    @staticmethod
    def choice(key, label, choices: Sequence[str], default=None, help="", show_if=""):
        options = tuple(choices)
        return Field(key, label, CHOICE, default if default is not None else options[0],
                     choices=options, help=help, show_if=show_if)

    @staticmethod
    def many(key, label, choices: Sequence[str], default=(), help="", show_if=""):
        return Field(key, label, MULTI, tuple(default), choices=tuple(choices),
                     help=help, show_if=show_if)

    @staticmethod
    def flag(key, label, default=False, help="", show_if=""):
        return Field(key, label, BOOL, default, help=help, show_if=show_if)

    @staticmethod
    def file(key, label, help="", required=True, filters="All files (*)", show_if=""):
        return Field(key, label, FILE, "", help=help, required=required,
                     filters=filters, show_if=show_if)

    @staticmethod
    def files(key, label, help="", required=True, filters="All files (*)", show_if=""):
        return Field(key, label, FILES, "", help=help, required=required,
                     filters=filters, show_if=show_if)

    @staticmethod
    def folder(key, label, help="", required=True, show_if=""):
        return Field(key, label, DIR, "", help=help, required=required, show_if=show_if)

    @staticmethod
    def save(key, label, help="", required=False, default="",
             filters="All files (*)", show_if=""):
        return Field(key, label, SAVE, default, help=help, required=required,
                     filters=filters, show_if=show_if)

    @staticmethod
    def color(key, label, default="#3b82f6", help=""):
        return Field(key, label, COLOR, default, help=help)

    @staticmethod
    def slider(key, label, default=50.0, minimum=0.0, maximum=100.0,
               suffix="", help=""):
        return Field(key, label, SLIDER, default, help=help, minimum=minimum,
                     maximum=maximum, suffix=suffix)


# --------------------------------------------------------------------------
# Output sink handed to every tool
# --------------------------------------------------------------------------
class Context:
    """What a running tool gets to talk to.

    Tools never print directly: they call :meth:`log` so the same text can go
    to the UI console, to stdout in CLI mode, or to a test sink.
    """

    def __init__(self, sink: Callable[[str], None] | None = None,
                 cancelled: Callable[[], bool] | None = None) -> None:
        self._sink = sink or (lambda line: None)
        self._cancelled = cancelled or (lambda: False)
        self.outputs: list[str] = []

    def log(self, message: Any = "") -> None:
        text = "" if message is None else str(message)
        for line in text.splitlines() or [""]:
            self._sink(line)

    def progress(self, value: float, note: str = "") -> None:
        """Report 0-100 progress; the UI shows it as a slim bar."""
        pct = max(0.0, min(100.0, float(value)))
        self._sink(f"\x00progress:{pct:.0f}:{note}")

    def check_cancel(self) -> None:
        if self._cancelled():
            raise ToolCancelled()

    def output(self, path: str) -> None:
        """Register a file the tool produced, so the UI can offer to open it."""
        if path and path not in self.outputs:
            self.outputs.append(path)
            self._sink(f"\x00output:{path}")


class ToolCancelled(Exception):
    """Raised when the user stops a run."""


class ToolError(Exception):
    """A tool failed in a way worth showing to the user verbatim."""


# --------------------------------------------------------------------------
# The tool itself
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Tool:
    id: str
    name: str
    category: str
    summary: str
    run: Callable[[dict, Context], Any]
    fields: tuple[Field, ...] = ()
    needs: tuple[str, ...] = ()
    destructive: bool = False
    keywords: str = ""
    platforms: tuple[str, ...] = ()   # empty == everywhere

    # -- helpers -----------------------------------------------------------
    def field_map(self) -> dict[str, Field]:
        return {f.key: f for f in self.fields}

    def defaults(self) -> dict[str, Any]:
        return {f.key: f.default_value() for f in self.fields}

    def normalise(self, values: dict[str, Any]) -> dict[str, Any]:
        out = self.defaults()
        for key, raw in values.items():
            fld = self.field_map().get(key)
            out[key] = fld.coerce(raw) if fld else raw
        return out

    def validate(self, values: dict[str, Any]) -> list[str]:
        problems = []
        for fld in self.fields:
            if fld.show_if and not values.get(fld.show_if):
                continue
            if fld.required and not str(values.get(fld.key) or "").strip():
                problems.append(f"{fld.label} is required")
        return problems

    def accepts_files(self) -> list[Field]:
        return [f for f in self.fields if f.kind in (FILE, FILES)]

    def primary_input(self) -> Field | None:
        for kind in (FILE, FILES, DIR):
            for fld in self.fields:
                if fld.kind == kind:
                    return fld
        return None

    @property
    def is_windows_only(self) -> bool:
        return tuple(self.platforms) == ("win",)


_REGISTRY: list[Tool] = []


def tool(**meta: Any):
    """Decorate a function to register it as a tool.

    ``run`` receives ``(values, ctx)`` and returns a string, a dict/list
    (rendered as JSON) or ``None`` when it already logged everything.
    """

    def register(fn: Callable[[dict, Context], Any]) -> Callable:
        params = inspect.signature(fn).parameters
        if len(params) != 2:
            raise TypeError(f"tool {meta.get('id')}: run() must take (values, ctx)")
        fields = tuple(meta.pop("fields", ()))
        keys = [f.key for f in fields]
        if len(keys) != len(set(keys)):
            raise ValueError(f"tool {meta.get('id')}: duplicate field keys")
        t = Tool(run=fn, fields=fields, **meta)
        fn._all4one_tool = t  # type: ignore[attr-defined]
        _REGISTRY.append(t)
        return fn

    return register


def collect(module: Any) -> Iterable[Tool]:
    """Pull every decorated function out of an imported module."""
    for value in vars(module).values():
        t = getattr(value, "_all4one_tool", None)
        if isinstance(t, Tool):
            yield t
