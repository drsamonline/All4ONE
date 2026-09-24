<div align="center">

# 🏗️ Utility Suite — Compilation & Release Guide

![PyInstaller](https://img.shields.io/badge/PyInstaller-6.x-orange?style=flat-square)
![Target](https://img.shields.io/badge/target-utility__suite.exe-0078D4?style=flat-square&logo=windows&logoColor=white)
![CI build](https://img.shields.io/badge/GitHub%20Actions-Windows%20runner-brightgreen?style=flat-square&logo=githubactions&logoColor=white)

*Author: Dr. Sohil Momin, BHMS*

</div>

## 0. Fastest path: automated CI build (no Windows machine needed) 🤖

This repository includes `.github/workflows/build-windows-exe.yml`. Push
the repository to GitHub and either:

- go to the **Actions** tab → **Build Windows executable** → **Run workflow**, or
- push a tag matching `v*` (e.g. `v2.1.3`) to also attach the build to a GitHub Release.

GitHub provides the Windows runner, so you don't need to own a Windows PC
to get a real `utility_suite.exe`. The workflow rebuilds the plugin ZIPs,
runs the full audit and test suite, builds with PyInstaller, smoke-tests
the resulting executable, and uploads `dist/utility_suite/` as a
downloadable artifact. If any audit/test step fails, the build stops
before producing an executable.

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

From the repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\BUILD_WINDOWS.ps1
```

The script:

1. validates Python
2. rebuilds plugin ZIPs
3. removes stale `build` and `dist` directories
4. runs the release audit
5. invokes PyInstaller with `build.spec`
6. produces `dist\utility_suite\utility_suite.exe`

## 4. Manual build

```powershell
python create_plugin_zips.py
python generate_catalogs.py   # refresh TOOL_CATALOG.md / EXPANSION_CATALOG.md
python audit.py               # fails if docs drifted from the registry
python -m PyInstaller build.spec --clean --noconfirm
```

## 5. Build output

The recommended distribution is onedir:

```text
dist\utility_suite\
├── utility_suite.exe
├── _internal\
├── plugins\
├── config.json
└── logs\
```

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
Get-FileHash .\dist\utility_suite\utility_suite.exe -Algorithm SHA256
```

## 7. Code-signing

For production distribution, sign the executable and installer with an organization-controlled Authenticode certificate. Verify the signature on a clean Windows machine before publication.

## 8. Inno Setup

The application is designed for portable onedir distribution. An installer can wrap the resulting `dist\utility_suite` directory with Inno Setup without changing the Python architecture.

## 9. Reproducibility

Plugin archives are rebuilt from source by `create_plugin_zips.py`. Release audits verify pack membership, handler metadata, command uniqueness, and absence of cache files in plugin ZIPs.
