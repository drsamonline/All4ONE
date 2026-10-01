"""Windows 10 (Fluent) styled desktop UI for Utility Suite.

Design goals:
  * Light, uncluttered start screen — no giant tool table on launch.
  * Windows-10-style selection boxes instead of listboxes/treeviews:
      - Category selector: flat toggle chips (Win10 "selector" style).
      - Tool picker: a dropdown ("combobox") selection box.
      - Run button: accent-colored Win10 button with hover highlight.
  * Everything the user needs is exactly where it is expected:
      search box on top, category chips below it, tool selection box,
      details panel, then args + run + output at the bottom.
"""

from __future__ import annotations

import os
import queue
import shlex
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

from .capability_checker import download_hint
from .preview import open_with_default, preview_file
from .tool_registry import ToolRegistry

try:  # single source of truth for the version string
    from . import __version__ as APP_VERSION
except Exception:  # pragma: no cover - defensive fallback
    APP_VERSION = "3.0.4"

# Tools that can delete/overwrite data or otherwise irreversibly change the
# system - the GUI confirms before running these.
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

# ---- Windows 10 light palette -------------------------------------------
BG = "#f3f3f3"          # window background
CARD = "#ffffff"        # card / surface
BORDER = "#e1e1e1"      # hairline borders
TEXT = "#191919"
SUBTLE = "#5d5d5d"
ACCENT = "#0078d4"      # Win10 default blue
ACCENT_HOVER = "#1a86d9"
CHIP_BG = "#ffffff"
CHIP_BORDER = "#bebebe"


class Win10Check(tk.Frame):
    """A Windows-10 style checkbox drawn from scratch (square box + tick)."""

    def __init__(self, master, text="", variable=None, command=None):
        super().__init__(master, bg=master.cget("bg"))
        self.var = variable if variable is not None else tk.IntVar(master=self)
        self.command = command
        self._box = tk.Canvas(self, width=20, height=20, bg=master.cget("bg"), highlightthickness=0)
        self._label = tk.Label(
            self, text=text, bg=master.cget("bg"), fg=TEXT, font=("Segoe UI", 10), anchor="w"
        )
        self._box.pack(side="left", padx=(0, 8), pady=4)
        self._label.pack(side="left")
        for w in (self, self._box, self._label):
            w.bind("<Button-1>", self._toggle)
        self._draw()

    def _toggle(self, _e=None):
        self.var.set(0 if self.var.get() else 1)
        self._draw()
        if self.command:
            self.command()

    def _draw(self):
        c = self._box
        c.delete("all")
        on = bool(self.var.get())
        border = ACCENT if on else CHIP_BORDER
        fill = ACCENT if on else CARD
        c.create_rectangle(3, 3, 17, 17, fill=fill, outline=border, width=2)
        if on:
            c.create_line(6, 10, 9, 13, fill="white", width=2, capstyle="round")
            c.create_line(9, 13, 15, 6, fill="white", width=2, capstyle="round")


class Chip(tk.Label):
    """Flat Win10 toggle 'chip' used for category selection."""

    def __init__(self, master, text, command):
        super().__init__(
            master,
            text=text,
            bg=CHIP_BG,
            fg=TEXT,
            font=("Segoe UI", 10),
            padx=14,
            pady=6,
            cursor="hand2",
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            highlightthickness=1,
            bd=0,
        )
        self.selected = False
        self._command = command
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda e: self.configure(bg=ACCENT_HOVER if self.selected else "#ececec"))
        self.bind("<Leave>", lambda e: self.configure(bg=ACCENT if self.selected else CHIP_BG))

    def _on_click(self, _e=None):
        self._command(self)

    def set_selected(self, sel: bool):
        self.selected = sel
        self.configure(bg=ACCENT if sel else CHIP_BG, fg="white" if sel else TEXT)


class UtilitySuiteGUI(tk.Tk):
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
        self.geometry(f"{int(1080 * min(self._scale, 1.25))}x{int(720 * min(self._scale, 1.25))}")
        self.minsize(800, 560)
        self.configure(bg=BG)
        self._selected: dict[str, Any] | None = None
        self._queue: queue.Queue[str] = queue.Queue()
        self._category: str | None = None
        self._chips: list[Chip] = []
        self._tools_by_label: dict[str, dict[str, Any]] = {}
        self._build_style()
        self._build_ui()
        self._build_body()
        self._populate()
        self.after(80, self._drain_output)

    def _build_style(self):
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
            padding=6,
        )
        style.map(
            "Win10.TCombobox",
            fieldbackground=[("readonly", CARD)],
            bordercolor=[("focus", ACCENT)],
        )
        style.configure("Win10.TNotebook.Tab", font=("Segoe UI", 10), padding=(12, 6))

    # ------------------------------------------------------------------ UI
    def _card(self, parent, **kw):
        return tk.Frame(
            parent,
            bg=CARD,
            highlightbackground=BORDER,
            highlightcolor=BORDER,
            highlightthickness=1,
            **kw,
        )

    def _build_ui(self):
        # Top bar: title + compact status + refresh
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(18, 8))
        tk.Label(top, text="Utility Suite", bg=BG, fg=TEXT, font=("Segoe UI", 17, "bold")).pack(side="left")
        self.status_lbl = tk.Label(top, text="", bg=BG, fg=SUBTLE, font=("Segoe UI", 9))
        self.status_lbl.pack(side="right", padx=(8, 0))
        self._ghost_button(top, "Refresh tools", self._refresh).pack(side="right", padx=(0, 8))

        # Search box (flat Win10 entry inside a bordered card)
        search_wrap = self._card(self, padx=2, pady=2)
        search_wrap.pack(fill="x", padx=24, pady=(4, 10))
        tk.Label(search_wrap, text="Search", bg=CARD, fg=SUBTLE, font=("Segoe UI", 9, "bold")).pack(
            side="left", padx=(10, 8)
        )
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_wrap, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat",
            font=("Segoe UI", 11), bd=0,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=6)
        self.search_var.trace_add("write", lambda *_: self._filter_tools())
        self.search_entry.bind("<Return>", lambda _e: self._filter_tools())
        self._ghost_button(search_wrap, "Clear", lambda: self.search_var.set("")).pack(side="right", padx=6)

        # Category selector: a horizontally scrollable single-row strip of
        # Win10 chips. A Canvas + inner frame lets the row overflow gracefully
        # (mouse wheel scrolls) instead of spilling widgets off the window.
        cat_card = self._card(self, padx=12, pady=8)
        cat_card.pack(fill="x", padx=24, pady=(0, 10))
        tk.Label(cat_card, text="Category", bg=CARD, fg=SUBTLE, font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w", padx=(2, 8), pady=(0, 6)
        )
        cat_card.columnconfigure(0, weight=1)
        self.chip_canvas = tk.Canvas(cat_card, bg=CARD, highlightthickness=0, height=38)
        self.chip_canvas.grid(row=1, column=0, sticky="ew")
        self.chip_holder = tk.Frame(self.chip_canvas, bg=CARD)
        self._chip_window = self.chip_canvas.create_window((0, 0), window=self.chip_holder, anchor="w")
        self.chip_holder.bind(
            "<Configure>",
            lambda _e: self.chip_canvas.configure(scrollregion=self.chip_canvas.bbox("all") or (0, 0, 0, 0)),
        )
        self.chip_canvas.bind(
            "<Configure>", lambda e: self.chip_canvas.itemconfigure(self._chip_window, width=max(e.width, 1))
        )
        for seq in ("<Button-4>", "<Button-5>", "<MouseWheel>"):
            self.chip_canvas.bind(seq, self._scroll_chips)

    def _scroll_chips(self, event):
        try:
            if event.num == 4:
                delta = -20
            elif event.num == 5:
                delta = 20
            else:
                delta = -20 if event.delta > 0 else 20
            self.chip_canvas.xview_scroll(delta, "units")
        except Exception:
            pass

    def _build_body(self):
        # Middle: tool selection box + details
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        pick_card = self._card(body, padx=12, pady=10)
        pick_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tk.Label(pick_card, text="Tool", bg=CARD, fg=SUBTLE, font=("Segoe UI", 9, "bold")).pack(
            anchor="w", pady=(0, 4)
        )
        self.tool_var = tk.StringVar()
        self.tool_combo = ttk.Combobox(
            pick_card, textvariable=self.tool_var, state="readonly",
            font=("Segoe UI", 11), style="Win10.TCombobox",
        )
        self.tool_combo.pack(fill="x")
        self.tool_combo.bind("<<ComboboxSelected>>", self._tool_selected)

        detail_card = self._card(body, padx=16, pady=14)
        detail_card.grid(row=1, column=0, sticky="nsew")
        detail_card.rowconfigure(4, weight=1)
        detail_card.columnconfigure(0, weight=1)
        self.detail_title = tk.Label(
            detail_card, text="Pick a category or search, then select a tool.",
            bg=CARD, fg=TEXT, font=("Segoe UI", 13, "bold"), anchor="w", justify="left", wraplength=900,
        )
        self.detail_title.grid(row=0, column=0, sticky="new")
        self.detail_meta = tk.Label(
            detail_card, text="", bg=CARD, fg=SUBTLE, font=("Segoe UI", 9),
            anchor="w", justify="left", wraplength=900,
        )
        self.detail_meta.grid(row=1, column=0, sticky="new", pady=(4, 0))

        def _rescale_wrap(event=None):
            # Keep text wrapping inside the window instead of spilling out.
            w = max(320, detail_card.winfo_width() - 40)
            self.detail_title.configure(wraplength=w)
            self.detail_meta.configure(wraplength=w)

        detail_card.bind("<Configure>", _rescale_wrap)

        # Bottom action bar: args + run + output
        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="both", expand=True, padx=24, pady=(10, 18))
        bottom.columnconfigure(0, weight=1)
        bottom.rowconfigure(3, weight=1)

        arg_row = tk.Frame(bottom, bg=BG)
        arg_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        arg_row.columnconfigure(0, weight=1)
        self.args_var = tk.StringVar()
        args_entry = tk.Entry(
            arg_row, textvariable=self.args_var, bg=CARD, fg=TEXT, insertbackground=TEXT,
            relief="flat", font=("Consolas", 10),
            highlightbackground=BORDER, highlightcolor=ACCENT, highlightthickness=1,
        )
        args_entry.grid(row=0, column=0, sticky="ew", ipady=6, padx=(0, 6))
        self._ghost_button(arg_row, "File…", self._insert_file_arg).grid(row=0, column=1, padx=2)
        self._ghost_button(arg_row, "Folder…", self._insert_folder_arg).grid(row=0, column=2, padx=(2, 6))
        self.run_btn = self._accent_button(arg_row, "Run", self._run)
        self.run_btn.grid(row=0, column=3, padx=2)

        opt_row = tk.Frame(bottom, bg=BG)
        opt_row.grid(row=1, column=0, sticky="w", pady=(0, 6))
        self.show_unavailable_var = tk.IntVar(value=0)
        Win10Check(
            opt_row, text="Show unavailable tools", variable=self.show_unavailable_var,
            command=self._filter_tools,
        ).pack(side="left", padx=(0, 16))

        out_card = self._card(bottom, padx=2, pady=2)
        out_card.grid(row=3, column=0, sticky="nsew")
        self.output = tk.Text(
            out_card, bg="#fbfbfb", fg=TEXT, insertbackground=TEXT, relief="flat", wrap="word",
            font=("Consolas", 10), height=9,
        )
        self.output.pack(fill="both", expand=True)

    def _accent_button(self, parent, text, command):
        btn = tk.Label(
            parent, text=text, bg=ACCENT, fg="white", font=("Segoe UI", 10, "bold"),
            padx=18, pady=6, cursor="hand2", bd=0,
        )
        btn.bind("<Button-1>", lambda _e: command())
        btn.bind("<Enter>", lambda _e: btn.configure(bg=ACCENT_HOVER))
        btn.bind("<Leave>", lambda _e: btn.configure(bg=ACCENT))
        return btn

    def _ghost_button(self, parent, text, command):
        btn = tk.Label(
            parent, text=text, bg=CARD, fg=TEXT, font=("Segoe UI", 10),
            padx=12, pady=5, cursor="hand2", bd=0,
            highlightbackground=CHIP_BORDER, highlightcolor=ACCENT, highlightthickness=1,
        )
        btn.bind("<Button-1>", lambda _e: command())
        btn.bind("<Enter>", lambda _e: btn.configure(bg="#ececec"))
        btn.bind("<Leave>", lambda _e: btn.configure(bg=CARD))
        return btn

    # ------------------------------------------------------------ data
    def _populate(self):
        cats = list(self.registry.list_categories().keys())
        total = len(self.registry.tools)
        avail = sum(1 for t in self.registry.tools.values() if t["available"])
        self.status_lbl.configure(text=f"{avail}/{total} tools ready — click for install guide")
        self.status_lbl.configure(cursor="hand2")
        self.status_lbl.bind("<Button-1>", lambda _e: self._install_guide())
        for chip in self._chips:
            chip.destroy()
        self._chips.clear()
        entries = [(None, "All")] + [(c, c) for c in cats]
        # Single scrollable row — stacking chips in a grid used to push the
        # lower rows (and everything below them) off-screen on small windows.
        for i, (cat, label) in enumerate(entries):
            chip = Chip(self.chip_holder, label, self._select_category)
            chip.cat = cat  # type: ignore[attr-defined]
            chip.grid(row=0, column=i, padx=3, pady=3)
            self._chips.append(chip)
        self._chips[0].set_selected(True)
        self._filter_tools()

    def _select_category(self, chip: Chip):
        for c in self._chips:
            c.set_selected(c is chip)
        self._category = chip.cat  # type: ignore[attr-defined]
        self._filter_tools()

    def _matching_tools(self) -> list[dict[str, Any]]:
        query = self.search_var.get().strip()
        tools = self.registry.search(query) if query else list(self.registry.tools.values())
        if self._category:
            tools = [t for t in tools if t.get("category") == self._category]
        if not self.show_unavailable_var.get():
            tools = [t for t in tools if t["available"]]
        tools = sorted(tools, key=lambda t: str(t.get("name", "")).lower())
        return tools[:500]  # keep the dropdown responsive

    def _install_guide(self):
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
        body = "\n\n".join(lines) or "Nothing is missing - every tool on this system is ready."
        dlg = tk.Toplevel(self)
        dlg.title("Install missing dependencies")
        dlg.geometry("680x520")
        dlg.configure(bg=BG)
        tk.Label(
            dlg, text="Download / install guide", bg=BG, fg=TEXT,
            font=("Segoe UI", 14, "bold"), anchor="w",
        ).pack(fill="x", padx=18, pady=(14, 4))
        tk.Label(
            dlg,
            text=(
                "Tools whose optional dependency is missing are hidden by default.\n"
                "Install anything below, then press 'Refresh tools' - it turns Ready automatically.\n"
                "After installing a pip package, restart Utility Suite so the new import is picked up."
            ),
            bg=BG, fg=SUBTLE, font=("Segoe UI", 9), justify="left", anchor="w",
        ).pack(fill="x", padx=18, pady=(0, 8))
        card = self._card(dlg, padx=2, pady=2)
        card.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        txt = tk.Text(card, wrap="word", font=("Consolas", 10), relief="flat", bg="#fbfbfb", height=10)
        scroll = ttk.Scrollbar(card, command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        txt.insert("1.0", body)
        txt.configure(state="disabled")
        btn_row = tk.Frame(dlg, bg=BG)
        btn_row.pack(fill="x", padx=18, pady=(0, 16))

        def copy_all():
            self.clipboard_clear()
            self.clipboard_append(body)

        self._ghost_button(btn_row, "Copy list", copy_all).pack(side="left", padx=(0, 8))
        self._accent_button(
            btn_row, "Refresh tools", lambda: (dlg.destroy(), self._refresh())
        ).pack(side="left")
        tk.Button(btn_row, text="Close", command=dlg.destroy, bg=CARD, relief="flat").pack(side="right")

    def _filter_tools(self):
        tools = self._matching_tools()
        labels = [f"{t['name']}  —  {t['cli_command']}" for t in tools]
        self.tool_combo["values"] = labels
        self._tools_by_label = dict(zip(labels, tools))
        if not labels:
            self.tool_var.set("")
            self._selected = None
            self.detail_title.configure(text="No tools match this filter.")
            self.detail_meta.configure(text="Try clearing the search or picking another category.")
            return
        current = self.tool_var.get()
        if current in labels:
            self._tool_selected()
        else:
            self.tool_var.set("")
            self._selected = None
            self.detail_title.configure(text=f"{len(labels)} tool(s) match — select one from the Tool box.")
            self.detail_meta.configure(text="")

    def _tool_selected(self, _event=None):
        label = self.tool_var.get()
        tool = self._tools_by_label.get(label)
        if not tool:
            return
        self._selected = tool
        self.detail_title.configure(text=f"{tool['name']}   [{tool['cli_command']}]")
        deps = ", ".join(tool.get("dependencies", []) or [])
        if tool["available"]:
            status = "Ready"
        else:
            miss = tool["missing_dependencies"]
            hints = "; ".join(f"{d}: {download_hint(d)}" for d in miss)
            status = f"Needs install — {hints}"
        meta = f"{tool.get('description', '')}\nCategory: {tool.get('category', '')}   •   Status: {status}"
        if deps and tool["available"]:
            meta += f"   •   Optional deps: {deps}"
        self.detail_meta.configure(text=meta)
        self.args_var.set("")

    # ------------------------------------------------------------ actions
    def _insert_file_arg(self):
        path = filedialog.askopenfilename(title="Choose a file")
        if path:
            self._append_arg(path)

    def _insert_folder_arg(self):
        path = filedialog.askdirectory(title="Choose a folder")
        if path:
            self._append_arg(path)

    def _append_arg(self, path):
        quoted = f'"{path}"' if " " in path else path
        current = self.args_var.get().strip()
        self.args_var.set(f"{current} {quoted}".strip())

    def _run(self):
        if not self._selected:
            messagebox.showinfo("Utility Suite", "Select a tool first.")
            return
        cmd = self._selected["cli_command"]
        if cmd in DESTRUCTIVE_TOOLS:
            if not messagebox.askyesno(
                "Confirm action",
                f"'{self._selected['name']}' can permanently delete or overwrite data.\nContinue?",
            ):
                return
        self.output.delete("1.0", tk.END)
        args = (
            shlex.split(self.args_var.get(), posix=(os.name != "nt")) if self.args_var.get().strip() else []
        )

        def worker():
            try:
                self.registry.run_tool(cmd, args, output=self._queue.put)
            finally:
                self._queue.put("__done__")

        self.run_btn.configure(text="Running…", cursor="watch")
        threading.Thread(target=worker, daemon=True).start()

    def _drain_output(self):
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

    def _preview(self):
        path = filedialog.askopenfilename(title="Choose a file to preview")
        if not path:
            return
        try:
            text = preview_file(path)
            self.output.delete("1.0", tk.END)
            self.output.insert("1.0", text)
        except Exception as exc:
            messagebox.showerror("Preview failed", str(exc))

    def _open(self):
        path = filedialog.askopenfilename(title="Choose a file to open")
        if not path:
            return
        try:
            open_with_default(path)
        except Exception as exc:
            messagebox.showerror("Open failed", str(exc))

    def _refresh(self):
        if self.on_refresh:
            self.registry = self.on_refresh()
        self._selected = None
        self._populate()
        self.output.insert(tk.END, "Tool inventory refreshed.\n")
