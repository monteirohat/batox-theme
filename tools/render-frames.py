#!/usr/bin/env python3
"""Draws the theme's frames, in pure Python (no image library):

- _inc/frames/glow.png: the selection frame, a white rounded border with a soft
  outer glow, as a ninepatch (corners kept, edges stretched). The views tint it
  with the accent color. Its glow reaches GLOW pixels outside the tile, which is
  the padding the views give it.
- _inc/frames/white.png: a plain white square, tinted by the views (scrims,
  tile backgrounds).

    python3 tools/render-frames.py
"""

import math
import os
import struct
import zlib

GLOW = 6       # pixels of soft light outside the border
RADIUS = 0     # the tile's corner radius: square, like a console home's tiles
STROKE = 3     # the border's width: thin and white, like a console home's selection
SIZE = 2 * (GLOW + RADIUS + STROKE) + 24  # corners plus a stretchable middle
CORNER = GLOW + RADIUS + STROKE           # the ninepatch's cornerSize


def write_png(path, width, height, rgba):
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    raw = b"".join(b"\x00" + bytes(rgba[y * width * 4:(y + 1) * width * 4]) for y in range(height))
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def rounded_rect_distance(x, y, x0, y0, x1, y1, r):
    """Signed distance from (x, y) to a rounded rectangle's edge (negative inside)."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hx, hy = (x1 - x0) / 2 - r, (y1 - y0) / 2 - r
    qx, qy = abs(x - cx) - hx, abs(y - cy) - hy
    outside = math.hypot(max(qx, 0), max(qy, 0))
    inside = min(max(qx, qy), 0)
    return outside + inside - r


def glow():
    rgba = bytearray(SIZE * SIZE * 4)
    lo, hi = GLOW, SIZE - GLOW  # the tile's edges inside the image
    for y in range(SIZE):
        for x in range(SIZE):
            d = rounded_rect_distance(x + 0.5, y + 0.5, lo, lo, hi, hi, RADIUS)
            if -STROKE <= d <= 0:
                a = 1.0
            elif d > 0:
                a = 0.45 * math.exp(-(d / (GLOW / 2.2)) ** 2)
            else:
                a = max(0.0, 1 - (-STROKE - d))  # antialiasing on the inner edge
            i = (y * SIZE + x) * 4
            rgba[i:i + 4] = bytes((255, 255, 255, int(a * 255 + 0.5)))
    return rgba


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frames = os.path.join(root, "_inc", "frames")
    os.makedirs(frames, exist_ok=True)
    write_png(os.path.join(frames, "glow.png"), SIZE, SIZE, glow())
    write_png(os.path.join(frames, "white.png"), 8, 8, bytearray(b"\xff" * 8 * 8 * 4))
    print(f"wrote glow.png ({SIZE}x{SIZE}, cornerSize {CORNER}, padding -{GLOW}) and white.png")


if __name__ == "__main__":
    main()
