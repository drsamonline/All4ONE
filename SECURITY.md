# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| < 2.1   | :x:                |

## Reporting a Vulnerability

Because Utility Suite is a system-utility workstation (file operations,
registry tools, process management, network diagnostics), please report
security vulnerabilities **privately** rather than in a public issue:

- Open a private security advisory via GitHub:
  *Security* tab → *Report a vulnerability*.
- Or email the maintainer (see `AUTHORS.md`).

Please include reproduction steps, affected version (`--version` output),
and any relevant log excerpts from `logs/utility_suite.log`. **Do not**
include files that may contain personal data.

Expected triage: acknowledgement within 7 days; fix or disposition within
30 days where feasible. Reports for unsupported versions may be closed
without action.

## Design Safeguards Already in Place

- Command execution requires an argument list; shell strings are disabled
  (`core/extended_ops.py::_run` raises on `str` commands, `shell=False`).
- The static release audit (`audit.py`) fails the build if any source file
  introduces `shell=True` or `os.system(` patterns.
- Plugin packs are plain Python shipped beside the executable; review third
  party plugins before adding them to `plugins/`.
