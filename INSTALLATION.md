**Author:** Dr. Sohil Momin, BHMS

# Utility Suite Installation Guide

## Windows portable installation

1. Extract the release ZIP to a directory such as `C:\Tools\UtilitySuite`.
2. Keep the `plugins` directory beside `utility_suite.exe`.
3. Keep `config.json` beside the executable.
4. Launch `utility_suite.exe` for the GUI or use the CLI.

The portable layout is intentionally self-contained and can be copied to another Windows machine.

## Source installation

Required:

- Windows 10/11 or later Windows version supported by Python
- Python 3.10 or newer

From the project directory:

```powershell
python --version
python run.py gui
```

No mandatory third-party runtime package is required for the standard-library tools.

## Optional features

Install optional dependencies only when required:

```powershell
python -m pip install pillow
python -m pip install pywin32
python -m pip install send2trash
```

FFmpeg, qpdf, Poppler and other external command-line programs must be installed separately and available on `PATH`.

## Command-line launcher

A release can expose `utility_suite.exe` directly. During source development, `run.py` is the launcher.

## Uninstallation

Portable installation: delete the Utility Suite directory. Preserve `config.json` or logs separately when desired.

## Security note

Only install plugin ZIPs from sources you trust. Plugins execute Python code within the user account and therefore have the same authority as the process running Utility Suite.
