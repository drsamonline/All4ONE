**Author:** Dr. Sohil Momin, BHMS

# Utility Suite Developer Guide

## Plugin contract

Each pack contains `__init__.py` with a `register_tools()` function returning metadata dictionaries.

Example:

```python
def register_tools():
    return [{
        "name": "Example Tool",
        "category": "Example",
        "description": "Does a concrete example task.",
        "handler": "operations.example_tool",
        "cli_command": "example-tool",
        "dependencies": []
    }]
```

Expansion packs use a shared lazy adapter factory so the project does not copy 10–20 identical wrapper functions into every pack. The operation implementation lives in `core/extended_ops.py` or a specialized module.

## Handler rules

- Accept a list of string arguments.
- Return an integer process-style status code.
- Print concise human-readable output for CLI use.
- Import heavy dependencies inside the operation that needs them.
- Never use shell command interpolation when a list of subprocess arguments is possible.
- Fail with a clear diagnostic rather than terminating the suite.

## Auditing

`audit.py` is static and release-oriented. Runtime resolution is covered by the test suite so normal audits do not create `__pycache__` noise in the source tree.

**Exit-code contract (CI gate):** `python audit.py` exits **0** on
`AUDIT PASSED` and **1** on `AUDIT FAILED` (propagated via
`raise SystemExit(main())`). Chain it with `&&` in release scripts — e.g.
`python audit.py && python create_plugin_zips.py` — so a failed audit stops
the pipeline loudly instead of silently shipping broken releases. The audit
is findings-only: it never mutates the tree, so delete stray `__pycache__/`
directories yourself before expecting a PASS (running the audit itself is
safe — it sets `sys.dont_write_bytecode` internally).

## Adding a tool

1. Add metadata to the appropriate pack.
2. Add the lazy operation mapping.
3. Implement the actual operation.
4. Add or update a smoke test.
5. Rebuild plugin ZIPs.
6. Run the audit again.

audit.py enforces the current catalogue size (EXPECTED_TOOLS = 539 as of the 2026-09 expansion). Bump that constant deliberately when adding or removing tools, and regenerate TOOL_CATALOG.md / EXPANSION_CATALOG.md from the live registry afterwards.

## Testing tiers - which one runs where

There are three layers of testing in this repository, and they are
**not interchangeable** - running the wrong one in the wrong place is
exactly what previously broke the Windows CI build:

1. **`audit.py`** - static, safe, fast. Checks catalogue integrity,
   syntax, handler wiring, plugin ZIP consistency, and a couple of
   packaging-regression guards (version-string drift, `build.spec`
   accidentally re-bundling `plugins/`). Runs everywhere: locally, in
   CI, on every platform. No side effects.

2. **`tests/test_suite.py`** (`python -B -m tests.test_suite`) -
   behavioral smoke tests against a disposable temp sandbox: config
   merging, split/join round-trips, CSV tools, zip-slip/tar-slip
   rejection, renamer. Deliberately scoped to tools with no real system
   side effects. Runs everywhere, including CI, before every build.

3. **`tests/test_all_tools.py`** - an exhaustive sweep that invokes
   *every one* of the 539 registered tools in its own subprocess. This
   is a **local/manual developer diagnostic only** - it is intentionally
   **not** part of the CI build pipeline. The reason: on a Linux dev
   machine, Windows-only tools (services, registry, event log, network
   adapter reset, System Restore, driver export, scheduled tasks) are
   correctly reported as "unavailable" and never actually execute. On a
   real Windows machine - including a GitHub Actions `windows-latest`
   runner - those same tools *are* available and the sweep will really
   run them: creating scheduled tasks, querying/starting/stopping real
   services, attempting a real System Restore checkpoint (often disabled
   on ephemeral cloud VMs and slow or unresponsive when it is), and
   `net-reset` in particular requests interactive UAC elevation, which
   never resolves on a headless CI runner. Every affected tool now has
   an explicit subprocess timeout so it can never hang the process
   indefinitely, but you still should not point this sweep at a shared
   or production Windows machine - run it only on a disposable VM/sandbox
   where side effects are acceptable.

If you want broader automated coverage in CI beyond `test_suite.py`
without this risk, the safe path is to extend `test_all_tools.py` with
an explicit allowlist/denylist by pack (skip `system_utils`,
`windows_power`, `automation`'s `schedule`, and `network_tools`'
`net-reset`) rather than running it unmodified in CI.
