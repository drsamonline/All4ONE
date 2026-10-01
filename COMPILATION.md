<div align="center">

# 🏗️ Utility Suite — Compilation & Release Guide

![PyInstaller](https://img.shields.io/badge/PyInstaller-6.x-orange?style=flat-square)
![Target](https://img.shields.io/badge/target-utility__suite.exe-0078D4?style=flat-square&logo=windows&logoColor=white)
![CI build](https://img.shields.io/badge/GitHub%20Actions-Windows%20runner-brightgreen?style=flat-square&logo=githubactions&logoColor=white)

*Author: Dr. Sohil Momin, BHMS*

</div>

## 0. Fastest path: automated CI build (no Windows machine needed) 🤖

This repository includes `.github/workflows/build-windows-exe.yml`. It runs
automatically — no manual action required — on:

- **every push to `main`** → builds the exe, uploads it as a run artifact, and
  refreshes the floating `latest-build` pre-release (a stable download URL for
  the most recent build),
- **a version tag** (e.g. `git tag v3.0.4 && git push origin v3.0.4`) → all of
  the above *plus* an official GitHub Release with release notes, or
- a manual **Actions** tab → **Build Windows executable** → **Run workflow**,
  if you ever want a one-off rebuild.

GitHub provides the Windows runner, so you don't need to own a Windows PC
to get a real `utility_suite.exe`. The workflow runs exactly one command —
`python build_single_exe.py` — which performs the entire pipeline: static
audit, bundle regeneration (`bundle/tools.dat`), smoke tests, PyInstaller
onefile build, packaged-exe self-check, and release-zip creation. The
single exe is uploaded as an artifact; tagged pushes (`v*`) additionally
publish `UtilitySuite-<version>-windows.zip` as a GitHub Release asset.
If any audit/test step fails, the build stops before producing an executable.

## 1. Build environment (manual/local build)

Recommended Windows release host:

- Windows 10/11
- Python 3.10+
- PowerShell 5+ / PowerShell 7+
- Network access for installing build dependencies

## 2. Install the builder

```powershell
python -m pip install --upgrade pip
python -m pip install --upgrade pyinstaller
```

Optional runtime packages can also be installed on the build host when you want them included in the executable environment.

## 3. Run the release build

From the repository root — one command, the whole pipeline:

```powershell
python build_single_exe.py
```

The script:

1. runs the static release audit (`audit.py`)
2. regenerates `bundle/tools.dat` from the source tree (all 45 packs + catalog)
3. runs behavioural smoke tests (`tests/test_suite.py`)
4. invokes PyInstaller with `build_onefile.spec` (**onefile** mode)
5. verifies the built exe reports >0 tools (`utility_suite.exe list`)
6. produces `dist\utility_suite.exe` and `dist\UtilitySuite-<version>-windows.zip`

Use `--skip-audit` / `--skip-tests` only while iterating locally.

## 4. Manual step-by-step build

```powershell
python generate_catalogs.py   # refresh TOOL_CATALOG.md / EXPANSION_CATALOG.md
python audit.py               # fails if docs drifted from the registry
python -c "from core.bundle import build_bundle; build_bundle('.')"  # regen tools.dat
python -B -m tests.test_suite
python -m PyInstaller build_onefile.spec --clean --noconfirm
```

## 5. Build output

The 3.0 release is a **single portable file**:

```text
dist\
├── utility_suite.exe                        # everything inside: runtime,
│                                            # all tool packs, catalog metadata
└── UtilitySuite-<version>-windows.zip           # release asset (exe only)
```

No `_internal\`, no `plugins\`, no sidecar `config.json` required — the exe
creates its own settings/logs next to itself on first run.

## 6. Release checklist

Before distribution:

```powershell
python generate_catalogs.py   # docs must match the registry (audit enforces it)
python audit.py
python -m tests.test_suite
python -m compileall -q .
```

Remove generated `__pycache__` folders before packaging source archives
(`python -m compileall` writes them; they are gitignored and do not fail
`audit.py`, but should not ship inside manual source archives):

```powershell
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
```

Generate release hashes with PowerShell:

```powershell
Get-FileHash .\dist\utility_suite.exe -Algorithm SHA256
```

## 7. Code-signing

For production distribution, sign the executable and installer with an organization-controlled Authenticode certificate. Verify the signature on a clean Windows machine before publication.

## 8. Inno Setup

The application ships as a single portable `utility_suite.exe`. An installer (e.g. Inno Setup) can wrap that one file without changing the Python architecture.

## 9. Reproducibility

`bundle/tools.dat` is rebuilt deterministically from source by `core.bundle.build_bundle()` (fixed timestamps, sorted entries), so repeated builds produce byte-identical archives. Release audits verify pack membership, handler metadata, and command uniqueness.

## Windows file-properties metadata (version_info.txt)

`build_onefile.spec` passes `version="version_info.txt"` to PyInstaller's EXE(),
which embeds a Win32 VERSIONINFO resource into `utility_suite.exe`. Right-click
the exe -> Properties -> Details and you will see:

| Field | Value |
|---|---|
| Company name / Author | Dr. Sohil Momin, BHMS |
| Product name | Utility Suite |
| File description | Utility Suite - 551 offline tools in one executable |
| File/Product version | 3.0.4.0 / 3.0.4 |
| Legal copyright | Copyright (C) 2026 Dr. Sohil Momin, BHMS |

When bumping the suite version, update the numbers in `version_info.txt`
(both `filevers`/`prodvers` tuples and the string fields) alongside
VERSION.txt, config.json and core/__init__.py — CI's version-sync gate checks
the latter three; version_info.txt is checked by review.
