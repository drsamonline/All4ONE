"""RFC 4122 UUID generation and validation helpers (stdlib uuid only)."""
from __future__ import annotations

import argparse
import uuid

GENERATORS = {
    "v1": lambda: str(uuid.uuid1()),
    "v3": None,  # needs namespace+name, handled below
    "v4": lambda: str(uuid.uuid4()),
    "v5": None,
    "nil": lambda: str(uuid.UUID(int=0)),
    "max": lambda: str(uuid.UUID(int=2**128 - 1)),
}


def run(args=None):
    p = argparse.ArgumentParser(description="Generate or validate RFC 4122 UUIDs.")
    p.add_argument("--version", choices=("v1", "v3", "v4", "v5", "nil", "max"), default="v4")
    p.add_argument("--count", type=int, default=1, help="How many UUIDs to generate.")
    p.add_argument("--name", help="Name string for v3/v5 (with --namespace).")
    p.add_argument("--namespace", help="Namespace UUID for v3/v5 (default: DNS namespace).")
    p.add_argument("--validate", metavar="UUID", help="Check whether TEXT is a valid UUID.")
    a = p.parse_args(args or [])

    if a.validate:
        try:
            parsed = uuid.UUID(a.validate)
        except ValueError as exc:
            print(f"INVALID: {exc}")
            return 1
        print(f"VALID  version={parsed.version} variant={parsed.variant} urn={parsed.urn}")
        return 0

    if a.count < 1 or a.count > 10000:
        print("--count must be between 1 and 10000.")
        return 2

    if a.version in ("v3", "v5"):
        if not a.name:
            print(f"--name is required for {a.version}.")
            return 2
        ns = uuid.UUID(a.namespace) if a.namespace else uuid.NAMESPACE_DNS
        fn = uuid.uuid3 if a.version == "v3" else uuid.uuid5
        for _ in range(a.count):
            print(fn(ns, a.name))
        return 0

    gen = GENERATORS[a.version]
    for _ in range(a.count):
        print(gen())
    return 0
