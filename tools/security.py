"""Security — passwords, encryption, secrets and two-factor codes."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import struct
import time
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import (
    human_size,
    iter_files,
    need_dir,
    need_file,
    out_path,
    report_table,
    require,
    run_command,
)

COMMON_PASSWORDS = {
    "password", "123456", "123456789", "qwerty", "abc123", "password1", "111111",
    "12345678", "iloveyou", "admin", "welcome", "monkey", "letmein", "dragon",
    "sunshine", "princess", "football", "charlie", "aa123456", "donald", "qwerty123",
    "india123", "password123", "1234567890", "master", "hello", "freedom", "whatever",
}


def _entropy_bits(password: str) -> float:
    pools = 0
    if re.search(r"[a-z]", password):
        pools += 26
    if re.search(r"[A-Z]", password):
        pools += 26
    if re.search(r"\d", password):
        pools += 10
    if re.search(r"[^A-Za-z0-9]", password):
        pools += 33
    if not password:
        return 0.0
    import math
    return len(password) * math.log2(pools or 1)


@tool(id="password-strength", name="Password Strength", category="Security",
      summary="Entropy, a crack-time estimate and the specific reasons a password is weak.",
      fields=[F.secret("password", "Password", required=True)])
def password_strength(v, ctx):
    password = v["password"]
    if not password:
        raise ToolError("Type a password to check")
    bits = _entropy_bits(password)
    guesses_per_second = 1e10  # a modern offline attack against a fast hash
    seconds = (2 ** bits) / guesses_per_second if bits else 0

    def human(seconds: float) -> str:
        if seconds < 1:
            return "instantly"
        for limit, name in ((60, "seconds"), (3600, "minutes"), (86400, "hours"),
                            (2_592_000, "days"), (31_536_000, "years")):
            if seconds < limit:
                divisor = {"seconds": 1, "minutes": 60, "hours": 3600,
                           "days": 86400, "years": 31_536_000}[name]
                return f"{seconds / divisor:.0f} {name}"
        if seconds < 31_536_000 * 1000:
            return f"{seconds / 31_536_000:.0f} years"
        if seconds < 31_536_000 * 1e6:
            return f"{seconds / 31_536_000 / 1000:.0f} thousand years"
        return "longer than the age of the universe"

    issues = []
    if len(password) < 12:
        issues.append("shorter than 12 characters")
    if password.lower() in COMMON_PASSWORDS:
        issues.append("appears in the common-password list")
    if re.fullmatch(r"[a-z]+", password):
        issues.append("lowercase only")
    if re.fullmatch(r"\d+", password):
        issues.append("digits only")
    if re.search(r"(.)\1{2,}", password):
        issues.append("repeated characters")
    if re.search(r"(012|123|234|345|456|567|678|789|890|abc|qwe|asd)", password.lower()):
        issues.append("contains a keyboard or numeric sequence")
    if re.search(r"(19|20)\d{2}", password):
        issues.append("contains a year")
    score = min(100, round(bits / 1.28))
    verdict = ("Very strong" if bits >= 90 else "Strong" if bits >= 70 else
               "Reasonable" if bits >= 50 else "Weak" if bits >= 30 else "Very weak")
    ctx.log(report_table([{"measure": "entropy", "value": f"{bits:.0f} bits"},
                          {"measure": "score", "value": f"{score}/100"},
                          {"measure": "verdict", "value": verdict},
                          {"measure": "crack time", "value": human(seconds)}]))
    for issue in issues:
        ctx.log(f"! {issue}")
    return {"entropy_bits": round(bits, 1), "score": score, "verdict": verdict,
            "estimated_crack_time": human(seconds), "issues": issues}


@tool(id="crack-time", name="Hash Crack Time", category="Security",
      summary="How long an attacker needs to brute-force a password hash, by algorithm.",
      fields=[F.secret("password", "Password", required=True),
              F.choice("algorithm", "Hash", ["MD5", "SHA-1", "SHA-256", "bcrypt", "Argon2"],
                       "SHA-256")])
def crack_time(v, ctx):
    bits = _entropy_bits(v["password"])
    speeds = {"MD5": 1e11, "SHA-1": 5e10, "SHA-256": 1e10, "bcrypt": 1e4, "Argon2": 1e3}
    rate = speeds[v["algorithm"]]
    seconds = (2 ** bits) / rate
    rows = []
    for algorithm, speed in speeds.items():
        estimate = (2 ** bits) / speed
        if estimate < 3600:
            human = f"{estimate:.0f} seconds"
        elif estimate < 86400:
            human = f"{estimate / 3600:.1f} hours"
        elif estimate < 31_536_000:
            human = f"{estimate / 86400:.1f} days"
        elif estimate < 31_536_000 * 1000:
            human = f"{estimate / 31_536_000:.0f} years"
        else:
            human = "millennia"
        rows.append({"hash": algorithm, "guesses_per_second": f"{speed:,.0f}",
                     "crack_time": human})
    ctx.log(report_table(rows))
    return {"entropy_bits": round(bits, 1), "algorithm": v["algorithm"],
            "seconds": f"{seconds:.3g}"}


@tool(id="secrets-scan", name="Scan for Secrets", category="Security",
      summary="Look through a project for API keys, tokens and private keys left in code.",
      fields=[F.folder("folder", "Project folder"),
              F.flag("skip_common", "Skip node_modules, .git and virtualenvs", True),
              F.save("report", "Save CSV to", required=False)])
def secrets_scan(v, ctx):
    from ._util import write_csv
    root = need_dir(v["folder"])
    patterns = [
        ("AWS access key", r"AKIA[0-9A-Z]{16}"),
        ("AWS secret", r"(?i)aws_?secret_?access_?key\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})"),
        ("Google API key", r"AIza[0-9A-Za-z\-_]{35}"),
        ("GitHub token", r"gh[pousr]_[0-9A-Za-z]{36}"),
        ("Slack token", r"xox[baprs]-[0-9A-Za-z\-]{10,72}"),
        ("Stripe key", r"(?:sk|pk)_(?:live|test)_[0-9A-Za-z]{24,}"),
        ("Private key", r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
        ("JWT", r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),
        ("Password in code", r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"][^'\"\s]{6,}['\"]"),
        ("Generic secret", r"(?i)(?:api[_-]?key|secret|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"),
    ]
    skip = {"node_modules", ".git", "venv", ".venv", "__pycache__", "dist", "build"}
    hits = []
    for path in iter_files(root, True):
        if v["skip_common"] and any(part in skip for part in path.parts):
            continue
        if path.suffix.lower() in (".png", ".jpg", ".zip", ".exe", ".pdf", ".dll", ".so"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for label, pattern in patterns:
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                snippet = match.group()[:12] + "…"
                hits.append({"kind": label, "file": path.name, "line": line,
                             "preview": snippet})
                ctx.log(f"{label}  {path.name}:{line}")
                break
        ctx.check_cancel()
    if not hits:
        return "No obvious secrets found."
    if v["report"].strip():
        target = write_csv(out_path(v["report"], "secrets.csv"), hits)
        ctx.output(str(target))
    return f"{len(hits)} potential secret(s) — review each one before sharing the code"


@tool(id="pii-scan", name="Scan for Personal Data", category="Security",
      summary="Find emails, phone numbers, card numbers and ID patterns in a folder.",
      fields=[F.folder("folder", "Folder"),
              F.flag("indian", "Include Indian-specific patterns (Aadhaar, PAN, GSTIN)", True)])
def pii_scan(v, ctx):
    root = need_dir(v["folder"])
    patterns = [
        ("Email", r"[\w.+-]+@[\w-]+\.[\w.]{2,}"),
        ("Phone (international)", r"\+\d{1,3}[\s-]?\d{6,14}"),
        ("Card number", r"\b(?:\d[ -]*?){13,16}\b"),
    ]
    if v["indian"]:
        patterns += [
            ("Aadhaar-like (12 digits)", r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
            ("PAN", r"\b[A-Z]{5}\d{4}[A-Z]\b"),
            ("GSTIN", r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z\d]\b"),
            ("IFSC", r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
        ]
    counts: dict[str, int] = {}
    samples: dict[str, str] = {}
    for path in iter_files(root, True):
        if path.suffix.lower() in (".png", ".jpg", ".zip", ".exe", ".pdf"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for label, pattern in patterns:
            for match in re.finditer(pattern, text):
                value = match.group()
                if label == "Card number" and not _luhn_ok(value):
                    continue
                counts[label] = counts.get(label, 0) + 1
                samples.setdefault(label, value[:6] + "…")
        ctx.check_cancel()
    if not counts:
        return "No personal data patterns found."
    rows = [{"type": label, "found": count, "example": samples.get(label, "")}
            for label, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)]
    ctx.log(report_table(rows, ["type", "found", "example"]))
    return f"{sum(counts.values())} potential personal data item(s) across {len(counts)} type(s)"


def _luhn_ok(number: str) -> bool:
    digits = [int(ch) for ch in re.sub(r"\D", "", number)]
    if not 13 <= len(digits) <= 19:
        return False
    checksum = 0
    for index, digit in enumerate(reversed(digits)):
        if index % 2:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


@tool(id="card-validate", name="Validate a Card Number", category="Security",
      summary="Check a card number's Luhn checksum and identify the network.",
      fields=[F.text("number", "Card number", required=True)])
def card_validate(v, ctx):
    digits = re.sub(r"\D", "", v["number"])
    if not digits:
        raise ToolError("Give a card number")
    networks = [("Visa", r"^4"), ("Mastercard", r"^(5[1-5]|2[2-7])"),
                ("American Express", r"^3[47]"), ("RuPay", r"^(60|65|81|82|508)"),
                ("Discover", r"^6(?:011|5)"), ("Diners Club", r"^3(?:0[0-5]|[68])"),
                ("JCB", r"^35")]
    network = next((name for name, pattern in networks if re.match(pattern, digits)), "unknown")
    valid = _luhn_ok(digits)
    return {"number_length": len(digits), "network": network, "luhn_valid": valid,
            "verdict": "valid checksum" if valid else "fails the Luhn check"}


@tool(id="entropy", name="Measure Entropy", category="Security",
      summary="Shannon entropy of a text or file — high values suggest encryption or compression.",
      fields=[F.file("file", "File", required=False),
              F.multi("text", "…or text", rows=5)])
def entropy(v, ctx):
    import math
    path = str(v["file"] or "").strip()
    data = need_file(path).read_bytes()[:4_000_000] if path else str(v["text"] or "").encode("utf-8")
    if not data:
        raise ToolError("Choose a file or type some text")
    counts = {}
    for byte in data:
        counts[byte] = counts.get(byte, 0) + 1
    total = len(data)
    value = -sum((count / total) * math.log2(count / total) for count in counts.values())
    verdict = ("encrypted or compressed" if value > 7.5 else
               "binary data" if value > 6 else
               "text" if value > 3 else "highly repetitive")
    return {"bytes": total, "entropy_bits_per_byte": round(value, 3),
            "maximum_possible": 8.0, "looks_like": verdict}


# --------------------------------------------------------------------------
# Encryption
# --------------------------------------------------------------------------
@tool(id="file-encrypt", name="Encrypt a File", category="Security",
      summary="AES-256 encryption with a passphrase — the file is useless without it.",
      needs=("cryptography",),
      fields=[F.file("file", "File to encrypt"),
              F.secret("password", "Passphrase", required=True),
              F.save("output", "Save encrypted file as", required=False)])
def file_encrypt(v, ctx):
    require("cryptography", "cryptography")
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    path = need_file(v["file"])
    salt = os.urandom(16)
    key = Scrypt(salt=salt, length=32, n=2 ** 15, r=8, p=1).derive(v["password"].encode())
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, path.read_bytes(), None)
    target = out_path(v["output"], path.name + ".a4e")
    target.write_bytes(b"ALL4ONE1" + salt + nonce + ciphertext)
    ctx.output(str(target))
    return (f"Encrypted {path.name} → {target.name} "
            f"({human_size(target.stat().st_size)}). Keep the passphrase safe — "
            f"there is no recovery.")


@tool(id="file-decrypt", name="Decrypt a File", category="Security",
      summary="Decrypt a file this app encrypted, given the right passphrase.",
      needs=("cryptography",),
      fields=[F.file("file", "Encrypted file", filters="Encrypted (*.a4e)"),
              F.secret("password", "Passphrase", required=True),
              F.save("output", "Save decrypted file as", required=False)])
def file_decrypt(v, ctx):
    require("cryptography", "cryptography")
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    path = need_file(v["file"])
    blob = path.read_bytes()
    if not blob.startswith(b"ALL4ONE1"):
        raise ToolError("That is not a file encrypted by this app")
    salt, nonce, ciphertext = blob[8:24], blob[24:36], blob[36:]
    key = Scrypt(salt=salt, length=32, n=2 ** 15, r=8, p=1).derive(v["password"].encode())
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    except Exception as exc:  # noqa: BLE001
        raise ToolError("Wrong passphrase, or the file is damaged") from exc
    name = path.name[:-4] if path.name.endswith(".a4e") else path.stem
    target = out_path(v["output"], name)
    target.write_bytes(plaintext)
    ctx.output(str(target))
    return f"Decrypted to {target.name} ({human_size(len(plaintext))})"


@tool(id="file-shred", name="Shred a File", category="Security",
      summary="Overwrite a file's contents before deleting it, so it cannot be recovered easily.",
      destructive=True,
      fields=[F.file("file", "File to shred"),
              F.integer("passes", "Overwrite passes", 3, minimum=1, maximum=7),
              F.flag("confirm", "Yes, shred it permanently", False)])
def file_shred(v, ctx):
    path = need_file(v["file"])
    if not v["confirm"]:
        return f"Would shred {path.name} with {v['passes']} passes. Tick the confirmation box."
    size = path.stat().st_size
    with open(path, "r+b") as handle:
        for pass_number in range(v["passes"]):
            handle.seek(0)
            remaining = size
            block = os.urandom(min(1 << 20, size or 1))
            while remaining > 0:
                chunk = min(len(block), remaining)
                handle.write(block[:chunk])
                remaining -= chunk
            handle.flush()
            os.fsync(handle.fileno())
            ctx.progress((pass_number + 1) / v["passes"] * 100, f"pass {pass_number + 1}")
    path.unlink()
    return f"Shredded {path.name} ({human_size(size)}, {v['passes']} passes)"


@tool(id="folder-shred", name="Shred a Folder", category="Security",
      summary="Overwrite and delete every file in a folder — irreversible, with a preview.",
      destructive=True,
      fields=[F.folder("folder", "Folder"),
              F.flag("preview", "Preview only (recommended first)", True),
              F.flag("confirm", "Yes, shred everything in it", False)])
def folder_shred(v, ctx):
    root = need_dir(v["folder"])
    files = [path for path in iter_files(root, True) if path.is_file()]
    if not files:
        return "That folder has no files."
    total = sum(path.stat().st_size for path in files)
    if v["preview"]:
        for path in files[:50]:
            ctx.log(f"would shred {path.relative_to(root)}")
        return f"{len(files)} file(s), {human_size(total)} — preview only, nothing deleted"
    if not v["confirm"]:
        raise ToolError("Tick the confirmation box to shred these files")
    done = 0
    for path in files:
        ctx.check_cancel()
        try:
            size = path.stat().st_size
            with open(path, "r+b") as handle:
                handle.write(os.urandom(size))
                handle.flush()
                os.fsync(handle.fileno())
            path.unlink()
            done += 1
        except OSError as exc:
            ctx.log(f"! {path.name}: {exc}")
    for folder in sorted((p for p in root.rglob("*") if p.is_dir()), reverse=True):
        try:
            folder.rmdir()
        except OSError:
            pass
    return f"Shredded {done} of {len(files)} file(s), {human_size(total)}"


@tool(id="pbkdf2", name="Derive a Key (PBKDF2)", category="Security",
      summary="Turn a passphrase into a fixed-length key, the way password managers do.",
      fields=[F.secret("password", "Passphrase", required=True),
              F.text("salt", "Salt", "all4one", help="A random string, stored alongside"),
              F.integer("iterations", "Iterations", 200000, minimum=1000, maximum=2000000),
              F.integer("length", "Key length (bytes)", 32, minimum=8, maximum=64)])
def pbkdf2(v, ctx):
    key = hashlib.pbkdf2_hmac("sha256", v["password"].encode(), v["salt"].encode(),
                              v["iterations"], v["length"])
    return {"hex": key.hex(), "base64": base64.b64encode(key).decode(),
            "iterations": v["iterations"], "length": v["length"]}


@tool(id="secure-compare", name="Constant-Time Compare", category="Security",
      summary="Compare two secrets without leaking timing information — for token checks.",
      fields=[F.secret("first", "First value", required=True),
              F.secret("second", "Second value", required=True)])
def secure_compare(v, ctx):
    match = hmac.compare_digest(v["first"].encode(), v["second"].encode())
    return {"match": match, "note": "compared in constant time"}


@tool(id="totp-generate", name="Two-Factor Code (TOTP)", category="Security",
      summary="Generate the current 6-digit authenticator code from a base32 secret.",
      fields=[F.secret("secret", "Base32 secret", required=True,
                       help="The code shown by Google Authenticator, without spaces"),
              F.integer("digits", "Digits", 6, minimum=6, maximum=8),
              F.integer("period", "Period (seconds)", 30, minimum=15, maximum=120)])
def totp_generate(v, ctx):
    secret = re.sub(r"\s+", "", v["secret"]).upper()
    secret += "=" * (-len(secret) % 8)
    try:
        key = base64.b32decode(secret)
    except Exception as exc:  # noqa: BLE001
        raise ToolError(f"That is not a valid base32 secret: {exc}") from exc
    counter = int(time.time()) // v["period"]
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    code %= 10 ** v["digits"]
    remaining = v["period"] - (int(time.time()) % v["period"])
    ctx.log(f"Current code: {str(code).zfill(v['digits'])}  ({remaining}s left)")
    return {"code": str(code).zfill(v["digits"]), "expires_in_seconds": remaining}


@tool(id="totp-verify", name="Verify a Two-Factor Code", category="Security",
      summary="Check whether a 6-digit code is valid for a secret, allowing clock drift.",
      fields=[F.secret("secret", "Base32 secret", required=True),
              F.text("code", "Code to verify", required=True),
              F.integer("window", "Allow ± windows", 1, minimum=0, maximum=5)])
def totp_verify(v, ctx):
    secret = re.sub(r"\s+", "", v["secret"]).upper()
    secret += "=" * (-len(secret) % 8)
    try:
        key = base64.b32decode(secret)
    except Exception as exc:  # noqa: BLE001
        raise ToolError(f"Invalid base32 secret: {exc}") from exc
    counter = int(time.time()) // 30
    for offset in range(-v["window"], v["window"] + 1):
        digest = hmac.new(key, struct.pack(">Q", counter + offset), hashlib.sha1).digest()
        start = digest[-1] & 0x0F
        value = struct.unpack(">I", digest[start:start + 4])[0] & 0x7FFFFFFF
        if str(value % 1_000_000).zfill(6) == v["code"].strip():
            return {"valid": True, "offset_windows": offset}
    return {"valid": False}


@tool(id="defender-scan", name="Scan a Folder With Defender", category="System",
      summary="Run a Windows Defender scan on a file or folder and report the result.",
      platforms=("win",),
      fields=[F.folder("folder", "Folder to scan"),
              F.choice("kind", "Scan type", ["Quick", "Full", "Custom"], "Custom")])
def defender_scan(v, ctx):
    from ._util import need_dir
    exe = Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / \
        "Windows Defender/MpCmdRun.exe"
    if not exe.exists():
        raise ToolError("Windows Defender's MpCmdRun.exe was not found")
    folder = need_dir(v["folder"])
    kind = {"Quick": "1", "Full": "2", "Custom": "3"}[v["kind"]]
    args = [str(exe), "-Scan", "-ScanType", kind]
    if v["kind"] == "Custom":
        args += ["-File", str(folder)]
    code, out, err = run_command(args, ctx=ctx, timeout=1800)
    if code == 0:
        return "Scan finished with no threats reported"
    if code == 2:
        raise ToolError("Defender reported a threat — open Windows Security for details")
    raise ToolError(f"Scan could not complete: {err.strip()[:200]}")


@tool(id="world-writable", name="World-Writable Files", category="Security",
      summary="Files anyone on the system can modify — a classic privilege-escalation hole.",
      fields=[F.folder("folder", "Folder")])
def world_writable(v, ctx):
    root = need_dir(v["folder"])
    hits = []
    for path in iter_files(root, True):
        try:
            mode = path.stat().st_mode
        except OSError:
            continue
        if mode & 0o002:
            hits.append({"file": path.name, "mode": oct(mode)[-3:],
                         "folder": str(path.parent)})
    if not hits:
        return "No world-writable files found."
    ctx.log(report_table(hits[:100], ["file", "mode", "folder"]))
    return f"{len(hits)} world-writable file(s)"


@tool(id="suspicious-names", name="Suspicious Filenames", category="Security",
      summary="Spot double extensions and disguises like invoice.pdf.exe.",
      fields=[F.folder("folder", "Folder")])
def suspicious_names(v, ctx):
    root = need_dir(v["folder"])
    risky = {".exe", ".scr", ".bat", ".cmd", ".js", ".vbs", ".ps1", ".jar", ".hta", ".msi"}
    documents = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".png", ".txt"}
    hits = []
    for path in iter_files(root, True):
        parts = path.name.split(".")
        if len(parts) >= 3:
            final = "." + parts[-1].lower()
            previous = "." + parts[-2].lower()
            if final in risky and previous in documents:
                hits.append({"file": path.name, "risk": "document extension then executable"})
                continue
        if path.suffix.lower() in risky:
            hits.append({"file": path.name, "risk": "executable file"})
        if re.search(r"[\u202a-\u202e\u2066-\u2069]", path.name):
            hits.append({"file": path.name, "risk": "bidirectional control characters"})
    if not hits:
        return "Nothing suspicious in those filenames."
    ctx.log(report_table(hits[:100], ["file", "risk"]))
    return f"{len(hits)} file(s) worth a second look"
