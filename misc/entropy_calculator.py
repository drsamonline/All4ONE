from __future__ import annotations

import argparse
import math
import re
import secrets
import string


def _charset_bits(pw: str) -> float:
    bits = 0.0
    if re.search(r"[a-z]", pw):
        bits += 26
    if re.search(r"[A-Z]", pw):
        bits += 26
    if re.search(r"[0-9]", pw):
        bits += 10
    specials = set(pw) & (set(string.punctuation) | set(" \t"))
    if specials:
        bits += len(specials)
    return bits


def run(args=None):
    p = argparse.ArgumentParser(description="Estimate password entropy and strength.")
    p.add_argument("--password", help="Password to analyse (omit to generate a strong one).")
    p.add_argument("--length", type=int, default=20, help="Generated password length (default 20).")
    p.add_argument("--count", type=int, default=3, help="How many candidates to generate (default 3).")
    a = p.parse_args(args or [])

    if not a.password:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}"
        for _ in range(max(1, min(a.count, 20))):
            pw = "".join(secrets.choice(alphabet) for _ in range(max(8, a.length)))
            print(pw)
        return 0

    pw = a.password
    charset = _charset_bits(pw)
    naive = len(pw) * (math.log2(charset) if charset else 0)
    # Shannon entropy of the character distribution (captures repeats/patterns).
    freq: dict[str, int] = {}
    for ch in pw:
        freq[ch] = freq.get(ch, 0) + 1
    shannon = -sum((c / len(pw)) * math.log2(c / len(pw)) for c in freq.values()) * len(pw) if pw else 0.0
    est = min(naive, shannon) if shannon else naive

    if est < 28:
        verdict = "WEAK — easily brute-forced; use 14+ random characters."
    elif est < 60:
        verdict = "MODERATE — okay for low-value accounts."
    elif est < 80:
        verdict = "STRONG — suitable for most accounts."
    else:
        verdict = "EXCELLENT — resistant to offline attacks."

    print(f"Length: {len(pw)}")
    print(f"Charset size: {int(charset)}")
    print(f"Naive entropy: {naive:.1f} bits")
    print(f"Shannon entropy: {shannon:.1f} bits")
    print(f"Estimated strength: {est:.1f} bits — {verdict}")
    return 0
