<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://placehold.co/900x180/0d1117/58a6ff?text=%E2%9A%99%EF%B8%8F+Utility+Suite&font=segoe-ui">
  <img alt="Utility Suite" src="https://placehold.co/900x180/f0f6fc/0969da?text=%E2%9A%99%EF%B8%8F+Utility+Suite&font=segoe-ui" width="720">
</picture>

# 🧰 Utility Suite

### ⚡ One workstation. **539 tools. 45 plugin packs.** Zero installer drama.

A modular, portable Windows utility workstation — pure-Python core, lazily loaded
plugin packs, CLI *and* desktop GUI, built to be compiled into a single `.exe`.

[![CI](https://github.com/sohil-momin/utility_suite/actions/workflows/ci.yml/badge.svg)](https://github.com/sohil-momin/utility_suite/actions/workflows/ci.yml)
[![Windows Build](https://github.com/sohil-momin/utility_suite/actions/workflows/build-windows-exe.yml/badge.svg)](https://github.com/sohil-momin/utility_suite/actions/workflows/build-windows-exe.yml)
![Version](https://img.shields.io/badge/version-2.1.3-blue?style=flat-square&logo=python&logoColor=white)
![Tools](https://img.shields.io/badge/tools-539-brightgreen?style=flat-square)
![Packs](https://img.shields.io/badge/plugin%20packs-45-8A2BE2?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Windows_10%2F11-0078D4?style=flat-square&logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/python-3.10%2B-yellow?style=flat-square&logo=python&logoColor=black)
![Dependencies](https://img.shields.io/badge/mandatory%20deps-0-orange?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-informational?style=flat-square)
![Size](https://img.shields.io/badge/installer-none%20—%20portable-lightgrey?style=flat-square)

*No registry pollution · No background services · Unplug it and walk away.*

</div>

---

## 🌈 What is this?

**Utility Suite** bundles **539 hand-crafted Windows utilities** into one coherent
workstation. Instead of fifty sketchy downloads, you get one audited codebase:
file ops, hashing, media tooling, PDF work, networking diagnostics, registry
editing helpers, clipboard history, automation, developer codecs, security
audits, disk maintenance, monitoring — and more.

Every tool is metadata-registered, **loaded lazily**, and declares its own
optional dependencies. A missing dependency (say, FFmpeg) disables exactly one
tool — never the suite.

## ✨ Highlights

<table>
<tr>
<td width="50%">

### 🧩 Modular by design
- **45 plugin packs** shipped as deterministic ZIP archives
- Drop-in extensibility: add a pack, register metadata, done
- Core stays tiny and stable; plugins never import each other

### 🪶 Portable & safe
- Runs from any folder — no install, no admin required for most tools
- Standard-library-first; heavy deps imported only when needed
- Safe archive extraction checks baked in

</td>
<td width="50%">

### 🔍 Audit-grade quality
- `audit.py` enforces **539/539 handler resolution**, unique commands,
  ZIP integrity, version sync, and **documentation freshness** on every release
- CI matrix (Linux + Windows) with smoke tests and catalogue drift gates
- Full docs: user guide, tool catalogue, expansion map, dev guide

### 🖥️ Two frontends, one engine
- Rich **CLI** (`python run.py …`) for scripting
- Desktop **GUI** with search, categories, async execution, previews

</td>
</tr>
</table>

## 📊 The numbers

| Metric | Value |
|---|---|
| 🛠️ Registered tools | **539** |
| 📦 Plugin packs | **45** |
| 🧪 Smoke-tested handlers | 539 / 539 ✅ |
| 🔒 Mandatory third-party deps | **0** |
| 🐍 Language | Python 3.10+ (stdlib-first) |
| 🖱️ Frontends | CLI + Tkinter GUI |
| 📄 Docs | 11 curated documents (~1,700 lines) |

## 🗺️ Tool category map

<details open>
<summary><b>🎯 45 packs at a glance — grouped by mission</b></summary>

| Category | Packs | Tools |
|---|---|---|
| 📁 **Files & Archives** | `file_ops` · `archive_tools` · `directory_tools` · `search_index` · `imaging_advanced` | 31 |
| 🔤 **Text, Docs & Data** | `text_tools` · `data_tools` · `conversion_tools` · `dev_tools` · `office_tools` · `pdf_tools` · `document_tools` | 92 |
| 💻 **Developer** | `developer_tools_advanced` · `shell_tools` · `package_tools` · `automation` · `misc` | 61 |
| 🌐 **Network** | `network_tools` · `network_diagnostics` · `net_advanced` | 41 |
| 🖥️ **Windows System** | `system_info` · `system_utils` · `windows_power` · `process_tools` · `window_manager` · `virtual_desktop` · `registry_tools` · `startup_automation` · `driver_tools` · `event_tools` · `security_tools` · `security_audit` | 138 |
| 🎨 **Media** | `audio_tools` · `media_tools` · `media_metadata` · `video_tools` · `image_batch` | 51 |
| 🧹 **Maintenance & Storage** | `maintenance` · `disk_advanced` · `storage_tools` · `backup_tools` · `clipboard_manager` · `time_productivity` · `monitoring_tools` · `diagnostics_extra` | 125 |

Full per-pack breakdown → **[EXPANSION_CATALOG.md](EXPANSION_CATALOG.md)** ·
All 539 tools described → **[TOOL_CATALOG.md](TOOL_CATALOG.md)**

</details>

## 🚀 Quick start

### From source (any OS for development, Windows for full functionality)

```powershell
git clone https://github.com/sohil-momin/utility_suite.git
cd utility_suite

python run.py list                    # browse all 539 tools
python run.py search image            # find tools by keyword
python run.py run checksum C:\f.txt --algorithm sha256   # run a tool
python run.py gui                     # launch the desktop GUI
```

### Prebuilt portable EXE

Grab `utility_suite.exe` from the latest [release](../../releases), unzip, run.
Build your own from source with [`COMPILATION.md`](COMPILATION.md) or let
GitHub Actions do it on a Windows runner via `build-windows-exe.yml`.

## 📖 Documentation map

<table>
<tr><th width="33%">📘 Read me first</th><th width="33%">🔧 Build & extend</th><th width="33%">✅ Verify & trust</th></tr>
<tr>
<td valign="top">

| Doc | For |
|---|---|
| 👤 [USER_GUIDE.md](USER_GUIDE.md) | End-user manual |
| 📥 [INSTALLATION.md](INSTALLATION.md) | Setup & portable use |
| 🗂️ [TOOL_CATALOG.md](TOOL_CATALOG.md) | All 539 tools |
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

## 🏗️ Architecture

```text
utility_suite/
├── core/                 # runtime, registry, lazy handlers, CLI + GUI
├── <pack>/               # 45 plugin-pack source directories
├── plugins/              # generated compressed plugin ZIPs (deterministic)
├── tests/                # smoke + integration tests
├── run.py                # entry point (CLI / GUI)
├── audit.py              # static release audit + docs-freshness gate
├── generate_catalogs.py  # regenerates TOOL_CATALOG.md / EXPANSION_CATALOG.md
├── create_plugin_zips.py # deterministic pack builder
├── build.spec            # PyInstaller specification
├── BUILD_WINDOWS.ps1     # Windows release build script
├── .github/workflows/    # ci.yml (Linux+Windows) + build-windows-exe.yml
├── VERSION.txt           # authoritative version; audit enforces sync
├── pyproject.toml        # ruff lint config
├── .editorconfig         # cross-editor formatting rules
├── LICENSE · SECURITY.md · AUTHORS.md
└── *.md                  # the documentation set above
```

## 🎯 Design principles

1. **Keep the core small and stable.**
2. **Isolate plugin logic** — plugins never reach into the core's guts.
3. Import heavy dependencies **only inside the operation that needs them**.
4. A missing optional dependency must **never crash the suite**.
5. Prefer **streaming I/O** for large files.
6. Never interpolate shell strings when an argument list suffices.
7. Plugin ZIPs stay **deterministic**, free of `__pycache__`/`.pyc`.
8. Add tools via **metadata + lazy handler** — never duplicate infrastructure.

## ✅ Validation & CI

The release process performs:

- 🐍 Python syntax compilation across all source files
- 🔢 Tool-count + unique-command checks (**539/539**)
- 📚 **Documentation freshness gate** — `TOOL_CATALOG.md`,
  `EXPANSION_CATALOG.md` and this README must match the live registry
  (regenerate anytime with `python generate_catalogs.py`)
- 📦 Plugin ZIP integrity + no embedded bytecode caches
- 🧬 Handler & dependency metadata validation
- 🏃 Runtime handler-resolution tests + functional smoke tests
- 🖥️ GitHub Actions: Linux validation, Windows validation, and a real
  `utility_suite.exe` build-and-test pipeline

`audit.py` exits **0 only on `AUDIT PASSED`**, so CI can rely on
`python audit.py && <next step>` failing loudly. Release hashes are generated
at distribution time with PowerShell `Get-FileHash` (see
[`COMPILATION.md`](COMPILATION.md)) rather than committed to the tree.

## 🤝 Contributing

Read [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) for the plugin contract and
testing tiers, then open a PR — CI will regenerate-check your catalogues for
you. Lint locally with `ruff check .` before pushing.

## 🙏 Acknowledgements

Built entirely with the Python standard library plus a handful of optional
integrations (Pillow, pywin32, FFmpeg/ffprobe, qpdf/pdftotext). Thanks to every
tester who ran a pack on a machine that shouldn't have worked.

## 📄 License & author

Released under the **[MIT License](LICENSE)** — free for personal and commercial use.

**Author:** Dr. Sohil Momin, BHMS · Reporting issues? See [SECURITY.md](SECURITY.md) for vulnerabilities, otherwise open an issue.

<div align="center">

⭐ *If Utility Suite saved you fifty downloads, star the repo.* ⭐

</div>
