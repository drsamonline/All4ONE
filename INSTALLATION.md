<div align="center">

# 📥 Utility Suite — Installation Guide

![Platform](https://img.shields.io/badge/platform-Windows_10%2F11-0078D4
![Install type](https://img.shields.io/badge/install-portable%20·%20no%20admin-brightgreen
![Mandatory deps](https://img.shields.io/badge/mandatory%20deps-0-orange

*Author: Dr. Sohil Momin, BHMS*

</div>

Pick your path — ⏱️ **60 seconds** for the portable EXE, or 🧑‍💻 a few minutes from source.

---

## 🅰️ Option A — Portable release (recommended)

> ✅ No installer · no registry writes · no admin rights needed.

Every release offers **three downloads** from the GitHub Releases page — pick
one:

| Download | Contains | Pick it if… |
|---|---|---|
| `UtilitySuite-<v>-windows-lite.zip` | `utility_suite.exe` only | You just want the app — all 551 tools are already embedded inside the exe |
| `UtilitySuite-<v>-windows-full.zip` | the exe **+** a `plugins/` folder with every pack zip + `README-FIRST.txt` | You want to add or remove packs without rebuilding |
| `UtilitySuite-<v>-plugins-all.zip` | every pack zip + `plugins.json` (no exe) | You only want the packs |

1. 📦 Download one of the three from the
   [GitHub Releases page](https://github.com/drsamonline/All4ONE/releases/latest).
2. 📂 Extract it to any folder, e.g. `C:\Tools\UtilitySuite`. The *lite* archive
   contains exactly **one file** — `utility_suite.exe` — with all 551 tools, the
   catalog and the runtime embedded inside. The *full* archive adds a `plugins/`
   folder holding every pack as a separate `.zip`.
3. 🚀 Double-click `utility_suite.exe` for the Windows 10-style GUI — or use it
   as a CLI. Settings (`config.json`) and `logs/` are created next to the exe
   on first run.

The portable layout is intentionally self-contained and can be copied to
another Windows machine on a USB stick.

```text
UtilitySuite/                 # lite download
├── utility_suite.exe     # runtime + 45 tool packs + catalog, all embedded
├── config.json           # created on first run (auto-merged on upgrade)
└── logs/                 # created/populated at runtime

UtilitySuite/                 # full download — adds removable packs
├── utility_suite.exe
├── README-FIRST.txt      # explains the three downloads
├── plugins/              # one .zip per pack; drop in / delete to add / remove
├── config.json
└── logs/
```

🧩 **Adding or removing packs?** Drop a pack `.zip` into the `plugins/` folder
beside the exe (or delete one) and restart. Full guide and the manifest URL:
[PLUGINS.md](PLUGINS.md).

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

> ⚠️ Only add plugin packs from sources you trust. Pack modules execute Python
> code within the user account and therefore have the same authority as the
> process running Utility Suite. In official releases all 45 packs are already
> embedded inside `utility_suite.exe`; review third-party pack source before
> dropping it into `plugins/` or rebuilding the bundle from a modified checkout.
> See [PLUGINS.md](PLUGINS.md) and [SECURITY.md](SECURITY.md).

---

<div align="center">

➡️ Next steps: [USER_GUIDE.md](USER_GUIDE.md) · build an EXE yourself: [COMPILATION.md](COMPILATION.md)

</div>
