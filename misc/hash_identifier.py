from __future__ import annotations

import argparse
import hashlib
import re

# (name, hex-lengths, regex hints) — ordered so more specific families win.
_FAMILIES = [
    ("MD5", {32}, r"^[0-9a-f]{32}$"),
    ("MD4", {32}, None),
    ("RIPEMD-160", {40}, None),
    ("SHA-1", {40}, r"^[0-9a-f]{40}$"),
    ("SHA-256 / HMAC-SHA256", {64}, r"^[0-9a-f]{64}$"),
    ("SHA-512", {128}, None),
    ("SHA-384", {96}, None),
    ("NTLM", {32}, None),
    ("MySQL(4.1+)", {41}, r"^\*[0-9A-F]{40}$"),
    ("PostgreSQL SCRAM/MD5", {35}, r"^md5[0-9a-f]{32}$"),
    ("CRC32", {8}, None),
    ("Adler-32", {8}, None),
    ("bcrypt", {60}, r"^\$2[aby]?\$\d{2}\$[./A-Za-z0-9]{53}$"),
    ("scrypt", {90, 97}, r"^\$s?crypt\$"),
    ("argon2", {100, 110, 120}, r"^\$argon2(id|i|d)\$v=\d+\$"),
    ("PBKDF2-SHA1", {32, 40}, None),
    ("DES Unix crypt", {13}, r"^[./0-9A-Za-z]{13}$"),
]

_LEN_BUCKETS: dict[int, list[str]] = {}
for _name, _lens, _pat in _FAMILIES:
    for _l in _lens:
        _LEN_BUCKETS.setdefault(_l, []).append(_name)


def run(args=None):
    p = argparse.ArgumentParser(description="Identify likely hash algorithm(s) from a hash string.")
    p.add_argument("hash")
    p.add_argument("--verify", metavar="TEXT", help="Optionally verify the hash against this plaintext.")
    a = p.parse_args(args or [])

    h = a.hash.strip()
    low = h.lower()
    if not re.fullmatch(r"[\$a-zA-Z0-9*+/=.:_-]+", h):
        print(f"'{h}' does not look like a hash string.")
        return 1

    candidates: list[str] = []
    for name, lens, pat in _FAMILIES:
        if len(h) not in lens:
            continue
        if pat and not re.match(pat, h):
            continue
        candidates.append(name)
    # Fallback: pure length heuristic on hex strings.
    if not candidates and re.fullmatch(r"[0-9a-f]{6,128}", low):
        candidates = _LEN_BUCKETS.get(len(low), ["Unknown"])

    print(f"Input: {h}")
    print(f"Length: {len(h)} chars")
    print(f"Candidates: {', '.join(candidates) if candidates else 'no match'}")

    if a.verify:
        data = a.verify.encode()
        table = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512,
            "sha384": hashlib.sha384,
            "sha224": hashlib.sha224,
            "blake2b": hashlib.blake2b,
            "blake2s": hashlib.blake2s,
        }
        for label, fn in table.items():
            digest = fn(data).hexdigest()
            if digest == low:
                print(f"MATCH: {label.upper()}('{a.verify}') == input")
                return 0
        print("VERIFY: no common hashlib algorithm matches the supplied plaintext.")
        return 1
    return 0
