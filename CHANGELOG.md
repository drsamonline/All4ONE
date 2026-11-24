# Changelog

## Unreleased

### Added

- **Amortisation Schedule (Numbers, the 408th tool).** The split every lender
  prints and no borrower reads: month by month, how much of each instalment is
  interest and how much actually repays the loan, plus what paying a little
  extra each month saves. It is not the EMI calculator — `emi-calc` gives one
  number and a year-by-year total; this gives the schedule itself, and every
  total in it is **summed from the rows**, never recomputed from the formula,
  because `instalment × months` is not what a borrower pays. Two things the
  naive version gets wrong are both pinned by tests: rounding the instalment to
  the paisa leaves a few paise over, and the old shape of this calculation
  answers a 60-month loan with a 61st payment of ₹0.02 — the last instalment is
  whatever is left, and the report says how far it differs from the usual one
  (₹0.02 more here, ₹8,948.91 less when an extra payment ends the loan early).
  Every figure is held in whole paise, so the principal column adds up to the
  loan exactly; ₹4.35 over 5 months is 5 × ₹0.87 and not the ₹0.18 a float
  schedule produces. An extra payment's saving is read off two schedules, not
  estimated: ₹2,000 a month on ₹5,00,000 at 9.5% clears it in 49 instalments
  instead of 60 and saves ₹26,459.16 of interest. Refusals are by name: a
  0-month tenure, a ₹0 loan, a negative extra, and a loan whose instalment
  rounds to nothing (₹1 at 50% over 40 years) — that one is refused rather than
  looped on, because a schedule of ₹0.00 payments never ends. `Every month` and
  `Year by year` agree on every total, and the CSV holds the same rows.
  `tests/test_amortisation.py` — 25 assertions; ten mutations, each red.
- **Pace & Speed (Numbers, the 407th tool).** A distance and a time in, a pace
  per kilometre and per mile, a speed in km/h and mph, and what the same pace
  would give you over 5K, 10K, a half and a full marathon. It is not a unit
  conversion, because the answer depends on **both** numbers. So neither is
  guessed: `27:30` is read as minutes and seconds **because you said so** (the
  choice is there, and the reading is printed back in words beside the time —
  a pace built on a guessed reading looks right); a zero distance and a zero
  time are both refused, because neither has a pace; `9:00 AM` is named as a
  time of day; `1h 30` is refused because 30 of what is not written down; `1:75`
  is refused because a colon form's parts are not free numbers; and a unit it
  does not know is named rather than assumed. Miles and metres are converted to
  kilometres once, so `5 miles in 44:14` and `5 km in 27:30` report the same
  pace per km. Hours are not wrapped at 24, and a pace past the hour keeps its
  hours (`1:06:00 per km`).


- **Add Up Times (Numbers, the 406th tool).** A column of durations — a
  timesheet, a playlist, a set of call lengths, a leave request — added into one
  total, in every form people actually write them: `1:30:00`, `1:30`, `90m`,
  `1h 30m`, `1h30m45s`, `1.5h`, `5400s`, `2d`. It does not guess. `1:30` is
  read as hours and minutes **because you said so** (there is a choice for
  minutes and seconds, and the per-line table shows what each line became);
  `1h 30` is refused because 30 of what is not written down; `1:75` is refused
  because a colon form's parts are not free numbers; `9:00 AM` is named as a
  time of day, not a length; a negative duration is refused. One unreadable line
  refuses the **whole** sum, because a partial total is a wrong total. Hours do
  not wrap at 24 (a 25-hour week is `25:00:00`, with the days named beside it),
  the total is carried in whole milliseconds so ten `0.1h` lines are exactly
  `01:00:00`, and decimal hours are reported for billing.

- **Find & Normalise Dates (Text, the 405th tool).** Dates arrive written every
  way a person writes them — `2025-04-03`, `3 April 2025`, `April 3, 2025`,
  `3rd-Apr-25`, `25/04/2025`, `03.04.2025` — and the tool rewrites every one it
  finds in prose into a single style you choose (ISO 8601, day-first, or a
  month name). It does not guess. `03/04/2025` is 3 April in India and 4 March
  in the US, so a date that could be read two ways is **left exactly as it was
  and listed**, and only your own "read ambiguous dates as" choice settles it;
  `31/02/2025` is listed as no such date rather than invented; `v1.2.34` and
  `12:30:45` are not dates and are not touched. A two-digit year follows the
  POSIX pivot (69-99 are the 1900s, 00-68 the 2000s). Every rewrite is shown in
  a table of found → becomes → why before the text is written.


### Fixed

- **A colon time can carry a fractional second, and survives a paste.**
  `27:30.5` was refused as a malformed `h:mm` even though a two-part time has
  always been allowed a fractional third part; the second part accepts one now,
  and the hours-and-minutes reading rounds it to whole milliseconds instead of
  raising on `int("30.5")`. And `27 : 30` — what a spreadsheet paste looks like
  — was refused as "not a duration" because the spaces sat around the colon;
  they are closed up before the form is read, so the paste is the same time.

- **A lone surrogate no longer crashes eleven tools.** Text that was decoded
  from bytes which were not valid UTF-8 — a Linux filename, a paste from a
  mis-encoded source — comes back as an unpaired surrogate, and every tool that
  encodes text to bytes died on `UnicodeEncodeError` with a traceback on screen.
  Base32, Base64, CRC32, Hash Text, HMAC, Text Fingerprint, Text to Binary, Hex,
  URL Encode, Measure Entropy and the file writers all encode through one helper
  now (`text_bytes`), which reproduces the original bytes when it can and a
  deterministic WTF-8 form when it cannot. A hash of such text is the hash of the
  bytes it stands for, not of a replacement character.
- **Text to Word accepts text Word cannot store.** A NUL or a C0 control in the
  input made python-docx raise `ValueError: All strings must be XML compatible`.
  Those characters are now replaced with `U+FFFD` and the run says how many,
  instead of failing the whole document.
- **Two documents understated the catalogue.** `PRIVACY.md` said 403 working tools and
  `INSTALLATION.md` said 380 while the registry runs 404. `scripts/audit.py` now reads every
  "N tools" claim in the prose against the registry, so the next drift fails the build rather
  than shipping in a privacy policy. Proven by restoring 403: the audit names the file and the
  number. A paragraph describing the previous version ("551 tools across 45 plugin packs") is
  history, not a claim about this one, and is skipped.

### Added

- **`tests/test_hostile_input.py`** — 60 text tools x 12 BLNS-shaped payloads
  (lone surrogates, NULs, bidi overrides, zero-width joiners, a 20 kB line), plus
  targeted assertions that the encoding is byte-exact and that the .docx really
  carries no NUL. It runs in CI beside the sweep. The sweep only ever proves a
  tool works on a well-formed fixture; this is the other half.

## 4.1.0 — 2026-11-10

### Added

- **Markdown Table to CSV** (`markdown-table-to-csv`) — the reverse of the
  existing `csv-to-markdown`: pull one table, or every table, out of a Markdown
  document and write it as CSV. It handles the cases a naive `split("|")` gets
  wrong — a pipe escaped as `\|`, a pipe inside inline code, a table written
  without outer pipes, a ragged row — and takes the output delimiter as an
  option. Covered by `tests/test_markdown_to_csv.py` (11 cases), which now runs
  in CI beside the sweep.

## 4.0.0 — the rebuild

A ground-up replacement of the 3.x utility suite. The plugin architecture, the
551-tool catalogue and the Tkinter interface are gone; what ships now is one flat
catalogue of verified tools, one page per tool, and a single portable binary.

### Removed

- **The plugin pack system.** 45 packs, `register_tools()` manifests, the Packs
  tab, the enable/disable model and `bundle/tools.dat` no longer exist. A tool
  module is discovered from `tools/` and that is the end of it.
- **Catalogue padding.** Tools that were thin adapters with near-duplicate or
  no-op behaviour ("Image Cropper — Crop image.", "Sparse File Inspector — report
  internals", "Version Bump Helper — assist with version bump tasks") were
  deleted rather than carried forward.
- **The single dense table.** One grid of 551 rows with a details pane and a
  free-text argument box has been replaced by per-tool pages with typed controls.
- **The old documentation set** (PLUGINS, COMPILATION, EXPANSION_CATALOG,
  AUDIT_REPORT and the 3.x guides) and the demo deploy workflow.

### Added

- **A declarative tool contract** (`core/tool.py`): a tool is a function plus a
  list of typed fields. The UI page, the CLI flags and the catalogue entry are
  all generated from that one declaration, so they cannot drift apart.
- **A desktop UI in PySide6**: sidebar navigation with live category counts,
  ranked search on `Ctrl+K`, favourites, recents, light and dark themes, and one
  page per tool with its own controls — text, multiline, numbers, dropdowns,
  toggles, colours, sliders, and file/folder pickers with drag-and-drop.
- **A real output console**: streamed lines, a progress bar when the tool reports
  progress, stop, copy, save, and an "open the produced file" action.
- **Safety in the UI**: destructive tools carry a badge and ask for confirmation;
  most preview their plan before acting.
- **Readiness instead of gating**: a tool missing an optional dependency stays
  listed, marked "needs setup", with the exact install line. Nothing is hidden.
- **Two gates in CI**: `scripts/audit.py` (metadata, versions, hygiene, imports,
  documentation coverage) and `tests/sweep.py` (executes every runnable tool
  against generated fixtures — 312/312 at release).
- **A landing page generated from the registry** (`scripts/landing.py`), so its
  tool counts cannot go stale.

### Changed

- **The catalogue is smaller and real: 403 tools across 16 categories**, each
  with a full-sentence description, its own options and a working
  implementation.
- **Categories were re-cut** for how people actually look for things: Files,
  Archives, Text, Data, Encoding, Images, PDF, Media, Documents, Network,
  System, Disk, Developer, Security, Numbers, Generators.
- **The CLI is generated from the same schemas** as the GUI: `list`, `search`,
  `show`, `run`, `deps`, with `--flag` / `--no-flag` for toggles.
- **The build is one command** (`python build.py`): clean → audit → sweep →
  catalogue → icon → PyInstaller onefile → verify → zip.
- **Dependencies are optional by design**: the app and 380 of its tools run on
  the standard library alone.

### Fixed (relative to 3.0.6)

- Tools that reported success while doing nothing are gone; the sweep makes that
  class of regression fail the build.
- Descriptions are unique across the whole catalogue and checked for the known
  boilerplate templates.
- Archive extraction validates every entry path (zip-slip and tar-slip).
- External programs are invoked with argument lists, never shell strings.
- The README, the catalogue and the landing page are generated or audited
  against the live registry, so the advertised numbers match the code.

---

## Earlier history

The 3.x line (3.0.0 → 3.0.6) is preserved in this repository's git history,
including its plugin packs, its 551-tool catalogue and the audit reports for each
hardening pass. `git log` before commit `7212639` has all of it.

Notable 3.x milestones, for reference: 2.1.2 single-file packaging, 3.0.0 the
embedded `bundle/tools.dat` archive, 3.0.5 the documentation-freshness gate,
3.0.6 the templated-description and shell-injection cleanup.
