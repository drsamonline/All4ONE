# Merge Notes — First Blueprint Package + Utility Suite 2.1.2 → 2.1.3

You uploaded two things in this project: an early 14-pack/51-tool
implementation of the original blueprint, and later a much more advanced
2.1.2 build (500 tools / 45 packs, GUI with file preview, deterministic
plugin builder). This version (2.1.3) uses the **2.1.2 tree as the base**
— it was the stronger, more complete codebase — and folds in an audit
pass plus a few improvements from the earlier package. Nothing from the
first package's tool catalogue was needed; its 14 base packs were already
present here in an equal or more complete form.

## Why 2.1.2 was kept as the base

- Already implements the blueprint's "500+ tools via expansion packs"
  roadmap item (Section 9.15), not just the 51-tool starting catalogue.
- Core engine already handled the important edge cases independently:
  recursive config merging, `SystemExit`-safe tool execution, zip-slip/
  tar-slip protected archive extraction, atomic config saves.
- Already had a working, more polished Tkinter GUI, including file
  preview/open-with-default-app (blueprint Section 8), which the first
  package did not implement.
- Already had a real automated test suite (`tests/test_suite.py`) and a
  static release auditor (`audit.py`) that both passed before I touched
  anything.

## What this pass audited and changed

**1. Exhaustive functional sweep.** Wrote `tests/test_all_tools.py`,
which invokes all 500 registered tools individually, each in its own
subprocess with a hard timeout, so one hang or crash can never affect the
result of the other 499. First run surfaced 6 tools that produced a raw
Python traceback in the console when given a directory instead of a file:
`count`, `download`, `filetype`, `hexview`, and `integrity-baseline`.

**2. Fixed those 6.** Each now checks its input up front and prints a
plain-English message ("Not a regular file (is it a directory?): ...",
"Not a valid http:// or https:// URL: ...") instead of letting the
exception surface. Functionally these were never true crashes — the tool
registry's catch-all already prevented the app itself from going down —
but the console output was ugly.

**3. Fixed the console-logging noise underneath that.** Root cause: the
registry logs every caught tool error with `logger.exception()`, which
includes a full stack trace, and the console handler had no filter, so
every "file not found"-class error was dumping a scary traceback into the
terminal even though it was already handled safely. Added a
`ConsoleFormatter` that keeps the console output to a single clean line
while the rotating file log (`logs/utility_suite.log`) still gets the full
traceback for debugging.

**4. Fixed an unhandled GUI-launch failure mode.** `utility_suite gui`
(and the no-argument default, which also opens the GUI) imported
`tkinter` directly with no fallback. On a Python install without Tk, or a
headless/SSH session with no display, this raised a raw
`ModuleNotFoundError` or `tk.TclError`. It now prints an actionable
message and exits cleanly; the CLI stays fully usable either way.

**5. Renamed a misleading module.** `security_tools/secure_delete.py` had
been repurposed to implement the "File Integrity Baseline" tool (SHA-256
hashing) rather than secure deletion — the real secure-delete tool lives
in `file_ops/secure_delete.py`. Renamed to `integrity_baseline.py` and
updated the handler wiring so the filename matches what it does.

**6. Removed stray runtime artifacts.** A `backup/` directory containing
two accidental SQLite database files (byproducts of an earlier test run
against nonexistent paths) and empty `logs/` contents were left in the
uploaded package. Removed; `.gitignore` extended to keep `*.db` and
`logs/*` out of future archives.

**7. GUI polish carried over from the first package.** Added a
confirmation dialog before running any tool that can delete or overwrite
data (`sdelete`, `dupefinder`, `backup-cleanup`, `backup-rotation`,
`backup-restore`, `mirror-backup`, `empty-clean`, `temp-clean`,
`junk-find`, `registry-key-deleter`, `registry-value-deleter`,
`registry-import`, `startup-folder-cleaner`), plus File.../Folder...
buttons next to the argument box that insert a correctly quoted path.

**8. Full-tree readability formatting pass (this update).** Ran `black`
(line length 110) across all 143 Python files, including
`core/extended_ops.py`, which the first version of this document flagged
as very dense. This is purely mechanical whitespace/line-break
normalization - no logic was touched - and the full audit, smoke-test
suite, and 500-tool sweep were re-run afterward with zero regressions.
`core/extended_ops.py` went from ~1,060 dense lines to ~2,630 clearly
spaced ones; the rest of the codebase (all pack modules) is now
consistently PEP-8 formatted too.

## Re-verified after every change

- `python audit.py` → PASS (500/500 tools, 45/45 packs, no cache residue)
- `python -B tests/test_suite.py` → PASS (deep-merge, split/join
  round-trip, CSV tools, diff, zip-slip/tar-slip rejection, renamer)
- `python tests/test_all_tools.py` → 500/500 OK, 0 timeouts, 0
  tracebacks, 0 crashes
- All three re-run again after the formatting pass → same result, 0 regressions

## Formatting note

The `black` pass (item 8 above) addressed the readability concern noted
below from the earlier draft of this document.

## What I did not rewrite

The shared implementation for the ~350 expansion-pack tools living in
`core/extended_ops.py` is written in a very dense, compact style (little
whitespace, several statements per line). It is functionally sound —
every operation is dispatched, exercised by the sweep above, and wrapped
in a catch-all — but it trades readability for size. Reformatting ~1,000
lines for style alone, with no functional bug to justify the risk of
introducing one, was not a good use of this pass; flagging it here so you
can decide if a future pass should prioritize readability over the
current compactness.

## Build pipeline fixes (this update — you reported the build failing)

The previous package's `.exe` build actually failed on any machine,
Windows included — this was never a Windows-specific issue. I actually
ran `pyinstaller build.spec` myself (Linux can run PyInstaller, it just
can't produce a *Windows* binary from it) to reproduce and confirm each
bug before fixing it:

**1. `build.spec` crashed immediately with `NameError: name '__file__' is
not defined`.** PyInstaller runs `.spec` files with `exec()`, which does
not define `__file__` the way a normal module import does. PyInstaller
instead injects `SPECPATH` into the exec namespace for exactly this
purpose. Fixed `ROOT = Path(__file__).resolve().parent` → 
`ROOT = Path(SPECPATH).resolve()`.

**2. Even after that fix, a built executable reported "Total tools: 0".**
This one was a genuine packaging design bug, not a typo: PyInstaller's
`datas=` mechanism always places bundled files inside the app's internal
resource folder (`dist/utility_suite/_internal/` in a onedir build) —
never directly beside the executable. The app, correctly, looks for
`plugins/` as a sibling of `utility_suite.exe` (matching the onedir
layout documented in `COMPILATION.md`, and the original blueprint's
Section 11.3), so the shipped plugins were silently unreachable. Fixed by
removing `plugins/` and `config.json` from `build.spec`'s `datas=`
entirely and instead copying `plugins/` next to the built executable as
a post-build step in both `BUILD_WINDOWS.ps1` and the GitHub Actions
workflow. `config.json` is intentionally not bundled at all — the app
already creates a fresh one beside the executable on first run. This also
restores the "just drop a new pack ZIP into `plugins/`, no rebuild
needed" extensibility the blueprint calls for, which packaging it inside
`_internal/` would have quietly broken.

**3. `--version` printed the stale `2.1.2`.** `core/__init__.py` had a
hardcoded version string left over from the previous release. Bumped to
`2.1.3` alongside the rest of the version-string updates already made
elsewhere in this document.

**4. Added a build-time verification gate.** `BUILD_WINDOWS.ps1` and the
CI workflow now run the freshly built `utility_suite.exe list` and
`--version` immediately after packaging and fail the build outright if
the tool count is 0 or the version string is missing — so a regression
like this one can never again silently ship as a "successful" build.

### Re-verified

- Built with `pyinstaller build.spec --clean --noconfirm` directly in
  this (Linux) sandbox to confirm the packaging logic itself is correct
  — PyInstaller can build and run its own executable format on any host
  OS, it just can't cross-compile to a *different* OS's binary format.
  The resulting Linux executable, with `plugins/` copied next to it as
  the real Windows build will be, reports **"Total tools: 500"** and
  `--version` → `2.1.3`.
- `python audit.py`, `python -B tests/test_suite.py`, and
  `python tests/test_all_tools.py` all re-run clean after these fixes:
  500/500 tools, 0 tracebacks, 0 crashes.
