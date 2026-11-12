"""Focused tests for the qr-code tool.

The sweep proves the tool *runs*; it cannot prove the code it draws is a QR
code. These tests read it back the way a scanner does — find the format
information, undo the mask, walk the codeword path, de-interleave the blocks —
and then check the payload and the error correction separately. A picture that
looks like a QR code and a QR code that carries the right bytes are not the same
thing, and only the second one scans.

The reader below is written from the standard rather than from ``tools/qr.py``:
its own reserved-area map, its own Reed-Solomon long division, its own mask
formulas. The one table it shares is the block structure, and that is pinned by
the published byte capacities in ``Capacities``.
"""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import registry  # noqa: E402
from core.runner import execute  # noqa: E402
from tools import qr  # noqa: E402

# --------------------------------------------------------------------------
# An independent reader
# --------------------------------------------------------------------------
ALIGNMENT = {
    1: (), 2: (6, 18), 3: (6, 22), 4: (6, 26), 5: (6, 30),
    6: (6, 34), 7: (6, 22, 38), 8: (6, 24, 42), 9: (6, 26, 46), 10: (6, 28, 50),
}

LEVEL_OF_BITS = {1: "L", 0: "M", 3: "Q", 2: "H"}


def reserved_map(version: int) -> list[list[bool]]:
    """Every module a data bit may NOT occupy, straight from the standard."""
    size = version * 4 + 17
    grid = [[False] * size for _ in range(size)]

    def fill(top: int, left: int, height: int, width: int) -> None:
        for row in range(top, top + height):
            for col in range(left, left + width):
                if 0 <= row < size and 0 <= col < size:
                    grid[row][col] = True

    fill(0, 0, 8, 8)                    # finder + separator, top left
    fill(0, size - 8, 8, 8)             # top right
    fill(size - 8, 0, 8, 8)             # bottom left
    for index in range(8, size - 8):    # timing
        grid[6][index] = True
        grid[index][6] = True
    for index in range(9):              # format information, both copies
        grid[8][index] = True
        grid[index][8] = True
    for index in range(8):
        grid[8][size - 1 - index] = True
        grid[size - 1 - index][8] = True
    if version >= 7:                    # version information, both copies
        fill(0, size - 11, 6, 3)
        fill(size - 11, 0, 3, 6)
    for row in ALIGNMENT[version]:      # alignment patterns
        for col in ALIGNMENT[version]:
            near_finder = ((row < 8 and col < 8)
                           or (row < 8 and col > size - 9)
                           or (row > size - 9 and col < 8))
            if not near_finder:
                fill(row - 2, col - 2, 5, 5)
    return grid


def mask_on(mask: int, row: int, col: int) -> bool:
    """The eight mask conditions, written out."""
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
        return (row * col) % 2 + (row * col) % 3 == 0
    if mask == 6:
        return ((row * col) % 2 + (row * col) % 3) % 2 == 0
    return ((row + col) % 2 + (row * col) % 3) % 2 == 0


def codewords(matrix, version: int, mask: int) -> list[int]:
    """Walk the two-column zigzag and return the unmasked codewords."""
    size = len(matrix)
    skip = reserved_map(version)
    bits: list[int] = []
    right = size - 1
    while right >= 1:
        if right == 6:
            right = 5
        upward = ((right + 1) & 2) == 0
        for step in range(size):
            row = size - 1 - step if upward else step
            for col in (right, right - 1):
                if skip[row][col]:
                    continue
                bit = bool(matrix[row][col])
                if mask_on(mask, row, col):
                    bit = not bit
                bits.append(1 if bit else 0)
        right -= 2
    total = qr._TOTAL_CODEWORDS[version] * 8
    return [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, total, 8)]


def blocks_of(version: int, level: str) -> list[int]:
    """The data-codeword count of each block, short blocks first."""
    per_block, count = qr._EC_BLOCKS[version][level]
    data = qr._TOTAL_CODEWORDS[version] - per_block * count
    short, long_blocks = divmod(data, count)
    return [short] * (count - long_blocks) + [short + 1] * long_blocks


def deinterleave(stream: list[int], version: int, level: str):
    """Undo the block interleave; returns (data blocks, error-correction blocks)."""
    lengths = blocks_of(version, level)
    per_block, count = qr._EC_BLOCKS[version][level]
    data = [[] for _ in range(count)]
    index = 0
    for column in range(max(lengths)):
        for block in range(count):
            if column < lengths[block]:
                data[block].append(stream[index])
                index += 1
    ecc = [[] for _ in range(count)]
    for _ in range(per_block):
        for block in range(count):
            ecc[block].append(stream[index])
            index += 1
    return data, ecc


# -- Reed-Solomon, by long division, with no shared code --------------------
def gf_multiply(a: int, b: int) -> int:
    product = 0
    while b:
        if b & 1:
            product ^= a
        a <<= 1
        if a & 0x100:
            a ^= 0x11D
        b >>= 1
    return product


def generator(degree: int) -> list[int]:
    """(x - a^0)(x - a^1)...(x - a^(degree-1)), highest power first."""
    poly = [1]
    power = 1
    for _ in range(degree):
        shifted = poly + [0]
        for index, coefficient in enumerate(poly):
            shifted[index + 1] ^= gf_multiply(coefficient, power)
        poly = shifted
        power = gf_multiply(power, 2)
    return poly


def remainder(data: list[int], degree: int) -> list[int]:
    divisor = generator(degree)
    work = list(data) + [0] * degree
    for start in range(len(data)):
        factor = work[start]
        if not factor:
            continue
        for offset, coefficient in enumerate(divisor):
            work[start + offset] ^= gf_multiply(coefficient, factor)
    return work[-degree:]


def payload_of(data_blocks: list[list[int]], version: int) -> tuple[str, int, int]:
    """Parse the message: mode, count, bytes. Returns (text, mode, count)."""
    bits: list[int] = []
    # the message runs through the blocks in order; the interleave is undone
    for block in data_blocks:
        for byte in block:
            bits.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
    mode = int("".join(map(str, bits[0:4])), 2)
    width = 8 if version <= 9 else 16
    count = int("".join(map(str, bits[4:4 + width])), 2)
    body = bits[4 + width:4 + width + count * 8]
    return bytes(int("".join(map(str, body[i:i + 8])), 2)
                 for i in range(0, len(body), 8)).decode("utf-8"), mode, count


LEVEL_BITS_OF = {1: "L", 0: "M", 3: "Q", 2: "H"}


def format_candidates() -> dict[int, tuple[str, int]]:
    """Every legal 15-bit format string, with the level and mask it means."""
    table: dict[int, tuple[str, int]] = {}
    for bits, level in ((1, "L"), (0, "M"), (3, "Q"), (2, "H")):
        for mask in range(8):
            data = (bits << 3) | mask
            remainder_bits = data
            for _ in range(10):
                remainder_bits = (remainder_bits << 1) ^ ((remainder_bits >> 9) * 0x537)
            table[((data << 10) | remainder_bits) ^ 0x5412] = (level, mask)
    return table


FORMAT = format_candidates()


def format_value(matrix, copy: int = 1) -> int:
    """The 15 format bits, read from the positions the standard puts them in."""
    size = len(matrix)
    if copy == 1:
        spots = ([(row, 8) for row in range(6)] + [(7, 8), (8, 8), (8, 7)]
                 + [(8, 14 - index) for index in range(9, 15)])
    else:
        spots = ([(8, size - 1 - index) for index in range(8)]
                 + [(size - 15 + index, 8) for index in range(8, 15)])
    return sum(int(matrix[row][col]) << index for index, (row, col) in enumerate(spots))


def read_format(matrix) -> tuple[str, int, int]:
    """Decode the format information the way a scanner does: nearest legal word."""
    value = format_value(matrix)
    best, distance = None, 99
    for candidate, meaning in FORMAT.items():
        gap = bin(candidate ^ value).count("1")
        if gap < distance:
            best, distance = meaning, gap
    assert best is not None and distance == 0, f"format information is {distance} bits off"
    return best[0], best[1], distance


def read_code(matrix) -> tuple[str, str, int]:
    """Recover (text, level, mask): format first, then the codewords it names."""
    version = (len(matrix) - 17) // 4
    level, mask, _ = read_format(matrix)
    stream = codewords(matrix, version, mask)
    data, ecc = deinterleave(stream, version, level)
    per_block, _ = qr._EC_BLOCKS[version][level]
    for block, check in zip(data, ecc, strict=True):
        assert remainder(block, per_block) == check, "the error correction does not verify"
    text, mode, count = payload_of(data, version)
    assert mode == 0b0100, f"mode indicator is {mode:#06b}, not byte mode"
    assert count == len(text.encode("utf-8")), "the character count disagrees with the payload"
    return text, level, mask


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------
def run_tool(**values):
    tool = registry.get("qr-code")
    payload = {"content": "", "level": "M", "module_size": 8, "quiet_zone": 4,
               "dark": "#000000", "light": "#ffffff", "format": "PNG", "output": ""}
    payload.update(values)
    return execute(tool, payload)


class RoundTrip(unittest.TestCase):
    """What was typed is what a scanner reads back."""

    CASES = ("HELLO", "https://drasmonline.github.io/All4ONE/", "alpha beta gamma",
             "नमस्ते दुनिया", "WIFI:T:WPA;S:MyNet;P:pass;;", "a" * 100, "a" * 271,
             "1234567890")

    def test_every_level_round_trips(self):
        for text in self.CASES:
            for level in "LMQH":
                try:
                    matrix = qr.encode(text, level)
                except ValueError:
                    continue        # too long for that level, covered below
                with self.subTest(text=text[:20], level=level):
                    recovered, found_level, mask = read_code(matrix)
                    self.assertEqual(recovered, text)
                    self.assertEqual(found_level, level)
                    self.assertIn(mask, range(8))

    def test_the_payload_is_byte_mode(self):
        matrix = qr.encode("HELLO", "L")
        level, mask, _ = read_format(matrix)
        data, _ = deinterleave(codewords(matrix, 1, mask), 1, level)
        _, mode, count = payload_of(data, 1)
        self.assertEqual(mode, 0b0100)
        self.assertEqual(count, 5)

    def test_more_than_one_block_still_round_trips(self):
        """v5-H is four blocks of 12, 12, 11 and 11 codewords — the case where
        putting the long blocks first scrambles every codeword."""
        matrix = qr.encode("नमस्ते दुनिया", "H")
        self.assertEqual((len(matrix) - 17) // 4, 5)
        self.assertEqual(blocks_of(5, "H"), [11, 11, 12, 12])
        self.assertEqual(read_code(matrix)[0], "नमस्ते दुनिया")


class Structure(unittest.TestCase):
    """The fixed patterns a scanner finds before it reads anything."""

    def setUp(self):
        self.matrix = qr.encode("https://example.com/", "M")
        self.size = len(self.matrix)

    def test_size_matches_the_version(self):
        self.assertEqual(self.size % 4, 1)
        self.assertEqual((self.size - 17) % 4, 0)

    def test_finder_patterns_are_in_three_corners(self):
        for top, left in ((0, 0), (0, self.size - 7), (self.size - 7, 0)):
            for row in range(7):
                for col in range(7):
                    ring = max(abs(row - 3), abs(col - 3))
                    self.assertEqual(self.matrix[top + row][left + col], ring != 2,
                                     f"finder at {top},{left} module {row},{col}")

    def test_separators_are_light(self):
        for col in range(8):
            self.assertFalse(self.matrix[7][col])
            self.assertFalse(self.matrix[col][7])

    def test_timing_patterns_alternate(self):
        for index in range(8, self.size - 8):
            self.assertEqual(self.matrix[6][index], index % 2 == 0)
            self.assertEqual(self.matrix[index][6], index % 2 == 0)

    def test_the_dark_module_is_set(self):
        self.assertTrue(self.matrix[self.size - 8][8])

    def test_alignment_patterns_are_drawn(self):
        # v2 at level M is 25x25 with one alignment pattern at (18, 18).
        matrix = qr.encode("x" * 20, "M")
        self.assertEqual(len(matrix), 25)
        self.assertTrue(matrix[18][18])
        self.assertFalse(matrix[17][18])
        self.assertTrue(matrix[16][16])

    def test_version_information_appears_from_version_seven(self):
        matrix = qr.encode("a" * 150, "L")
        self.assertGreaterEqual((len(matrix) - 17) // 4, 7)
        # the 18 version bits are drawn twice; both copies must agree
        size = len(matrix)
        top_right = [matrix[i // 3][size - 11 + i % 3] for i in range(18)]
        bottom_left = [matrix[size - 11 + i % 3][i // 3] for i in range(18)]
        self.assertEqual(top_right, bottom_left)
        self.assertEqual(int("".join("1" if b else "0" for b in reversed(top_right)), 2),
                         qr._version_bits((size - 17) // 4))


class FormatInformation(unittest.TestCase):
    """The 15 bits that tell a scanner which level and mask were used."""

    def test_format_information_names_the_level_that_was_asked_for(self):
        for level in "LMQH":
            matrix = qr.encode("format check", level)
            found, mask, distance = read_format(matrix)
            self.assertEqual((found, distance), (level, 0))
            self.assertIn(mask, range(8))

    def test_both_copies_of_the_format_information_agree(self):
        for level in "LMQH":
            matrix = qr.encode("format check", level)
            self.assertEqual(format_value(matrix, 1), format_value(matrix, 2))

    def test_the_middle_of_the_code_is_where_the_mask_was_applied(self):
        """Undo the wrong mask and the checksum stops verifying."""
        matrix = qr.encode("https://example.com/mask", "M")
        version = (len(matrix) - 17) // 4
        level, mask, _ = read_format(matrix)
        wrong = (mask + 1) % 8
        stream = codewords(matrix, version, wrong)
        data, ecc = deinterleave(stream, version, level)
        per_block, _ = qr._EC_BLOCKS[version][level]
        self.assertTrue(any(remainder(block, per_block) != check
                            for block, check in zip(data, ecc, strict=True)))

    def test_damage_to_the_data_breaks_the_checksum(self):
        """The error correction covers the payload, not just the framing."""
        matrix = [row[:] for row in qr.encode("https://example.com/recovery", "H")]
        version = (len(matrix) - 17) // 4
        level, mask, _ = read_format(matrix)
        before = codewords(matrix, version, mask)
        deinterleave(before, version, level)
        for row, col in ((12, 12), (13, 12), (14, 12)):
            matrix[row][col] = not matrix[row][col]
        after = codewords(matrix, version, mask)
        damaged = deinterleave(after, version, level)
        self.assertNotEqual(before, after)
        per_block, _ = qr._EC_BLOCKS[version][level]
        # the received block no longer agrees with the checksum it carries
        self.assertTrue(any(remainder(block, per_block) != check
                            for block, check in zip(damaged[0], damaged[1], strict=True)))


class Capacities(unittest.TestCase):
    """The published byte capacities, version 1 to 10."""

    PUBLISHED = {
        "L": (17, 32, 53, 78, 106, 134, 154, 192, 230, 271),
        "M": (14, 26, 42, 62, 84, 106, 122, 152, 180, 213),
        "Q": (11, 20, 32, 46, 60, 74, 86, 108, 130, 151),
        "H": (7, 14, 24, 34, 44, 58, 64, 84, 98, 119),
    }

    def test_every_version_and_level_matches_the_table(self):
        for level, expected in self.PUBLISHED.items():
            for version, size in enumerate(expected, start=1):
                with self.subTest(level=level, version=version):
                    self.assertEqual(qr._max_bytes(version, level), size)

    def test_the_largest_payload_fits_and_one_more_byte_does_not(self):
        self.assertEqual(len(qr.encode("a" * 271, "L")), 57)
        with self.assertRaises(ValueError):
            qr.encode("a" * 272, "L")

    def test_too_long_names_the_limit_rather_than_truncating(self):
        result = run_tool(content="a" * 300, level="M")
        self.assertFalse(result.ok)
        self.assertIn("213", result.error or "")


class Codewords(unittest.TestCase):
    """Golden values, so a change to the encoder cannot pass unnoticed."""

    def test_hello_at_version_one_level_l(self):
        bits = qr._bit_stream(b"HELLO", 1, "L")
        self.assertEqual(qr._codewords(bits),
                         [0x40, 0x54, 0x84, 0x54, 0xC4, 0xC4, 0xF0,
                          0xEC, 0x11, 0xEC, 0x11, 0xEC, 0x11, 0xEC, 0x11,
                          0xEC, 0x11, 0xEC, 0x11])

    def test_hello_error_correction(self):
        bits = qr._bit_stream(b"HELLO", 1, "L")
        data = qr._codewords(bits)
        self.assertEqual(qr._add_error_correction(data, 1, "L")[len(data):],
                         [0x4D, 0x2A, 0xD3, 0xBB, 0x9F, 0x20, 0x84])

    def test_the_remainder_agrees_with_long_division(self):
        data = [0x40, 0x54, 0x84, 0x54, 0xC4, 0xC4, 0xF0, 0xEC, 0x11]
        self.assertEqual(qr._rs_remainder(data, 10), remainder(data, 10))

    def test_masks_are_distinct(self):
        seen = {tuple(mask_on(mask, row, col) for row in range(6) for col in range(6))
                for mask in range(8)}
        self.assertEqual(len(seen), 8)


class Output(unittest.TestCase):
    """The two files it writes, read back rather than trusted."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.target = str(Path(self.folder.name) / "code.png")

    def test_png_and_svg_are_written(self):
        result = run_tool(content="https://example.com/", format="Both",
                          output=self.target)
        self.assertTrue(result.ok, result.error)
        for suffix in (".png", ".svg"):
            self.assertTrue(Path(self.folder.name, "code" + suffix).exists())

    def test_the_png_is_a_real_png_of_the_right_size(self):
        run_tool(content="https://example.com/", module_size=4, quiet_zone=2,
                 output=self.target)
        blob = Path(self.target).read_bytes()
        self.assertTrue(blob.startswith(b"\x89PNG\r\n\x1a\n"))
        width, height = struct.unpack(">II", blob[16:24])
        matrix = qr.encode("https://example.com/", "M")
        side = (len(matrix) + 4) * 4
        self.assertEqual((width, height), (side, side))
        # the IDAT must decompress to whole scanlines of the declared depth
        start = blob.index(b"IDAT") - 4
        length = struct.unpack(">I", blob[start:start + 4])[0]
        raw = zlib.decompress(blob[start + 8:start + 8 + length])
        self.assertEqual(len(raw), side * (1 + side * 3))

    def test_the_png_pixels_are_the_module_matrix(self):
        try:
            from PIL import Image
        except ImportError:                                  # pragma: no cover
            self.skipTest("Pillow is not installed")
        run_tool(content="HELLO", module_size=3, quiet_zone=1, output=self.target)
        image = Image.open(self.target).convert("L")
        matrix = qr.encode("HELLO", "M")
        count = len(matrix)
        for row in range(count):
            for col in range(count):
                pixel = image.getpixel(((1 + col) * 3 + 1, (1 + row) * 3 + 1))
                self.assertEqual(pixel < 128, matrix[row][col],
                                 f"module {row},{col} is the wrong colour")

    def test_the_svg_is_a_scalable_path_with_the_quiet_zone(self):
        result = run_tool(content="HELLO", format="SVG", module_size=6,
                          quiet_zone=4, output=self.target)
        self.assertTrue(result.ok, result.error)
        text = Path(self.folder.name, "code.svg").read_text(encoding="utf-8")
        matrix = qr.encode("HELLO", "M")
        side = (len(matrix) + 8) * 6
        self.assertIn(f'width="{side}"', text)
        self.assertIn(f'viewBox="0 0 {side} {side}"', text)
        self.assertIn("shape-rendering=\"crispEdges\"", text)
        self.assertEqual(text.count("<path"), 1)

    def test_colours_are_honoured(self):
        run_tool(content="HELLO", format="SVG", dark="#102030", light="#fefefe",
                 output=self.target)
        text = Path(self.folder.name, "code.svg").read_text(encoding="utf-8")
        self.assertIn('fill="#102030"', text)
        self.assertIn('fill="#fefefe"', text)


class BadInput(unittest.TestCase):
    def test_nothing_to_encode_is_refused(self):
        result = run_tool(content="   ")
        self.assertFalse(result.ok)
        self.assertIn("required", (result.error or "").lower())

    def test_a_bad_colour_is_refused_by_name(self):
        result = run_tool(content="HELLO", dark="blueish", output="")
        self.assertFalse(result.ok)
        self.assertIn("Not a colour", result.error or "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
