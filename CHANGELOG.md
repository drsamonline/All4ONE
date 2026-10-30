# Changelog

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
