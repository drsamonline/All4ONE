<div align="center">

# 👤 Utility Suite — User Guide

**Version 2.1.3** · 539 tools · 45 plugin packs · CLI + GUI

![Platform](https://img.shields.io/badge/platform-Windows_10%2F11-0078D4?style=flat-square&logo=windows&logoColor=white)
![Level](https://img.shields.io/badge/level-beginner%20→%20power%20user-brightgreen?style=flat-square)
![Reading time](https://img.shields.io/badge/reading%20time-10%20min-blue?style=flat-square)

*Author: Dr. Sohil Momin, BHMS*

</div>

> 🧭 **New here?** Read sections **1–3**, then jump to the 🚀 cheat sheet at the
> bottom. Everything else is reference material you can skim on demand.

## 📚 Table of contents

| | Section | | Section |
|---|---|---|---|
| 1️⃣ | [Overview](#1️⃣-overview) | 6️⃣ | [Plugin packs](#6️⃣-plugin-packs-) |
| 2️⃣ | [Starting the application](#2️⃣-starting-the-application-) | 7️⃣ | [Optional dependencies](#7️⃣-optional-dependencies-) |
| 3️⃣ | [Tool availability](#3️⃣-tool-availability-) | 8️⃣ | [Configuration](#8️⃣-configuration-) |
| 4️⃣ | [Paths & quoting](#4️⃣-paths--quoting-) | 9️⃣ | [Logs & troubleshooting](#9️⃣-logs--troubleshooting-) |
| 5️⃣ | [Safety first](#5️⃣-safety-first-) | 🔟 | [Updating](#t%EF%B8%8F-updating) · [🚀 Cheat sheet](#-cheat-sheet) |

---

## 1️⃣ Overview

Utility Suite is a single workstation for common **file, Windows, networking,
media, data, developer, security, storage, backup, productivity, and diagnostic**
tasks. The catalogue contains **539 tools organized into 45 plugin packs**.

The application deliberately does not bundle every external engine. Tools that
need an external program are marked 🚫 **Unavailable** until that capability is
installed. This keeps the application smaller and follows the project's
dependency-isolation design — one missing tool never breaks the suite.

💡 **Tip:** browse all 539 tools with descriptions in
[TOOL_CATALOG.md](TOOL_CATALOG.md), or per-pack counts in
[EXPANSION_CATALOG.md](EXPANSION_CATALOG.md).

## 2️⃣ Starting the application 🖥️

### GUI (recommended for new users)

Run `utility_suite.exe` from the built release directory, or from source:

```powershell
python run.py gui
```

The GUI provides:

| Feature | What it does |
|---|---|
| 🗂️ Category navigation | Jump between the 45 packs visually |
| 🔍 Full-text tool search | Type a word, find the tool |
| 🟢 Availability status | See instantly what can run on this machine |
| 📋 Selected-tool metadata | Arguments, dependencies, description |
| ⌨️ Argument entry | One field per argument — no shell quoting pain |
| ⏳ Asynchronous execution | Long jobs never freeze the window |
| 🖨️ Output console | Results stream into a scrollable pane |
| 👁️ File preview/open actions | Preview results or open them in associated apps |
| 🔄 Plugin refresh | Reload packs without restarting |

### CLI (for scripting and power users)

```powershell
utility_suite.exe list                                        # all 539 tools
utility_suite.exe list --category "File Operations"           # filter by category
utility_suite.exe search "duplicate"                          # keyword search
utility_suite.exe run checksum C:\data\file.bin --algorithm sha256
utility_suite.exe preview C:\data\notes.txt                   # peek at a file
utility_suite.exe open C:\data\report.pdf                     # open in default app
utility_suite.exe refresh                                     # reload plugin packs
```

From source, replace `utility_suite.exe` with `python run.py`.

## 3️⃣ Tool availability 🟢🚫

Every tool reports its state up front:

- 🟢 **AVAILABLE** — all declared dependencies are present; run it immediately.
- 🚫 **UNAVAILABLE** — one or more declared dependencies are missing; the tool
  stays visible so you know what the suite supports and what to install
  (see [section 7](#7️⃣-optional-dependencies-)).

💡 **Tip:** the CLI prints the missing dependency name for unavailable tools —
install exactly that, run `refresh`, and the tool lights up green.

## 4️⃣ Paths & quoting 🛤️

Use normal Windows quoting for paths containing spaces:

```powershell
utility_suite.exe run checksum "C:\My Files\report.pdf" --algorithm sha256
```

The GUI uses Windows-friendly argument parsing for ordinary command-line
arguments — in the GUI you can usually paste unquoted paths directly.

⚠️ **Watch out:** trailing backslashes before a closing quote (`"C:\dir\"`) can
confuse any Windows shell. Prefer `"C:\dir"` without the final slash.

## 5️⃣ Safety first ⚠️

> 🔴 Destructive or system-changing operations should be treated as
> **administrative tools**. Review the target path and arguments *before*
> executing. Take a backup before touching registries, services, partitions,
> drivers, or large directory trees.

✅ Good practice: archive extraction inside the suite uses path validation
intended to prevent files from escaping the destination directory — but always
extract archives you trust into folders you control.

## 6️⃣ Plugin packs 📦

A plugin pack is a ZIP placed in the `plugins` directory. Refresh the catalogue
after adding a valid pack:

```powershell
utility_suite.exe refresh
```

The loader expects:

1. the package name to match the archive stem, and
2. the archive to contain a Python package exposing `register_tools()` metadata.

Developing your own pack? Follow the contract in
[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md).

## 7️⃣ Optional dependencies 🧩

Typical optional components and what they unlock:

| Component | Unlocks | Install |
|---|---|---|
| 🖼️ Pillow | Image operations | `pip install pillow` |
| 🪟 pywin32 | Advanced Windows/COM integration | `pip install pywin32` |
| 🎬 FFmpeg + ffprobe | Audio/video processing | `winget install Gyan.FFmpeg` |
| 📑 qpdf | PDF structural operations | `winget install qpdf.qpdf` |
| 📃 Poppler `pdftotext`/`pdfinfo` | PDF text/metadata extraction | `winget install oschwartz10612.Poppler` |
| 🗑️ send2trash | Safe recycle-bin deletion | `pip install send2trash` |

Install only the components needed for the tools you actually use — the suite
is designed around zero mandatory third-party packages.

## 8️⃣ Configuration ⚙️

`config.json` controls plugin location, logging, threading, indexing, hashing
and UI behavior. New defaults are **merged recursively** with existing user
configuration, so upgrading never erases unrelated settings.

💡 **Tip:** keep a copy of your tuned `config.json` when replacing the app
files during an update ([section 🔟](#t%EF%B8%8F-updating)).

## 9️⃣ Logs & troubleshooting 🩺

Application logs are written under `logs/` in the portable release directory
(the directory ships empty and is populated at runtime). First aid:

```powershell
utility_suite.exe list            # did the packs load at all?
utility_suite.exe search <term>   # is the tool registered?
```

| Symptom | Likely cause | Fix |
|---|---|---|
| 🚫 Tool shows Unavailable | Missing optional dependency | Install it (§7), then `refresh` |
| ❌ Execution fails | Bad arguments / permissions | Read the output console + `logs/` entry |
| 📦 Pack doesn't appear | ZIP name ≠ package name, or no `register_tools()` | Fix the pack (§6) and `refresh` |
| 🐢 Slow startup | Many packs + first-run indexing | Normal; subsequent runs are cached |

The core catches handler exceptions, so one faulty tool never terminates the
entire application — check the log for the traceback.

## 🔟 Updating 🔄

Replace the application files and plugin ZIPs with the newer release,
preserving `config.json` if you need local settings. Run the audit/build
validation (`python audit.py`) before distributing a customized release.

---

## 🚀 Cheat sheet

```text
GUI                 python run.py gui
List everything     python run.py list
Find a tool         python run.py search <keyword>
Run a tool          python run.py run <command> <args...>
Hash a file         python run.py run checksum "C:\f.bin" --algorithm sha256
Preview / Open      python run.py preview C:\notes.txt | python run.py open C:\r.pdf
Reload packs        python run.py refresh
Where are logs?     logs/utility_suite.log
```

<div align="center">

📖 Next: setup details in [INSTALLATION.md](INSTALLATION.md) ·
building from source in [COMPILATION.md](COMPILATION.md) ·
found a bug? Open an issue — found a *security* issue? See [SECURITY.md](SECURITY.md)

</div>
