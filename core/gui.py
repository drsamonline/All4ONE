"""Polished Tkinter desktop UI for Utility Suite."""

from __future__ import annotations

import os
import queue
import shlex
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

from .preview import open_with_default, preview_file
from .tool_registry import ToolRegistry

# Tools that can delete/overwrite data or otherwise irreversibly change the
# system - the GUI confirms before running these, mirroring the extra
# caution a person would want before clicking a destructive action.
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


class UtilitySuiteGUI(tk.Tk):
    def __init__(self, registry: ToolRegistry, *, on_refresh=None) -> None:
        super().__init__()
        self.registry = registry
        self.on_refresh = on_refresh
        self.title("Utility Suite — Dr. Sohil Momin")
        self.geometry("1200x760")
        self.minsize(980, 640)
        self.configure(bg="#0f1115")
        self._selected: dict[str, Any] | None = None
        self._queue: queue.Queue[str] = queue.Queue()
        self._build_style()
        self._build_ui()
        self._populate_categories()
        self.after(80, self._drain_output)

    def _build_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#0f1115")
        style.configure("Panel.TFrame", background="#171a21")
        style.configure("TLabel", background="#0f1115", foreground="#e8ebf2")
        style.configure(
            "Title.TLabel", background="#0f1115", foreground="#ffffff", font=("Segoe UI", 22, "bold")
        )
        style.configure("Sub.TLabel", background="#0f1115", foreground="#8f98aa", font=("Segoe UI", 10))
        style.configure("Card.TFrame", background="#171a21")
        style.configure("Card.TLabel", background="#171a21", foreground="#e8ebf2", font=("Segoe UI", 10))
        style.configure(
            "CardTitle.TLabel", background="#171a21", foreground="#ffffff", font=("Segoe UI", 15, "bold")
        )
        style.configure("CardMeta.TLabel", background="#171a21", foreground="#9aa6ba", font=("Segoe UI", 9))
        style.configure(
            "PanelHeader.TLabel", background="#171a21", foreground="#71809a", font=("Segoe UI", 9, "bold")
        )
        style.configure(
            "Treeview",
            background="#13161c",
            fieldbackground="#13161c",
            foreground="#e5e7eb",
            rowheight=32,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#1e2430",
            foreground="#b9c3d5",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        )
        style.map("Treeview", background=[("selected", "#2b3852")])
        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
            background="#5b8cff",
            foreground="white",
        )
        style.map("Accent.TButton", background=[("active", "#739cff")])
        style.configure("Ghost.TButton", padding=(10, 7), background="#202631", foreground="#dce2ed")
        style.configure("TEntry", fieldbackground="#171a21", foreground="#e8ebf2", insertcolor="#ffffff")
        style.configure("TNotebook", background="#0f1115", borderwidth=0)
        style.configure("TNotebook.Tab", background="#171a21", foreground="#b7c0d1", padding=(14, 8))

    def _build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill="x", padx=22, pady=(18, 10))
        ttk.Label(header, text="Utility Suite — Dr. Sohil Momin", style="Title.TLabel").pack(side="left")
        ttk.Label(
            header, text="Windows utility workstation • dynamic plugin-powered catalogue", style="Sub.TLabel"
        ).pack(side="left", padx=14, pady=(9, 0))
        ttk.Button(header, text="Refresh", style="Ghost.TButton", command=self._refresh).pack(side="right")

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=22, pady=(0, 18))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body, style="Panel.TFrame", padding=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.configure(width=240)
        ttk.Label(
            left, text="TOOLS", background="#171a21", foreground="#71809a", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(0, 8))
        self.cat_list = tk.Listbox(
            left,
            bg="#171a21",
            fg="#dce3f1",
            selectbackground="#2b3852",
            selectforeground="#ffffff",
            bd=0,
            highlightthickness=0,
            activestyle="none",
            font=("Segoe UI", 10),
        )
        self.cat_list.pack(fill="both", expand=True)
        self.cat_list.bind("<<ListboxSelect>>", self._category_changed)

        right = ttk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        search_bar = ttk.Frame(right)
        search_bar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        search_bar.columnconfigure(0, weight=1)
        self.search_var = tk.StringVar()
        entry = ttk.Entry(search_bar, textvariable=self.search_var)
        entry.grid(row=0, column=0, sticky="ew")
        entry.bind("<KeyRelease>", lambda _e: self._filter())
        ttk.Button(
            search_bar, text="Clear", style="Ghost.TButton", command=lambda: self.search_var.set("")
        ).grid(row=0, column=1, padx=(8, 0))

        main = ttk.Frame(right, style="Panel.TFrame", padding=14)
        main.grid(row=1, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)
        self.tool_tree = ttk.Treeview(
            main, columns=("category", "status", "description"), show="headings", selectmode="browse"
        )
        for col, text, width in (
            ("category", "Category", 160),
            ("status", "Status", 95),
            ("description", "Description", 520),
        ):
            self.tool_tree.heading(col, text=text)
            self.tool_tree.column(col, width=width, anchor="w")
        self.tool_tree.grid(row=0, column=0, sticky="nsew")
        self.tool_tree.bind("<<TreeviewSelect>>", self._tool_selected)

        detail = ttk.Frame(main, style="Card.TFrame", padding=14)
        detail.grid(row=1, column=0, sticky="ew", pady=(12, 10))
        detail.columnconfigure(0, weight=1)
        self.detail_title = ttk.Label(detail, text="Select a tool", style="CardTitle.TLabel")
        self.detail_title.grid(row=0, column=0, sticky="w")
        self.detail_meta = ttk.Label(detail, text="", style="CardMeta.TLabel")
        self.detail_meta.grid(row=1, column=0, sticky="w", pady=(4, 0))
        actions = ttk.Frame(detail, style="Card.TFrame")
        actions.grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Button(actions, text="Preview", style="Ghost.TButton", command=self._preview).pack(
            side="left", padx=4
        )
        ttk.Button(actions, text="Open File", style="Ghost.TButton", command=self._open).pack(
            side="left", padx=4
        )

        exec_panel = ttk.Frame(main, style="Card.TFrame", padding=12)
        exec_panel.grid(row=2, column=0, sticky="nsew")
        exec_panel.columnconfigure(0, weight=1)
        exec_panel.rowconfigure(2, weight=1)
        ttk.Label(exec_panel, text="ARGUMENTS", style="PanelHeader.TLabel").grid(row=0, column=0, sticky="w")
        self.args_var = tk.StringVar()
        ttk.Entry(exec_panel, textvariable=self.args_var).grid(row=1, column=0, sticky="ew", pady=(5, 8))
        btn_row = ttk.Frame(exec_panel, style="Card.TFrame")
        btn_row.grid(row=1, column=1, padx=(8, 0))
        ttk.Button(btn_row, text="File...", style="Ghost.TButton", command=self._insert_file_arg).pack(
            side="left", padx=2
        )
        ttk.Button(btn_row, text="Folder...", style="Ghost.TButton", command=self._insert_folder_arg).pack(
            side="left", padx=2
        )
        ttk.Button(btn_row, text="Run Selected Tool", style="Accent.TButton", command=self._run).pack(
            side="left", padx=(6, 0)
        )
        self.output = tk.Text(
            exec_panel,
            bg="#101217",
            fg="#dce3ef",
            insertbackground="#ffffff",
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
        )
        self.output.grid(row=2, column=0, columnspan=2, sticky="nsew")

    def _populate_categories(self):
        self.categories = list(self.registry.list_categories().keys())
        self.cat_list.delete(0, tk.END)
        self.cat_list.insert(tk.END, "All Tools")
        for cat in self.categories:
            self.cat_list.insert(tk.END, cat)
        self.cat_list.selection_set(0)
        self._filter()

    def _category_changed(self, _event=None):
        self._filter()

    def _filter(self):
        query = self.search_var.get().strip()
        selected = self.cat_list.curselection()
        category = None if not selected or selected[0] == 0 else self.cat_list.get(selected[0])
        tools = self.registry.search(query)
        if category:
            tools = [t for t in tools if t.get("category") == category]
        self.tool_tree.delete(*self.tool_tree.get_children())
        for tool in tools:
            status = "Ready" if tool["available"] else "Missing"
            self.tool_tree.insert(
                "",
                "end",
                iid=tool["cli_command"],
                values=(tool.get("category", ""), status, tool.get("description", "")),
            )

    def _tool_selected(self, _event=None):
        sel = self.tool_tree.selection()
        if not sel:
            return
        tool = self.registry.get_tool(sel[0])
        self._selected = tool
        self.detail_title.configure(text=tool["name"])
        status = (
            "AVAILABLE" if tool["available"] else f"UNAVAILABLE • {', '.join(tool['missing_dependencies'])}"
        )
        self.detail_meta.configure(text=f"{tool['category']}  •  {tool['cli_command']}  •  {status}")
        self.args_var.set("")

    def _insert_file_arg(self):
        path = filedialog.askopenfilename(title="Choose a file")
        if path:
            self._append_arg(path)

    def _insert_folder_arg(self):
        path = filedialog.askdirectory(title="Choose a folder")
        if path:
            self._append_arg(path)

    def _append_arg(self, path):
        quoted = shlex.quote(path) if os.name != "nt" else (f'"{path}"' if " " in path else path)
        current = self.args_var.get().strip()
        self.args_var.set(f"{current} {quoted}".strip())

    def _run(self):
        if not self._selected:
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
        threading.Thread(
            target=lambda: self.registry.run_tool(cmd, args, output=self._queue.put), daemon=True
        ).start()

    def _drain_output(self):
        try:
            while True:
                self.output.insert(tk.END, self._queue.get_nowait() + "\n")
                self.output.see(tk.END)
        except queue.Empty:
            pass
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
        self._populate_categories()
        self.output.insert(tk.END, "Plugin inventory refreshed.\n")
