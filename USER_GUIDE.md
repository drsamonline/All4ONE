# All4one — User Guide

Everything you need to get work done without opening a manual: what the window
does, how a tool page works, and where things live.

---

## 1. Opening the app

Run `All4one.exe`. There is no installer and no sign-in. The window opens on the
**Home** page, which is a search box, four counters, your favourites and recents,
and the category grid.

If you prefer the command line, the same file is a CLI — see
[section 8](#8-command-line-in-a-hurry).

---

## 2. Finding a tool

Three ways, all of them fast:

| Where | How |
|---|---|
| Sidebar search | `Ctrl+K`, type a word, results appear as you type |
| Home search box | same thing, larger |
| Sidebar categories | click a category to see its tools as cards |

Search looks at the tool's name, its category, its description and its keywords.
"split" finds PDF page splitting, file splitting and text splitting; "resize"
finds the image and video tools; "hash" finds hashing, checksums and
verification.

Press `Enter` in the search box: if exactly one tool matches, it opens directly.

---

## 3. A tool page

Every tool has its own page. The layout is the same everywhere:

**Header** — the tool's name, its category, whether it is ready to run, and a
star to add it to Favourites. A red "changes data" badge means the tool can
delete or overwrite something.

**Options (left)** — the tool's controls, generated from the tool's own
definition:

| Control | What it is |
|---|---|
| Text box | free text, e.g. a find/replace term |
| Large text box | paste content, or leave it and pick a file instead |
| Number box | integers and decimals, already limited to sensible ranges |
| Dropdown | a fixed list of choices |
| Toggle | on/off |
| Colour picker | swatch plus a hex field |
| Slider | a range with a live readout |
| File / folder picker | **Browse…** or drag a file straight onto the field |

Fields marked `*` are required. Where one option only matters when another is
on, it hides itself until it applies. **Reset** puts everything back to the
defaults.

**Output (right)** — a console that fills in as the tool works. Above it: a
progress bar when the tool reports progress, and four buttons — copy, save to a
file, open the produced file, clear.

**Run** — the blue button, or `Ctrl+Enter`. **Stop** appears while a job runs and
stops it cleanly.

Under the buttons you will see the equivalent command line, updated live. It is
selectable, so you can copy it into a script.

---

## 4. Favourites and recents

Star a tool from its page. Favourites appear on Home and in the sidebar.
Recently used tools appear automatically, newest first — the list holds the last
twelve. Clear it from **Settings**.

---

## 5. When a tool says "needs setup"

Some tools work through an external program (FFmpeg for video, Tesseract for OCR)
or an optional Python package (Pillow for images). Those tools are always listed
— they are never hidden — but they show a "needs setup" badge and a line telling
you exactly what is missing.

Open **Dependencies** in the sidebar to see every optional component, whether it
is installed, and the install line or download page for each. Press **Re-check**
after installing; no restart needed.

Nothing in that list is required. The app and 380 of its tools run on the Python
standard library alone.

---

## 6. Safety

- Tools that delete or overwrite are badged **changes data** and ask for
  confirmation before they run.
- Most of them also have a preview: bulk rename, folder cleaning, delete-by-list
  and shredding all show you what they would do first.
- Archive extraction refuses entries that would write outside the destination
  folder.
- External programs are run with argument lists, never through a shell string.

If you are nervous about a destructive tool, point it at a copy of the folder
first and read the preview.

---

## 7. Settings

| Setting | What it does |
|---|---|
| Appearance | dark or light; the sun/moon button in the sidebar does the same |
| Ask before a tool that changes data | the confirmation prompt |
| Wrap long lines | console line wrapping |
| Preferences file | where the small JSON file lives; you can open the folder |

All4one stores nothing else: no history of what you processed, no telemetry, no
accounts. Delete the preferences file and it forgets you completely.

---

## 8. Command line in a hurry

```powershell
All4one.exe list                     # every tool, grouped by category
All4one.exe list --category PDF      # one category
All4one.exe search hash              # ranked search
All4one.exe show pdf-merge           # options and defaults for one tool
All4one.exe deps                     # optional extras and their status
```

Running a tool uses the same option names the page shows:

```powershell
All4one.exe run hash-file --file report.pdf --algorithm sha256
All4one.exe run bulk-rename --folder C:\photos --mode "Find & replace" `
            --find IMG --replace holiday --apply
All4one.exe run gst-calc --amount 10000 --rate 18
All4one.exe run pdf-extract-pages --file book.pdf --pages "1-3,7" --output ch1.pdf
```

Toggles are `--flag` and `--no-flag`. Anything with a space goes in quotes.

---

## 9. Keyboard shortcuts

| Keys | Action |
|---|---|
| `Ctrl+K` or `Ctrl+F` | focus search |
| `Ctrl+Enter` | run the current tool |
| `Esc` | go back (or focus search from Home) |
| `Tab` / `Shift+Tab` | move between options |
| `Enter` in search | open the tool if only one matches |

---

## 10. If something looks wrong

- **A tool failed.** The console keeps the error, including the reason the tool
  gave. Copy it and open an issue.
- **A tool is missing.** It is not: check the category in the sidebar. Every
  registered tool is listed, always.
- **Output is empty.** Some tools produce only a file; use the open-output button
  next to the console.
- **Antivirus complained.** A PyInstaller onefile binary unpacks itself at
  startup, which some scanners flag. The source is all here; build it yourself
  if you prefer.
