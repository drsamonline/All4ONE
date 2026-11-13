"""Hostile input: no tool may answer a bad paste with a Python traceback.

    python tests/test_hostile_input.py

The sweep (``tests/sweep.py``) proves every runnable tool works on *well-formed*
fixtures. This is the other half: the text a person actually pastes — a lone
surrogate from a mis-decoded file, a NUL, a bidi override, a 20 kB line — must
either produce a result or a ``ToolError`` the UI can show. Anything else is a
crash, and the runner turns a crash into a traceback on screen.

The payloads are a BLNS-shaped subset (the Big List of Naughty Strings, MIT),
chosen for what breaks Python and XML rather than for what breaks a database.
"""
from __future__ import annotations

import base64
import hashlib
import signal
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import registry  # noqa: E402
from core.tool import ToolError  # noqa: E402
from tools import documents  # noqa: E402
from tools._util import text_bytes, xml_safe  # noqa: E402

ok = 0
fail = 0


def check(name, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1
        print("PASS  " + name)
    else:
        fail += 1
        print("FAIL  " + name + (("  (" + str(detail) + ")") if detail else ""))


class Ctx:
    """Collects what a tool logged, so a note can be asserted on."""

    def __init__(self):
        self.lines = []
        self.outputs = []

    def log(self, message=""):
        self.lines.append(str(message))

    def progress(self, value, note=""):
        pass

    def check_cancel(self):
        pass

    def output(self, path):
        self.outputs.append(path)


class Timeout(Exception):
    pass


def _alarm(_signum, _frame):
    raise Timeout()


HAS_ALARM = hasattr(signal, "SIGALRM")
if HAS_ALARM:
    signal.signal(signal.SIGALRM, _alarm)


# --------------------------------------------------------------------------
# The payload matrix
# --------------------------------------------------------------------------
PAYLOADS = {
    "lone surrogate (surrogateescape)": "\ud800abc",
    "NUL": "a\x00b",
    "C0 controls": "\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f",
    "bidi override": "\u202eabc\u202c",
    "zero-width joiners": "a\u200bb\u200dc\u200ed",
    "combining marks": "e\u0301" * 50,
    "quotes and a script tag": 'he said "it\'s" <script>alert(1)</script> & \u00a0nbsp',
    "HTML entities": "&amp;&lt;&gt;&#0;&#x1F600;",
    "CRLF mix": "\r\n\r\r\n\n",
    "emoji and a flag": "\U0001F600\U0001F1EE\U0001F1F3",
    "spreadsheet formula": "=1+1,@SUM(A1),+cmd|' /C calc'!A0",
    "20 kB single line": "x" * 20000,
}

# File-shaped tools are covered by the sweep; here we only exercise the ones a
# pasted block of text reaches.
SKIP_IDS = {
    "hash-folder", "hash-every-file", "base64-file",  # file inputs, not text
}


def text_tools():
    for t in registry.all_tools():
        keys = {f.key for f in t.fields}
        if "text" not in keys or t.destructive or t.id in SKIP_IDS:
            continue
        if any(f.kind in ("file", "files", "dir") and f.required for f in t.fields):
            continue
        yield t


def run(tool, payload):
    values = tool.defaults()
    values["text"] = payload
    for fld in tool.fields:
        if fld.kind == "save":
            values[fld.key] = ""
    values = tool.normalise(values)
    ctx = Ctx()
    if HAS_ALARM:
        signal.setitimer(signal.ITIMER_REAL, 15)
    try:
        return tool.run(values, ctx), ctx
    finally:
        if HAS_ALARM:
            signal.setitimer(signal.ITIMER_REAL, 0)


# --------------------------------------------------------------------------
# 1. The matrix: every text tool x every payload
# --------------------------------------------------------------------------
crashes = []
slow = []
covered = 0
for tool in text_tools():
    covered += 1
    for label, payload in PAYLOADS.items():
        try:
            run(tool, payload)
        except ToolError:
            pass                     # a refusal the UI can show is fine
        except Timeout:
            slow.append((tool.id, label))
        except Exception as exc:     # noqa: BLE001 - the whole point
            crashes.append((tool.id, label, type(exc).__name__, str(exc)[:120]))

check("the matrix covered the text tools (%d tools x %d payloads)"
      % (covered, len(PAYLOADS)), covered >= 60, covered)
check("no text tool raises on hostile input", not crashes,
      "; ".join("%s/%s %s" % (c[0], c[1], c[2]) for c in crashes[:6]))
check("no text tool hangs on hostile input", not slow, slow[:6])


# --------------------------------------------------------------------------
# 2. A lone surrogate is encoded back to the bytes it came from
# --------------------------------------------------------------------------
original = b"caf\xe9.txt"                      # Latin-1 bytes, not valid UTF-8
decoded = original.decode("utf-8", "surrogateescape")
check("surrogateescape decoding produces a lone surrogate", "\udce9" in decoded, repr(decoded))
check("text_bytes round-trips to the original bytes", text_bytes(decoded) == original,
      text_bytes(decoded))

lone = "\ud800abc"
digest = documents_and_encoding = None
hash_tool = registry.get("hash-text")
result, _ = run(hash_tool, lone)
check("hash-text answers a lone surrogate instead of crashing", isinstance(result, str))
check("hash-text hashes the bytes the text stands for",
      result == hashlib.sha256(b"\xed\xa0\x80abc").hexdigest(), result)

b64_tool = registry.get("base64-encode")
_, b64_ctx = run(b64_tool, lone)
encoded = "".join(b64_ctx.lines).strip()
check("base64-encode answers a lone surrogate", bool(encoded), b64_ctx.lines)
check("base64 decodes back to those same bytes",
      base64.b64decode(encoded) == b"\xed\xa0\x80abc", encoded)

# The regression itself: this is what used to raise UnicodeEncodeError.
try:
    lone.encode("utf-8")
    check("a plain str.encode would still raise (the guard is the helper)", False)
except UnicodeEncodeError:
    check("a plain str.encode would still raise (the guard is the helper)", True)


# --------------------------------------------------------------------------
# 3. xml_safe: what a document writer can and cannot store
# --------------------------------------------------------------------------
check("NUL is replaced", "\x00" not in xml_safe("a\x00b"), repr(xml_safe("a\x00b")))
check("a lone surrogate is replaced", xml_safe("\ud800") == "\ufffd", repr(xml_safe("\ud800")))
check("a tab and a newline survive", xml_safe("a\tb\nc") == "a\tb\nc")
check("ordinary text is untouched", xml_safe("नमस्ते — ok") == "नमस्ते — ok")


# --------------------------------------------------------------------------
# 4. Text to Word: a pasted NUL produces a document, and says what it changed
# --------------------------------------------------------------------------
docx_tool = registry.get("text-to-docx")
if docx_tool is None:
    check("text-to-docx is registered", False)
else:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "hostile.docx"
        values = docx_tool.normalise({"text": "line one\x00\nline\x01two\nfine",
                                      "title": "Hostile \x00title", "output": str(target)})
        ctx = Ctx()
        message = docx_tool.run(values, ctx)
        check("text-to-docx writes a document from NUL-bearing text", target.exists(), message)
        check("it says what it changed", any("replaced" in line for line in ctx.lines), ctx.lines)
        with zipfile.ZipFile(target) as zf:
            xml = zf.read("word/document.xml").decode("utf-8")
        check("the stored XML carries no NUL", "\x00" not in xml)
        check("the surrounding words survive", "line one" in xml and "fine" in xml)
        check("the replacement character is where the NUL was", "\ufffd" in xml)


# --------------------------------------------------------------------------
# 5. A refusal still looks like a refusal, never like a crash
# --------------------------------------------------------------------------
decode_tool = registry.get("base64-decode")
try:
    run(decode_tool, "!!!! not base64 !!!!")
    check("junk Base64 is refused with a ToolError", False, "returned a result")
except ToolError as exc:
    check("junk Base64 is refused with a ToolError", "base64" in str(exc).lower(), exc)
except Exception as exc:  # noqa: BLE001
    check("junk Base64 is refused with a ToolError", False, type(exc).__name__)


print("\n%d passed, %d failed" % (ok, fail))
sys.exit(0 if fail == 0 else 1)
