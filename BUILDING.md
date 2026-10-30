# All4one — Building & Releasing

## One command

```bash
python build.py
```

It runs, in order:

1. **Clean** — removes `__pycache__` and stray `.pyc` files from the tree.
2. **Audit** — `scripts/audit.py`: catalogue integrity, version sync, repository
   hygiene, module imports, documentation coverage.
3. **Sweep** — `tests/sweep.py`: executes every runnable tool against generated
   fixtures. A failure stops the build.
4. **Catalogue** — regenerates `TOOL_CATALOG.md` from the live registry.
5. **Icon and version resource** — draws `assets/all4one.ico` and writes the
   Windows version block from `VERSION`.
6. **PyInstaller** — one file, no external assets, tool modules collected
   explicitly so the dynamic discovery survives freezing.
7. **Verify** — runs `list` on the freshly built binary and fails if it does not
   answer.
8. **Package** — `dist/All4one-<version>-windows.zip` containing the executable
   and a short `README-FIRST.txt`.

Useful flags: `python build.py --skip-tests` skips step 3 while iterating.

Output:

```
dist/All4one.exe
dist/All4one-<version>-windows.zip
```

## What goes into the binary

- `main.py` as the entry point.
- `core`, `ui` and every `tools` module, collected with `--collect-submodules`
  because the registry discovers tool modules at runtime — PyInstaller cannot see
  through `pkgutil.iter_modules` on its own.
- `TOOL_CATALOG.md`, bundled as documentation.
- Nothing else. Icons are inline SVG, the stylesheet is a Python string, and
  there are no image, font or data files to ship.

Qt modules the app never touches (WebEngine, Quick, 3D, Multimedia, Charts, Sql,
Designer, Help, and friends) are excluded in `EXCLUDES` in `build.py`, along with
`tkinter`. That is most of the size difference between a default PySide6 build
and this one.

## Why the Windows build happens on GitHub Actions

PyInstaller cannot cross-compile: a Windows `.exe` must be produced on Windows.
`.github/workflows/build-windows.yml` runs on `windows-latest`, and:

- **every push to `main`** builds the exe, uploads it as a run artifact, and
  refreshes the floating **`latest-build`** pre-release so there is always a
  current download at a stable URL;
- **a `v*` tag** additionally publishes a permanent release with generated notes;
- **manual dispatch** builds one-offs from the Actions tab.

`.github/workflows/ci.yml` runs on Linux and is the gate: audit, full sweep,
catalogue freshness, a CLI smoke test, and a headless UI build that walks every
page and uploads the screenshots.

## Releasing

1. Bump the version in `VERSION` and `core/__init__.py` — the audit fails if they
   disagree, or if the README badge drifts.
2. Regenerate the catalogue: `python scripts/catalogue.py`.
3. Commit, then tag and push:

```bash
git tag v4.0.0
git push origin v4.0.0
```

The tag build publishes `All4one-4.0.0-windows.zip` to a GitHub Release.

## Building locally on Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-build.txt
pip install pillow pypdf openpyxl python-docx cryptography psutil   # for the sweep
python build.py
```

The first run downloads nothing else — the toolchain is PyInstaller plus PySide6.

## Troubleshooting

**`ModuleNotFoundError: tools.<something>` in the frozen binary.** A tool module
was added after the build and `--collect-submodules tools` was not applied. Use
`build.py` rather than calling PyInstaller by hand.

**The window does not appear on Windows but the process runs.** The build used
`--console` instead of `--windowed`; `build.py` chooses per platform.

**Antivirus flags the binary.** Expected for unsigned PyInstaller onefiles. Code
signing is the only real fix; the source is public so users can build it.

**The exe is much larger than expected.** An exclude was dropped, or a new
dependency pulled in a large package. Check `EXCLUDES` first.

**The sweep fails on a machine without optional packages.** Install
`requirements-optional.txt`, or run `python build.py --skip-tests` — the audit
still runs.
