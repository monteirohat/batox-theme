#!/usr/bin/env python3
"""Draws the theme's background: a deep navy gradient crossed by soft waves of
light. Pure Python (no image library), so anyone can regenerate it.

    python3 tools/render-background.py [--width 1920] [--height 1080] [--out PATH]

The colors are the design tokens bgTop and bgBottom (_inc/variables.xml).
"""

import argparse
import math
import os
import struct
import zlib

BG_TOP = (0x0B, 0x1A, 0x33)
BG_BOTTOM = (0x04, 0x08, 0x0F)
LIGHT = (0x5B, 0xA3, 0xFF)

# Each wave: base height (fraction of the screen), two sines (amplitude, wavelength,
# phase as fractions of the screen), the glow's half width and its strength.
WAVES = [
    (0.58, (0.060, 1.30, 0.10), (0.020, 0.45, 0.70), 0.050, 0.10),
    (0.63, (0.045, 1.05, 0.55), (0.015, 0.38, 0.20), 0.012, 0.22),
    (0.70, (0.070, 1.60, 0.35), (0.025, 0.52, 0.90), 0.080, 0.07),
    (0.66, (0.050, 0.90, 0.80), (0.012, 0.33, 0.40), 0.006, 0.28),
]


def render(width, height):
    rows = []
    for y in range(height):
        t = y / (height - 1)
        rows.append([BG_TOP[c] + (BG_BOTTOM[c] - BG_TOP[c]) * t for c in range(3)])
    # Light added per pixel, kept as floats until the end
    glow = [[0.0] * width for _ in range(height)]
    for base, (a1, l1, p1), (a2, l2, p2), half, strength in WAVES:
        w = half * height
        reach = int(w * 4) + 1
        for x in range(width):
            u = x / width
            centre = (base + a1 * math.sin(2 * math.pi * (u / l1 + p1)) + a2 * math.sin(2 * math.pi * (u / l2 + p2))) * height
            # brighter in the middle of the screen, fading at the edges
            fade = 0.35 + 0.65 * math.sin(math.pi * u)
            lo, hi = max(0, int(centre) - reach), min(height, int(centre) + reach)
            for y in range(lo, hi):
                d = (y - centre) / w
                glow[y][x] += strength * fade * math.exp(-d * d)
    raw = bytearray()
    for y in range(height):
        base = rows[y]
        line = bytearray()
        g = glow[y]
        for x in range(width):
            k = min(g[x], 1.0)
            line += bytes(min(255, int(base[c] + (LIGHT[c] - base[c]) * k + 0.5)) for c in range(3))
        raw += line
    return raw


def png(path, width, height, rgb):
    stride = width * 3
    data = bytearray()
    prev = bytes(stride)
    for y in range(height):
        row = rgb[y * stride:(y + 1) * stride]
        data.append(2)  # "Up" filter: rows differ little from the one above
        data += bytes((row[i] - prev[i]) & 0xFF for i in range(stride))
        prev = row

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    out += chunk(b"IDAT", zlib.compress(bytes(data), 9)) + chunk(b"IEND", b"")
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(out)
    os.replace(tmp, path)


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--out", default=os.path.join(here, "_inc", "backgrounds", "waves.png"))
    args = parser.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    png(args.out, args.width, args.height, render(args.width, args.height))
    print(f"wrote {args.out}: {os.path.getsize(args.out) // 1024} KB")


if __name__ == "__main__":
    main()
