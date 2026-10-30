# All4one — Developer Guide

How the code is put together and how to add a tool. It is deliberately short,
because adding a tool is deliberately short.

---

## The shape of the code

```text
core/tool.py        the contract: Field, Tool, Context, the @tool decorator
core/registry.py    discovery, validation, categories, ranking, readiness
core/runner.py      one execution path for UI and CLI (streaming, cancel, errors)
core/deps.py        optional dependency probes and install hints
core/cli.py         argparse front-end built from the same field schemas
core/settings.py    the small JSON preferences file
ui/theme.py         design tokens + the entire stylesheet
ui/icons.py         line icons as inline SVG
ui/widgets.py       cards, chips, field editors, the output console
ui/pages.py         home, category, search, tool page, settings, dependencies
ui/window.py        sidebar shell, navigation history, search
tools/*.py          18 modules; the tools themselves
scripts/audit.py    release gate: catalogue integrity, versions, hygiene
scripts/catalogue.py  regenerates TOOL_CATALOG.md from the registry
tests/sweep.py      executes every runnable tool against generated fixtures
build.py            audit → sweep → PyInstaller onefile → zip
```

The rule that keeps this small: **a tool declares what it needs; nothing else
knows anything about it.** The UI, the CLI and the catalogue all read the same
declaration.

---

## Adding a tool

Add a function to any module in `tools/`. That is the entire process — no
registration, no manifest, no plugin packaging.

```python
from core.tool import F, ToolError, tool
from ._util import need_file


@tool(
    id="csv-column-total",                       # kebab-case, unique, stable
    name="Add Up a CSV Column",                  # what the page is called
    category="Data",                             # must be a known category
    summary="Sum one numeric column of a CSV and report the total and the mean.",
    keywords="sum total add column csv",         # extra search terms
    fields=[
        F.file("file", "CSV file", filters="CSV (*.csv)"),
        F.text("column", "Column name", required=True),
        F.flag("skip_blanks", "Ignore empty cells", True),
    ],
)
def csv_column_total(values, ctx):
    path = need_file(values["file"], "CSV file")
    ...
    ctx.log(f"{total:,.2f}")
    return {"column": column, "total": total, "mean": mean}
```

What you get for free: a page in the app with those three controls, a CLI
(`all4one run csv-column-total --file x.csv --column amount`), a row in the
catalogue, search indexing, favourites, and the audit checking your metadata.

### The function signature

`values` is a dict of already-coerced option values (ints are ints, toggles are
bools, multi-selects are lists). `ctx` is a `Context`:

| Call | Effect |
|---|---|
| `ctx.log(text)` | a line in the console / stdout |
| `ctx.progress(percent, note)` | the progress bar and status text |
| `ctx.check_cancel()` | raises `ToolCancelled` if the user pressed Stop |
| `ctx.output(path)` | registers a produced file for the "open" button |

Return a `str` to print it, a `dict`/`list` to render it as JSON, or `None` if
you already logged everything.

Raise `ToolError("plain-language reason")` for anything the user can fix — a
missing file, a bad option, a locked PDF. The message is shown verbatim. Any
other exception is caught by the runner, shown with its traceback, and never
takes the app down.

### Field kinds

| Factory | Kind | Renders as |
|---|---|---|
| `F.text` | `text` | single-line box |
| `F.secret` | `password` | masked box |
| `F.multi` | `multiline` | text area (`rows=`) |
| `F.integer` | `int` | spin box (`minimum`, `maximum`, `suffix`) |
| `F.number` | `float` | decimal spin box |
| `F.choice` | `choice` | dropdown (`choices`) |
| `F.many` | `multi` | comma list → `list[str]` |
| `F.flag` | `bool` | toggle |
| `F.file` | `file` | picker + drag-and-drop (`filters`) |
| `F.files` | `files` | multi-file picker → `|`-joined string |
| `F.folder` | `dir` | folder picker |
| `F.save` | `save` | save-as picker |
| `F.color` | `color` | swatch + hex |
| `F.slider` | `slider` | slider with readout |

Useful keyword arguments on any field: `help` (the small grey line under the
control), `required`, `placeholder`, `show_if` (a toggle key that must be on for
this field to appear).

### Metadata worth setting

| Argument | When |
|---|---|
| `needs=("ffmpeg",)` | the tool shells out to or imports an optional component; keys live in `core/deps.py` |
| `destructive=True` | the tool deletes or overwrites data — adds the red badge and a confirmation |
| `platforms=("win",)` | Windows-only; the tool still appears elsewhere, marked unavailable |
| `keywords="..."` | extra words that should find this tool in search |

Add a dependency key to `core/deps.py` (with its `hint` and `url`) if you need a
new external component.

### Style rules the audit enforces

- `id` is kebab-case and unique.
- `summary` is a full sentence, unique across the catalogue, at least 20
  characters — no "Crop image." placeholders.
- `category` is one of `core.registry.CATEGORY_NAMES`.
- every `needs` key exists in `deps.DEPS`.
- no duplicate field keys within a tool.

---

## Adding a category

Add a `Category(name, blurb)` to `CATEGORIES` in `core/registry.py` and an icon
name to `CATEGORY_ICONS` in `ui/icons.py`. The sidebar, home grid, catalogue and
counts all follow automatically.

---

## Adding a field kind

1. Add the constant to `KINDS` in `core/tool.py` plus a factory in `F`.
2. Add `coerce()` handling if the value is not a string.
3. Add a branch to `FieldEditor._build()` and `FieldEditor.value()` in
   `ui/widgets.py`.
4. Add a `KIND_LABEL` entry in `scripts/catalogue.py`.

Nothing else needs to change — tools and the CLI pick it up from the schema.

---

## Testing

```bash
python scripts/audit.py     # metadata, versions, hygiene, imports (~1s)
python tests/sweep.py       # runs every runnable tool against fixtures
```

`tests/sweep.py` generates its own fixtures (CSV, JSON, PNG, PDF, XLSX, DOCX,
SQLite, ZIP, TAR) in `tests/fixtures/`, works out a plausible value for every
option of every tool, runs it with a 25-second timeout, and reports failures. A
new tool is picked up automatically; if it needs a particular fixture, extend
`file_fixture()` or `text_fixture()` in that file.

Tools that cannot be swept here are listed in `SKIP_TOOLS` with a reason: they
need a live network, a real git repository, admin rights, or a Windows kernel.
Keep that list short and keep the reason honest.

Windows-only tools are skipped on Linux and macOS because they cannot run, not
because they are untested: on a Windows runner the sweep also executes the
read-only ones listed in `SAFE_WINDOWS_TOOLS` (services, event log, disks,
firewall state, installed programs and so on). Destructive Windows tools are
never swept — the `destructive` flag keeps them out.

### UI check

```bash
QT_QPA_PLATFORM=offscreen python smoke_ui.py
```

Builds the window without a display, walks home → category → tool page →
dependencies → light theme, and writes screenshots to `shots/`. CI runs this on
every push.

---

## Code style

- Standard library first. A new dependency needs a good reason and a `needs` key.
- `ruff check .` with the config in `pyproject.toml`; line length 100.
- Tools never print directly — always `ctx.log`, so the console and stdout stay
  in sync.
- Never build a shell string: pass argument lists to `run_command()`.
- Errors users can act on are `ToolError`; everything else is a bug.

## Pull request checklist

- [ ] `python scripts/audit.py` passes
- [ ] `python tests/sweep.py` passes
- [ ] `python scripts/catalogue.py` run and `TOOL_CATALOG.md` committed
- [ ] new tools have a real `summary`, sensible `help` text and defaults
- [ ] destructive tools are marked and, where meaningful, preview before acting
- [ ] the equivalent CLI command works
