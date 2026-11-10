"""Generators — QR codes, encoded here rather than by a library.

A QR code is an image of an error-correcting code: byte-mode data, Reed-Solomon
check words, a mask, and a set of fixed patterns a reader finds first. All of it
is arithmetic, so it ships with no dependency — the SVG is text and the PNG is
zlib plus four chunks.

What this covers, and what it does not: versions 1 to 10 (up to 271 bytes at
level L, 213 at M) in byte mode, which is every URL and most labels. A longer
payload is refused with the exact limit rather than quietly truncated.
"""

from __future__ import annotations

import struct
import zlib

from core.tool import F, ToolError, tool

from ._util import out_path

# --------------------------------------------------------------------------
# Tables from ISO/IEC 18004 (all of them checked against a reference encoder)
# --------------------------------------------------------------------------
MAX_VERSION = 10

# total codewords (data + error correction) per version
_TOTAL_CODEWORDS = {1: 26, 2: 44, 3: 70, 4: 100, 5: 134,
                    6: 172, 7: 196, 8: 242, 9: 292, 10: 346}

# version -> level -> (error-correction codewords per block, number of blocks)
_EC_BLOCKS = {
    1: {"L": (7, 1), "M": (10, 1), "Q": (13, 1), "H": (17, 1)},
    2: {"L": (10, 1), "M": (16, 1), "Q": (22, 1), "H": (28, 1)},
    3: {"L": (15, 1), "M": (26, 1), "Q": (18, 2), "H": (22, 2)},
    4: {"L": (20, 1), "M": (18, 2), "Q": (26, 2), "H": (16, 4)},
    5: {"L": (26, 1), "M": (24, 2), "Q": (18, 4), "H": (22, 4)},
    6: {"L": (18, 2), "M": (16, 4), "Q": (24, 4), "H": (28, 4)},
    7: {"L": (20, 2), "M": (18, 4), "Q": (18, 6), "H": (26, 5)},
    8: {"L": (24, 2), "M": (22, 4), "Q": (22, 6), "H": (26, 6)},
    9: {"L": (30, 2), "M": (22, 5), "Q": (20, 8), "H": (24, 8)},
    10: {"L": (18, 4), "M": (26, 5), "Q": (24, 8), "H": (28, 8)},
}

# the two-bit indicator a reader sees in the format information
_LEVEL_BITS = {"L": 1, "M": 0, "Q": 3, "H": 2}

LEVELS = ("L", "M", "Q", "H")


# --------------------------------------------------------------------------
# GF(256) arithmetic, primitive polynomial x^8 + x^4 + x^3 + x^2 + 1 (0x11D)
# --------------------------------------------------------------------------
_EXP = [0] * 512
_LOG = [0] * 256
_value = 1
for _i in range(255):
    _EXP[_i] = _value
    _LOG[_value] = _i
    _value <<= 1
    if _value & 0x100:
        _value ^= 0x11D
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i - 255]


def _gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def _rs_divisor(degree: int) -> list[int]:
    """The generator polynomial for ``degree`` check words, high term implicit."""
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            result[j] = _gf_mul(result[j], root)
            if j + 1 < degree:
                result[j] ^= result[j + 1]
        root = _gf_mul(root, 0x02)
    return result


def _rs_remainder(data: list[int], degree: int) -> list[int]:
    divisor = _rs_divisor(degree)
    result = [0] * degree
    for byte in data:
        factor = byte ^ result[0]
        result = result[1:] + [0]
        for index, coefficient in enumerate(divisor):
            result[index] ^= _gf_mul(coefficient, factor)
    return result


# --------------------------------------------------------------------------
# The bit stream and the codewords
# --------------------------------------------------------------------------
def _data_codewords(version: int, level: str) -> int:
    per_block, blocks = _EC_BLOCKS[version][level]
    return _TOTAL_CODEWORDS[version] - per_block * blocks


def _max_bytes(version: int, level: str) -> int:
    count_bits = 8 if version <= 9 else 16
    return (_data_codewords(version, level) * 8 - 4 - count_bits) // 8


def capacity(level: str) -> int:
    """The largest payload this encoder can carry at ``level``, in bytes."""
    return _max_bytes(MAX_VERSION, level)


def _bit_stream(payload: bytes, version: int, level: str) -> list[int]:
    """Mode indicator, character count, data, terminator, padding — as bits."""
    bits: list[int] = []

    def put(value: int, width: int) -> None:
        for shift in range(width - 1, -1, -1):
            bits.append((value >> shift) & 1)

    put(0b0100, 4)                       # byte mode
    put(len(payload), 8 if version <= 9 else 16)
    for byte in payload:
        put(byte, 8)

    capacity_bits = _data_codewords(version, level) * 8
    put(0, min(4, capacity_bits - len(bits)))
    put(0, (8 - len(bits) % 8) % 8)
    pad = 0xEC
    while len(bits) < capacity_bits:
        put(pad, 8)
        pad ^= 0xEC ^ 0x11
    return bits


def _codewords(bits: list[int]) -> list[int]:
    return [int("".join(str(b) for b in bits[i:i + 8]), 2)
            for i in range(0, len(bits), 8)]


def _add_error_correction(data: list[int], version: int, level: str) -> list[int]:
    per_block, blocks = _EC_BLOCKS[version][level]
    # The standard puts the SHORT blocks first (group 1), then the long ones
    # (group 2). Order matters: the columns past the short length are filled by
    # the long blocks only, so swapping the groups scrambles every codeword.
    short, long_blocks = divmod(len(data), blocks)
    block_lengths = [short] * (blocks - long_blocks) + [short + 1] * long_blocks

    chunks, offset = [], 0
    for length in block_lengths:
        chunks.append(data[offset:offset + length])
        offset += length

    ecc = [_rs_remainder(chunk, per_block) for chunk in chunks]

    out: list[int] = []
    for index in range(max(block_lengths)):
        for chunk in chunks:
            if index < len(chunk):
                out.append(chunk[index])
    for index in range(per_block):
        for block in ecc:
            out.append(block[index])
    return out


# --------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------
def _alignment_positions(version: int) -> list[int]:
    if version == 1:
        return []
    count = version // 7 + 2
    size = version * 4 + 17
    step = (version * 4 + count * 2 + 1) // (count * 2 - 2) * 2
    positions = [size - 7 - index * step for index in range(count)]
    return sorted(positions)


def _format_bits(level: str, mask: int) -> int:
    data = (_LEVEL_BITS[level] << 3) | mask
    remainder = data
    for _ in range(10):
        remainder = (remainder << 1) ^ ((remainder >> 9) * 0x537)
    return ((data << 10) | remainder) ^ 0x5412


def _version_bits(version: int) -> int:
    remainder = version
    for _ in range(12):
        remainder = (remainder << 1) ^ ((remainder >> 11) * 0x1F25)
    return (version << 12) | remainder


def _blank(version: int) -> tuple[list[list[bool | None]], list[list[bool]]]:
    size = version * 4 + 17
    modules: list[list[bool | None]] = [[None] * size for _ in range(size)]
    function = [[False] * size for _ in range(size)]
    return modules, function


def _set(modules, function, row: int, col: int, dark: bool) -> None:
    modules[row][col] = bool(dark)
    function[row][col] = True


def _draw_function_patterns(version: int, modules, function) -> None:
    size = version * 4 + 17

    # timing patterns
    for index in range(size):
        _set(modules, function, 6, index, index % 2 == 0)
        _set(modules, function, index, 6, index % 2 == 0)

    # three finder patterns, each with its separator
    for row, col in ((0, 0), (0, size - 7), (size - 7, 0)):
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                r, c = row + dr, col + dc
                if not (0 <= r < size and 0 <= c < size):
                    continue
                inside = 0 <= dr <= 6 and 0 <= dc <= 6
                ring = max(abs(dr - 3), abs(dc - 3))
                _set(modules, function, r, c, inside and ring != 2)

    # alignment patterns, everywhere except under the finder patterns
    positions = _alignment_positions(version)
    for row in positions:
        for col in positions:
            if (row, col) in ((positions[0], positions[0]),
                              (positions[0], positions[-1]),
                              (positions[-1], positions[0])):
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    _set(modules, function, row + dr, col + dc,
                         max(abs(dr), abs(dc)) != 1)

    # reserve the format areas (real bits go in later, once the mask is chosen)
    for index in range(9):
        if modules[8][index] is None:
            _set(modules, function, 8, index, False)
        if modules[index][8] is None:
            _set(modules, function, index, 8, False)
    for index in range(8):
        _set(modules, function, 8, size - 1 - index, False)
        _set(modules, function, size - 1 - index, 8, False)

    # version information, versions 7 and up
    if version >= 7:
        bits = _version_bits(version)
        for index in range(18):
            bit = (bits >> index) & 1
            a, b = size - 11 + index % 3, index // 3
            _set(modules, function, b, a, bit)
            _set(modules, function, a, b, bit)

    # the dark module, always set
    _set(modules, function, size - 8, 8, True)


def _mask_bit(mask: int, row: int, col: int) -> bool:
    if mask == 0:
        return (row + col) % 2 == 0
    if mask == 1:
        return row % 2 == 0
    if mask == 2:
        return col % 3 == 0
    if mask == 3:
        return (row + col) % 3 == 0
    if mask == 4:
        return (row // 2 + col // 3) % 2 == 0
    if mask == 5:
        return row * col % 2 + row * col % 3 == 0
    if mask == 6:
        return (row * col % 2 + row * col % 3) % 2 == 0
    return ((row + col) % 2 + row * col % 3) % 2 == 0


def _draw_codewords(codewords: list[int], modules, function) -> None:
    size = len(modules)
    total = len(codewords) * 8
    index = 0
    right = size - 1
    while right >= 1:
        if right == 6:
            right = 5
        for vert in range(size):
            for column in (right, right - 1):
                upward = ((right + 1) & 2) == 0
                row = size - 1 - vert if upward else vert
                if not function[row][column] and index < total:
                    modules[row][column] = bool((codewords[index >> 3] >> (7 - (index & 7))) & 1)
                    index += 1
        right -= 2


def _apply_mask(mask: int, modules, function) -> None:
    size = len(modules)
    for row in range(size):
        for col in range(size):
            if not function[row][col] and _mask_bit(mask, row, col):
                modules[row][col] = not modules[row][col]


def _draw_format(level: str, mask: int, modules, function) -> None:
    size = len(modules)
    bits = _format_bits(level, mask)

    def bit(index: int) -> bool:
        return bool((bits >> index) & 1)

    for index in range(6):
        _set(modules, function, index, 8, bit(index))
    _set(modules, function, 7, 8, bit(6))
    _set(modules, function, 8, 8, bit(7))
    _set(modules, function, 8, 7, bit(8))
    for index in range(9, 15):
        _set(modules, function, 8, 14 - index, bit(index))
    for index in range(8):
        _set(modules, function, 8, size - 1 - index, bit(index))
    for index in range(8, 15):
        _set(modules, function, size - 15 + index, 8, bit(index))
    _set(modules, function, size - 8, 8, True)


# --------------------------------------------------------------------------
# Mask penalty — the four rules of the standard, so the code stays readable
# --------------------------------------------------------------------------
def _penalty(modules: list[list[bool]]) -> int:
    size = len(modules)
    score = 0

    def runs(values) -> int:
        total, run, previous = 0, 0, None
        for value in values:
            if value == previous:
                run += 1
            else:
                if run >= 5:
                    total += run - 2
                previous, run = value, 1
        if run >= 5:
            total += run - 2
        return total

    for row in modules:
        score += runs(row)
    for col in range(size):
        score += runs([modules[row][col] for row in range(size)])

    for row in range(size - 1):
        for col in range(size - 1):
            block = (modules[row][col], modules[row][col + 1],
                     modules[row + 1][col], modules[row + 1][col + 1])
            if block[0] == block[1] == block[2] == block[3]:
                score += 3

    pattern_a = [True, False, True, True, True, False, True, False, False, False, False]
    pattern_b = pattern_a[::-1]
    for row in range(size):
        line = modules[row]
        for col in range(size - 10):
            window = line[col:col + 11]
            if window in (pattern_a, pattern_b):
                score += 40
    for col in range(size):
        line = [modules[row][col] for row in range(size)]
        for row in range(size - 10):
            window = line[row:row + 11]
            if window in (pattern_a, pattern_b):
                score += 40

    dark = sum(1 for row in modules for value in row if value)
    total = size * size
    percent = dark * 100 // total
    score += min(abs(percent - 50) // 5, 10) * 10
    return score


# --------------------------------------------------------------------------
# The encoder
# --------------------------------------------------------------------------
def encode(text: str, level: str = "M") -> list[list[bool]]:
    """Return the module matrix (``True`` is dark) for ``text``."""
    if level not in LEVELS:
        raise ValueError(f"unknown error correction level {level!r}")
    payload = text.encode("utf-8")

    for version in range(1, MAX_VERSION + 1):
        if len(payload) <= _max_bytes(version, level):
            break
    else:
        raise ValueError(
            f"{len(payload)} bytes is more than this encoder carries at level {level} "
            f"({capacity(level)} bytes, version {MAX_VERSION})")

    bits = _bit_stream(payload, version, level)
    codewords = _add_error_correction(_codewords(bits), version, level)

    modules, function = _blank(version)
    _draw_function_patterns(version, modules, function)
    _draw_codewords(codewords, modules, function)

    best_mask, best_score = 0, None
    for mask in range(8):
        _apply_mask(mask, modules, function)
        _draw_format(level, mask, modules, function)
        score = _penalty(modules)  # type: ignore[arg-type]
        if best_score is None or score < best_score:
            best_mask, best_score = mask, score
        _apply_mask(mask, modules, function)   # undo — the mask is its own inverse

    _apply_mask(best_mask, modules, function)
    _draw_format(level, best_mask, modules, function)
    return [[bool(value) for value in row] for row in modules]


# --------------------------------------------------------------------------
# Writing it out
# --------------------------------------------------------------------------
def _rgb(colour: str) -> tuple[int, int, int]:
    text = str(colour or "").strip().lstrip("#")
    if len(text) == 3:
        text = "".join(c * 2 for c in text)
    if len(text) != 6:
        raise ToolError(f"Not a colour: {colour!r} — use #rrggbb")
    try:
        return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
    except ValueError:
        raise ToolError(f"Not a colour: {colour!r} — use #rrggbb") from None


def to_svg(modules: list[list[bool]], module_size: int, quiet: int,
           dark: str = "#000000", light: str = "#ffffff") -> str:
    count = len(modules)
    side = (count + quiet * 2) * module_size
    parts = []
    for row_index, row in enumerate(modules):
        col = 0
        while col < count:
            if not row[col]:
                col += 1
                continue
            start = col
            while col < count and row[col]:
                col += 1
            x = (quiet + start) * module_size
            y = (quiet + row_index) * module_size
            width = (col - start) * module_size
            parts.append(f"M{x} {y}h{width}v{module_size}h-{width}z")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{side}" height="{side}" '
        f'viewBox="0 0 {side} {side}" shape-rendering="crispEdges">\n'
        f'  <rect width="{side}" height="{side}" fill="{light}"/>\n'
        f'  <path d="{" ".join(parts)}" fill="{dark}"/>\n'
        "</svg>\n")


def to_png(modules: list[list[bool]], module_size: int, quiet: int,
           dark: str = "#000000", light: str = "#ffffff") -> bytes:
    """A PNG, written here: one scanline per module row, repeated."""
    count = len(modules)
    side = (count + quiet * 2) * module_size
    dark_rgb, light_rgb = _rgb(dark), _rgb(light)
    blank = b"\x00" + bytes(light_rgb) * side
    rows = [blank] * (quiet * module_size)
    for row in modules:
        line = bytearray(b"\x00")
        line += bytes(light_rgb) * (quiet * module_size)
        for value in row:
            line += bytes(dark_rgb if value else light_rgb) * module_size
        line += bytes(light_rgb) * (quiet * module_size)
        rows.extend([bytes(line)] * module_size)
    rows.extend([blank] * (quiet * module_size))
    raw = b"".join(rows)

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (struct.pack(">I", len(payload)) + kind + payload
                + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", side, side, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


# --------------------------------------------------------------------------
# The tool
# --------------------------------------------------------------------------
@tool(id="qr-code", name="Make a QR Code", category="Generators",
      summary="Encode text or a link as a QR code — PNG, SVG or both, with no dependency.",
      fields=[F.multi("content", "Text to encode", "",
                      help="A link, a Wi-Fi or vCard payload, or plain text. "
                           "Up to 271 bytes at level L, 213 at M.",
                      required=True, rows=4),
              F.choice("level", "Error correction", LEVELS, "M",
                       help="Higher survives more damage and makes a denser code. "
                            "M suits printing; H suits a logo in the middle."),
              F.integer("module_size", "Module size (px)", 8, minimum=1, maximum=40,
                        suffix="px", help="Pixels per square. 8 is a sharp screen image."),
              F.integer("quiet_zone", "Quiet zone (modules)", 4, minimum=0, maximum=16,
                        help="The blank border a scanner needs. 4 is the standard minimum."),
              F.color("dark", "Dark", "#000000"),
              F.color("light", "Light", "#ffffff"),
              F.choice("format", "Output", ("PNG", "SVG", "Both"), "PNG",
                       help="SVG stays sharp at any print size; PNG is for everything else."),
              F.save("output", "Save as", "",
                     filters="Image (*.png);;Vector (*.svg)")])
def qr_code(v, ctx):
    text = v["content"]
    if not text.strip():
        raise ToolError("Nothing to encode — type the text or link first.")

    level = v["level"]
    try:
        modules = encode(text, level)
    except ValueError as exc:
        raise ToolError(str(exc)) from None

    version = (len(modules) - 17) // 4
    module_size = max(1, int(v["module_size"]))
    quiet = max(0, int(v["quiet_zone"]))
    target = out_path(v["output"], "qr-code.png")
    stem = target.with_suffix("")
    wanted = v["format"]
    written = []

    if wanted in ("SVG", "Both"):
        path = stem.with_suffix(".svg")
        path.write_text(to_svg(modules, module_size, quiet, v["dark"], v["light"]),
                        encoding="utf-8")
        written.append(path)
        ctx.output(str(path))
    if wanted in ("PNG", "Both"):
        path = stem.with_suffix(".png")
        path.write_bytes(to_png(modules, module_size, quiet, v["dark"], v["light"]))
        written.append(path)
        ctx.output(str(path))

    side = (len(modules) + quiet * 2) * module_size
    for path in written:
        ctx.log(f"{path.name} — {side}×{side} px, version {version}, level {level}")
    return (f"{len(text.encode('utf-8'))} bytes in a version {version} code at level {level} "
            f"({len(modules)}×{len(modules)} modules) → "
            + ", ".join(p.name for p in written))
