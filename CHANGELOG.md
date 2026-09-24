# Changelog

All notable changes to **Utility Suite** are documented in this file.
This project follows semantic versioning; the authoritative version string
lives in `VERSION.txt` and is mirrored by `config.json` (`"version"` field)
and `core/__init__.py`. A regression guard in `audit.py` fails the release
audit if these drift apart.

## [Unreleased]

### Documentation
- `README.md`: architecture tree now lists every top-level asset that ships
  with the repository (CI workflow, `VERSION.txt`, `DEVELOPER_GUIDE.md`,
  `TOOL_CATALOG.md`, `EXPANSION_CATALOG.md`); the Validation section no
  longer claims committed "Release SHA-256 generation" — hashes are
  produced at distribution time via `Get-FileHash` (`COMPILATION.md`).
- `AUDIT_REPORT.txt`: refreshed after the repository-cleanup pass —
  file/line counts updated for the post-cleanup tree and the cleanup is
  recorded alongside the other 2.1.3 fixes.

### Repository cleanup
- Removed superseded/historical artifacts (`FINAL_MAX_AUDIT.md`,
  `MERGE_NOTES.md`), duplicate committed release-hash files
  (`RELEASE_MANIFEST.txt`, `RELEASE_SHA256.txt`), a broken
  `launch_gui.bat`, a committed empty runtime log, and dead code
  (`core/file_scanner.py` — its functions were never imported; verified by
  static reference scan plus a full audit + smoke-suite run). All
  documentation references were repointed to `CHANGELOG.md`.

## [2.1.3] — 2026-09-24

### Fixed
- **Audit exit-code contract (`audit.py`)** — verified and hardened
  documentation of the CI-critical contract: `main()` returns 1 when any
  problem is found and the failure is propagated via
  `raise SystemExit(main())`. The module now also sets
  `sys.dont_write_bytecode = True` at import time so running the audit
  cannot litter the source tree with `__pycache__` directories that its own
  clutter check would flag. (The earlier "exit 0 despite AUDIT FAILED"
  report was traced to stale bytecode caches from an external compile check,
  not a code defect; caches were purged and both PASS/FAIL paths re-tested.)
- **Version-string drift (`config.json`)** — `"version"` synced from
  `2.1.2` → `2.1.3` to match `VERSION.txt` and the README, satisfying the
  audit's packaging-regression guard.

### Added
- This `CHANGELOG.md`, giving releases a single per-version fix history
  alongside `AUDIT_REPORT.txt` (latest machine-generated audit output).

### Documentation
- `README.md`: Validation section now states the `audit.py` exit-code
  contract and the findings-only (non-mutating) behavior, and points to
  this changelog.
- `DEVELOPER_GUIDE.md`: Auditing section documents the exit codes, the
  `&&` release-checklist idiom, and the manual cache-cleanup requirement.

## [2.1.2]

- Baseline 500-tool / 45-pack tree: GUI with file preview, deterministic
  plugin ZIP builder, static release audit.
