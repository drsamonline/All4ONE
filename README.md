<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://placehold.co/900x180/0d1117/58a6ff?text=%E2%9A%99%EF%B8%8F+Utility+Suite&font=segoe-ui">
  <img alt="Utility Suite — 551 portable Windows tools in one EXE" src="https://placehold.co/900x180/f0f6fc/0969da?text=%E2%9A%99%EF%B8%8F+Utility+Suite&font=segoe-ui" width="720">
</picture>

# 🧰 Utility Suite

### ⚡ **551 Windows tools. ONE portable `.exe`. Zero installs, zero bloat, zero telemetry.**

Stop downloading sketchy utilities. **Utility Suite** is a free, open-source,
portable Windows toolbox — file ops, hashing, PDF & Office batch tools, image
editing, video/audio conversion, network diagnostics, registry helpers, disk
cleaning, security audits and **hundreds more** — compiled into a single
`utility_suite.exe` you can keep on a USB stick forever.

[![CI](https://github.com/drsamonline/All4ONE/actions/workflows/ci.yml/badge.svg)](https://github.com/drsamonline/All4ONE/actions/workflows/ci.yml)
[![Build Windows executable](https://github.com/drsamonline/All4ONE/actions/workflows/build-windows-exe.yml/badge.svg)](https://github.com/drsamonline/All4ONE/actions/workflows/build-windows-exe.yml)
![Release](https://img.shields.io/github/v/release/drsamonline/All4ONE?style=flat-square&color=brightgreen)
![Downloads](https://img.shields.io/github/downloads/drsamonline/All4ONE/total?style=flat-square&label=downloads&color=blue)
![Tools](https://img.shields.io/badge/tools-551-brightgreen?style=flat-square)
![Packs](https://img.shields.io/badge/plugin%20packs-45-8A2BE2?style=flat-square)
![Dependencies](https://img.shields.io/badge/mandatory%20deps-0-orange?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D4?style=flat-square&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/python-3.10%2B-yellow?style=flat-square&logo=python&logoColor=black)
![License](https://img.shields.io/badge/license-MIT-informational?style=flat-square)
![Author](https://img.shields.io/badge/author-Dr.%20Sohil%20Momin%2C%20BHMS-fuchsia?style=flat-square)

**📥 [Download the latest release →](https://github.com/drsamonline/All4ONE/releases/latest)**
·
**🖥️ [GUI + CLI features](#-gui--cli-two-frontends-one-engine)**
·
**📚 [Full tool catalogue (551)](TOOL_CATALOG.md)**

*No installer · No registry pollution · No background services · Unplug it and walk away.*

</div>

---

<!-- TABLE OF CONTENTS -->
<details open>
<summary><b>📑 Table of contents</b></summary>

- [Why Utility Suite?](#-why-utility-suite)
- [Quick start (60 seconds)](#-quick-start-60-seconds)
- [What can it do? (feature map)](#-what-can-it-do-feature-map)
- [GUI + CLI: two frontends, one engine](#-gui--cli-two-frontends-one-engine)
- [Smart dependency handling (`deps`)](#-smart-dependency-handling-deps)
- [Numbers at a glance](#-numbers-at-a-glance)
- [Building & releasing](#-building--releasing)
- [Documentation map](#-documentation-map)
- [Architecture](#-architecture)
- [Contributing](#-contributing)
- [FAQ](#-faq)

</details>

## 🔥 Why Utility Suite?

| ❌ Typical freeware toolkits | ✅ Utility Suite |
|---|---|
| Bundlers, adware, "optional" toolbars | **Zero ads, zero telemetry, MIT-licensed, fully auditable source** |
| Installers that litter the registry | **One portable `.exe` — run from any folder or USB drive** |
| Closed binaries you can't inspect | Every line is Python; `audit.py` verifies **551/551 handlers** on every release |
| One job per download (50 downloads for 50 jobs) | **551 tools across 45 plugin packs** in a single file |
| Breaks when a dependency is missing | A missing optional dep disables *exactly one* tool — never the suite |

Every tool is metadata-registered, **lazily loaded**, and declares its own
optional dependencies. CI runs Linux validation on every push **and** builds
the real Windows single-file EXE on version tags via GitHub Actions.

## 🚀 Quick start (60 seconds)

### Prebuilt portable EXE (recommended)

1. 📥 Grab `UtilitySuite-<version>-windows.zip` from the
   **[latest release](https://github.com/drsamonline/All4ONE/releases/latest)**.
2. Unzip — it contains **exactly one file**: `utility_suite.exe`.
3. Double-click for the GUI, or use it as a CLI:

```powershell
.\utility_suite.exe list                          # browse all 551 tools
.\utility_suite.exe search image                  # find tools by keyword
.\utility_suite.exe run checksum C:\f.txt --algorithm sha256
.\utility_suite.exe run ip-calc 192.168.1.10/24   # subnet math in one line
.\utility_suite.exe deps                          # what's missing + where to download it
```

### From source (any OS for development, Windows for full functionality)

```powershell
git clone https://github.com/drsamonline/All4ONE.git
cd All4ONE

python run.py list                    # browse all 551 tools
python run.py run csv-query staff.csv --numeric salary --stats
python run.py gui                     # launch the desktop GUI
```

**Zero mandatory `pip install`s** — the suite runs on the standard library alone.

## 🗺️ What can it do? (feature map)

<details open>
<summary><b>🎯 45 packs · 551 tools — grouped by mission</b></summary>

| Category | Packs | Tools | Try this |
|---|---|---|---|
| 📁 **Files & Archives** | `file_ops` · `archive_tools` · `directory_tools` · `search_index` · `imaging_advanced` | 31 | `run tree-print .` |
| 🔤 **Text, Docs & Data** | `text_tools` · `data_tools` · `conversion_tools` · `dev_tools` · `office_tools` · `pdf_tools` · `document_tools` | 92 | `run json-schema data.json` |
| 💻 **Developer** | `developer_tools_advanced` · `shell_tools` · `package_tools` · `automation` · `misc` | 73 | `run hash-identify <digest>` |
| 🌐 **Network** | `network_tools` · `network_diagnostics` · `net_advanced` | 41 | `run ip-calc 10.0.0.5/28` |
| 🖥️ **Windows System** | `system_info` · `system_utils` · `windows_power` · `process_tools` · `window_manager` · `virtual_desktop` · `registry_tools` · `startup_automation` · `driver_tools` · `event_tools` · `security_tools` · `security_audit` | 138 | `run password-entropy --password hunter2` |
| 🎨 **Media** | `audio_tools` · `media_tools` · `media_metadata` · `video_tools` · `image_batch` | 51 | `run b64-codec --encode hello` |
| 🧹 **Maintenance & Storage** | `maintenance` · `disk_advanced` · `storage_tools` · `backup_tools` · `clipboard_manager` · `time_productivity` · `monitoring_tools` · `diagnostics_extra` | 125 | `run bytes-units 4.5GiB --to MiB` |

All 551 tools described one-by-one → **[TOOL_CATALOG.md](TOOL_CATALOG.md)** ·
Per-pack counts → **[EXPANSION_CATALOG.md](EXPANSION_CATALOG.md)**

</details>

## 🖥️ GUI + CLI: two frontends, one engine

- **Desktop GUI** (Tkinter): instant search across 551 tools, scrollable
  category chips, async execution, live previews, DPI-aware layout. Click the
  **"X/551 tools ready"** status-bar label any time to open the built-in
  install guide.
- **CLI / scripting**: every GUI action has an identical command, so the same
  exe drops into PowerShell, batch files, or scheduled automation.

## 🩹 Smart dependency handling (`deps`)

Heavy tools (FFmpeg video conversion, Poppler PDF extraction, Tesseract OCR…)
need external binaries — but they can **never break the suite**. Run:

```powershell
.\utility_suite.exe deps
```

…and you get every missing dependency, how many tools it unlocks, and a direct
download link: FFmpeg → gyan.dev, pdftotext → poppler-windows releases,
Python packages → exact `pip install …` lines. Nothing else to configure.

## 📊 Numbers at a glance

| Metric | Value |
|---|---|
| 🛠️ Registered tools | **551** |
| 📦 Plugin packs | **45** |
| 🧪 Smoke-tested handlers | 551 / 551 ✅ |
| 🔒 Mandatory third-party deps | **0** |
| 🐍 Language | Python 3.10+ (stdlib-first) |
| 🖱️ Frontends | CLI + Tkinter GUI |
| 📄 Documentation | 10 curated documents |
| 📦 Release format | ONE file: `utility_suite.exe` (~12 MB) |
| 👤 Author | Dr. Sohil Momin, BHMS (embedded in the EXE's file properties) |

## 🏗️ Building & releasing

> [!IMPORTANT]
> **Every push to `main` automatically builds the Windows EXE** — no tag and
> no manual action required. The Linux validation workflow (`ci.yml`) gates
> the tree, and `build-windows-exe.yml` fires on:
>
> 1. **any push to `main`** → builds `utility_suite.exe`, uploads it as a
>    run artifact, and refreshes the floating **`latest-build`** pre-release
>    so there is always a current download at the same URL,
> 2. **pushing a version tag** → all of the above *plus* a permanent GitHub
>    Release with auto-generated notes, or
> 3. a manual **Actions → Build Windows executable → Run workflow** for one-offs.
>
> Tagging is now only needed when you want an *official numbered release*;
> plain pushes still produce a working `.exe`. 👇

PyInstaller cannot cross-compile a Windows binary from Linux/macOS, so the
real `.exe` is built on a **Windows GitHub Actions runner**. The entire local
pipeline is one command:

```powershell
python build_single_exe.py    # audit → bundle → tests → exe → verify → zip
```

To publish a release, **bump the version, then push a version tag** — the
tagged build attaches `UtilitySuite-<version>-windows.zip` to an auto-generated
GitHub Release (with author/version metadata embedded in the binary):

```bash
# 1. sync the version everywhere (VERSION.txt is authoritative; audit.py enforces sync)
# 2. tag and push
git tag v3.0.5.1 && git push origin v3.0.5.1
```

If you just want the newest `.exe` without cutting a release, grab it from the
floating [`latest-build` pre-release](https://github.com/drsamonline/All4ONE/releases/tag/latest-build)
— it is overwritten automatically by every successful push to `main`.

Full details: [COMPILATION.md](COMPILATION.md).

## 📖 Documentation map

<table>
<tr><th width="33%">📘 Read me first</th><th width="33%">🔧 Build & extend</th><th width="33%">✅ Verify & trust</th></tr>
<tr>
<td valign="top">

| Doc | For |
|---|---|
| 👤 [USER_GUIDE.md](USER_GUIDE.md) | End-user manual |
| 📥 [INSTALLATION.md](INSTALLATION.md) | Setup & portable use |
| 🗂️ [TOOL_CATALOG.md](TOOL_CATALOG.md) | All 551 tools |
| 📦 [EXPANSION_CATALOG.md](EXPANSION_CATALOG.md) | Per-pack counts |

</td>
<td valign="top">

| Doc | For |
|---|---|
| 🧑‍💻 [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | Plugin contract & testing |
| 🏗️ [COMPILATION.md](COMPILATION.md) | Release / EXE builds |
| 🧾 [CHANGELOG.md](CHANGELOG.md) | Release history |

</td>
<td valign="top">

| Doc | For |
|---|---|
| 🔍 [AUDIT_REPORT.txt](AUDIT_REPORT.txt) | Latest audit verdict |
| 🛡️ [SECURITY.md](SECURITY.md) | Vulnerability reporting |
| ⚖️ [LICENSE](LICENSE) | MIT license |

</td>
</tr>
</table>

## 🏛️ Architecture

```text
utility_suite/
├── core/                 # runtime, registry, lazy handlers, CLI + GUI
├── <pack>/               # 45 tool-pack source directories
├── bundle/tools.dat      # deterministic single-archive bundle (ships inside the exe)
├── tests/                # smoke + integration tests
├── run.py                # entry point (CLI / GUI)
├── audit.py              # static release audit + docs-freshness gate
├── generate_catalogs.py  # regenerates TOOL_CATALOG.md / EXPANSION_CATALOG.md
├── build_onefile.spec    # PyInstaller SINGLE-FILE specification
├── build_single_exe.py   # one-command automated release pipeline
├── .github/workflows/    # ci.yml (Linux) + build-windows-exe.yml (main pushes + tagged releases)
├── VERSION.txt           # authoritative version; audit enforces sync
└── LICENSE · SECURITY.md · AUTHORS.md · *.md docs set
```

Design principles: small stable core · plugins never import each other · heavy
deps imported only where needed · a missing optional dep must never crash the
suite · streaming I/O for large files · deterministic pyc-free bundle · ship
one file.

## 🤝 Contributing

Read [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) for the plugin contract and
testing tiers, then open a PR — CI checks your catalogues are regenerated for
you. Lint locally with `ruff check .` before pushing. Ideas welcome: new tools,
new packs, docs, translations.

## ❓ FAQ

**Is it really free?** Yes — MIT licensed, free for personal *and* commercial use.
**Does it need admin rights?** Not for most tools; a few system helpers prompt normally.
**Will it slow my PC down?** It's a portable exe — nothing runs in the background.
**Why do some tools say "unavailable"?** They need an optional binary (FFmpeg etc.) —
run `utility_suite.exe deps` for one-click instructions.
**Can I script it?** Every GUI feature has an identical CLI command.

## 🙏 Acknowledgements

Built entirely with the Python standard library plus optional integrations
(Pillow, pywin32, FFmpeg/ffprobe, qpdf/pdftotext, Tesseract). Thanks to every
tester who ran a pack on a machine that shouldn't have worked.

## 📄 License & author

Released under the **[MIT License](LICENSE)** — free for personal and commercial use.

**Author:** Dr. Sohil Momin, BHMS · Found a vulnerability? See [SECURITY.md](SECURITY.md); otherwise open an issue.

<div align="center">

### ⭐ If Utility Suite saved you fifty sketchy downloads, star this repo — it takes one second and keeps the project alive. ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=drsamonline/All4ONE&type=Date)](https://star-history.com/#drsamonline/All4ONE&Date)

</div>

<!-- SEO keywords (harmless, helps repo search): windows portable tools, single exe toolkit,
python utilities suite, offline tools, ffmpeg frontend, pdf tools windows, image batch resize,
network diagnostics, registry editor cli, disk cleaner portable, hashing tools,
open source windows toolbox, utility belt alternative, sysinternals-like -->
