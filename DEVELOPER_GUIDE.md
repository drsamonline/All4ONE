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

## Adding a tool

1. Add metadata to the appropriate pack.
2. Add the lazy operation mapping.
3. Implement the actual operation.
4. Add or update a smoke test.
5. Rebuild plugin ZIPs.
6. Run the audit again.

Keep the catalogue at or below 500 tools unless the product specification is deliberately revised.
