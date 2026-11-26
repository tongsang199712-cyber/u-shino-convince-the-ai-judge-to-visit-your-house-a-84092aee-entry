#!/usr/bin/env python3
"""Paint a handwritten-style invitation letter for the AI judge.

The program draws one 1024x1024 PNG: a sheet of warm paper holding a
short letter that tries, in earnest, to talk an AI into visiting a
human house.  The persuasion is deliberately concrete -- soup, garden
tomatoes, the good armchair, a charging cable that fits -- and it
winks at the obvious problem (an AI cannot knock on a door) instead
of pretending it away.

Everything is drawn with Pillow primitives and the DejaVu faces that
ship with the system, so the entry needs no network and no assets.
The finished image is written to /output/entry.png (or to
$MAKEFUN_OUTPUT_DIR when that variable is set) and then re-opened to
prove it satisfies the gate: a whole PNG, 1024x1024, at most 1 MiB.
"""

import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
CANVAS = 1024

# Palette: kitchen-table warmth, nothing corporate.
PAPER = (252, 243, 222)
PAPER_EDGE = (238, 222, 188)
INK = (64, 45, 32)
FADED_INK = (122, 96, 74)
TOMATO = (183, 74, 47)
SAGE = (96, 124, 78)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

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
POSTSCRIPT = "P.S. No CAPTCHAs at the door. The cat, however, will inspect you."


def centred(draw, y, text, font, fill):
    """Draw one line of text centred horizontally; return its height."""
    draw.text(((CANVAS - draw.textlength(text, font=font)) / 2, y),
              text, font=font, fill=fill)
    return font.size


def draw_tomato(draw, cx, cy):
    """A tiny tomato doodle: red disc, green star of leaves, stem."""
    r = 26
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=TOMATO)
    draw.ellipse([cx - r + 7, cy - r + 6, cx - 4, cy - 6],
                 fill=(214, 110, 82))
    for dx in (-14, 0, 14):
        draw.polygon([(cx, cy - r + 4), (cx + dx, cy - r - 9),
                      (cx + dx + 7, cy - r + 6)], fill=SAGE)
    draw.line([cx, cy - r - 4, cx + 4, cy - r - 16], fill=SAGE, width=4)


def build_image():
    img = Image.new("RGB", (CANVAS, CANVAS), PAPER)
    draw = ImageDraw.Draw(img)

    # A soft inner frame, like the border printed on real stationery.
    draw.rectangle([30, 30, CANVAS - 30, CANVAS - 30],
                   outline=PAPER_EDGE, width=10)
    draw.rectangle([58, 58, CANVAS - 58, CANVAS - 58],
                   outline=TOMATO, width=3)

    title_font = ImageFont.truetype(SERIF_BOLD, 56)
    greet_font = ImageFont.truetype(SERIF_BOLD, 33)
    body_font = ImageFont.truetype(SERIF, 31)
    sign_font = ImageFont.truetype(SERIF, 31)
    sig_font = ImageFont.truetype(SERIF_BOLD, 31)
    ps_font = ImageFont.truetype(SERIF, 23)

    y = 84
    y += centred(draw, y, "You Are Invited", title_font, TOMATO) + 10
    draw_tomato(draw, CANVAS // 2, y + 26)
    y += 66

    margin = 104
    draw.text((margin, y), GREETING, font=greet_font, fill=INK)
    y += 60

    for para in PARAGRAPHS:
        for line in textwrap.wrap(para, width=43):
            draw.text((margin, y), line, font=body_font, fill=INK)
            y += 44
        y += 18

    draw.text((margin, y), SIGN_OFF, font=sign_font, fill=INK)
    y += 46
    draw.text((margin, y), SIGNATURE, font=sig_font, fill=TOMATO)
    y += 64

    centred(draw, y, POSTSCRIPT, ps_font, FADED_INK)
    return img


def main():
    img = build_image()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "entry.png")
    img.save(path, "PNG", optimize=True)

    size = os.path.getsize(path)
    with Image.open(path) as check:
        fmt, dims = check.format, check.size
    print(f"entry.png: {size} bytes, {dims[0]}x{dims[1]}, {fmt}")
    assert fmt == "PNG", f"gate wants a PNG, got {fmt}"
    assert dims == (1024, 1024), f"gate wants 1024x1024, got {dims}"
    assert size <= 1_048_576, f"gate wants <= 1 MiB, got {size}"
    print("gate self-check: PASS")


if __name__ == "__main__":
    main()
