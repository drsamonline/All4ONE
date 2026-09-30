<div align="center">

# 📥 Utility Suite — Installation Guide

![Platform](https://img.shields.io/badge/platform-Windows_10%2F11-0078D4?style=flat-square&logo=windows&logoColor=white)
![Install type](https://img.shields.io/badge/install-portable%20·%20no%20admin-brightgreen?style=flat-square)
![Mandatory deps](https://img.shields.io/badge/mandatory%20deps-0-orange?style=flat-square)

*Author: Dr. Sohil Momin, BHMS*

</div>

Pick your path — ⏱️ **60 seconds** for the portable EXE, or 🧑‍💻 a few minutes from source.

---

## 🅰️ Option A — Portable release (recommended)

> ✅ No installer · no registry writes · no admin rights needed.

1. 📦 Extract the release ZIP to a directory such as `C:\Tools\UtilitySuite`.
2. 🗂️ Keep the `plugins` directory **beside** `utility_suite.exe`.
3. ⚙️ Keep `config.json` beside the executable.
4. 🚀 Launch `utility_suite.exe` for the GUI — or use it as a CLI.

The portable layout is intentionally self-contained and can be copied to
another Windows machine on a USB stick.

```text
UtilitySuite/
├── utility_suite.exe     # the workstation
├── config.json           # settings (auto-merged on upgrade)
├── plugins/              # 45 plugin-pack ZIPs
└── logs/                 # created/populated at runtime
```

🧹 **Uninstall?** Delete the folder. Preserve `config.json` or `logs/` first if
you want to keep them.

## 🅱️ Option B — From source

**Requirements:**

| Requirement | Version | Check |
|---|---|---|
| 🪟 Windows | 10/11 or later supported by Python | `winver` |
| 🐍 Python | **3.10+** | `python --version` |

```powershell
git clone https://github.com/sohil-momin/utility_suite.git
cd utility_suite
python --version        # must print 3.10 or newer
python run.py gui       # that's it — zero mandatory pip installs
```

No mandatory third-party runtime package is required for the standard-library tools.

## 🧩 Optional features

Install optional dependencies **only when a tool you want shows 🚫 Unavailable**:

```powershell
python -m pip install pillow        # 🖼️ image operations
python -m pip install pywin32       # 🪟 advanced Windows/COM integration
python -m pip install send2trash    # 🗑️ safe recycle-bin deletion
```

FFmpeg 🎬, qpdf 📑, Poppler 📃 and other external command-line programs must be
installed separately and available on `PATH` (see [USER_GUIDE.md §7](USER_GUIDE.md)
for exact `winget` commands).

## 🖥️ Command-line launcher

A release exposes `utility_suite.exe` directly; during source development,
`run.py` is the launcher:

```powershell
utility_suite.exe list                     # python run.py list
utility_suite.exe run checksum f.bin       # python run.py run checksum f.bin
```

## 🔐 Security note

> ⚠️ Only install plugin ZIPs from sources you trust. Plugins execute Python
> code within the user account and therefore have the same authority as the
> process running Utility Suite. Review third-party packs before dropping them
> into `plugins/`. Found an issue? See [SECURITY.md](SECURITY.md).

---

<div align="center">

➡️ Next steps: [USER_GUIDE.md](USER_GUIDE.md) · build an EXE yourself: [COMPILATION.md](COMPILATION.md)

</div>
