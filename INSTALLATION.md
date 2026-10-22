<div align="center">

# 📥 Utility Suite — Installation Guide

![Platform](https://img.shields.io/badge/platform-Windows_10%2F11-0078D4?style=flat-square)
![Install type](https://img.shields.io/badge/install-portable%20·%20no%20admin-brightgreen?style=flat-square)
![Mandatory deps](https://img.shields.io/badge/mandatory%20deps-0-orange?style=flat-square)

*Author: Dr. Sohil Momin, BHMS*

</div>

Pick your path — ⏱️ **60 seconds** for the portable EXE, or 🧑‍💻 a few minutes from source.

---

## 🅰️ Option A — Portable release (recommended)

> ✅ No installer · no registry writes · no admin rights needed.

Every release offers **one download** from the GitHub Releases page:

| Download | Contains |
|---|---|
| `UtilitySuite-<v>-windows.zip` | `utility_suite.exe` (+ a short `README-FIRST.txt`) |

All 551 tools across the 45 built-in packs are already embedded inside the exe
— there are no separate plugin-pack downloads.

1. 📦 Download it from the
   [GitHub Releases page](https://github.com/drsamonline/All4ONE/releases/latest).
2. 📂 Extract it to any folder, e.g. `C:\Tools\UtilitySuite`. The archive
   contains exactly **one program file** — `utility_suite.exe` — with all 551
   tools, the catalogue and the runtime embedded inside.
3. 🚀 Double-click `utility_suite.exe` for the Windows 10-style GUI — or use it
   as a CLI. Settings (`config.json`) and `logs/` are created next to the exe
   on first run.

The portable layout is intentionally self-contained and can be copied to
another Windows machine on a USB stick.

```text
UtilitySuite/
├── utility_suite.exe     # runtime + 45 tool packs + catalogue, all embedded
├── config.json           # created on first run (auto-merged on upgrade)
└── logs/                 # created/populated at runtime
```

🧩 **Turning packs on or off?** All packs are built in — open the Packs view in
the app and toggle the packs you want. See [PLUGINS.md](PLUGINS.md) for how to
enable/disable a pack and how the guided dependency install works.

🧹 **Uninstall?** Delete the folder. Preserve `config.json` or `logs/` first if
you want to keep them.

## 🅱️ Option B — From source

**Requirements:**

| Requirement | Version | Check |
|---|---|---|
| 🪟 Windows | 10/11 or later supported by Python | `winver` |
| 🐍 Python | **3.10+** | `python --version` |

```powershell
git clone https://github.com/drsamonline/All4ONE.git
cd All4ONE
python --version        # must print 3.10 or newer
python run.py gui       # that's it — zero mandatory pip installs
```

No mandatory third-party runtime package is required for the standard-library tools.

## 🧩 Optional features

Don't know what's missing? Ask the suite itself — it lists every unmet
dependency, how many tools each one unlocks, and where to download it:

```powershell
python run.py deps        # or: utility_suite.exe deps
```

Install optional dependencies **only when a tool you want shows 🚫 Unavailable**:

```powershell
python -m pip install pillow        # 🖼️ image operations
python -m pip install pywin32       # 🪟 advanced Windows/COM integration
python -m pip install send2trash    # 🗑️ safe recycle-bin deletion
```

FFmpeg 🎬, qpdf 📑, Poppler 📃 and other external command-line programs must be
installed separately and available on `PATH` (the `deps` command prints their exact
download URLs; see also [USER_GUIDE.md §7](USER_GUIDE.md) for `winget` commands).

## 🖥️ Command-line launcher

A release exposes `utility_suite.exe` directly; during source development,
`run.py` is the launcher:

```powershell
utility_suite.exe list                     # python run.py list
utility_suite.exe run checksum f.bin       # python run.py run checksum f.bin
```

## 🔐 Security note

> ⚠️ Pack modules execute Python code within the user account and therefore have
> the same authority as the process running Utility Suite. In official releases
> all 45 packs are already embedded inside `utility_suite.exe`, so there is
> nothing to add — treat any pack from outside this repository with the same
> caution you would any other program. See [PLUGINS.md](PLUGINS.md) and
> [SECURITY.md](SECURITY.md).

---

<div align="center">

➡️ Next steps: [USER_GUIDE.md](USER_GUIDE.md) · build an EXE yourself: [COMPILATION.md](COMPILATION.md)

</div>
