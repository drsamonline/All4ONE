"""Headless GUI harness.

``tkinter`` is unavailable in CI/sandbox images and there is no display, so the
real GUI cannot be rendered or screenshotted.  This harness installs a *fake*
``tkinter`` (a stub that records construction and supports the widget API the
GUI actually uses), then imports and fully constructs :class:`UtilitySuiteGUI`
against it.  That proves the widget tree — including the new Plugins panel —
builds without ``AttributeError`` / ``NameError`` / ``TypeError``, and lets us
drive the panel's handlers with synthetic events.

When a *working* real tkinter is present the harness skips itself cleanly, so it
never interferes with a developer running the app for real.

Run:  python -B -m tests.test_gui_headless
"""

from __future__ import annotations

import sys
import types

sys.dont_write_bytecode = True

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# --------------------------------------------------------------------------- #
# Fake tkinter
# --------------------------------------------------------------------------- #
class _Event:
    """Minimal stand-in for a Tk event object."""

    def __init__(self, **kw):
        self.num = 0
        self.delta = 0
        self.width = 800
        self.height = 600
        self.widget = None
        for key, value in kw.items():
            setattr(self, key, value)


class TclError(Exception):
    pass


class _Variable:
    def __init__(self, master=None, value=None, **kw):
        self._value = "" if value is None else value
        self._callbacks: list = []

    def get(self):
        return self._value

    def set(self, value):
        self._value = value
        for callback in list(self._callbacks):
            callback("", "", "write")

    def trace_add(self, _mode, callback):
        self._callbacks.append(callback)
        return f"trace{len(self._callbacks)}"


class StringVar(_Variable):
    def __init__(self, master=None, value="", **kw):
        super().__init__(master, "" if value is None else value)


class IntVar(_Variable):
    def __init__(self, master=None, value=0, **kw):
        super().__init__(master, 0 if value is None else value)


class _Widget:
    """Base for every fake widget: records calls instead of drawing."""

    def __init__(self, master=None, **kw):
        self.master = master
        self._kw = dict(kw)
        self._children: list = []
        self._bindings: dict = {}
        self._after: list = []
        if isinstance(master, _Widget):
            master._children.append(self)

    # --- options ---
    def cget(self, key):
        return self._kw.get(key, "")

    def configure(self, **kw):
        self._kw.update(kw)
        return None

    config = configure

    def __setitem__(self, key, value):
        self._kw[key] = value

    def __getitem__(self, key):
        return self._kw.get(key, 0)

    # --- geometry ---
    def pack(self, **kw):
        self._kw["_pack"] = kw
        return self

    def grid(self, **kw):
        self._kw["_grid"] = kw
        return self

    def pack_forget(self):
        return None

    grid_forget = pack_forget

    def columnconfigure(self, *a, **k):
        return None

    rowconfigure = columnconfigure

    def winfo_children(self):
        return list(self._children)

    def winfo_width(self):
        return int(self._kw.get("width", 800) or 800)

    def winfo_height(self):
        return 600

    def winfo_fpixels(self, *_a):
        return 96.0

    def focus_set(self):
        return None

    def title(self, *_a):
        return None

    def geometry(self, *_a):
        return None

    def minsize(self, *_a):
        return None

    def mainloop(self, *_a):
        return None

    def bind(self, sequence, func=None, add=None):
        if func is not None:
            self._bindings[sequence] = func
        return f"bind{len(self._bindings)}"

    def bind_all(self, sequence, func=None, add=None):
        return f"bindall{sequence}"

    def unbind(self, sequence, funcid=None):
        self._bindings.pop(sequence, None)

    def after(self, ms, func=None, *args):
        self._after.append((ms, func))
        return f"after{len(self._after)}"

    def clipboard_clear(self):
        return None

    def clipboard_append(self, *_a):
        return None

    def destroy(self):
        for child in list(self._children):
            child.destroy()
        self._children = []
        if isinstance(self.master, _Widget) and self in self.master._children:
            self.master._children.remove(self)


class Tk(_Widget):
    def __init__(self, *a, **kw):
        super().__init__(None)


class Frame(_Widget):
    pass


class Label(_Widget):
    pass


class Button(_Widget):
    pass


class Entry(_Widget):
    def insert(self, *_a):
        return None

    def delete(self, *_a):
        return None

    def get(self):
        return ""

    def select_range(self, *_a):
        return None


class Text(_Widget):
    def insert(self, index, text, *_a):
        return None

    def delete(self, *_a):
        return None

    def see(self, *_a):
        return None

    def yview(self, *_a):
        return None


class Canvas(_Widget):
    def delete(self, *_a):
        return None

    def create_rectangle(self, *a, **k):
        return 1

    def create_line(self, *a, **k):
        return 2

    def create_window(self, *a, **k):
        return 3

    def itemconfigure(self, *a, **k):
        return None

    def bbox(self, *_a):
        return (0, 0, 100, 100)

    def xview_scroll(self, *_a):
        return None

    def yview(self, *_a):
        return None

    def xview(self, *_a):
        return None

    def yview_scroll(self, *_a):
        return None


class Toplevel(_Widget):
    pass


class _Style:
    def __init__(self, master=None):
        pass

    def theme_use(self, *_a):
        return None

    def configure(self, *a, **k):
        return None

    def map(self, *a, **k):
        return None


class _Combobox(_Widget):
    pass


class _Scrollbar(_Widget):
    def set(self, *_a):
        return None


class _Progressbar(_Widget):
    pass


class _Notebook(_Widget):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self._tabs: list = []
        self._selected = 0

    def add(self, child, text=""):
        self._tabs.append((child, text))

    def select(self):
        return self._tabs[self._selected][0] if self._tabs else None

    def index(self, item):
        for position, (child, _text) in enumerate(self._tabs):
            if child is item:
                return position
        raise TclError("not a tab")

    def tabs(self):
        return tuple(str(child) for child, _text in self._tabs)


class _Treeview(_Widget):
    def __init__(self, master=None, columns=(), show="", selectmode="", style="", **kw):
        super().__init__(master, **kw)
        self._columns = list(columns)
        self._rows: dict = {}
        self._order: list = []
        self._selection: tuple = ()
        self._focused = None
        self._counter = 0

    def heading(self, column, **kw):
        return None

    def column(self, column, **kw):
        return None

    def insert(self, parent, index, **kw):
        self._counter += 1
        iid = f"I{self._counter}"
        self._rows[iid] = kw.get("values", ())
        self._order.append(iid)
        return iid

    def delete(self, *items):
        for iid in items:
            self._rows.pop(iid, None)
            if iid in self._order:
                self._order.remove(iid)

    def get_children(self, item=None):
        return tuple(self._order)

    def selection(self):
        return self._selection

    def selection_set(self, iid):
        self._selection = (iid,)
        callback = self._bindings.get("<<TreeviewSelect>>")
        if callback:
            callback(_Event())

    def focus(self, iid):
        self._focused = iid

    def yview(self, *_a):
        return None

    def values(self, iid):
        return self._rows.get(iid)


def _install_fake_tkinter() -> None:
    tk = types.ModuleType("tkinter")
    tk.Tk, tk.Toplevel, tk.Frame, tk.Label, tk.Button = Tk, Toplevel, Frame, Label, Button
    tk.Entry, tk.Text, tk.Canvas = Entry, Text, Canvas
    tk.StringVar, tk.IntVar, tk.TclError = StringVar, IntVar, TclError
    tk.END = "end"

    ttk = types.ModuleType("tkinter.ttk")
    ttk.Style, ttk.Combobox, ttk.Notebook = _Style, _Combobox, _Notebook
    ttk.Treeview, ttk.Scrollbar, ttk.Progressbar = _Treeview, _Scrollbar, _Progressbar

    filedialog = types.ModuleType("tkinter.filedialog")
    filedialog.askopenfilename = lambda **kw: ""
    filedialog.askdirectory = lambda **kw: ""

    messagebox = types.ModuleType("tkinter.messagebox")
    messagebox.showinfo = lambda *a, **k: None
    messagebox.showerror = lambda *a, **k: None
    messagebox.askyesno = lambda *a, **k: False

    tk.ttk = ttk
    tk.filedialog = filedialog
    tk.messagebox = messagebox

    sys.modules["tkinter"] = tk
    sys.modules["tkinter.ttk"] = ttk
    sys.modules["tkinter.filedialog"] = filedialog
    sys.modules["tkinter.messagebox"] = messagebox


def _real_tkinter_works() -> bool:
    try:
        import tkinter as real

        root = real.Tk()
        root.destroy()
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------- #
def main() -> int:
    if _real_tkinter_works():
        print("real tkinter + display available — skipping the fake-tkinter harness")
        return 0

    _install_fake_tkinter()

    from core import plugin_installer as pi
    from core.cli import build_registry
    from core.gui import UtilitySuiteGUI

    registry = build_registry()
    app = UtilitySuiteGUI(registry, on_refresh=build_registry)

    # --- widget tree built ---
    assert app.notebook is not None
    assert len(app.notebook._tabs) == 2, "expected a Tools tab and a Plugins tab"
    assert app.tools_tab in [child for child, _ in app.notebook._tabs]
    assert app.plugins_tab in [child for child, _ in app.notebook._tabs]

    # --- tool table populated without a click ---
    rows = app.tool_tree.get_children()
    assert rows, "tool table is empty"
    assert len(rows) == len(app._tools_by_iid)
    first_values = app.tool_tree.values(rows[0])
    assert len(first_values) == 3, "rows must carry name + category + status"

    # --- status header shows a readiness count ---
    assert "ready" in app.status_lbl.cget("text").lower()

    # --- search narrows the table, and selection updates the details pane ---
    app.search_var.set("checksum")
    narrowed = app.tool_tree.get_children()
    assert narrowed, "search for a known tool returned nothing"
    assert app._selected is not None, "a row should be auto-selected"
    assert "checksum" in app.detail_title.cget("text").lower()
    app._clear_filters()
    assert len(app.tool_tree.get_children()) == len(rows)

    # --- Plugins panel: header, rows, states ---
    app._available = [
        pi.PackInfo(name="audio_tools", title="Audio Tools", tools=12, size=2048, file="audio_tools.zip"),
        pi.PackInfo(name="video_tools", title="Video Tools", tools=8, size=4096, file="video_tools.zip"),
    ]
    fake_installed = pi.InstalledPack(name="audio_tools", path=ROOT / "plugins" / "audio_tools.zip", size=2048, kind="zip")
    real_list_installed = pi.list_installed
    pi.list_installed = lambda *_a, **_k: [fake_installed]  # type: ignore[assignment]
    try:
        app._render_plugins()
    finally:
        pi.list_installed = real_list_installed  # type: ignore[assignment]

    assert app.plugins_count_lbl.cget("text") == "Installed 1 of 2 packs", app.plugins_count_lbl.cget("text")
    assert len(app.plugins_holder.winfo_children()) == 2, "both catalogue rows should render"

    # state logic
    assert app._pack_state(app._available[0], fake_installed)[2] == "remove"       # same size -> installed
    assert app._pack_state(app._available[1], None)[2] == "download"               # absent -> download
    assert app._pack_state(app._available[0], pi.InstalledPack("audio_tools", ROOT, 999, "zip"))[2] == "download"

    # --- synthetic plugin events must not raise and must update the UI ---
    app._handle_plugin_event(("progress", 50, 100))
    assert "50%" in app.plugins_status.cget("text")
    app._handle_plugin_event(("progress", 1024, 0))  # unknown total -> pulse branch
    app._handle_plugin_event(("download_done", pi.DownloadResult(ok=False, name="x", error="network unavailable")))
    assert "Download failed" in app.plugins_status.cget("text")
    app._handle_plugin_event(("manifest", pi.ManifestResult(ok=False, error="network unavailable (offline)")))
    assert "Offline" in app.plugins_status.cget("text"), app.plugins_status.cget("text")

    # --- the catalogue loads lazily, only when the Plugins tab is shown ---
    loads: list = []
    app._load_manifest = lambda: loads.append(True)  # type: ignore[assignment]
    app.notebook._selected = 0  # Tools tab
    app._manifest_loaded = False
    app._on_tab_changed()
    assert loads == [], "Tools tab must not fetch the catalogue"
    app.notebook._selected = 1  # Plugins tab
    app._on_tab_changed()
    assert loads == [True], "selecting the Plugins tab should fetch the catalogue once"

    # --- install-from-file with no file chosen degrades gracefully ---
    app._install_pack_from_file()
    # --- remove with the confirm dialog answering "no" must not delete anything ---
    app._remove_pack("audio_tools")
    # --- install guide dialog builds ---
    app._install_guide()
    # --- keyboard helpers ---
    app._focus_search()
    app._clear_filters()

    print("GUI HARNESS PASSED")
    print("  Tools tab + Plugins tab constructed; tool table and plugin rows rendered")
    print("  search/selection, plugin states, progress/offline/download events all handled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
