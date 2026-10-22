<div align="center">

# 🧩 Utility Suite — Plugin Packs

![Packs](https://img.shields.io/badge/plugin%20packs-45-8A2BE2
![Tools](https://img.shields.io/badge/tools-551-brightgreen
![Distribution](https://img.shields.io/badge/distribution-one%20exe-blue

*Author: Dr. Sohil Momin, BHMS*

</div>

Utility Suite is **one self-contained application**. All **45 packs (551 tools)**
are compiled into `utility_suite.exe` — there are **no separate pack downloads**
and nothing to install alongside the app. This document explains what a pack is,
how to turn one on or off inside the app, and what happens when a pack needs an
external program that is not on your machine yet.

---

## What is a plugin pack?

A *plugin pack* is a self-contained Python package that registers a group of
related tools with the suite. Each pack's `__init__.py` exposes a single
function:

```python
def register_tools() -> list[dict]:
    ...
```

`register_tools()` returns one metadata dictionary per tool — its name,
category, description, handler, CLI command and any optional external
dependencies. The suite reads that metadata and only imports a handler when the
tool is actually run.

**Every official pack is already inside the exe.** At build time the pack
sources and their metadata are compiled into a single archive,
`bundle/tools.dat`, which is embedded inside `utility_suite.exe`. A released
build therefore needs exactly one file to run and already contains every tool.

---

## Enabling and disabling a pack

Because everything is built in, "installing" a pack is not something you do —
you simply choose which packs are active:

1. Open the app and go to the **Packs view** (the tab that lists the tool
   packs and their tool counts).
2. **Toggle a pack** to enable or disable it.
3. Disabling a pack only **hides its tools** from the tool list and search — it
   does not delete anything and does not change the exe. Re-enabling it brings
   the tools straight back.

That is the whole model: the exe is fixed, and the Packs view is a preference
over which of the built-in packs you want to see. Use it to keep the tool list
focused on the packs you actually use.

> 💡 Packs that only use the Python standard library are always ready. Packs that
> drive an external program may show some tools as unavailable until that
> program is present — see the next section.

---

## When a pack's external dependency is missing

Some packs do their work through an external command-line program rather than
pure Python — for example:

| Pack area | Typical external program |
|---|---|
| 🎬 Audio / video conversion | **FFmpeg** + **ffprobe** |
| 📑 PDF structural operations | **qpdf** |
| 📃 PDF text / metadata extraction | **Poppler** (`pdftotext`, `pdfinfo`) |
| 🔎 OCR / image scanning | **Tesseract** |
| 🖼️ Image operations | **Pillow** (Python package) |
| 🪟 Advanced Windows / COM work | **pywin32** (Python package) |

When you **enable** a pack whose external program is not available, the pack
still loads — nothing crashes — but the affected tools are reported as
**unavailable** instead of ready. A single missing program affects only the
tools that need it; it never disables the whole suite.

You then have two clean choices:

- **Install the missing program** so those tools light up, or
- **Disable the pack** if you do not need those tools (see above).

---

## Guided dependency install

You are never left guessing what to install. For any tool that is unavailable,
the suite reports the missing dependency by name and points you at where to get
it:

- In the app, an unavailable tool (and the pack it belongs to) shows the
  **missing dependency** and a short install hint — the exact package name, a
  `pip install …` line for Python packages, or the vendor download page for a
  standalone program such as FFmpeg.
- From the command line, ask the suite to list everything it is missing, how
  many tools each item unlocks, and where to get it:

```powershell
utility_suite.exe deps
```

After you install the component, refresh the tool list (or restart the app) and
the tools that depended on it become available. You only ever install the
components for the packs you actually use — there are **zero mandatory
third-party dependencies** to run the app itself.

> ⚠️ **Security.** Every pack is Python code and runs with the same authority as
> the app. The official packs are reviewed and shipped inside the signed release
> exe; treat any pack from outside this repository with the same caution you
> would any other program. See [SECURITY.md](SECURITY.md).

---

## Writing a pack

A pack is any Python package whose `__init__.py` defines `register_tools()`:

```python
# my_pack/__init__.py
def register_tools():
    return [
        {
            "name": "My Example Tool",
            "category": "My Category",
            "description": "Does one concrete thing.",
            "handler": "operations.my_example",   # dotted path inside the pack
            "cli_command": "my-example",
            "dependencies": [],                    # e.g. ["ffmpeg"]
        }
    ]
```

Rules:

- `register_tools()` must return a **list** of dictionaries.
- Each dictionary must supply a unique `cli_command` and a non-empty `handler`.
- A handler is a callable that accepts a list of string arguments and returns an
  integer status code; import heavy dependencies inside the handler.
- Keep `__init__.py` import-light — it is executed at load time.

A new pack joins the built-in set by living in the repository as a top-level
package and being picked up by the bundle build, so it ships inside the exe like
every other pack. Regenerate the embedded bundle and the catalogues with the
normal build/validation pipeline:

```powershell
python generate_catalogs.py     # refresh TOOL_CATALOG.md / EXPANSION_CATALOG.md
python build_single_exe.py      # audit → bundle → tests → exe → verify → zip
```

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for the full tool contract and
testing tiers, and [COMPILATION.md](COMPILATION.md) for release builds.

---

<div align="center">

⬅️ [README](README.md) · [INSTALLATION.md](INSTALLATION.md) · [USER_GUIDE.md](USER_GUIDE.md)

</div>
