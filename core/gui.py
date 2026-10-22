"""Desktop UI for Utility Suite.

Layout
------
One toolbar, two dense tabs, one primary action per screen:

* **Tools** — a search/filter bar over a scannable tool table
  (name + category + state), a details pane, an argument row with the primary
  *Run* action, and live output.  Argument pickers (``File…`` / ``Folder…``)
  and the output actions (``Preview…`` / ``Open…`` / ``Open folder…``) are shown
  **only when the selected tool's metadata says they apply** — a tool with no
  metadata keeps the old behaviour (every control is shown).
* **Packs** — every pack as a row with its title, tool count, how many tools are
  runnable right now, an *Enabled* toggle, and a *Get dependencies* action when
  something is missing.  There is no download of packs: all 45 packs are built
  into the application.

The window title, the app name/branding and the colour palette are unchanged
from the shipped build.  ``tkinter`` is optional — importing this module without
it is handled by :mod:`core.cli`.
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

from . import dependencies as deps
from .capability_checker import download_hint
from .preview import open_with_default, preview_file
from .tool_registry import ToolRegistry

try:  # single source of truth for the version string
    from . import __version__ as APP_VERSION
except Exception:  # pragma: no cover - defensive fallback
    APP_VERSION = "3.0.6"

# Tools that can delete/overwrite data or otherwise irreversibly change the
# system.  This is the legacy list; tool metadata (``destructive: true``) is the
# preferred source and this set is kept as a fallback for tools without it.
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

# ---- Shipped palette (unchanged from the released build) -------------------
BG = "#f3f3f3"          # window background
CARD = "#ffffff"        # card / surface
BORDER = "#e1e1e1"      # hairline borders
TEXT = "#191919"
SUBTLE = "#5d5d5d"
ACCENT = "#0078d4"      # Win10 default blue
ACCENT_HOVER = "#1a86d9"
CHIP_BORDER = "#bebebe"
OK = "#107c10"          # "ready / installed" green

ALL_CATEGORY = "All"
_PAD = 16               # single horizontal gutter used everywhere


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
    """The application window: a Tools tab and a Packs tab."""

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
        self.minsize(880, 560)
        self.configure(bg=BG)

        self._selected: dict[str, Any] | None = None
        self._queue: queue.Queue[str] = queue.Queue()
        self._tools_by_iid: dict[str, dict[str, Any]] = {}
        # Which conditional controls are currently visible (also asserted by the
        # headless harness, which cannot measure geometry).
        self.control_state: dict[str, bool] = {
            "file": True,
            "folder": True,
            "preview": True,
            "open": True,
            "open_folder": True,
        }

        self._build_style()
        self._build_header()
        self._build_tabs()
        self._populate()
        self._render_packs()
        self.search_entry.focus_set()
        self.after(80, self._drain_output)

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

    @staticmethod
    def _set_visible(widget, visible: bool, pack_opts: dict | None = None) -> None:
        """Show/hide a widget without destroying it.

        ``pack_opts`` is given for pack-managed widgets (the output actions):
        a widget must be shown/hidden with the geometry manager that owns it,
        so grid-managed widgets use ``grid``/``grid_remove`` and pack-managed
        ones are re-packed with their original options.
        """
        try:
            if pack_opts is not None:
                if visible:
                    widget.pack(**pack_opts)
                else:
                    widget.pack_forget()
            elif visible:
                widget.grid()
            else:
                widget.grid_remove()
        except Exception:  # pragma: no cover - defensive
            pass

    def _build_header(self) -> None:
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=_PAD, pady=(14, 6))
        tk.Label(top, text="Utility Suite", bg=BG, fg=TEXT, font=("Segoe UI", 17, "bold")).pack(side="left")
        self._ghost_button(top, "Refresh", self._refresh).pack(side="right")
        # Compact readiness readout; click for the dependency guide.
        self.status_lbl = tk.Label(top, text="", bg=BG, fg=SUBTLE, font=("Segoe UI", 9), cursor="hand2")
        self.status_lbl.pack(side="right", padx=(0, 10))
        self.status_lbl.bind("<Button-1>", lambda _e: self._install_guide())

    def _build_tabs(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=(0, 12))
        self.tools_tab = tk.Frame(self.notebook, bg=BG)
        self.packs_tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tools_tab, text="  Tools  ")
        self.notebook.add(self.packs_tab, text="  Packs  ")
        self._build_tools_tab(self.tools_tab)
        self._build_packs_tab(self.packs_tab)
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
            ("status", "State", 150),
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

        detail = tk.Frame(side, bg=BG)
        detail.grid(row=0, column=0, sticky="ew")
        detail.columnconfigure(0, weight=1)
        self.detail_title = tk.Label(
            detail, text="Select a tool to see what it does.",
            bg=BG, fg=TEXT, font=("Segoe UI", 12, "bold"), anchor="w", justify="left", wraplength=520,
        )
        self.detail_title.grid(row=0, column=0, sticky="ew", padx=2, pady=(2, 0))
        self.detail_meta = tk.Label(
            detail, text="", bg=BG, fg=SUBTLE, font=("Segoe UI", 9), anchor="w", justify="left",
            wraplength=520,
        )
        self.detail_meta.grid(row=1, column=0, sticky="ew", padx=2, pady=(4, 8))

        def _rescale_wrap(event=None):
            # Keep text wrapping inside the pane instead of spilling out.
            width = max(300, side.winfo_width() - 30)
            self.detail_title.configure(wraplength=width)
            self.detail_meta.configure(wraplength=width)

        side.bind("<Configure>", _rescale_wrap)

        arg_row = tk.Frame(side, bg=BG)
        arg_row.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        arg_row.columnconfigure(0, weight=1)
        self.args_var = tk.StringVar()
        self.args_entry = tk.Entry(
            arg_row, textvariable=self.args_var, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat",
            font=("Consolas", 10), highlightbackground=BORDER, highlightcolor=ACCENT, highlightthickness=1,
        )
        self.args_entry.grid(row=0, column=0, sticky="ew", ipady=6, padx=(0, 6))
        self.file_btn = self._ghost_button(arg_row, "File…", self._insert_file_arg)
        self.file_btn.grid(row=0, column=1, padx=2)
        self.folder_btn = self._ghost_button(arg_row, "Folder…", self._insert_folder_arg)
        self.folder_btn.grid(row=0, column=2, padx=2)
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
        # The output actions are pack-managed; remember their pack options so
        # they can be hidden and shown again by _set_visible.
        self._output_pack_opts = {
            "open_folder": {"side": "right", "padx": (4, 8), "pady": 3},
            "open": {"side": "right", "padx": 4, "pady": 3},
            "preview": {"side": "right", "padx": 4, "pady": 3},
        }
        self.open_folder_btn = self._ghost_button(out_bar, "Open folder…", self._open_folder)
        self.open_folder_btn.pack(**self._output_pack_opts["open_folder"])
        self.open_btn = self._ghost_button(out_bar, "Open…", self._open)
        self.open_btn.pack(**self._output_pack_opts["open"])
        self.preview_btn = self._ghost_button(out_bar, "Preview…", self._preview)
        self.preview_btn.pack(**self._output_pack_opts["preview"])
        self.output = tk.Text(
            out_card, bg="#fbfbfb", fg=TEXT, insertbackground=TEXT, relief="flat", wrap="word",
            font=("Consolas", 10), height=8,
        )
        out_scroll = ttk.Scrollbar(out_card, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=out_scroll.set)
        self.output.grid(row=1, column=0, sticky="nsew")
        out_scroll.grid(row=1, column=1, sticky="ns")

    # ------------------------------------------------------------------- Packs
    def _build_packs_tab(self, parent) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        bar = tk.Frame(parent, bg=BG)
        bar.grid(row=0, column=0, sticky="ew", padx=(_PAD - 6), pady=(10, 8))
        bar.columnconfigure(0, weight=1)
        self.packs_count_lbl = tk.Label(bar, text="", bg=BG, fg=TEXT, font=("Segoe UI", 11, "bold"))
        self.packs_count_lbl.grid(row=0, column=0, sticky="w")
        self._ghost_button(bar, "Enable all", self._enable_all_packs).grid(row=0, column=1, padx=(6, 4))
        self._ghost_button(bar, "Dependency guide", self._install_guide).grid(row=0, column=2, padx=(4, 0))

        list_card = self._card(parent)
        list_card.grid(row=1, column=0, sticky="nsew", padx=(_PAD - 6))
        list_card.rowconfigure(0, weight=1)
        list_card.columnconfigure(0, weight=1)
        self.packs_canvas = tk.Canvas(list_card, bg=CARD, highlightthickness=0)
        self.packs_canvas.grid(row=0, column=0, sticky="nsew")
        packs_scroll = ttk.Scrollbar(list_card, orient="vertical", command=self.packs_canvas.yview)
        packs_scroll.grid(row=0, column=1, sticky="ns")
        self.packs_canvas.configure(yscrollcommand=packs_scroll.set)
        self.packs_holder = tk.Frame(self.packs_canvas, bg=CARD)
        self._packs_window = self.packs_canvas.create_window((0, 0), window=self.packs_holder, anchor="nw")
        self.packs_holder.bind(
            "<Configure>",
            lambda _e: self.packs_canvas.configure(scrollregion=self.packs_canvas.bbox("all") or (0, 0, 0, 0)),
        )
        self.packs_canvas.bind(
            "<Configure>", lambda e: self.packs_canvas.itemconfigure(self._packs_window, width=max(e.width, 1))
        )

        foot = tk.Frame(parent, bg=BG)
        foot.grid(row=2, column=0, sticky="ew", padx=(_PAD - 6), pady=(8, 12))
        foot.columnconfigure(0, weight=1)
        self.packs_status = tk.Label(
            foot, text="", bg=BG, fg=SUBTLE, font=("Segoe UI", 9), anchor="w", justify="left"
        )
        self.packs_status.grid(row=0, column=0, sticky="ew")

    # -------------------------------------------------------------- tool data
    def _populate(self) -> None:
        categories = sorted(self.registry.list_categories().keys())
        values = [ALL_CATEGORY, *categories]
        self.category_combo["values"] = values
        if self.category_var.get() not in values:
            self.category_var.set(ALL_CATEGORY)
        total = len(self.registry.enabled_tools())
        available = sum(1 for tool in self.registry.enabled_tools() if tool["available"])
        self.status_lbl.configure(text=f"{available}/{total} ready — dependency guide")
        self._filter_tools()

    def _matching_tools(self) -> list[dict[str, Any]]:
        query = self.search_var.get().strip()
        tools = self.registry.search(query) if query else self.registry.enabled_tools()
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
            self.detail_meta.configure(text="Try clearing the search, picking another category, or enabling a pack.")
            self._apply_tool_controls(None)

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
        self.detail_meta.configure(text=self._describe_tool(tool))
        if changed:
            self.args_var.set("")
        self._apply_tool_controls(tool)

    def _describe_tool(self, tool: dict[str, Any]) -> str:
        deps_ = ", ".join(tool.get("dependencies", []) or [])
        if tool["available"]:
            status = "Ready"
        else:
            status = "Needs install — " + "; ".join(
                f"{dep}: {download_hint(dep)}" for dep in tool["missing_dependencies"]
            )
        meta = f"{tool.get('description', '')}\nCategory: {tool.get('category', '')}   •   State: {status}"
        if deps_ and tool["available"]:
            meta += f"   •   Optional deps: {deps_}"
        extra = []
        if tool.get("destructive"):
            extra.append("changes or deletes data — you will be asked to confirm")
        accepts = tool.get("accepts")
        if accepts == "file":
            extra.append("takes a file")
        elif accepts == "folder":
            extra.append("takes a folder")
        elif accepts == "none":
            extra.append("needs no arguments")
        if extra:
            meta += "\n" + "   •   ".join(extra)
        return meta

    def _apply_tool_controls(self, tool: dict[str, Any] | None) -> None:
        """Show only the controls that apply to the selected tool.

        A tool with no ``accepts``/``produces`` metadata keeps the previous
        behaviour: every control is shown.
        """
        accepts = tool.get("accepts") if tool else None
        produces = tool.get("produces") if tool else None
        show_file = accepts in (None, "file")
        show_folder = accepts in (None, "folder")
        show_output_actions = produces in (None, "file")
        self.control_state = {
            "file": show_file,
            "folder": show_folder,
            "preview": show_output_actions,
            "open": show_output_actions,
            "open_folder": show_output_actions,
        }
        self._set_visible(self.file_btn, show_file)
        self._set_visible(self.folder_btn, show_folder)
        # Re-pack in the original order so the buttons keep their positions.
        self._set_visible(self.open_folder_btn, show_output_actions, self._output_pack_opts["open_folder"])
        self._set_visible(self.open_btn, show_output_actions, self._output_pack_opts["open"])
        self._set_visible(self.preview_btn, show_output_actions, self._output_pack_opts["preview"])

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
        missing = deps.missing_dependencies(self.registry.enabled_tools())
        if not missing:
            self._notify("Dependencies", "Nothing is missing — every tool in your enabled packs is ready.")
            return
        dialog = tk.Toplevel(self)
        dialog.title("Missing dependencies")
        dialog.geometry("700x540")
        dialog.configure(bg=BG)
        tk.Label(
            dialog, text="Download / install guide", bg=BG, fg=TEXT, font=("Segoe UI", 14, "bold"), anchor="w"
        ).pack(fill="x", padx=18, pady=(14, 4))
        tk.Label(
            dialog,
            text=(
                "Tools whose optional dependency is missing are marked 'Needs: …' in the tool list.\n"
                "Install anything below, then press 'Refresh' — it turns Ready automatically.\n"
                "Prefer not to install? Open the Packs tab and disable that pack instead."
            ),
            bg=BG, fg=SUBTLE, font=("Segoe UI", 9), justify="left", anchor="w",
        ).pack(fill="x", padx=18, pady=(0, 8))
        card = self._card(dialog)
        card.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        text = tk.Text(card, wrap="word", font=("Consolas", 10), relief="flat", bg="#fbfbfb", height=10)
        scroll = ttk.Scrollbar(card, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)
        body = self._install_guide_text(missing)
        text.insert("1.0", body)
        text.configure(state="disabled")
        row = tk.Frame(dialog, bg=BG)
        row.pack(fill="x", padx=18, pady=(0, 16))

        def copy_all():
            try:
                self.clipboard_clear()
                self.clipboard_append(body)
            except Exception:
                pass

        self._ghost_button(row, "Copy list", copy_all).pack(side="left", padx=(0, 8))
        self._accent_button(row, "Refresh", lambda: (dialog.destroy(), self._refresh())).pack(side="left")

    def _install_guide_text(self, missing: dict[str, int]) -> str:
        lines = []
        for dep, count in sorted(missing.items(), key=lambda kv: (-kv[1], kv[0].lower())):
            plan = deps.install_plan(dep)
            packs = deps.packs_using(dep, self.registry.tools.values())
            head = f"{dep} ({count} tool{'s' if count != 1 else ''})"
            if packs:
                head += f"  — packs: {', '.join(packs)}"
            lines.append(head)
            if plan["known"]:
                lines.append(f"    {plan['summary']}")
                first = plan["steps"][0] if plan["steps"] else None
                if first:
                    if first["command"]:
                        lines.append(f"    -> {first['command']}")
                    elif first["url"]:
                        lines.append(f"    -> {first['url']}")
                    else:
                        lines.append(f"    -> {first['label']}")
            else:
                lines.append(f"    -> {download_hint(dep)}")
            lines.append("")
        return "\n".join(lines).strip()

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
        destructive = bool(self._selected.get("destructive")) or command in DESTRUCTIVE_TOOLS
        if destructive and not self._confirm(
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
        """Rebuild the registry (via the app's own callback) and repopulate.

        This is the single refresh path: enabling or disabling a pack calls it,
        so the preference takes effect without a restart.
        """
        if self.on_refresh:
            self.registry = self.on_refresh()
        self._selected = None
        self._populate()
        self._render_packs()
        try:
            self.output.insert(tk.END, "Tool inventory refreshed.\n")
        except Exception:
            pass

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

    # ------------------------------------------------------------------- Packs
    def _missing_for_pack(self, pack: str) -> list[str]:
        """Dependencies that at least one tool of ``pack`` still needs."""
        missing: list[str] = []
        for tool in self.registry.tools.values():
            if tool.get("pack") == pack:
                for dep in tool.get("missing_dependencies", []) or []:
                    if dep not in missing:
                        missing.append(dep)
        return missing

    def _render_packs(self) -> None:
        for child in self.packs_holder.winfo_children():
            child.destroy()
        summaries = self.registry.pack_summaries()
        for summary in summaries:
            self._pack_row(self.packs_holder, summary)
        enabled = sum(1 for s in summaries if s["enabled"])
        self.packs_count_lbl.configure(text=f"{enabled} of {len(summaries)} packs enabled")
        if not summaries:
            tk.Label(
                self.packs_holder, bg=CARD, fg=SUBTLE, font=("Segoe UI", 10),
                text="No packs found.", anchor="w",
            ).pack(fill="x", padx=12, pady=16)

    def _pack_row(self, parent, summary: dict[str, Any]) -> None:
        """Render one pack row: title, facts, state, toggle and (if needed) deps."""
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", padx=10, pady=2)
        row.columnconfigure(1, weight=1)

        missing = self._missing_for_pack(summary["name"])
        facts = f"{summary['name']}   •   {summary['tool_count']} tools   •   {summary['runnable']} runnable"
        if missing:
            facts += f"   •   needs {', '.join(missing)}"

        tk.Label(
            row, text=summary["title"], bg=CARD, fg=TEXT, font=("Segoe UI", 10, "bold"), anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=6)
        tk.Label(row, text=facts, bg=CARD, fg=SUBTLE, font=("Segoe UI", 9), anchor="w").grid(
            row=0, column=1, sticky="w", padx=(12, 12)
        )
        state_text = "Enabled" if summary["enabled"] else "Disabled"
        state_color = OK if summary["enabled"] else SUBTLE
        tk.Label(row, text=state_text, bg=CARD, fg=state_color, font=("Segoe UI", 9, "bold")).grid(
            row=0, column=2, padx=(0, 10)
        )

        var = tk.IntVar(master=self, value=1 if summary["enabled"] else 0)

        def on_toggle(name=summary["name"], variable=var):
            self._toggle_pack(name, bool(variable.get()))

        Win10Check(row, text="", variable=var, command=on_toggle).grid(row=0, column=3, padx=(0, 8))

        if missing:
            self._ghost_button(row, "Get dependencies", lambda n=summary["name"]: self._show_pack_deps(n)).grid(
                row=0, column=4
            )

    def _toggle_pack(self, name: str, enabled: bool) -> None:
        """Handle a pack toggle; prompt when enabling a pack with missing deps."""
        if enabled:
            missing = self._missing_for_pack(name)
            if missing:
                decision = self._prompt_enable_missing(name, missing)
                if decision == "keep_disabled":
                    self._set_packs_status(
                        f"'{name}' left disabled. Its tools need: {', '.join(missing)}."
                    )
                    self._render_packs()
                    return
                # "download" — enable it (tools show as 'Needs: …') and open the guide.
                self.registry.set_pack_enabled(name, True)
                self._refresh()
                self._show_pack_deps(name)
                return
        self.registry.set_pack_enabled(name, enabled)
        self._refresh()

    def _prompt_enable_missing(self, name: str, missing: list[str]) -> str:
        """Ask how to proceed when enabling a pack whose dependencies are absent.

        Returns ``"download"`` or ``"keep_disabled"``.  With no dialog available
        we default to ``"keep_disabled"`` — we never enable-and-assume silently.
        """
        if messagebox is None:
            return "keep_disabled"
        try:
            ok = messagebox.askyesno(
                "Dependencies missing",
                f"'{name}' needs: {', '.join(missing)}.\n\n"
                "Choose Yes to see how to install them (the pack is enabled and its "
                "tools stay marked 'Needs: …' until they are present).\n"
                "Choose No to keep the pack disabled.",
            )
        except Exception:
            return "keep_disabled"
        return "download" if ok else "keep_disabled"

    def _enable_all_packs(self) -> None:
        self.registry.preferences.reset()
        self._refresh()

    def _show_pack_deps(self, name: str) -> None:
        """Guided, honest instructions for a pack's missing dependencies."""
        missing = self._missing_for_pack(name)
        if not missing:
            self._set_packs_status(f"'{name}' has every dependency installed.")
            return
        self._set_packs_status(f"'{name}' needs: {', '.join(missing)}.")
        self._show_dependency_dialog(name, missing)

    def _show_dependency_dialog(self, pack: str, missing: list[str]) -> None:
        """A dialog that tells the user exactly how to get each dependency.

        It never downloads anything: it shows the recommended package-manager
        command and the official vendor page, and offers a one-click
        'Disable this pack' escape hatch.
        """
        dialog = tk.Toplevel(self)
        dialog.title(f"Dependencies for {pack}")
        dialog.geometry("700x520")
        dialog.configure(bg=BG)
        tk.Label(
            dialog, text=f"{pack} — missing dependencies", bg=BG, fg=TEXT,
            font=("Segoe UI", 13, "bold"), anchor="w",
        ).pack(fill="x", padx=18, pady=(14, 2))
        tk.Label(
            dialog,
            text=(
                "Install a dependency with the command shown, then press Refresh.\n"
                "Nothing is downloaded automatically — you stay in control."
            ),
            bg=BG, fg=SUBTLE, font=("Segoe UI", 9), justify="left", anchor="w",
        ).pack(fill="x", padx=18, pady=(0, 8))

        card = self._card(dialog)
        card.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        text = tk.Text(card, wrap="word", font=("Consolas", 10), relief="flat", bg="#fbfbfb", height=12)
        scroll = ttk.Scrollbar(card, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)

        body_lines: list[str] = []
        for dep in missing:
            plan = deps.install_plan(dep)
            body_lines.append(f"{dep}")
            if plan["known"]:
                body_lines.append(f"  What it is : {plan['summary']}")
                body_lines.append(f"  Why needed : {plan['why']}")
                for step in plan["steps"]:
                    body_lines.append(f"  - {step['label']}")
                    if step["command"]:
                        body_lines.append(f"      $ {step['command']}")
                    if step["url"]:
                        body_lines.append(f"      {step['url']}")
                    if step["note"]:
                        body_lines.append(f"      {step['note']}")
            else:
                body_lines.append(f"  -> {download_hint(dep)}")
            body_lines.append("")
        body = "\n".join(body_lines).strip()
        text.insert("1.0", body)
        text.configure(state="disabled")

        row = tk.Frame(dialog, bg=BG)
        row.pack(fill="x", padx=18, pady=(0, 16))

        def copy_all():
            try:
                self.clipboard_clear()
                self.clipboard_append(body)
            except Exception:
                pass

        def disable_pack():
            self.registry.set_pack_enabled(pack, False)
            dialog.destroy()
            self._refresh()
            self._set_packs_status(f"'{pack}' disabled — its tools are hidden until you re-enable it.")

        self._ghost_button(row, "Copy instructions", copy_all).pack(side="left", padx=(0, 8))
        self._ghost_button(row, "Disable this pack", disable_pack).pack(side="left", padx=(0, 8))
        self._accent_button(row, "Refresh", lambda: (dialog.destroy(), self._refresh())).pack(side="left")

    def _set_packs_status(self, message: str) -> None:
        try:
            self.packs_status.configure(text=message)
        except Exception:  # pragma: no cover - defensive
            pass
