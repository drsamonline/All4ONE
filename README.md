**Author:** Dr. Sohil Momin, BHMS

# Utility Suite 2.1.3 — 500-Tool Windows Utility Workstation

Utility Suite is a modular Windows utility workstation built around a small core and dynamically discovered plugin packs. The repository contains **500 tools across 45 plugin packs**. Tools are registered through metadata, loaded lazily, and can declare optional or platform-specific dependencies. A missing dependency disables only the affected tool.

## What is included

- 500 registered tools / 500 unique CLI commands
- 45 plugin packs delivered as compressed ZIP archives
- CLI and desktop GUI
- Lazy plugin discovery and lazy handler loading
- Dependency/capability detection
- Recursive backward-compatible configuration merging
- Standard-library-first implementations
- Optional integrations for Pillow, pywin32, FFmpeg/ffprobe, qpdf/pdftotext and Windows system commands
- SQLite indexing support
- Safe archive extraction checks
- Audit and smoke-test tooling
- Windows build script and PyInstaller specification
- Complete user, installation and compilation documentation

## Quick start (source)

```powershell
python --version
python run.py list
python run.py search image
python run.py run checksum C:\path\file.txt --algorithm sha256
python run.py gui
```

For a portable Windows release, read `INSTALLATION.md` and `COMPILATION.md`. A GitHub Actions workflow (`.github/workflows/build-windows-exe.yml`) can also build and test a real `utility_suite.exe` on a Windows runner automatically — no Windows machine required on your end. See `CHANGELOG.md` for what changed in each release.

## Architecture

```text
utility_suite/
├── core/                 # core runtime, registry, GUI, shared operations
├── <pack>/               # plugin-pack source
├── plugins/              # generated compressed plugin ZIPs
├── tests/                # smoke/integration tests
├── audit.py              # static release audit
├── create_plugin_zips.py # deterministic pack builder
├── build.spec            # PyInstaller build specification
├── BUILD_WINDOWS.ps1    # Windows release build script
├── USER_GUIDE.md         # end-user manual
├── INSTALLATION.md       # installation guide
└── COMPILATION.md        # developer/release build guide
```

## Design principles

1. Keep the core small and stable.
2. Keep plugin logic isolated from the core.
3. Import heavy dependencies only inside the operation that needs them.
4. Do not allow missing optional dependencies to crash the suite.
5. Prefer streaming I/O for large files.
6. Never use shell string interpolation when a subprocess argument list is sufficient.
7. Keep plugin ZIPs deterministic and free of `__pycache__`/`.pyc` artifacts.
8. Add a tool by metadata + a lazy handler; do not duplicate infrastructure code.

## Validation

The release process performs:

- Python syntax compilation
- Tool-count and command uniqueness checks
- Plugin ZIP integrity checks
- Handler metadata checks
- Dependency metadata checks
- Duplicate-name/description checks
- Runtime handler-resolution tests
- Functional smoke tests
- Release SHA-256 generation

`audit.py` enforces a strict exit-code contract: it exits **0** only on
`AUDIT PASSED` and **1** on `AUDIT FAILED`, so CI gates (and local release
checklists) can rely on `python audit.py && <next step>` failing loudly.
Note the audit is findings-only — clean stray `__pycache__/` directories
yourself before expecting a PASS.

See `AUDIT_REPORT.txt` for the latest release audit result and
`CHANGELOG.md` for per-release fix history.
