from __future__ import annotations

import argparse
import base64
import binascii


def run(args=None):
    p = argparse.ArgumentParser(description="Strict Base64 encode/decode with validation.")
    p.add_argument("text", nargs="?", help="Input string (omit to read from --file).")
    p.add_argument("--file", help="Read input from a file instead.")
    p.add_argument("--decode", action="store_true", help="Decode instead of encode.")
    p.add_argument("--urlsafe", action="store_true", help="Use URL-safe alphabet (-_ instead of +/).")
    p.add_argument("--no-pad", action="store_true", help="Strip '=' padding on encode / tolerate missing on decode.")
    a = p.parse_args(args or [])

    if a.file:
        data = open(a.file, "rb").read()
    elif a.text is not None:
        data = a.text.encode()
    else:
        print("Provide TEXT or --file.")
        return 2

    enc = base64.urlsafe_b64encode if a.urlsafe else base64.b64encode
    dec = base64.urlsafe_b64decode if a.urlsafe else base64.b64decode

    if a.decode:
        raw = data.strip()
        pad = (-len(raw)) % 4
        if a.no_pad and pad:
            raw += b"=" * pad
        try:
            out = dec(raw)
        except (binascii.Error, ValueError) as exc:
            print(f"Invalid Base64: {exc}")
            return 1
        try:
            print(out.decode())
        except UnicodeDecodeError:
            print(out.hex())
        return 0

    out = enc(data).decode().rstrip("=") if a.no_pad else enc(data).decode()
    print(out)
    return 0
