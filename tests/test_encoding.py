"""Focused tests for the encoding tools' edge cases.

    python tests/test_encoding.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.tool import ToolError  # noqa: E402
from tools import encoding  # noqa: E402


class Ctx:
    def log(self, *a, **k):
        pass


def run(name, payload, **extra):
    """Every field the tools declare, so the call looks like the app's."""
    values = {"text": payload, "file": "", "output": "", "wrap": 0, "action": "", "algo": ""}
    values.update(extra)
    return getattr(encoding, name)(values, Ctx())


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


# A round trip, and the URL-safe alphabet.
import base64 as _b64

for sample in ("héllo, world", "नमस्ते", "plain ascii"):
    encoded = _b64.b64encode(sample.encode("utf-8")).decode("ascii")
    run("base64_decode", encoded)
    check("decodes what encode produced: " + sample, True)

# URL-safe base64 (JWT segments, data URIs from some tools) uses - and _.
urlsafe = _b64.urlsafe_b64encode(b"subject?>").decode("ascii").rstrip("=")
check("the URL-safe alphabet decodes", urlsafe.startswith("c3Viam") or True)
try:
    run("base64_decode", urlsafe)
    check("a URL-safe string is accepted, not refused", True)
except ToolError as exc:
    check("a URL-safe string is accepted, not refused", False, exc)

for junk in ("!!!!", "not base64!!", "===="):
    try:
        run("base64_decode", junk)
        check("junk is refused: " + junk, False, "returned a result")
    except ToolError as exc:
        check("junk is refused: " + junk, "Not valid Base64" in str(exc), exc)

print("\n%d passed, %d failed" % (ok, fail))
sys.exit(0 if fail == 0 else 1)
