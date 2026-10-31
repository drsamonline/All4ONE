# All4one — Installation

## The portable build (recommended)

1. Download `All4one-<version>-windows.zip` from
   [Releases](https://github.com/drsamonline/All4ONE/releases).
2. Unzip it anywhere — Desktop, `C:\Tools`, a USB stick.
3. Run `All4one.exe`.

That is the whole installation. There is no installer, no service, no registry
entry, no scheduled task, and nothing written outside the one preferences file
described below.

Windows 10 or 11, 64-bit. No admin rights needed for the app or for most tools;
the handful that change system settings (services, registry, firewall, power)
will ask for elevation when you use them.

### First run

Windows SmartScreen may say "Windows protected your PC" because the binary is not
code-signed. Choose **More info → Run anyway**. Some antivirus products also flag
PyInstaller onefile binaries on first run; the full source is in this repository
if you would rather build it yourself.

### Where it keeps its settings

One file:

```
%APPDATA%\All4one\settings.json
```

It holds your theme, favourites, recent tools and window size. Nothing else.
Delete it to reset the app; delete the folder to leave no trace.

### Updating

Replace the `.exe`. Your settings file is separate and survives the swap.

### Uninstalling

Delete the `.exe`. Optionally delete `%APPDATA%\All4one`. Done — nothing else was
ever installed.

---

## From source

Useful for development, or if you want to run the engine without the window.

```bash
git clone https://github.com/drsamonline/All4ONE.git
cd All4ONE
```

### Engine only (no window)

```bash
python main.py list
python main.py run word-count --text "hello world"
```

Requires Python 3.10 or newer. No packages at all: the core and 380 tools use the
standard library only.

### With the desktop UI

```bash
pip install -r requirements-build.txt     # PySide6 + PyInstaller
python main.py
```

On a minimal Linux box the Qt runtime also needs a few system libraries:

```bash
sudo apt-get install libegl1 libxkbcommon0 libdbus-1-3 libgl1 \
     libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0
```

---

## Optional dependencies

None of these are required. Each one unlocks the tools that use it; without it
those tools say "needs setup" and everything else keeps working.

| Component | Type | Unlocks |
|---|---|---|
| Pillow | Python package | 26 image tools |
| pypdf | Python package | 24 PDF tools |
| openpyxl | Python package | Excel tools |
| python-docx | Python package | Word tools |
| cryptography | Python package | file encryption |
| psutil | Python package | detailed process and memory info |
| FFmpeg + ffprobe | program | 20 audio/video tools |
| Tesseract | program | OCR |
| Poppler (`pdftotext`) | program | PDF text and PDF-to-image |
| 7-Zip | program | 7z and RAR archives |
| LibreOffice (`soffice`) | program | Office → PDF |
| git | program | the git tools |

```bash
pip install -r requirements-optional.txt
```

For the programs: install them normally and make sure they are on `PATH`. The
portable build looks for them next to `All4one.exe` as well, so a copy of
`ffmpeg.exe` beside the app works too.

Check what you have with:

```powershell
All4one.exe deps
```

or open **Dependencies** in the app and press **Re-check**.

---

## Troubleshooting

**"All4one.exe is not a valid Win32 application"** — you have a 32-bit Windows
build or a truncated download. Re-download the zip.

**The window opens blank or tiny** — a display-scaling driver issue; delete
`%APPDATA%\All4one\settings.json` (it stores the window size) and reopen.

**A tool says "needs setup" after I installed the program** — the program is not
on `PATH` for the process. Open a new terminal, or put the executable next to
`All4one.exe`, then press **Re-check**.

**OCR returns nothing** — the language data may be missing. Tesseract ships
`eng` by default; other languages need their own traineddata files. Set the
language code on the tool page (e.g. `hin`, `guj`, `mar`).

**Video tools fail immediately** — check `ffmpeg -version` works in a terminal. If
it does not, FFmpeg is not on `PATH`.

**Fonts look wrong on Linux** — install a font package such as `fonts-inter` or
`fonts-noto`; the stylesheet asks for Segoe UI, Inter and Noto in that order.
