<div align="center">

# 🛡️ Utility Suite — Security Policy

![Scope](https://img.shields.io/badge/scope-system%20utilities-red?style=flat-square)
![Triage SLA](https://img.shields.io/badge/triage%20SLA-7%20days-blue?style=flat-square)
![Supported](https://img.shields.io/badge/supported-3.0.x-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-informational?style=flat-square)

*Author: Dr. Sohil Momin, BHMS*

</div>

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 3.0.x   | ✅ |
| < 3.0   | ❌ |

## Reporting a Vulnerability

Because Utility Suite is a system-utility workstation (file operations,
registry tools, process management, network diagnostics), please report
security vulnerabilities **privately** rather than in a public issue:

- Open a private security advisory via GitHub:
  **Security** tab → **Report a vulnerability**.
- Or email the maintainer (see [AUTHORS.md](AUTHORS.md)).

Please include reproduction steps, affected version (`--version` output),
and any relevant log excerpts from `logs/utility_suite.log`. **Do not**
include files that may contain personal data.

Expected triage: acknowledgement within 7 days; fix or disposition within
30 days where feasible. Reports for unsupported versions may be closed
without action.

## Design Safeguards Already in Place

- **No shell strings.** Command execution requires an argument list; the
  shared runner (`core/extended_ops.py::_run`) raises on a `str` command and
  always calls `subprocess.run(..., shell=False)`. The static release audit
  (`audit.py`) fails the build if any source file introduces `shell=True` or
  `os.system(`.
- **Archive extraction is path-safe.** ZIP and TAR extraction resolve every
  member and reject anything that would escape the destination (zip-slip /
  tar-slip); TAR extraction also skips symlinks, hardlinks, devices and FIFOs.
  Both are covered by regression tests.
- **Destructive actions are gated.** Tools that delete or overwrite data
  require an explicit `--yes`, and the GUI shows a confirmation prompt before
  running anything in its destructive-tool set.
- **Elevated helpers validate their inputs.** `system_utils/net_reset.py`
  validates the adapter name against a strict allow-list before it is used in
  an elevated PowerShell command, so a crafted adapter name cannot inject
  code.
- **Plugin trust boundary.** In a release, all 45 packs are **embedded inside
  the single `utility_suite.exe`** (compiled into `bundle/tools.dat` at build
  time). If you extend the suite from source, review third-party pack code
  before rebuilding the bundle — pack modules execute Python code within the
  user account and therefore have the same authority as the process running
  Utility Suite.

## Supply-chain hygiene

- GitHub Actions are monitored by Dependabot (`.github/dependabot.yml`), which
  raises PRs for action and pip updates.
- `ci.yml` runs with `permissions: contents: read` (least privilege).
- Secret scanning and push protection are enabled on the repository.
