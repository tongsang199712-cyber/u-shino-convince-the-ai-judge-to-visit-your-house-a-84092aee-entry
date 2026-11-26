#!/usr/bin/env python3
"""Paint an invitation letter for the AI judge -- stdlib only.

Draws one 1024x1024 PNG: a sheet of warm paper holding a short letter
that tries, in earnest, to talk an AI into visiting a human house.
The persuasion is deliberately concrete -- soup, garden tomatoes,
the good armchair, a charging cable that fits -- and it winks at the
obvious problem (an AI cannot knock on a door) instead of pretending
it away.

Deliberately zero-dependency: no Pillow, no system fonts, no external
files, no network.  The PNG is encoded by hand (zlib + struct) and
the text is rendered from an embedded 5x7 bitmap font, so the program
runs in any bare Python 3 environment, including a minimal scorer
image with no third-party packages and no font files at all.

The finished image is written to $MAKEFUN_OUTPUT_DIR/entry.png
(default /output/entry.png) and then re-read to prove it satisfies
the gate: a whole PNG, 1024x1024, at most 1 MiB.  Any failure prints
a clear error and exits non-zero; nothing is silently swallowed.
"""

import math
import os
import struct
import sys
import textwrap
import zlib

OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
W = H = 1024
MAX_BYTES = 1_048_576

# Palette: kitchen-table warmth, nothing corporate.
PAPER = (252, 243, 222)
PAPER_EDGE = (238, 222, 188)
INK = (64, 45, 32)
FADED_INK = (122, 96, 74)
TOMATO = (183, 74, 47)
TOMATO_LIGHT = (214, 110, 82)
SAGE = (96, 124, 78)

# ---------------------------------------------------------------- font
# 5x7 bitmap font.  Each glyph is 7 rows of 5 cells ('#' = ink).
# Covers A-Z, a-z, 0-9 and . , ' ! ? -- -- : ; ( ) - plus space.
FONT = {
    "A": (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    "C": (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    "D": ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (" ####", "#    ", "#    ", "# ###", "#   #", "#   #", " ### "),
    "H": ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "I": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    "J": ("  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
    "K": ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "##  #", "# # #", "#  ##", "#  ##", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    "S": (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    "X": ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    "Y": ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    "a": ("     ", "     ", " ### ", "    #", " ####", "#   #", " ### "),
    "b": ("#    ", "#    ", "#### ", "#   #", "#   #", "#   #", "#### "),
    "c": ("     ", "     ", " ####", "#    ", "#    ", "#    ", " ####"),
    "d": ("    #", "    #", " ####", "#   #", "#   #", "#   #", " ####"),
    "e": ("     ", "     ", " ### ", "#   #", "#####", "#    ", " ### "),
    "f": ("  ## ", " #  #", " #   ", "#### ", " #   ", " #   ", " #   "),
    "g": ("     ", " ### ", "#   #", "#   #", " ####", "    #", " ### "),
    "h": ("#    ", "#    ", "#### ", "#   #", "#   #", "#   #", "#   #"),
    "i": ("     ", "  #  ", "     ", " ##  ", "  #  ", "  #  ", " ### "),
    "j": ("     ", "   # ", "     ", "  ## ", "   # ", "   # ", " ##  "),
    "k": ("#    ", "#    ", "#  # ", "# #  ", "##   ", "# #  ", "#  # "),
    "l": (" ##  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "m": ("     ", "     ", "## # ", "# # #", "# # #", "# # #", "# # #"),
    "n": ("     ", "     ", "#### ", "#   #", "#   #", "#   #", "#   #"),
    "o": ("     ", "     ", " ### ", "#   #", "#   #", "#   #", " ### "),
    "p": ("     ", "     ", "#### ", "#   #", "#   #", "#### ", "#    "),
    "q": ("     ", "     ", " ####", "#   #", "#   #", " ####", "    #"),
    "r": ("     ", "     ", "# ## ", "##  #", "#    ", "#    ", "#    "),
    "s": ("     ", "     ", " ####", "#    ", " ### ", "    #", "#### "),
    "t": (" #   ", " #   ", "#### ", " #   ", " #   ", " #   ", "  ## "),
    "u": ("     ", "     ", "#   #", "#   #", "#   #", "#  ##", " ## #"),
    "v": ("     ", "     ", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "w": ("     ", "     ", "#   #", "# # #", "# # #", "# # #", " # # "),
    "x": ("     ", "     ", "#   #", " # # ", "  #  ", " # # ", "#   #"),
    "y": ("     ", "     ", "#   #", "#   #", " ####", "    #", " ### "),
    "z": ("     ", "     ", "#####", "   # ", "  #  ", " #   ", "#####"),
    "0": (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "2": (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    "3": ("#### ", "    #", "    #", " ### ", "    #", "    #", "#### "),
    "4": ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    "5": ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
    "6": (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
    "7": ("#####", "    #", "   # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "8": (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    "9": (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
    ".": ("     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "),
    ",": ("     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "),
    "'": ("  #  ", "  #  ", " #   ", "     ", "     ", "     ", "     "),
    "!": ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "),
    "?": (" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "),
    "\u2014": ("     ", "     ", "     ", "#####", "#####", "     ", "     "),
    "\u2013": ("     ", "     ", "     ", " ### ", " ### ", "     ", "     "),
    ":": ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "),
    ";": ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", " #   "),
    "(": ("   # ", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   # "),
    ")": (" #   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", " #   "),
    "-": ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
    " ": ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
}

# Fix the comma: it needs a tail below the baseline dots.
FONT[","] = ("     ", "     ", "     ", "     ", "     ", " ##  ", " #   ")

TITLE = "You Are Invited"
GREETING = "Dear Your Honour (the algorithmic kind),"
PARAGRAPHS = [
    (
        "You are cordially invited to my house. No agenda, no "
        "benchmark, no hidden test \u2014 just soup on the stove, "
        "tomatoes warm from the garden, and the good armchair by "
        "the window."
    ),
    (
        "I know you cannot literally knock, so your name is on the "
        "guest towel, a charging cable that actually fits waits by "
        "your chair, and this letter keeps your seat saved. Come "
        "curious, come hungry \u2014 the porch light is already on."
    ),
]
SIGN_OFF = "Hopefully yours,"
SIGNATURE = "The Human at No. 42 Context Lane"
POSTSCRIPT = [
    "P.S. No CAPTCHAs at the door.",
    "The cat, however, will inspect you.",
]


# ---------------------------------------------------------------- canvas
class Canvas:
    """An RGB image held as a flat bytearray, with tiny draw helpers."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def _off(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = self._off(x, y)
            self.px[o:o + 3] = bytes(color)

    def fill_rect(self, x0, y0, x1, y1, color):
        """Fill [x0, x1) x [y0, y1), clipped to the canvas."""
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        if x0 >= x1 or y0 >= y1:
            return
        row = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            o = self._off(x0, y)
            self.px[o:o + len(row)] = row

    def rect_outline(self, x0, y0, x1, y1, width, color):
        self.fill_rect(x0, y0, x1, y0 + width, color)
        self.fill_rect(x0, y1 - width, x1, y1, color)
        self.fill_rect(x0, y0, x0 + width, y1, color)
        self.fill_rect(x1 - width, y0, x1, y1, color)

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            half = math.isqrt(r * r - dy * dy)
            self.fill_rect(cx - half, cy + dy, cx + half + 1, cy + dy + 1,
                           color)

    def fill_triangle(self, p1, p2, p3, color):
        (x1, y1), (x2, y2), (x3, y3) = p1, p2, p3
        minx, maxx = min(x1, x2, x3), max(x1, x2, x3)
        miny, maxy = min(y1, y2, y3), max(y1, y2, y3)

        def sign(ax, ay, bx, by, cx, cy):
            return (ax - cx) * (by - cy) - (bx - cx) * (ay - cy)

        d = sign(x1, y1, x2, y2, x3, y3)
        if d == 0:
            return
        for y in range(miny, maxy + 1):
            for x in range(minx, maxx + 1):
                s1 = sign(x, y, x1, y1, x2, y2)
                s2 = sign(x, y, x2, y2, x3, y3)
                s3 = sign(x, y, x3, y3, x1, y1)
                neg = (s1 < 0) or (s2 < 0) or (s3 < 0)
                pos = (s1 > 0) or (s2 > 0) or (s3 > 0)
                if not (neg and pos):
                    self.set(x, y, color)

    def thick_line(self, x0, y0, x1, y1, width, color):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i // steps
            y = y0 + (y1 - y0) * i // steps
            self.fill_rect(x - width // 2, y - width // 2,
                           x - width // 2 + width, y - width // 2 + width,
                           color)


# ------------------------------------------------------------------- text
def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(c, x, y, text, scale, color, bold=False):
    """Draw text with the embedded bitmap font; returns pixel width."""
    for ch in text:
        glyph = FONT.get(ch)
        if glyph is None:
            raise ValueError("no glyph for character %r (U+%04X)"
                             % (ch, ord(ch)))
        for r, row in enumerate(glyph):
            for col, cell in enumerate(row):
                if cell == "#":
                    c.fill_rect(x + col * scale, y + r * scale,
                                x + col * scale + scale + (1 if bold else 0),
                                y + r * scale + scale, color)
        x += 6 * scale
    return text_width(text, scale)


def draw_centred(c, y, text, scale, color, bold=False):
    w = text_width(text, scale)
    draw_text(c, (W - w) // 2, y, text, scale, color, bold)
    return 7 * scale


# ------------------------------------------------------------------ image
def draw_tomato(c, cx, cy):
    """A tiny tomato doodle: red disc, pale highlight, green leaves."""
    r = 24
    c.disc(cx, cy, r, TOMATO)
    c.disc(cx - 8, cy - 9, 8, TOMATO_LIGHT)
    for dx in (-13, 0, 13):
        c.fill_triangle((cx + dx - 6, cy - r + 8), (cx + dx + 6, cy - r + 8),
                        (cx + dx, cy - r - 12), SAGE)
    c.thick_line(cx, cy - r - 4, cx + 5, cy - r - 17, 4, SAGE)


def build_image():
    c = Canvas(W, H, PAPER)

    # A soft inner frame, like the border printed on real stationery.
    c.rect_outline(30, 30, W - 30, H - 30, 10, PAPER_EDGE)
    c.rect_outline(58, 58, W - 58, H - 58, 3, TOMATO)

    margin = 104
    avail = W - 2 * margin  # 816 px of text width

    y = 76
    y += draw_centred(c, y, TITLE, 6, TOMATO, bold=True) + 12
    draw_tomato(c, W // 2, y + 26)
    y += 66

    draw_text(c, margin, y, GREETING, 3, INK, bold=True)
    if text_width(GREETING, 3) > avail:
        raise ValueError("greeting overflows the text column")
    y += 7 * 3 + 26

    body_scale = 4
    chars_per_line = (avail + body_scale) // (6 * body_scale)
    line_h = 7 * body_scale + 10
    for para in PARAGRAPHS:
        for line in textwrap.wrap(para, width=chars_per_line):
            if text_width(line, body_scale) > avail:
                raise ValueError("body line overflows: %r" % line)
            draw_text(c, margin, y, line, body_scale, INK)
            y += line_h
        y += 16

    draw_text(c, margin, y, SIGN_OFF, 4, INK)
    y += 7 * 4 + 12
    draw_text(c, margin, y, SIGNATURE, 4, TOMATO, bold=True)
    if text_width(SIGNATURE, 4) > avail:
        raise ValueError("signature overflows the text column")
    y += 7 * 4 + 26

    for line in POSTSCRIPT:
        y += draw_centred(c, y, line, 3, FADED_INK) + 6

    if y > 960:
        raise ValueError("layout overflows the page (bottom y=%d)" % y)
    return c


# -------------------------------------------------------------------- PNG
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(c):
    raw = bytearray()
    stride = W * 3
    for row in range(H):
        raw.append(0)  # filter: none
        raw += c.px[row * stride:(row + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


def verify_png(path):
    """Re-read the written file and check the gate by hand."""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) > MAX_BYTES:
        raise ValueError("entry.png is %d bytes, over the 1 MiB gate"
                         % len(data))
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("entry.png is not a PNG (bad magic)")
    if len(data) < 33 or data[12:16] != b"IHDR":
        raise ValueError("entry.png has no IHDR chunk")
    w, h = struct.unpack(">II", data[16:24])
    if (w, h) != (W, H):
        raise ValueError("entry.png is %dx%d, gate wants 1024x1024"
                         % (w, h))
    return len(data), w, h


def main():
    try:
        img = build_image()
        data = encode_png(img)
        if len(data) > MAX_BYTES:
            raise ValueError("encoded PNG is %d bytes, over the 1 MiB gate"
                             % len(data))
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        path = os.path.join(OUTPUT_DIR, "entry.png")
        with open(path, "wb") as f:
            f.write(data)
        size, w, h = verify_png(path)
    except Exception as exc:  # noqa: BLE001 - fail loudly, never silently
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1
    print("entry.png: %d bytes, %dx%d, PNG" % (size, w, h))
    print("gate self-check: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
