"""Shared lazy adapter factory for expansion-plugin handlers."""

from __future__ import annotations
from collections.abc import Callable


def make_handler(operation: str) -> Callable[[list[str]], int]:
    """Return a tiny adapter that invokes the shared implementation lazily."""

    def handler(args: list[str] | None = None) -> int:
        from .extended_ops import run_extended

        return run_extended(list(args or []), operation)

    handler.__name__ = operation.lower().replace(" ", "_").replace("-", "_")
    handler.__doc__ = f"Run the Utility Suite operation: {operation}."
    return handler
