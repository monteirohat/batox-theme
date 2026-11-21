#!/usr/bin/env python3
"""Draws the theme's frames, in pure Python (no image library):

- _inc/frames/white.png: a plain white square, tinted by the views (scrims,
  tile backgrounds).
- _inc/frames/selector.png: the selected row of a list, as the home's selected
  tile: its color (homeTileSelected) inside a white frame (selectionColor), both
  read from _inc/variables.xml. Drawn at a row's size at 1080p, so the frame
  keeps its width when the engine stretches the image over the row.

    python3 tools/render-frames.py
"""

import os
import struct
import xml.etree.ElementTree as ET
import zlib


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


SELECTOR = (691, 54)  # a row of the game list at 1080p: 0.36 of the width, a twelfth of the list
SELECTOR_FRAME = 4    # the frame's width, as the home's selection (4.5 px)


def selector(root):
    tokens = ET.parse(os.path.join(root, "_inc", "variables.xml")).getroot().find("variables")

    def color(name):
        value = tokens.findtext(name).strip().ljust(8, "F")
        return bytes(int(value[i:i + 2], 16) for i in (0, 2, 4, 6))

    fill, frame = color("homeTileSelected"), color("selectionColor")
    width, height = SELECTOR
    rgba = bytearray()
    for y in range(height):
        for x in range(width):
            edge = min(x, y, width - 1 - x, height - 1 - y) < SELECTOR_FRAME
            rgba += frame if edge else fill
    return rgba


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frames = os.path.join(root, "_inc", "frames")
    os.makedirs(frames, exist_ok=True)
    write_png(os.path.join(frames, "selector.png"), *SELECTOR, selector(root))
    write_png(os.path.join(frames, "white.png"), 8, 8, bytearray(b"\xff" * 8 * 8 * 4))
    print("wrote selector.png and white.png")


if __name__ == "__main__":
    main()
