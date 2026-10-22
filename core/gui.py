"""Windows-10 (Fluent) styled desktop UI for Utility Suite.

Design goals:
  * Two compact tabs — **Tools** and **Plugins** — instead of one long page.
  * Tools tab: a single search/filter bar over a scannable tool table
    (name + category + availability visible at a glance), a details pane, an
    argument row with the primary *Run* action, and live output.
  * Plugins tab: browse the remote catalogue and the installed packs in one
    list, download / remove / install-from-file, all without leaving the app.
  * Everything is dense and quiet: one accent (primary) action per screen,
    hairline borders, consistent 16 px gutters, keyboard-first navigation.

The window title, the app name/branding and the colour palette are unchanged
from the shipped build.
"""

from __future__ import annotations

import os
import queue
import shlex
import sys
import threading
import tkinter as tk
from pathlib import Path
from typing import Any

from tkinter import ttk

try:  # the file picker is optional — a stripped build must still run
    from tkinter import filedialog
except Exception:  # pragma: no cover - defensive
    filedialog = None  # type: ignore[assignment]

try:
    from tkinter import messagebox
except Exception:  # pragma: no cover - defensive
    messagebox = None  # type: ignore[assignment]

from . import plugin_installer as plugin_packs
from .capability_checker import download_hint
from .plugin_installer import PackInfo
from .preview import open_with_default, preview_file
from .tool_registry import ToolRegistry

try:  # single source of truth for the version string
    from . import __version__ as APP_VERSION
except Exception:  # pragma: no cover - defensive fallback
    APP_VERSION = "3.0.6"

# Tools that can delete/overwrite data or otherwise irreversibly change the
# system — the GUI confirms before running these.
DESTRUCTIVE_TOOLS = {
    "sdelete",
    "dupefinder",
    "backup-cleanup",
    "backup-rotation",
    "backup-restore",
    "mirror-backup",
    "empty-clean",
    "temp-clean",
    "junk-find",
    "registry-key-deleter",
    "registry-value-deleter",
    "registry-import",
    "startup-folder-cleaner",
}

# ---- Windows 10 light palette (unchanged from the shipped build) ----------
BG = "#f3f3f3"          # window background
CARD = "#ffffff"        # card / surface
BORDER = "#e1e1e1"      # hairline borders
TEXT = "#191919"
SUBTLE = "#5d5d5d"
ACCENT = "#0078d4"      # Win10 default blue
ACCENT_HOVER = "#1a86d9"
CHIP_BG = "#ffffff"
CHIP_BORDER = "#bebebe"
OK = "#107c10"          # "ready / installed" green

ALL_CATEGORY = "All"
_PAD = 16               # single horizontal gutter used everywhere


def _human_size(size: int) -> str:
    """Format a byte count as a short human string (e.g. ``1.2 MB``)."""
    if size <= 0:
        return "—"
    units = ("B", "KB", "MB", "GB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


class Win10Check(tk.Frame):
    """A Windows-10 style checkbox drawn from scratch (square box + tick)."""

    def __init__(self, master, text="", variable=None, command=None):
        super().__init__(master, bg=master.cget("bg"))
        self.var = variable if variable is not None else tk.IntVar(master=self)
        self.command = command
        self._box = tk.Canvas(self, width=18, height=18, bg=master.cget("bg"), highlightthickness=0)
        self._label = tk.Label(
            self, text=text, bg=master.cget("bg"), fg=TEXT, font=("Segoe UI", 10), anchor="w"
        )
        self._box.pack(side="left", padx=(0, 6), pady=2)
        self._label.pack(side="left")
        for widget in (self, self._box, self._label):
            widget.bind("<Button-1>", self._toggle)
        self._draw()

    def _toggle(self, _event=None):
        self.var.set(0 if self.var.get() else 1)
        self._draw()
        if self.command:
            self.command()

    def _draw(self):
        canvas = self._box
        canvas.delete("all")
        on = bool(self.var.get())
        canvas.create_rectangle(
            3, 3, 15, 15, fill=ACCENT if on else CARD, outline=ACCENT if on else CHIP_BORDER, width=2
        )
        if on:
            canvas.create_line(5, 9, 8, 12, fill="white", width=2, capstyle="round")
            canvas.create_line(8, 12, 13, 5, fill="white", width=2, capstyle="round")


class UtilitySuiteGUI(tk.Tk):
    """The application window: a Tools tab and a Plugins tab."""

    def __init__(self, registry: ToolRegistry, *, on_refresh=None) -> None:
        super().__init__()
        self.registry = registry
        self.on_refresh = on_refresh

        # DPI awareness must be set *before* the window is realised, otherwise
        # on 125/150% Windows displays every widget keeps its tiny 96-DPI size
        # while fonts/layout scale -> text and buttons spill out of the window.
        if sys.platform == "win32":
            try:
                import ctypes

                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass
        self._scale = max(1.0, min(2.0, self.winfo_fpixels("1i") / 72.0))
        self.title(f"Utility Suite {APP_VERSION} — by Dr. Sohil Momin, BHMS")
        self.geometry(f"{int(1120 * min(self._scale, 1.25))}x{int(720 * min(self._scale, 1.25))}")
        self.minsize(860, 560)
        self.configure(bg=BG)

        self._selected: dict[str, Any] | None = None
        self._queue: queue.Queue[str] = queue.Queue()
        self._plugin_queue: queue.Queue[tuple] = queue.Queue()
        self._tools_by_iid: dict[str, dict[str, Any]] = {}

        # Plugin-panel state.
        self._available: list[PackInfo] = []
        self._manifest_loaded = False
        self._manifest_loading = False
        self._plugin_busy = False
        self._progress_pulse = 0

        self._build_style()
        self._build_header()
        self._build_tabs()
        self._populate()
        self.search_entry.focus_set()
        self.after(80, self._drain_output)
        self.after(120, self._drain_plugins)

    # ------------------------------------------------------------------ chrome
    def _build_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Win10.TCombobox",
            fieldbackground=CARD,
            background=CARD,
            foreground=TEXT,
            arrowcolor=TEXT,
            bordercolor=BORDER,
            lightcolor=CARD,
            darkcolor=CARD,
            padding=5,
        )
        style.map(
            "Win10.TCombobox",
            fieldbackground=[("readonly", CARD)],
            bordercolor=[("focus", ACCENT)],
        )
        style.configure(
            "Win10.Treeview",
            background=CARD,
            fieldbackground=CARD,
            foreground=TEXT,
            rowheight=24,
            bordercolor=BORDER,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Win10.Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#fafafa", relief="flat"
        )
        style.configure("Win10.TNotebook.Tab", font=("Segoe UI", 10), padding=(16, 7))
        style.configure("Win10.Horizontal.TProgressbar", troughcolor=BORDER, background=ACCENT, thickness=6)

    def _card(self, parent, **kw):
        return tk.Frame(
            parent,
            bg=CARD,
            highlightbackground=BORDER,
            highlightcolor=BORDER,
            highlightthickness=1,
            **kw,
        )

    def _accent_button(self, parent, text, command):
        """Primary action button (accent-filled)."""
        btn = tk.Label(
            parent, text=text, bg=ACCENT, fg="white", font=("Segoe UI", 10, "bold"),
            padx=18, pady=6, cursor="hand2", bd=0,
        )
        btn.bind("<Button-1>", lambda _e: command())
        btn.bind("<Enter>", lambda _e: btn.configure(bg=ACCENT_HOVER))
        btn.bind("<Leave>", lambda _e: btn.configure(bg=ACCENT))
        return btn

    def _ghost_button(self, parent, text, command):
        """Secondary action button (outlined, quiet)."""
        btn = tk.Label(
            parent, text=text, bg=CARD, fg=TEXT, font=("Segoe UI", 10),
            padx=12, pady=5, cursor="hand2", bd=0,
            highlightbackground=CHIP_BORDER, highlightcolor=ACCENT, highlightthickness=1,
        )
        btn.bind("<Button-1>", lambda _e: command())
        btn.bind("<Enter>", lambda _e: btn.configure(bg="#ececec"))
        btn.bind("<Leave>", lambda _e: btn.configure(bg=CARD))
        return btn

    def _build_header(self) -> None:
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=_PAD, pady=(14, 6))
        tk.Label(top, text="Utility Suite", bg=BG, fg=TEXT, font=("Segoe UI", 17, "bold")).pack(side="left")
        self._ghost_button(top, "Refresh tools", self._refresh).pack(side="right")
        # Compact readiness readout; click for the install guide (was a
        # separate status label + a duplicate hint elsewhere).
        self.status_lbl = tk.Label(top, text="", bg=BG, fg=SUBTLE, font=("Segoe UI", 9), cursor="hand2")
        self.status_lbl.pack(side="right", padx=(0, 10))
        self.status_lbl.bind("<Button-1>", lambda _e: self._install_guide())

    def _build_tabs(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=(0, 12))
        self.tools_tab = tk.Frame(self.notebook, bg=BG)
        self.plugins_tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tools_tab, text="  Tools  ")
        self.notebook.add(self.plugins_tab, text="  Plugins  ")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._build_tools_tab(self.tools_tab)
        self._build_plugins_tab(self.plugins_tab)
        # Keyboard-first: Ctrl+F focuses search, Enter runs, Esc clears.
        self.bind_all("<Control-f>", self._focus_search)
        self.bind_all("<Control-F>", self._focus_search)
        self.bind_all("<Escape>", self._clear_filters)

    # ------------------------------------------------------------------- Tools
    def _build_tools_tab(self, parent) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        bar = tk.Frame(parent, bg=BG)
        bar.grid(row=0, column=0, sticky="ew", padx=(_PAD - 6), pady=(10, 8))
        bar.columnconfigure(1, weight=1)
        tk.Label(bar, text="Search", bg=BG, fg=SUBTLE, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            bar, textvariable=self.search_var, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat",
            font=("Segoe UI", 11), highlightbackground=BORDER, highlightcolor=ACCENT, highlightthickness=1,
        )
        self.search_entry.grid(row=0, column=1, sticky="ew", ipady=5)
        self.search_var.trace_add("write", lambda *_: self._filter_tools())
        self.search_entry.bind("<Return>", lambda _e: self._run())

        tk.Label(bar, text="Category", bg=BG, fg=SUBTLE, font=("Segoe UI", 9, "bold")).grid(
            row=0, column=2, padx=(12, 6)
        )
        self.category_var = tk.StringVar(value=ALL_CATEGORY)
        self.category_combo = ttk.Combobox(
            bar, textvariable=self.category_var, state="readonly", width=20, style="Win10.TCombobox",
            font=("Segoe UI", 10),
        )
        self.category_combo.grid(row=0, column=3)
        self.category_combo.bind("<<ComboboxSelected>>", lambda _e: self._filter_tools())

        # Default ON: unavailable tools stay visible (marked "Needs: …") rather
        # than being hidden, so the list never overstates what is ready.
        self.show_unavailable_var = tk.IntVar(value=1)
        Win10Check(
            bar, text="Show unavailable", variable=self.show_unavailable_var, command=self._filter_tools
        ).grid(row=0, column=4, padx=(14, 0))
        self._ghost_button(bar, "Clear", self._clear_filters).grid(row=0, column=5, padx=(12, 0))

        main = tk.Frame(parent, bg=BG)
        main.grid(row=1, column=0, sticky="nsew", padx=(_PAD - 6), pady=(0, 12))
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=4)
        main.rowconfigure(0, weight=1)

        # Left: the scannable tool table.
        list_card = self._card(main)
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        list_card.rowconfigure(0, weight=1)
        list_card.columnconfigure(0, weight=1)
        self.tool_tree = ttk.Treeview(
            list_card, columns=("name", "category", "status"), show="headings",
            selectmode="browse", style="Win10.Treeview",
        )
        for column, heading, width in (
            ("name", "Tool", 220),
            ("category", "Category", 130),
            ("status", "Status", 150),
        ):
            self.tool_tree.heading(column, text=heading, anchor="w")
            self.tool_tree.column(column, width=width, anchor="w", stretch=(column == "name"))
        tree_scroll = ttk.Scrollbar(list_card, orient="vertical", command=self.tool_tree.yview)
        self.tool_tree.configure(yscrollcommand=tree_scroll.set)
        self.tool_tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll.grid(row=0, column=1, sticky="ns")
        self.tool_tree.bind("<<TreeviewSelect>>", self._tool_selected)
        self.tool_tree.bind("<Return>", lambda _e: self._run())
        self.tool_tree.bind("<Double-1>", lambda _e: self._run())

        # Right: details + arguments + output.
        side = tk.Frame(main, bg=BG)
        side.grid(row=0, column=1, sticky="nsew")
        side.columnconfigure(0, weight=1)
        side.rowconfigure(2, weight=1)

        detail_card = self._card(side)
        detail_card.grid(row=0, column=0, sticky="ew")
        detail_card.columnconfigure(0, weight=1)
        self.detail_title = tk.Label(
            detail_card, text="Select a tool to see what it does.",
            bg=CARD, fg=TEXT, font=("Segoe UI", 12, "bold"), anchor="w", justify="left", wraplength=520,
        )
        self.detail_title.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 0))
        self.detail_meta = tk.Label(
            detail_card, text="", bg=CARD, fg=SUBTLE, font=("Segoe UI", 9), anchor="w", justify="left",
            wraplength=520,
        )
        self.detail_meta.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 10))

        def _rescale_wrap(event=None):
            # Keep text wrapping inside the pane instead of spilling out.
            width = max(300, detail_card.winfo_width() - 30)
            self.detail_title.configure(wraplength=width)
            self.detail_meta.configure(wraplength=width)

        detail_card.bind("<Configure>", _rescale_wrap)

        arg_row = tk.Frame(side, bg=BG)
        arg_row.grid(row=1, column=0, sticky="ew", pady=(8, 6))
        arg_row.columnconfigure(0, weight=1)
        self.args_var = tk.StringVar()
        args_entry = tk.Entry(
            arg_row, textvariable=self.args_var, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat",
            font=("Consolas", 10), highlightbackground=BORDER, highlightcolor=ACCENT, highlightthickness=1,
        )
        args_entry.grid(row=0, column=0, sticky="ew", ipady=6, padx=(0, 6))
        self._ghost_button(arg_row, "File…", self._insert_file_arg).grid(row=0, column=1, padx=2)
        self._ghost_button(arg_row, "Folder…", self._insert_folder_arg).grid(row=0, column=2, padx=2)
        self.run_btn = self._accent_button(arg_row, "Run", self._run)
        self.run_btn.grid(row=0, column=3, padx=(6, 0))

        out_card = self._card(side)
        out_card.grid(row=2, column=0, sticky="nsew")
        out_card.rowconfigure(1, weight=1)
        out_card.columnconfigure(0, weight=1)
        out_bar = tk.Frame(out_card, bg=CARD)
        out_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(out_bar, text="Output", bg=CARD, fg=SUBTLE, font=("Segoe UI", 9, "bold")).pack(
            side="left", padx=(10, 0), pady=6
        )
        self._ghost_button(out_bar, "Open folder…", self._open_folder).pack(side="right", padx=(4, 8), pady=3)
        self._ghost_button(out_bar, "Open…", self._open).pack(side="right", padx=4, pady=3)
        self._ghost_button(out_bar, "Preview…", self._preview).pack(side="right", padx=4, pady=3)
        self.output = tk.Text(
            out_card, bg="#fbfbfb", fg=TEXT, insertbackground=TEXT, relief="flat", wrap="word",
            font=("Consolas", 10), height=8,
        )
        out_scroll = ttk.Scrollbar(out_card, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=out_scroll.set)
        self.output.grid(row=1, column=0, sticky="nsew")
        out_scroll.grid(row=1, column=1, sticky="ns")

    # ----------------------------------------------------------------- Plugins
    def _build_plugins_tab(self, parent) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        bar = tk.Frame(parent, bg=BG)
        bar.grid(row=0, column=0, sticky="ew", padx=(_PAD - 6), pady=(10, 8))
        bar.columnconfigure(0, weight=1)
        self.plugins_count_lbl = tk.Label(
            bar, text="", bg=BG, fg=TEXT, font=("Segoe UI", 11, "bold")
        )
        self.plugins_count_lbl.grid(row=0, column=0, sticky="w")
        self._ghost_button(bar, "Install from file…", self._install_pack_from_file).grid(
            row=0, column=1, padx=(6, 4)
        )
        self._ghost_button(bar, "Refresh", self._load_manifest).grid(row=0, column=2, padx=(4, 0))

        list_card = self._card(parent)
        list_card.grid(row=1, column=0, sticky="nsew", padx=(_PAD - 6))
        list_card.rowconfigure(0, weight=1)
        list_card.columnconfigure(0, weight=1)
        self.plugins_canvas = tk.Canvas(list_card, bg=CARD, highlightthickness=0)
        self.plugins_canvas.grid(row=0, column=0, sticky="nsew")
        plugins_scroll = ttk.Scrollbar(list_card, orient="vertical", command=self.plugins_canvas.yview)
        plugins_scroll.grid(row=0, column=1, sticky="ns")
        self.plugins_canvas.configure(yscrollcommand=plugins_scroll.set)
        self.plugins_holder = tk.Frame(self.plugins_canvas, bg=CARD)
        self._plugins_window = self.plugins_canvas.create_window((0, 0), window=self.plugins_holder, anchor="nw")
        self.plugins_holder.bind(
            "<Configure>",
            lambda _e: self.plugins_canvas.configure(
                scrollregion=self.plugins_canvas.bbox("all") or (0, 0, 0, 0)
            ),
        )
        self.plugins_canvas.bind(
            "<Configure>", lambda e: self.plugins_canvas.itemconfigure(self._plugins_window, width=max(e.width, 1))
        )

        foot = tk.Frame(parent, bg=BG)
        foot.grid(row=2, column=0, sticky="ew", padx=(_PAD - 6), pady=(8, 12))
        foot.columnconfigure(0, weight=1)
        self.plugins_status = tk.Label(
            foot, text="", bg=BG, fg=SUBTLE, font=("Segoe UI", 9), anchor="w", justify="left"
        )
        self.plugins_status.grid(row=0, column=0, sticky="ew")
        self.plugins_progress = ttk.Progressbar(
            foot, mode="determinate", maximum=100, style="Win10.Horizontal.TProgressbar"
        )
        self.plugins_progress.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        self._set_plugin_status("Open this tab to load the pack catalogue.")
        self._render_plugins()

    # -------------------------------------------------------------- tool data
    def _populate(self) -> None:
        categories = sorted(self.registry.list_categories().keys())
        values = [ALL_CATEGORY, *categories]
        self.category_combo["values"] = values
        if self.category_var.get() not in values:
            self.category_var.set(ALL_CATEGORY)
        total = len(self.registry.tools)
        available = sum(1 for tool in self.registry.tools.values() if tool["available"])
        self.status_lbl.configure(text=f"{available}/{total} ready — install guide")
        self._filter_tools()

    def _matching_tools(self) -> list[dict[str, Any]]:
        query = self.search_var.get().strip()
        tools = self.registry.search(query) if query else list(self.registry.tools.values())
        category = self.category_var.get()
        if category and category != ALL_CATEGORY:
            tools = [tool for tool in tools if tool.get("category") == category]
        if not self.show_unavailable_var.get():
            tools = [tool for tool in tools if tool["available"]]
        return sorted(tools, key=lambda tool: str(tool.get("name", "")).lower())

    def _filter_tools(self) -> None:
        previous = self._selected
        tools = self._matching_tools()
        self.tool_tree.delete(*self.tool_tree.get_children())
        self._tools_by_iid = {}
        for tool in tools:
            status = "Ready" if tool["available"] else "Needs: " + ", ".join(tool["missing_dependencies"])
            iid = self.tool_tree.insert("", "end", values=(tool["name"], tool.get("category", ""), status))
            self._tools_by_iid[iid] = tool
        # Keep the current tool selected when it survives the new filter,
        # otherwise fall back to the first row so the details pane is never blank.
        target = next((iid for iid, tool in self._tools_by_iid.items() if tool is previous), None)
        if target is None and tools:
            target = self.tool_tree.get_children()[0]
        if target is not None:
            self.tool_tree.selection_set(target)
            self.tool_tree.focus(target)
            self._tool_selected()
        else:
            self._selected = None
            self.detail_title.configure(text="No tools match this filter.")
            self.detail_meta.configure(text="Try clearing the search or picking another category.")

    def _tool_selected(self, _event=None) -> None:
        selection = self.tool_tree.selection()
        if not selection:
            return
        tool = self._tools_by_iid.get(selection[0])
        if not tool:
            return
        # Only wipe the argument box when the *tool* actually changes, so
        # re-filtering the list does not discard arguments the user typed.
        changed = tool is not self._selected
        self._selected = tool
        self.detail_title.configure(text=f"{tool['name']}   [{tool['cli_command']}]")
        deps = ", ".join(tool.get("dependencies", []) or [])
        if tool["available"]:
            status = "Ready"
        else:
            status = "Needs install — " + "; ".join(
                f"{dep}: {download_hint(dep)}" for dep in tool["missing_dependencies"]
            )
        meta = f"{tool.get('description', '')}\nCategory: {tool.get('category', '')}   •   Status: {status}"
        if deps and tool["available"]:
            meta += f"   •   Optional deps: {deps}"
        self.detail_meta.configure(text=meta)
        if changed:
            self.args_var.set("")

    def _clear_filters(self, _event=None):
        self.search_var.set("")
        self.category_var.set(ALL_CATEGORY)
        self._filter_tools()
        return "break"

    def _focus_search(self, _event=None):
        self.search_entry.focus_set()
        return "break"

    # ------------------------------------------------------------- install guide
    def _install_guide(self) -> None:
        """Show exactly what to download so unavailable tools turn green."""
        missing: dict[str, int] = {}
        for tool in self.registry.tools.values():
            if not tool["available"]:
                for dep in tool["missing_dependencies"]:
                    missing[dep] = missing.get(dep, 0) + 1
        win32 = sys.platform == "win32"
        lines = []
        for dep, count in sorted(missing.items(), key=lambda kv: (-kv[1], kv[0].lower())):
            hint = download_hint(dep)
            tag = " [Windows only]" if hint.startswith("Built into Windows") and not win32 else ""
            lines.append(f"{dep} ({count} tool{'s' if count != 1 else ''}){tag}\n    -> {hint}")
        body = "\n\n".join(lines) or "Nothing is missing — every tool on this system is ready."

        dialog = tk.Toplevel(self)
        dialog.title("Install missing dependencies")
        dialog.geometry("680x520")
        dialog.configure(bg=BG)
        tk.Label(
            dialog, text="Download / install guide", bg=BG, fg=TEXT, font=("Segoe UI", 14, "bold"), anchor="w"
        ).pack(fill="x", padx=18, pady=(14, 4))
        tk.Label(
            dialog,
            text=(
                "Tools whose optional dependency is missing are marked 'Needs: …' in the tool list.\n"
                "Install anything below, then press 'Refresh tools' — it turns Ready automatically.\n"
                "After installing a pip package, restart Utility Suite so the new import is picked up."
            ),
            bg=BG, fg=SUBTLE, font=("Segoe UI", 9), justify="left", anchor="w",
        ).pack(fill="x", padx=18, pady=(0, 8))
        card = self._card(dialog, padx=2, pady=2)
        card.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        text = tk.Text(card, wrap="word", font=("Consolas", 10), relief="flat", bg="#fbfbfb", height=10)
        scroll = ttk.Scrollbar(card, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        text.insert("1.0", body)
        text.configure(state="disabled")
        row = tk.Frame(dialog, bg=BG)
        row.pack(fill="x", padx=18, pady=(0, 16))

        def copy_all():
            self.clipboard_clear()
            self.clipboard_append(body)

        self._ghost_button(row, "Copy list", copy_all).pack(side="left", padx=(0, 8))
        self._accent_button(row, "Refresh tools", lambda: (dialog.destroy(), self._refresh())).pack(side="left")

    # -------------------------------------------------------------- arguments
    def _ask_file(self, **kw) -> str | None:
        if filedialog is None:
            self._error("File picker unavailable", "This build has no file dialog; type the path instead.")
            return None
        try:
            return filedialog.askopenfilename(**kw) or None
        except Exception as exc:
            self._error("File picker failed", str(exc))
            return None

    def _ask_dir(self, **kw) -> str | None:
        if filedialog is None:
            self._error("File picker unavailable", "This build has no file picker; type the path instead.")
            return None
        try:
            return filedialog.askdirectory(**kw) or None
        except Exception as exc:
            self._error("File picker failed", str(exc))
            return None

    def _insert_file_arg(self) -> None:
        path = self._ask_file(title="Choose a file")
        if path:
            self._append_arg(path)

    def _insert_folder_arg(self) -> None:
        path = self._ask_dir(title="Choose a folder")
        if path:
            self._append_arg(path)

    def _append_arg(self, path: str) -> None:
        quoted = f'"{path}"' if " " in path else path
        current = self.args_var.get().strip()
        self.args_var.set(f"{current} {quoted}".strip())

    def _first_path_in_args(self) -> str | None:
        """Return the first argument that looks like an existing path, if any."""
        raw = self.args_var.get().strip()
        if not raw:
            return None
        try:
            tokens = shlex.split(raw, posix=(os.name != "nt"))
        except ValueError:
            tokens = raw.split()
        for token in tokens:
            if Path(token).exists():
                return token
        return None

    # ------------------------------------------------------------------ actions
    def _run(self) -> None:
        if not self._selected:
            self._notify("Utility Suite", "Select a tool first.")
            return
        command = self._selected["cli_command"]
        if command in DESTRUCTIVE_TOOLS and not self._confirm(
            "Confirm action",
            f"'{self._selected['name']}' can permanently delete or overwrite data.\nContinue?",
        ):
            return
        self.output.delete("1.0", tk.END)
        args = shlex.split(self.args_var.get(), posix=(os.name != "nt")) if self.args_var.get().strip() else []

        def worker():
            try:
                self.registry.run_tool(command, args, output=self._queue.put)
            finally:
                self._queue.put("__done__")

        self.run_btn.configure(text="Running…", cursor="watch")
        threading.Thread(target=worker, daemon=True).start()

    def _drain_output(self) -> None:
        done = False
        try:
            while True:
                line = self._queue.get_nowait()
                if line == "__done__":
                    done = True
                    continue
                self.output.insert(tk.END, line + "\n")
                self.output.see(tk.END)
        except queue.Empty:
            pass
        if done:
            self.run_btn.configure(text="Run", cursor="hand2")
        self.after(80, self._drain_output)

    def _preview(self) -> None:
        path = self._ask_file(title="Choose a file to preview")
        if not path:
            return
        try:
            text = preview_file(path)
        except Exception as exc:
            self._error("Preview failed", str(exc))
            return
        self.output.delete("1.0", tk.END)
        self.output.insert("1.0", text)

    def _open(self) -> None:
        path = self._ask_file(title="Choose a file to open")
        if not path:
            return
        try:
            open_with_default(path)
        except Exception as exc:
            self._error("Open failed", str(exc))

    def _open_folder(self) -> None:
        """Open a folder in the system file manager.

        Prefers the folder of a path already typed in the arguments box (that is
        usually where a tool writes its output); otherwise asks for one.
        """
        typed = self._first_path_in_args()
        folder = None
        if typed:
            candidate = Path(typed)
            folder = str(candidate.parent if candidate.is_file() else candidate)
        if not folder:
            folder = self._ask_dir(title="Choose a folder to open")
        if not folder:
            return
        try:
            open_with_default(folder)
        except Exception as exc:
            self._error("Open folder failed", str(exc))

    def _refresh(self) -> None:
        """Rebuild the registry (via the app's own callback) and repopulate."""
        if self.on_refresh:
            self.registry = self.on_refresh()
        self._selected = None
        self._populate()
        self.output.insert(tk.END, "Tool inventory refreshed.\n")

    # ------------------------------------------------------------------ dialogs
    def _notify(self, title: str, message: str) -> None:
        if messagebox is None:
            return
        try:
            messagebox.showinfo(title, message)
        except Exception:
            pass

    def _error(self, title: str, message: str) -> None:
        if messagebox is not None:
            try:
                messagebox.showerror(title, message)
                return
            except Exception:
                pass
        try:
            self.output.insert(tk.END, f"{message}\n")
        except Exception:
            pass

    def _confirm(self, title: str, message: str) -> bool:
        # Without a dialog we cannot obtain consent, so refuse rather than act.
        if messagebox is None:
            return False
        try:
            return bool(messagebox.askyesno(title, message))
        except Exception:
            return False

    # ----------------------------------------------------------------- Plugins
    def _on_tab_changed(self, _event=None) -> None:
        try:
            selected = self.notebook.index(self.notebook.select())
        except Exception:
            return
        if selected == 1 and not self._manifest_loaded and not self._manifest_loading:
            self._load_manifest()

    def _set_plugin_status(self, message: str) -> None:
        self.plugins_status.configure(text=message)

    def _load_manifest(self) -> None:
        """Fetch the remote catalogue in the background (never blocks the UI)."""
        if self._manifest_loading:
            return
        self._manifest_loading = True
        self._set_plugin_status("Loading plugin catalogue…")

        def worker():
            self._plugin_queue.put(("manifest", plugin_packs.fetch_manifest()))

        threading.Thread(target=worker, daemon=True).start()

    def _render_plugins(self) -> None:
        for child in self.plugins_holder.winfo_children():
            child.destroy()
        installed = {pack.name: pack for pack in plugin_packs.list_installed()}
        catalogue = {info.name: info for info in self._available}

        for info in self._available:
            self._plugin_row(self.plugins_holder, info, installed.get(info.name))
        for name, pack in sorted(installed.items()):
            if name not in catalogue:
                self._plugin_row(self.plugins_holder, PackInfo(name=name, title=name, size=pack.size), pack)

        if not self._available and not installed:
            tk.Label(
                self.plugins_holder, bg=CARD, fg=SUBTLE, font=("Segoe UI", 10),
                text="No packs yet. Press Refresh to browse the catalogue, or install one from a file.",
                anchor="w",
            ).pack(fill="x", padx=12, pady=16)

        count = len(installed)
        if self._available:
            self.plugins_count_lbl.configure(text=f"Installed {count} of {len(self._available)} packs")
        else:
            self.plugins_count_lbl.configure(text=f"Installed {count} pack{'s' if count != 1 else ''}")

    def _plugin_row(self, parent, info: PackInfo, installed) -> None:
        """Render one pack row: title, facts, state, and its action button."""
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", padx=10, pady=2)
        row.columnconfigure(1, weight=1)

        facts = [info.name]
        if info.tools:
            facts.append(f"{info.tools} tools")
        if info.size:
            facts.append(_human_size(info.size))
        if info.description:
            facts.append(info.description)

        tk.Label(row, text=info.title or info.name, bg=CARD, fg=TEXT, font=("Segoe UI", 10, "bold"),
                 anchor="w").grid(row=0, column=0, sticky="w", pady=6)
        tk.Label(row, text="   ".join(facts), bg=CARD, fg=SUBTLE, font=("Segoe UI", 9), anchor="w").grid(
            row=0, column=1, sticky="w", padx=(12, 12)
        )

        state_text, state_color, action = self._pack_state(info, installed)
        tk.Label(row, text=state_text, bg=CARD, fg=state_color, font=("Segoe UI", 9, "bold")).grid(
            row=0, column=2, padx=(0, 10)
        )
        if action == "download":
            self._accent_button(row, "Download", lambda i=info: self._download_pack(i)).grid(row=0, column=3)
        elif action == "remove":
            self._ghost_button(row, "Remove", lambda n=info.name: self._remove_pack(n)).grid(row=0, column=3)

    @staticmethod
    def _pack_state(info: PackInfo, installed) -> tuple[str, str, str]:
        """Return ``(state_text, colour, action)`` for a pack row."""
        if installed is None:
            return "Not installed", SUBTLE, "download"
        if info.size and installed.size and info.size != installed.size:
            return "Update available", ACCENT, "download"
        return "Installed", OK, "remove"

    def _download_pack(self, info: PackInfo) -> None:
        if self._plugin_busy:
            return
        self._plugin_busy = True
        self._set_plugin_status(f"Downloading {info.title or info.name}…")
        self.plugins_progress.configure(value=0)

        def progress(done: int, total: int) -> None:
            self._plugin_queue.put(("progress", done, total))

        def worker():
            result = plugin_packs.download_pack(
                info.name, progress=progress, file=info.file, expected_size=info.size
            )
            self._plugin_queue.put(("download_done", result))

        threading.Thread(target=worker, daemon=True).start()

    def _remove_pack(self, name: str) -> None:
        if self._plugin_busy:
            return
        if not self._confirm("Remove pack", f"Remove the '{name}' plugin pack?\nIts tools will disappear."):
            return
        try:
            result = plugin_packs.remove_pack(name)
        except plugin_packs.PluginInstallerError as exc:
            self._set_plugin_status(f"Could not remove {name}: {exc}")
            return
        if result.ok:
            self._set_plugin_status(f"Removed {name}.")
            self._refresh()
        else:
            self._set_plugin_status(f"Could not remove {name}: {result.error}")
        self._render_plugins()

    def _install_pack_from_file(self) -> None:
        path = self._ask_file(
            title="Choose a plugin pack",
            filetypes=[("Plugin packs", "*.zip *.py"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            result = plugin_packs.install_from_file(path)
        except plugin_packs.PluginInstallerError as exc:
            self._set_plugin_status(f"Could not install: {exc}")
            return
        if result.ok:
            self._set_plugin_status(f"Installed {result.name}.")
            self._refresh()
        else:
            self._set_plugin_status(f"Could not install: {result.error}")
        self._render_plugins()

    def _drain_plugins(self) -> None:
        try:
            while True:
                self._handle_plugin_event(self._plugin_queue.get_nowait())
        except queue.Empty:
            pass
        self.after(120, self._drain_plugins)

    def _handle_plugin_event(self, event: tuple) -> None:
        kind = event[0]
        if kind == "progress":
            self._update_progress(event[1], event[2])
        elif kind == "manifest":
            result = event[1]
            self._manifest_loading = False
            self._manifest_loaded = True
            if result.ok:
                self._available = result.packs
                self._set_plugin_status(f"Catalogue loaded — {len(result.packs)} packs available.")
            else:
                self._available = []
                self._set_plugin_status(
                    f"Offline — {result.error}. Installed packs still work; try Refresh when online."
                )
            self._render_plugins()
        elif kind == "download_done":
            result = event[1]
            self._plugin_busy = False
            self.plugins_progress.configure(value=0)
            if result.ok:
                self._set_plugin_status(f"Installed {result.name} ({_human_size(result.bytes_written)}).")
                self._refresh()
            else:
                self._set_plugin_status(f"Download failed: {result.error}")
            self._render_plugins()

    def _update_progress(self, done: int, total: int) -> None:
        if total > 0:
            self.plugins_progress.configure(value=min(100.0, done * 100.0 / total))
            self._set_plugin_status(
                f"Downloading… {done * 100 // total}% ({_human_size(done)} of {_human_size(total)})"
            )
        else:
            # No Content-Length: pulse so the user still sees activity.
            self._progress_pulse = (self._progress_pulse + 7) % 100
            self.plugins_progress.configure(value=self._progress_pulse)
            self._set_plugin_status(f"Downloading… {_human_size(done)}")
