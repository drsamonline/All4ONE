**Author:** Dr. Sohil Momin, BHMS

# Utility Suite User Guide

## 1. Overview

Utility Suite is a single workstation for common file, Windows, networking, media, data, developer, security, storage, backup, productivity, and diagnostic tasks. The catalogue contains 500 tools organized into 45 plugin packs.

The application deliberately does not bundle every external engine. Tools that need an external program are marked **Unavailable** until that capability is installed. This keeps the application smaller and follows the project's dependency-isolation design.

## 2. Starting the application

### GUI

Run `utility_suite.exe` from the built release directory, or from source:

```powershell
python run.py gui
```

The GUI provides:

- category navigation
- full-text tool search
- availability status
- selected-tool metadata
- argument entry
- asynchronous execution
- output console
- file preview/open actions
- plugin refresh

### CLI

```powershell
utility_suite.exe list
utility_suite.exe list --category "File Operations"
utility_suite.exe search "duplicate"
utility_suite.exe run checksum C:\data\file.bin --algorithm sha256
utility_suite.exe preview C:\data\notes.txt
utility_suite.exe open C:\data\report.pdf
utility_suite.exe refresh
```

## 3. Tool availability

A tool can be:

- **AVAILABLE** — all declared dependencies are present.
- **UNAVAILABLE** — one or more declared dependencies are missing.

Unavailable tools remain visible so users know what the suite supports and what needs to be installed.

## 4. Paths and quoting

Use normal Windows quoting for paths containing spaces:

```powershell
utility_suite.exe run checksum "C:\My Files\report.pdf" --algorithm sha256
```

The GUI uses Windows-friendly argument parsing for ordinary command-line arguments.

## 5. Safety

Destructive or system-changing operations should be treated as administrative tools. Review the target path and arguments before executing them. Use a backup before modifying registries, services, partitions, drivers, or large directory trees.

Archive extraction uses path validation intended to prevent files from escaping the destination directory.

## 6. Plugin packs

A plugin pack is a ZIP placed in the `plugins` directory. Refresh the catalogue after adding a valid pack:

```powershell
utility_suite.exe refresh
```

The loader expects the package name to match the archive stem and the archive to contain a Python package with `register_tools()` metadata.

## 7. Optional dependencies

Typical optional components include:

- Pillow — image operations
- pywin32 — advanced Windows/COM integration
- FFmpeg + ffprobe — audio/video processing
- qpdf — PDF structural operations
- Poppler `pdftotext`/`pdfinfo` — PDF text/metadata extraction
- send2trash — safe recycle-bin deletion workflows

Install only the components needed for the tools you use.

## 8. Configuration

`config.json` controls plugin location, logging, threading, indexing, hashing and UI behavior. New defaults are merged recursively with existing user configuration so adding a newer configuration key does not erase unrelated settings.

## 9. Logs and troubleshooting

Application logs are written under `logs/` in the portable release directory. Start with:

```powershell
utility_suite.exe list
utility_suite.exe search <term>
```

If a tool is unavailable, inspect its declared dependency. If execution fails, review the output and log entry; the core catches handler exceptions so one faulty tool does not terminate the entire application.

## 10. Updating

Replace the application files and plugin ZIPs with the newer release, preserving `config.json` if you need local settings. Run the audit/build validation before distributing a customized release.
