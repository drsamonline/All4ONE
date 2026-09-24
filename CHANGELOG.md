# Changelog

All notable changes to **Utility Suite** are documented in this file.
This project follows semantic versioning; the authoritative version string
lives in `VERSION.txt` and is mirrored by `config.json` (`"version"` field)
and `core/__init__.py`. A regression guard in `audit.py` fails the release
audit if these drift apart.

## [Unreleased]

### Added
- `LICENSE` (MIT): the repository previously shipped no license at all,
  which legally defaults to "all rights reserved" and blocked any
  publication or downstream use. Copyright (c) 2026 Dr. Sohil Momin —
  matching the author credit in README.md and AUTHORS.md.
- Catalogue expanded from 500 to 539 tools across the existing 45 packs:
  39 new pure-Python tools (slugify-converter, subnet-calculator,
  multi-hash, json-diff, cron-explainer, clipboard history ring, SSL
  expiry monitor, venv size reporter, temp-file aging cleaner, resource
  snapshot diff, base64/hex/url codecs, and more).
- `SECURITY.md`: private vulnerability-reporting policy appropriate for a
  system-utility project, plus a summary of the existing execution-safety
  guards (argument-list-only `_run`, audit-enforced `shell=True` ban).
- `.github/workflows/ci.yml`: Linux validation job (ruff lint advisory +
  hard gates on `audit.py` and the smoke-test suite) so every push/PR is
  checked without needing a Windows runner.
- `.editorconfig`: consistent encoding/indent/whitespace rules across
  editors (LF + trim whitespace by default; Markdown exempt for hard line
  breaks; `.bat`/`.ps1` stay CRLF).
- `pyproject.toml`: ruff configuration only — this project is not a pip
  package and is still run via `python run.py`.

### Changed
- Version single-source-of-truth: `VERSION.txt` remains canonical, but
  `audit.py` now enforces it against **every** version literal in the tree
  (`core/__init__.py`, `config.json`, `build.spec` header) using static
  text matching instead of importing `core` — the old import-based check
  risked re-introducing the exact `__pycache__` self-sabotage class of bug
  that was fixed below. Verified: desyncing any literal fails the audit.
- Error handling: silent `except Exception:` fallbacks in
  `core/extended_ops.py` (JSON-input parse, psutil-availability probes,
  clipboard window teardown) now log a debug-level message with the caught
  exception before falling back, so failures are diagnosable in
  `logs/utility_suite.log` while console output stays clean.

### Fixed
- `.gitignore` regression (post-expansion): the 539-tool expansion commit had
  silently reduced `.gitignore` to a single rule (`plugins/*.zip`), so every
  runtime artifact produced by the new tools (`__pycache__/`, `logs/utility_suite.log`,
  `logs/sweep_results.json`) showed up as untracked clutter in PR diffs. The full
  ignore set is restored: bytecode caches, `logs/*` (except `.gitkeep`), build/dist,
  ruff/pytest caches, venvs, OS and editor junk.
- CI (Linux + Windows GitHub Actions builds failing): a subsequent commit
  had force-added tracked clutter (`__pycache__`/*.pyc files and an empty
  `logs/utility_suite.log`) and emptied `.gitignore`, so the audit's
  tracked-cache gate correctly failed every job. The four files are now
  untracked, `.gitignore` is restored (plus ruff/pytest cache entries),
  `audit.py` gained a companion gate rejecting any tracked non-`.gitkeep`
  file under `logs/`, `ci.yml` fails fast with a dedicated "No committed
  build/cache artifacts" step, and `build-windows-exe.yml` runs the audit
  before the ZIP rebuild so clutter errors surface first.
- `audit.py`: the source-tree cache-clutter gate scanned every
  `__pycache__` directory on disk, including untracked, gitignored ones
  that the interpreter itself writes while the audit imports the plugin
  loader. Plain `python audit.py` therefore always failed with
  "Build tree contains __pycache__" (it could only pass under
  `python -B`). The check now flags only *tracked* `__pycache__`/`.pyc`
  files; ZIP cache scanning and all other gates are unchanged.

### Documentation
- Full documentation sync after the 539-tool expansion: every guide that
  still quoted the stale 500-tool baseline was updated (README title and
  feature list, USER_GUIDE intro, DEVELOPER_GUIDE sweep description and
  catalogue-size rule, AUDIT_REPORT stats and expansion post-mortem).
- `TOOL_CATALOG.md` and `EXPANSION_CATALOG.md` regenerated from the live
  tool registry so all 539 tools and per-pack counts are listed; fixed an
  unresolved template artifact (`Plugin packs: {len({p for p,_ in entries})}`)
  that had been committed as literal text in TOOL_CATALOG.md's header.
- `DEVELOPER_GUIDE.md`: replaced the obsolete "keep the catalogue at or
  below 500 tools" rule with the current policy (bump `EXPECTED_TOOLS` in
  `audit.py` deliberately and regenerate both catalogues afterwards).
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
