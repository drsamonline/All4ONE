# Changelog

All notable changes to **Utility Suite** are documented in this file.
This project follows semantic versioning; the authoritative version string
lives in `VERSION.txt` and is mirrored by `config.json` (`"version"` field),
`core/__init__.py`, and the `build_onefile.spec` header. A regression guard in
`audit.py` fails the release audit if these drift apart.

## [3.0.5.1] — 2026-10-01

### Fixed
- **Windows build**: verified green on tag v3.0.5.1 (run 36850493868). The only
  failing Windows run in the last week was 58544a2 (VarFileInfo parse error),
  already fixed before v3.0.5/v3.0.5.1 were tagged; historical failures
  (Sep 24/30) were "Static release audit" steps rejecting tracked .pyc clutter
  — now prevented by the restored .gitignore guard.
- **Version metadata mismatch**: released exe reported ProductVersion 3.0.5
  while the tag/release was v3.0.5.1. `build_single_exe.py` now regenerates
  `version_info.txt` from VERSION.txt at the start of every build, so embedded
  FileVersion/ProductVersion can never drift from the release again.
- Version synced to 3.0.5.1 across VERSION.txt, config.json, core/__init__.py,
  version_info.txt, README badge/snippet and USER_GUIDE header.

## [3.0.5] — 2026-10-01

### Added
- **Author metadata embedded in the Windows EXE**: new `version_info.txt`
  (Win32 VERSIONINFO resource) wired into `build_onefile.spec`. Right-click
  `utility_suite.exe` → Properties → Details now shows Company/Author
  "Dr. Sohil Momin, BHMS", Product "Utility Suite", Copyright 2026.
- COMPILATION.md documents the version-resource file and the version-bump
  checklist that includes it.

### Fixed
- v3.0.4 release asset was mis-named `UtilitySuite-3.0.4-windows.zip` while
  the tag/release is v3.0.5; the zip's internal VERSION.txt is now bumped to
  3.0.5 so future builds produce `UtilitySuite-3.0.5-windows.zip`.
- Version strings synced 3.0.4 → 3.0.5 across VERSION.txt, config.json,
  core/__init__.py, build_onefile.spec, version_info.txt and all docs.

## [3.0.4.1] — 2026-10-01

### Fixed
- **Windows EXE author metadata**: `build_onefile.spec` now passes
  `version="version_info.txt"` to PyInstaller, embedding a Win32 VERSIONINFO
  resource so `utility_suite.exe` → Properties → Details shows
  *Company/Author: Dr. Sohil Momin, BHMS*, Product: Utility Suite, version 3.0.4.
- Documented the new `version_info.txt` file and its role in COMPILATION.md.

## [3.0.4] — 2026-10-01

### Fixed
- **GUI layout overflow:** the main window is now DPI-aware
  (`SetProcessDpiAwareness` before window realization) and the category chip
  strip was replaced with a single horizontally scrollable canvas, so buttons
  and text no longer spill off-screen on scaled Windows displays. Detail-pane
  text wrapping recomputes on window resize.
- **"Only 491/551 tools available" false negatives:** `core/capability_checker.py`
  previously probed pip packages (`python-docx`, `openpyxl`, `Pillow`, …) with
  `shutil.which()` — an executable lookup that can never succeed for importable
  modules — so ~50 installed-but-misdetected tools were hidden. The checker now
  resolves Python packages via `importlib.util.find_spec`, recognises Windows
  built-ins (`powershell`, `ipconfig`, `reg`, `schtasks`, `wevtutil`, …) by
  platform, and accepts common Linux equivalents for network tools.
- **`.gitignore` re-corrupted to a `(empty)` stub (regression):** housekeeping
  commit `e81a728` ("Fix hardcoded tool count in catalog badge and clear
  .gitignore") overwrote the full ignore set restored in 3.0.1 with a literal
  7-byte `(empty)` file, silently re-opening the exact clutter loophole that
  had caused old build artifacts to keep returning. The complete ignore set is
  now restored (bytecode caches, `build/`, `dist/`, `logs/*` except
  `.gitkeep`, virtual environments, ruff/pytest/mypy caches, OS/editor junk,
  `.env`/local overrides), the nine tracked `core/__pycache__/*.pyc` files and
  `logs/utility_suite.log` are untracked again, and verified with
  `git check-ignore`. The audit's tracked-artifact gate continues to guard
  against recurrence.

### Added
- **Dependency download guide:** new `deps` command (`utility_suite.exe deps` /
  `python run.py deps`) lists every missing optional dependency grouped by how
  many tools it unlocks, each with a direct download source — FFmpeg →
  gyan.dev/ffmpeg/builds, pdftotext/pdfunite → poppler-windows releases, qpdf
  → GitHub releases, GnuPG → gnupg.org/download, Tesseract → UB-Mannheim
  installer, plus exact `pip install …` lines for Python packages. Running an
  unavailable tool prints the same per-dependency hint. In the GUI the
  status-bar "X/551 tools ready" label opens a clickable install-guide dialog
  with a copyable list and refresh button.
- README gains an Author shield badge; version strings bumped 3.0.3 → 3.0.4
  across VERSION.txt, config.json, core/__init__.py and build_onefile.spec.

### Documentation
- **USER_GUIDE.md:** new "⭐ New in 3.0.x — quick try" cheat-sheet block under
  🚀 Cheat sheet listing runnable examples for all twelve tools added in
  3.0.2/3.0.3 (`hash-identify`, `password-entropy`, `b64-codec`,
  `json-schema`, `csv-query`, `text-diff`, `ip-calc`, `ini-tool`, `uuid-tool`,
  `tree-print`, `bytes-units`, `rand-file`). Every example was executed
  against the live registry before being written down, so the documented
  flags match the actual argument parsers exactly (e.g. `--password` for
  `password-entropy`, `--version v4` for `uuid-tool`, positional size + `-o`
  for `rand-file`).
- **README.md:** Quick start snippets now showcase two of the new tools
  (`ip-calc` subnet math from the exe, `csv-query --stats` from source).
- Verified remaining documents (TOOL_CATALOG.md, EXPANSION_CATALOG.md,
  AUDIT_REPORT.txt, AUTHORS.md, COMPILATION.md, INSTALLATION.md,
  DEVELOPER_GUIDE.md, SECURITY.md) are current at 551 tools / 45 packs /
  version 3.0.3; regenerated catalogs confirmed byte-identical to the live
  registry.

## [3.0.3] — 2026-10-01

Second tool-expansion wave: eight more **stdlib-only** tools added to the
`misc` pack (7 → 15 tools), registry grown from **543 → 551**. Per the
project rule, nothing in this release introduces an external dependency that
could break the single-EXE Windows build — every handler imports only Python
standard-library modules (`csv`, `difflib`, `ipaddress`, `configparser`,
`uuid`, `os`, `secrets`, `argparse`).

### Added
- `csv-query` (CSV Query) — filter rows (`--where COL=VALUE`, repeatable),
  project columns, numeric aggregates (`--numeric col` → count/min/max/sum/avg),
  stdin support and `--limit`. Complements the read-only `data_tools` CSV suite.
- `text-diff` (Text Diff) — unified/context line diff between two files using
  `difflib` (no external diff binary), plus `--summary` change counts.
- `ip-calc` (IP Subnet Calculator) — IPv4 network math: netmask/CIDR/dotted
  mask input, network/broadcast/wildcard/host-count/first-hosts listing.
- `ini-tool` (INI Toolkit) — inspect, `--get SECTION.KEY`, `--set` (writes
  back) and `--json` export of INI config files via `configparser`.
- `uuid-tool` (UUID Toolkit) — bulk generation of v1/v3/v4/v5/nil/max UUIDs
  and validation of any RFC 4122 string (`--validate`).
- `tree-print` (Directory Tree Viewer) — classic `tree`-style ASCII output
  with `--sizes`, `--depth`, `--dirs` and entry-limit safety.
- `bytes-units` (Byte Unit Converter) — decimal vs binary storage units
  (KB/KiB/MB/MiB/GiB/TiB…), accepts attached suffixes like `4.5GiB`.
- `rand-file` (Random File Generator) — creates cryptographically-random
  test files of any size (`secrets.token_bytes`, chunked) for benchmarking.

### Changed
- `audit.py`: EXPECTED_TOOLS raised 543 → 551; `tests/test_suite.py`
  assertions synced.
- `bundle/tools.dat` regenerated (deterministic); TOOL_CATALOG.md,
  EXPANSION_CATALOG.md, README.md, USER_GUIDE.md, INSTALLATION.md,
  DEVELOPER_GUIDE.md, AUTHORS.md and AUDIT_REPORT.txt re-synced to the live
  551-tool registry.
- Removed three `.pyc` files under `core/__pycache__/` that had been tracked
  by a later housekeeping commit despite the restored `.gitignore`; the audit
  clutter gate caught them immediately — the guard works as intended.

## [3.0.2] — 2026-10-01

Tool expansion: four new dependency-free tools added to the `misc` pack
(3 → 7 tools), registry grown from **539 → 543** across the same 45 packs.

### Added
- `hash-identify` (Hash Identifier) — recognises likely hash algorithm from a
  digest string (MD5/SHA-1/SHA-256/SHA-512/NTLM/bcrypt/argon2/MySQL/etc.) via
  length + format heuristics, with optional `--verify <plaintext>` against all
  common hashlib algorithms. Useful for security triage and CTF work.
- `password-entropy` (Password Entropy Calculator) — estimates charset-based
  and Shannon entropy of a password with a WEAK/MODERATE/STRONG/EXCELLENT
  verdict, or generates strong `secrets`-based random passwords
  (`--length/--count`). Complements `security_tools` and `security_audit`.
- `b64-codec` (Base64 Codec) — strict Base64 encode/decode with `--urlsafe`
  and `--no-pad` modes and file input; complements the existing loose base64
  helpers in `data_tools`.
- `json-schema` (JSON Schema Explorer) — prints a leaf-path schema
  (`path<TAB>type<TAB>value`) of any JSON document with optional `--keys`
  regex filter; pairs with the pre-existing `json-diff` in `dev_tools`.

### Changed
- `audit.py`: EXPECTED_TOOLS raised 539 → 543.
- `bundle/tools.dat` regenerated (deterministic); TOOL_CATALOG.md,
  EXPANSION_CATALOG.md, README.md, USER_GUIDE.md, INSTALLATION.md,
  DEVELOPER_GUIDE.md and AUTHORS.md re-synced to the live 543-tool registry.

## [3.0.1] — 2026-10-01

Post-release hygiene patch: the repository kept re-accumulating build clutter
and stale docs after every merge because the ignore rules had silently been
destroyed.

### Fixed
- **`.gitignore` restored (root cause):** the merged cleanup commit shipped
  `.gitignore` as a literal 7-byte `(empty)` stub. With no ignore rules,
  `dist/`, `build/`, `__pycache__/*.pyc` and runtime logs were no longer
  excluded and kept getting force-added back into release commits — the old
  build files that persisted in the tree. The full ruleset is now committed:
  bytecode caches, `build/`, `dist/`, venvs, `logs/*` (except `.gitkeep`),
  ruff/pytest/mypy caches, and OS/editor junk.
- **No Windows EXE despite green CI:** by design, a plain push to `main` only
  runs the Linux validation (`ci.yml`). The single-file Windows build fires on
  a `v*` tag push or a manual *Run workflow*. Documented prominently in README
  ("Building & releasing") so the tag step is never missed again.
- `AUDIT_REPORT.txt` header corrected to 130 Python files (matches
  `python audit.py` output) and annotated with the post-merge repair pass.

## [3.0.0] — 2026-10-01

The single-file release: everything now ships inside **one portable
`utility_suite.exe`** — runtime, all 45 tool packs, and catalog metadata
embedded via `bundle/tools.dat`. No `plugins/` folder, no sidecar files.

### Added
- `core/bundle.py`: deterministic in-memory tool bundle (`bundle/tools.dat`)
  that replaces the external `plugins/` directory at runtime (loaded via
  `zipimport` from PyInstaller's `_MEIPASS`).
- `build_onefile.spec` + `build_single_exe.py`: one-command release pipeline
  (audit → bundle regeneration → smoke tests → PyInstaller onefile build →
  packaged-exe self-check → `UtilitySuite-<version>-windows.zip`).
- `.github/workflows/build-windows-exe.yml`: automated Windows EXE build on a
  `windows-latest` runner. Triggered by pushing a `v*` tag (builds *and*
  publishes a GitHub Release with the zip attached) or manually via
  *Run workflow*. PyInstaller cannot cross-compile from Linux, so this job —
  not `ci.yml` — produces the real binary.

### Changed
- Version bumped to **3.0.0** everywhere (`VERSION.txt`, `config.json`,
  `core/__init__.py`, `build_onefile.spec`); README/docs refreshed for the
  single-file architecture and the tag-driven release flow.
- Releases are cut by pushing a version tag; ordinary pushes to `main` are
  validated by `ci.yml` only (Linux: ruff advisory + hard gates on
  `audit.py`, catalogue drift, tracked-artifact hygiene, and the smoke suite).

### Fixed
- **Windows CI build never triggered**: the workflow only ran on `v*` tags,
  which had never been pushed, so no Windows artifact/release existed. The
  flow is now documented end-to-end (README "Building & releasing",
  COMPILATION.md §0) — push `v3.0.0` to publish the first built exe.
- Repository clutter removed: stale one-shot helper scripts (`scripts/
  descriptions_map.py`, `scripts/write_descriptions.py` — their registry
  rewrites are already committed), a redundant `bundle/.gitkeep` (the
  directory always contains the tracked `tools.dat`), and a truncated
  `.gitignore` (two rules) restored to the full ignore set covering bytecode
  caches, `logs/*`, `build/`, `dist/`, venvs, ruff/pytest caches, and OS/editor
  junk — the root cause of previously re-committed build artifacts.
- Documentation drift: every guide still quoting the pre-3.0 layout
  (external plugin ZIPs, `plugins/` folder, version 2.1.3 badges) was
  rewritten for the embedded-bundle, single-exe reality.
- Full bug/error/build sweep (2026-09-30):
  - `.gitignore` had been corrupted into a literal 7-byte file containing the
    text "(empty)" - every ignore rule was gone, so bytecode caches and
    runtime logs (`logs/sweep_results.json`, which `tests/test_all_tools.py`
    writes) were getting force-added into releases again. Restored the full
    ruleset and untracked the committed log artifact.
  - `audit.py` README-freshness gate used a regex that could never match the
    README's actual bolding style (`**...packs.**` with the period inside the
    bold run), making `python audit.py` fail spuriously even when docs were
    correct. The pattern now tolerates both styles; CI is green again.
  - README overview line restated as "**539 tools across 45 plugin packs**"
    to satisfy the docs-freshness contract.
  - 486 placeholder tool descriptions ("<Name>: <cmd> operation.") left by an
    incomplete catalog-regeneration pass were replaced with meaningful
    sentences in all 33 affected pack registries; TOOL_CATALOG.md /
    EXPANSION_CATALOG.md regenerated and plugin ZIPs rebuilt from source.
- `generate_catalogs.py` added for deterministic doc regeneration (see Added).

### Added
- `generate_catalogs.py`: TOOL_CATALOG.md and EXPANSION_CATALOG.md are now
  *generated* from the live registry (same AST-literal source `audit.py`
  uses), replacing hand-maintained copies that repeatedly drifted stale.
  Also fixes a long-standing content bug: every tool description in the
  committed catalogue had been mangled into boilerplate ("<Name>. Uses safe,
  dependency-aware execution...") instead of the real one-line description
  from the pack metadata; both files were regenerated with correct text.
- New documentation-freshness gates so outdated docs can never ship again:
  `audit.py` fails the release when the TOOL_CATALOG.md / EXPANSION_CATALOG.md
  headers or the README overview disagree with the registry counts, and
  `ci.yml` gained a "Catalogues are up to date" step that regenerates them
  and diffs against the commit.
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
  runtime artifact produced by new tools (`__pycache__/`, `logs/utility_suite.log`,
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
- Tool descriptions in pack metadata: 486 of 539 registered descriptions had
  been mangled into boilerplate ("<Name>. Uses safe, dependency-aware
  execution...") at some point in the source packs themselves — the earlier
  "regenerated catalogue" fix only re-copied the bad source text. Every
  affected description was rewritten from the tool name/command into a real
  one-line summary; `generate_catalogs.py` now renders accurate descriptions,
  and TOOL_CATALOG.md was regenerated from the corrected registry.
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
