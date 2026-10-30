"""Encoding — base64, hex, URLs, hashes and ciphers."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import html
import re
import textwrap
import urllib.parse
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import human_size, need_file, out_path, read_text, report_table, write_text


def _payload(v, key: str = "text") -> str:
    path = str(v.get("file") or "").strip()
    if path:
        return read_text(need_file(path))
    text = str(v.get(key) or "")
    if not text:
        raise ToolError("Type something, or choose a file")
    return text


def _result(v, ctx, text: str, name: str = "result.txt") -> str:
    if str(v.get("output") or "").strip():
        target = write_text(out_path(v["output"], name), text)
        ctx.output(str(target))
        ctx.log(f"Saved to {target}")
    ctx.log(text if len(text) <= 4000 else text[:4000] + " …")
    return f"{len(text)} characters" if len(text) > 4000 else ""


# --------------------------------------------------------------------------
# Base64 / base32 / ascii85
# --------------------------------------------------------------------------
@tool(id="base64-encode", name="Base64 Encode", category="Encoding",
      summary="Encode text or a file to Base64, with optional line wrapping.",
      keywords="base64 encode b64 text file",
      fields=[F.multi("text", "Text", rows=8),
              F.file("file", "…or read a file", required=False),
              F.integer("wrap", "Wrap at (characters, 0 = no wrapping)", 76, minimum=0, maximum=200),
              F.save("output", "Save result to", required=False)])
def base64_encode(v, ctx):
    raw = _payload(v).encode("utf-8")
    encoded = base64.b64encode(raw).decode("ascii")
    if v["wrap"]:
        encoded = "\n".join(textwrap.wrap(encoded, v["wrap"]))
    return _result(v, ctx, encoded, "encoded.txt")


@tool(id="base64-decode", name="Base64 Decode", category="Encoding",
      summary="Turn Base64 back into text, tolerating line breaks and missing padding.",
      keywords="base64 decode b64 text unpack",
      fields=[F.multi("text", "Base64", rows=8),
              F.file("file", "…or read from a file", required=False),
              F.save("output", "Save result to", required=False)])
def base64_decode(v, ctx):
    raw = re.sub(r"\s+", "", _payload(v))
    raw += "=" * (-len(raw) % 4)
    try:
        decoded = base64.b64decode(raw, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise ToolError(f"Not valid Base64: {exc}") from exc
    try:
        text = decoded.decode("utf-8")
    except UnicodeDecodeError:
        ctx.log(f"! Result is binary ({human_size(len(decoded))}); showing a hex preview")
        return _result(v, ctx, decoded[:256].hex(" "), "decoded.bin")
    return _result(v, ctx, text, "decoded.txt")


@tool(id="base64-file", name="Base64 a File", category="Encoding",
      summary="Encode a file to Base64 text, or rebuild a file from Base64 — for embedding.",
      keywords="base64 file embed data uri binary",
      fields=[F.file("file", "File"),
              F.choice("action", "Action", ["Encode file to Base64", "Decode Base64 file to binary"],
                       "Encode file to Base64"),
              F.save("output", "Save result to", required=False)])
def base64_file(v, ctx):
    path = need_file(v["file"])
    if v["action"].startswith("Encode"):
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        target = out_path(v["output"], path.name + ".b64.txt")
        write_text(target, "\n".join(textwrap.wrap(encoded, 76)))
        ctx.output(str(target))
        return f"{human_size(path.stat().st_size)} → {human_size(target.stat().st_size)} text ({target.name})"
    raw = re.sub(r"\s+", "", read_text(path))
    raw += "=" * (-len(raw) % 4)
    try:
        data = base64.b64decode(raw)
    except (binascii.Error, ValueError) as exc:
        raise ToolError(f"Not valid Base64: {exc}") from exc
    target = out_path(v["output"], path.stem.replace(".b64", "") or "decoded.bin")
    target.write_bytes(data)
    ctx.output(str(target))
    return f"Wrote {human_size(len(data))} to {target}"


@tool(id="base32-codec", name="Base32 Encode / Decode", category="Encoding",
      summary="Base32 is case-insensitive and human-readable — good for codes people retype.",
      keywords="base32 encode decode code",
      fields=[F.multi("text", "Text", rows=6),
              F.choice("action", "Action", ["Encode", "Decode"], "Encode")])
def base32_codec(v, ctx):
    text = v["text"].strip()
    if not text:
        raise ToolError("Type something first")
    if v["action"] == "Encode":
        return base64.b32encode(text.encode("utf-8")).decode("ascii")
    try:
        return base64.b32decode(text.upper() + "=" * (-len(text) % 8)).decode("utf-8", "replace")
    except (binascii.Error, ValueError) as exc:
        raise ToolError(f"Not valid Base32: {exc}") from exc


@tool(id="ascii85-codec", name="Ascii85 Encode / Decode", category="Encoding",
      summary="Compact text-safe binary encoding, as used inside PDF files.",
      keywords="ascii85 base85 encode decode pdf",
      fields=[F.multi("text", "Text", rows=6),
              F.choice("action", "Action", ["Encode", "Decode"], "Encode")])
def ascii85_codec(v, ctx):
    text = v["text"].strip()
    if not text:
        raise ToolError("Type something first")
    try:
        if v["action"] == "Encode":
            return base64.a85encode(text.encode("utf-8")).decode("ascii")
        return base64.a85decode(text.encode("ascii")).decode("utf-8", "replace")
    except (binascii.Error, ValueError) as exc:
        raise ToolError(f"Ascii85 error: {exc}") from exc


# --------------------------------------------------------------------------
# Hex
# --------------------------------------------------------------------------
@tool(id="hex-encode", name="Text to Hex", category="Encoding",
      summary="Convert text to hexadecimal bytes, spaced or continuous.",
      keywords="hex encode hexadecimal bytes convert",
      fields=[F.multi("text", "Text", rows=6),
              F.flag("spaces", "Separate bytes with spaces", True),
              F.flag("prefix", "Prefix each byte with 0x", False),
              F.save("output", "Save result to", required=False)])
def hex_encode(v, ctx):
    raw = v["text"].encode("utf-8")
    if not raw:
        raise ToolError("Type something first")
    if v["prefix"]:
        text = " ".join(f"0x{b:02x}" for b in raw)
    elif v["spaces"]:
        text = raw.hex(" ")
    else:
        text = raw.hex()
    return _result(v, ctx, text, "hex.txt")


@tool(id="hex-decode", name="Hex to Text", category="Encoding",
      summary="Turn hexadecimal back into readable text, ignoring spaces, colons and 0x.",
      keywords="hex decode hexadecimal text convert",
      fields=[F.multi("text", "Hex", rows=6),
              F.save("output", "Save result to", required=False)])
def hex_decode(v, ctx):
    raw = re.sub(r"(?i)0x", "", v["text"])
    raw = re.sub(r"[^0-9a-fA-F]", "", raw)
    if len(raw) % 2:
        raw = "0" + raw
    try:
        data = bytes.fromhex(raw)
    except ValueError as exc:
        raise ToolError(f"Not valid hex: {exc}") from exc
    return _result(v, ctx, data.decode("utf-8", errors="replace"), "decoded.txt")


@tool(id="hexdump", name="Hex Dump", category="Encoding",
      summary="Classic offset/hex/ASCII view of a file's first bytes — inspect any binary.",
      keywords="hexdump hex view binary inspect bytes offset ascii",
      fields=[F.file("file", "File"),
              F.integer("offset", "Start at byte", 0, minimum=0),
              F.integer("length", "Bytes to show", 512, minimum=16, maximum=65536),
              F.save("output", "Save dump to", required=False)])
def hexdump(v, ctx):
    path = need_file(v["file"])
    with open(path, "rb") as fh:
        fh.seek(v["offset"])
        data = fh.read(v["length"])
    lines = []
    for start in range(0, len(data), 16):
        chunk = data[start:start + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk).ljust(47)
        text_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{v['offset'] + start:08x}  {hex_part}  |{text_part}|")
    body = "\n".join(lines)
    if v["output"].strip():
        target = write_text(out_path(v["output"], "dump.txt"), body)
        ctx.output(str(target))
    ctx.log(body)
    return f"{len(data)} byte(s) from {path.name}"


# --------------------------------------------------------------------------
# URLs & HTML
# --------------------------------------------------------------------------
@tool(id="url-encode", name="URL Encode", category="Encoding",
      summary="Percent-encode text so it is safe inside a URL or query string.",
      keywords="url encode percent escape query string",
      fields=[F.multi("text", "Text", rows=6),
              F.choice("mode", "Mode", ["Component (everything escaped)", "Whole URL (keep :/?#)"],
                       "Component (everything escaped)")])
def url_encode(v, ctx):
    text = v["text"]
    if not text:
        raise ToolError("Type something first")
    return (urllib.parse.quote(text, safe="") if v["mode"].startswith("Component")
            else urllib.parse.quote(text, safe=":/?#[]@!$&'()*+,;=~"))


@tool(id="url-decode", name="URL Decode", category="Encoding",
      summary="Turn %20-style escapes back into readable text.",
      keywords="url decode unescape percent query",
      fields=[F.multi("text", "Text", rows=6),
              F.flag("plus_is_space", "Treat + as a space", True)])
def url_decode(v, ctx):
    text = v["text"].strip()
    if not text:
        raise ToolError("Type something first")
    if v["plus_is_space"]:
        text = text.replace("+", " ")
    return urllib.parse.unquote(text)


@tool(id="url-parts", name="Break Down a URL", category="Encoding",
      summary="Split a URL into scheme, host, port, path, query parameters and fragment.",
      keywords="url parse parts query params domain host",
      fields=[F.text("url", "URL", "https://example.com:8443/a/b?x=1&y=2#top", required=True)])
def url_parts(v, ctx):
    parsed = urllib.parse.urlsplit(v["url"].strip())
    params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    ctx.log(report_table([{"parameter": k, "value": val} for k, val in params],
                         ["parameter", "value"]) if params else "(no query parameters)")
    return {
        "scheme": parsed.scheme, "host": parsed.hostname,
        "port": parsed.port or "(default)", "path": parsed.path,
        "query": parsed.query, "fragment": parsed.fragment,
        "username": parsed.username or "",
        "file_name": Path(parsed.path).name,
        "parameters": dict(params),
    }


@tool(id="html-encode", name="Escape HTML", category="Encoding",
      summary="Escape characters so text displays literally on a web page.",
      keywords="html escape encode entities safe",
      fields=[F.multi("text", "Text", rows=6),
              F.flag("quotes", "Escape quotes too", True)])
def html_encode(v, ctx):
    text = v["text"]
    if not text:
        raise ToolError("Type something first")
    return html.escape(text, quote=v["quotes"])


@tool(id="html-decode", name="Unescape HTML", category="Encoding",
      summary="Turn &amp; and &#39; entities back into real characters.",
      keywords="html unescape decode entities",
      fields=[F.multi("text", "Text", rows=6)])
def html_decode(v, ctx):
    text = v["text"]
    if not text:
        raise ToolError("Type something first")
    return html.unescape(text)


@tool(id="unicode-escape", name="Unicode Escapes", category="Encoding",
      summary="Convert text to \\uXXXX escapes, or turn escapes back into real characters.",
      keywords="unicode escape codepoint u+ convert ascii",
      fields=[F.multi("text", "Text", rows=6),
              F.choice("action", "Action", ["Escape to \\uXXXX", "Unescape to characters",
                                            "Show code points"], "Escape to \\uXXXX")])
def unicode_escape(v, ctx):
    text = v["text"]
    if not text:
        raise ToolError("Type something first")
    if v["action"].startswith("Escape"):
        return text.encode("unicode_escape").decode("ascii")
    if v["action"].startswith("Unescape"):
        try:
            return text.encode("ascii", "backslashreplace").decode("unicode_escape")
        except UnicodeDecodeError as exc:
            raise ToolError(f"Could not decode the escapes: {exc}") from exc
    rows = [{"character": ch, "code_point": f"U+{ord(ch):04X}", "decimal": ord(ch),
             "utf8": ch.encode("utf-8").hex(" ")} for ch in dict.fromkeys(text)]
    ctx.log(report_table(rows[:80]))
    return f"{len(rows)} distinct character(s)"


@tool(id="punycode", name="International Domains", category="Encoding",
      summary="Convert an international domain to punycode (xn--) and back.",
      keywords="punycode idn domain international xn--",
      fields=[F.text("domain", "Domain", "उदाहरण.भारत", required=True),
              F.choice("action", "Action", ["To punycode", "From punycode"], "To punycode")])
def punycode(v, ctx):
    domain = v["domain"].strip()
    if not domain:
        raise ToolError("Give a domain name")
    if v["action"] == "To punycode":
        return domain.encode("idna").decode("ascii")
    try:
        return domain.encode("ascii").decode("idna")
    except UnicodeError as exc:
        raise ToolError(f"Not a valid punycode domain: {exc}") from exc


# --------------------------------------------------------------------------
# Ciphers & codelines
# --------------------------------------------------------------------------
@tool(id="rot13", name="ROT13 / Caesar Shift", category="Encoding",
      summary="Rotate letters by a chosen shift — ROT13 for puzzles, ROT47 for symbols.",
      keywords="rot13 caesar shift cipher rotate letters",
      fields=[F.multi("text", "Text", rows=6),
              F.integer("shift", "Shift by", 13, minimum=1, maximum=25),
              F.choice("alphabet", "Alphabet", ["Letters only", "Letters and digits"], "Letters only")])
def rot13(v, ctx):
    text = v["text"]
    if not text:
        raise ToolError("Type something first")
    out = []
    for ch in text:
        if ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            out.append(chr((ord(ch) - base + v["shift"]) % 26 + base))
        elif v["alphabet"] == "Letters and digits" and ch.isdigit():
            out.append(chr((ord(ch) - ord("0") + v["shift"]) % 10 + ord("0")))
        else:
            out.append(ch)
    return "".join(out)


@tool(id="morse-code", name="Morse Code", category="Encoding",
      summary="Translate text to Morse, or Morse back to text.",
      keywords="morse code dots dashes translate telegraph",
      fields=[F.multi("text", "Text or Morse", rows=6),
              F.choice("action", "Action", ["Text → Morse", "Morse → Text"], "Text → Morse")])
def morse_code(v, ctx):
    table = {"A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.",
             "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..", "M": "--", "N": "-.",
             "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-", "U": "..-",
             "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--", "Z": "--..",
             "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
             "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
             ".": ".-.-.-", ",": "--..--", "?": "..--..", "!": "-.-.--", "/": "-..-.",
             "-": "-....-", "(": "-.--.", ")": "-.--.-", " ": "/"}
    text = v["text"].strip()
    if not text:
        raise ToolError("Type something first")
    if v["action"].startswith("Text"):
        return " ".join(table.get(ch.upper(), "") for ch in text).strip()
    reverse = {value: key for key, value in table.items()}
    words = text.split(" / ")
    out = []
    for word in words:
        out.append("".join(reverse.get(code, "?") for code in word.split()))
    return " ".join(out)


@tool(id="text-to-binary", name="Text to Binary", category="Encoding",
      summary="Show text as 8-bit binary, or read binary back into text.",
      keywords="binary bits text convert 01001",
      fields=[F.multi("text", "Text or binary", rows=6),
              F.choice("action", "Action", ["Text → binary", "Binary → text"], "Text → binary")])
def text_to_binary(v, ctx):
    text = v["text"]
    if not text.strip():
        raise ToolError("Type something first")
    if v["action"].startswith("Text"):
        return " ".join(f"{byte:08b}" for byte in text.encode("utf-8"))
    bits = re.sub(r"[^01]", "", text)
    if len(bits) % 8:
        raise ToolError("The binary is not a whole number of bytes")
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)).decode("utf-8", "replace")


# --------------------------------------------------------------------------
# Hashes
# --------------------------------------------------------------------------
ALGORITHMS = ["sha256", "sha1", "md5", "sha512", "sha3_256", "blake2b", "blake2s"]


@tool(id="hash-text", name="Hash Text", category="Encoding",
      summary="Fingerprint a piece of text with any common hash algorithm.",
      keywords="hash text sha256 md5 checksum fingerprint digest",
      fields=[F.multi("text", "Text", rows=6),
              F.choice("algorithm", "Algorithm", ALGORITHMS, "sha256"),
              F.flag("uppercase", "Uppercase the result", False)])
def hash_text(v, ctx):
    text = v["text"]
    if not text:
        raise ToolError("Type something first")
    digest = hashlib.new(v["algorithm"], text.encode("utf-8")).hexdigest()
    return digest.upper() if v["uppercase"] else digest


@tool(id="hash-file", name="Hash a File", category="Encoding",
      summary="Compute a file's checksum to prove it is the file you think it is.",
      keywords="hash file checksum sha256 md5 verify digest",
      fields=[F.file("file", "File"),
              F.choice("algorithm", "Algorithm", ALGORITHMS, "sha256"),
              F.save("output", "Save checksum to", required=False)])
def hash_file_tool(v, ctx):
    from ._util import hash_file as digest_file
    path = need_file(v["file"])
    ctx.progress(5, "reading")
    digest = digest_file(path, v["algorithm"])
    ctx.log(f"{v['algorithm']}  {digest}")
    if v["output"].strip():
        target = write_text(out_path(v["output"], path.name + ".hash"),
                            f"{digest}  {path.name}\n")
        ctx.output(str(target))
    return {"file": path.name, "bytes": path.stat().st_size, v["algorithm"]: digest}


@tool(id="hash-all", name="All Checksums at Once", category="Encoding",
      summary="Every common hash for one file, in a single pass — for release notes.",
      keywords="hash all algorithms checksums release digests",
      fields=[F.file("file", "File"),
              F.save("output", "Save checksums to", required=False)])
def hash_all(v, ctx):
    path = need_file(v["file"])
    algorithms = ["md5", "sha1", "sha256", "sha512", "blake2b"]
    digests = {name: hashlib.new(name) for name in algorithms}
    read = 0
    size = path.stat().st_size or 1
    with open(path, "rb") as fh:
        while True:
            block = fh.read(1 << 20)
            if not block:
                break
            read += len(block)
            for digest in digests.values():
                digest.update(block)
            ctx.progress(read / size * 100, f"{human_size(read)} of {human_size(size)}")
            ctx.check_cancel()
    rows = [{"algorithm": name, "digest": digest.hexdigest()} for name, digest in digests.items()]
    ctx.log(report_table(rows))
    if v["output"].strip():
        target = write_text(out_path(v["output"], path.name + ".checksums.txt"),
                            "\n".join(f"{r['algorithm']}: {r['digest']}" for r in rows) + "\n")
        ctx.output(str(target))
    return f"{len(rows)} checksum(s) for {path.name}"


@tool(id="hmac-calc", name="HMAC Signature", category="Encoding",
      summary="Sign a message with a secret key — how APIs verify that a request is genuine.",
      keywords="hmac signature sign key api secret",
      fields=[F.multi("text", "Message", rows=5),
              F.secret("key", "Secret key", required=True),
              F.choice("algorithm", "Algorithm", ["sha256", "sha1", "md5", "sha512"], "sha256")])
def hmac_calc(v, ctx):
    message = v["text"].encode("utf-8")
    if not message:
        raise ToolError("Type a message to sign")
    signature = hmac.new(v["key"].encode("utf-8"), message, v["algorithm"]).hexdigest()
    ctx.log(f"hex: {signature}")
    ctx.log(f"base64: {base64.b64encode(bytes.fromhex(signature)).decode()}")
    return {"algorithm": v["algorithm"], "signature": signature}


@tool(id="crc32", name="CRC32 Checksum", category="Encoding",
      summary="The quick 32-bit checksum used to detect accidental file corruption.",
      keywords="crc32 checksum crc file integrity",
      fields=[F.file("file", "File", required=False),
              F.multi("text", "…or text", rows=4)])
def crc32(v, ctx):
    import zlib
    path = str(v["file"] or "").strip()
    data = need_file(path).read_bytes() if path else str(v["text"] or "").encode("utf-8")
    if not data:
        raise ToolError("Choose a file or type some text")
    value = zlib.crc32(data) & 0xFFFFFFFF
    return {"crc32_hex": f"{value:08x}", "crc32_decimal": value, "bytes": len(data)}


@tool(id="hash-identify", name="Identify a Hash", category="Encoding",
      summary="Work out which algorithm produced a hash from its length and characters.",
      keywords="identify hash type algorithm length guess",
      fields=[F.text("hash", "Hash", required=True)])
def hash_identify(v, ctx):
    value = re.sub(r"\s", "", v["hash"])
    length = len(value)
    if not re.fullmatch(r"[0-9a-fA-F]+", value):
        raise ToolError("That does not look like a hex hash")
    guesses = {
        32: ["MD5", "NTLM", "MD4"], 40: ["SHA-1", "MySQL5"], 56: ["SHA-224"],
        64: ["SHA-256", "SHA3-256", "BLAKE2s"], 96: ["SHA-384"], 128: ["SHA-512", "SHA3-512", "BLAKE2b"],
        16: ["CRC32 / MySQL323"], 8: ["CRC32 (no padding)"],
    }.get(length, [])
    if not guesses:
        return {"length": length, "guess": "unknown length — not a standard hex digest"}
    return {"length": length, "likely": guesses[0], "could_also_be": guesses[1:]}


@tool(id="jwt-decode", name="Decode a JWT", category="Encoding",
      summary="Read a JSON Web Token's header and payload — signature is shown, not verified.",
      keywords="jwt token decode bearer claims json web token",
      fields=[F.multi("text", "Token", rows=5)])
def jwt_decode(v, ctx):
    token = v["text"].strip()
    parts = token.split(".")
    if len(parts) != 3:
        raise ToolError("A JWT has three dot-separated parts")
    import json as jsonlib

    def segment(part: str, label: str):
        padded = part + "=" * (-len(part) % 4)
        try:
            return jsonlib.loads(base64.urlsafe_b64decode(padded))
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"The {label} is not valid base64 JSON: {exc}") from exc

    header = segment(parts[0], "header")
    payload = segment(parts[1], "payload")
    ctx.log("HEADER")
    ctx.log(jsonlib.dumps(header, indent=2))
    ctx.log("PAYLOAD")
    ctx.log(jsonlib.dumps(payload, indent=2))
    for claim in ("exp", "iat", "nbf"):
        if claim in payload:
            import datetime as dt
            ctx.log(f"{claim}: {dt.datetime.fromtimestamp(payload[claim])}")
    ctx.log("Signature is shown only — this tool does not verify it.")
    return {"algorithm": header.get("alg"), "type": header.get("typ"),
            "claims": list(payload.keys())}


@tool(id="text-fingerprint", name="Text Fingerprint", category="Encoding",
      summary="A short, stable ID for a block of text — handy for spotting duplicates.",
      keywords="fingerprint id short hash duplicate text",
      fields=[F.multi("text", "Text", rows=6),
              F.integer("length", "Length", 12, minimum=4, maximum=64)])
def text_fingerprint(v, ctx):
    text = " ".join(v["text"].split())
    if not text:
        raise ToolError("Type something first")
    digest = hashlib.sha256(text.lower().encode("utf-8")).hexdigest()[:v["length"]]
    return {"fingerprint": digest, "characters": len(text), "words": len(text.split())}
