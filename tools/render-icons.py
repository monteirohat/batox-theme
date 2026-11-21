#!/usr/bin/env python3
"""Draws the theme's own icons, flat and white: the top bar's controller, gun and wheel, the
menu's icons (_inc/icons/menu/), and the picture that stands for a game without a
cover, a faint controller on a tile of the strip's color (_inc/icons/). The systems' tiles show
their brand logos instead (views/system.xml).

    python3 tools/render-icons.py

Every icon is drawn on a 100 x 100 grid from a few shapes; each part is one path whose holes
(fill-rule evenodd) show the background through it.
"""

import math
import os
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --- shapes (SVG path data) -------------------------------------------------

def rr(x, y, w, h, r=0):
    r = min(r, w / 2, h / 2)
    if r <= 0:
        return f"M{x},{y}h{w}v{h}h{-w}z"
    return (f"M{x + r},{y}h{w - 2 * r}a{r},{r} 0 0 1 {r},{r}v{h - 2 * r}a{r},{r} 0 0 1 {-r},{r}"
            f"h{-(w - 2 * r)}a{r},{r} 0 0 1 {-r},{-r}v{-(h - 2 * r)}a{r},{r} 0 0 1 {r},{-r}z")


def circle(cx, cy, r):
    return f"M{cx - r},{cy}a{r},{r} 0 1 0 {2 * r},0a{r},{r} 0 1 0 {-2 * r},0z"


def poly(points):
    return "M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in points) + "z"


def plus(cx, cy, size, thick):
    a, b = size / 2, thick / 2
    return poly([(cx - b, cy - a), (cx + b, cy - a), (cx + b, cy - b), (cx + a, cy - b), (cx + a, cy + b),
                 (cx + b, cy + b), (cx + b, cy + a), (cx - b, cy + a), (cx - b, cy + b), (cx - a, cy + b),
                 (cx - a, cy - b), (cx - b, cy - b)])


def diamond(cx, cy, d, r):
    return [circle(cx, cy - d, r), circle(cx + d, cy, r), circle(cx, cy + d, r), circle(cx - d, cy, r)]


def part(base, *holes):
    return base + "".join(holes)


def arc(cx, cy, r_out, r_in, start, end, n=24):
    """A piece of a ring, from one angle to another (degrees, 0 at the top, clockwise)."""
    def at(r, a):
        t = math.radians(a - 90)
        return cx + r * math.cos(t), cy + r * math.sin(t)
    angles = [start + (end - start) * i / n for i in range(n + 1)]
    return poly([at(r_out, a) for a in angles] + [at(r_in, a) for a in reversed(angles)])


def gear(cx, cy, r_out, r_in, teeth):
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * (i + .5) / (teeth * 4)
        r = r_out if i % 4 in (0, 1) else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly(pts)


def svg(parts, view="0 0 100 100"):
    body = [f'<path fill="#FFFFFF" fill-rule="evenodd" d="{p}"/>' for p in parts]
    w, h = view.split()[2:]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" width="{w}" height="{h}">\n'
            + "\n".join(body) + "\n</svg>\n")


# --- icons ------------------------------------------------------------------

# The top bar's input devices (views/screen.xml). Square, with the drawing in the middle: the
# engine gives each device a square slot as tall as the bar and centers the image on it, so a wider
# image spills over its neighbor.
ICONS = {
    "controller": ([part(rr(10, 32, 80, 36, 18), plus(30, 50, 16, 5.5), *diamond(70, 50, 8, 3.6))],
                   "8 8 84 84"),
    "gun": ([part(poly([(8, 30), (84, 30), (88, 34), (88, 44), (44, 44), (40, 52), (46, 52), (44, 58),
                        (34, 58), (30, 74), (14, 74), (22, 44), (8, 44)]), circle(37, 51, 3))],
            "6 10 84 84"),
    "wheel": ([part(circle(50, 50, 40), circle(50, 50, 31)),
               part(rr(18, 44, 64, 10, 4)),
               part(rr(45, 50, 10, 32, 4)),
               part(circle(50, 50, 9), circle(50, 50, 4))],
              "8 8 84 84"),
}


# The menu's icons (views/menu.xml), one per entry the engine names
MENU = {
    "Kodi": [part(rr(10, 18, 80, 64, 8), poly([(40, 34), (68, 50), (40, 66)]))],
    "System": [part(gear(50, 50, 42, 32, 8), circle(50, 50, 14))],
    "Updates": [part(poly([(42, 10), (58, 10), (58, 44), (74, 44), (50, 70), (26, 44), (42, 44)])),
                part(poly([(12, 62), (24, 62), (24, 78), (76, 78), (76, 62), (88, 62), (88, 90), (12, 90)]))],
    "Games": [part(poly([(18, 10), (72, 10), (84, 22), (84, 90), (18, 90)]), rr(30, 18, 30, 18, 2), rr(28, 50, 46, 30, 3))],
    "Controllers": [part(rr(6, 28, 88, 44, 22), plus(30, 50, 20, 7), *diamond(70, 50, 9, 4.2))],
    "UI": [part(rr(8, 14, 84, 72, 6), rr(16, 30, 26, 48, 2), rr(48, 30, 36, 20, 2), rr(48, 56, 36, 22, 2))],
    "Sound": [part(poly([(10, 38), (28, 38), (50, 18), (50, 82), (28, 62), (10, 62)])),
              part(arc(50, 50, 24, 16, 35, 145)), part(arc(50, 50, 40, 32, 35, 145))],
    "Network": [part(arc(50, 78, 66, 56, -45, 45)), part(arc(50, 78, 46, 36, -45, 45)),
                part(arc(50, 78, 26, 16, -45, 45)), part(circle(50, 78, 7))],
    "Planemode": [part(poly([(46, 6), (54, 6), (58, 38), (92, 58), (92, 68), (58, 58), (56, 80), (68, 90), (68, 96),
                             (50, 90), (32, 96), (32, 90), (44, 80), (42, 58), (8, 68), (8, 58), (42, 38)]))],
    "Scraper": [part(circle(42, 42, 30), circle(42, 42, 20)),
                part(poly([(60, 67), (67, 60), (92, 85), (85, 92)]))],
    "Advanced": [part(rr(10, 20, 80, 8, 4)), part(circle(34, 24, 11), circle(34, 24, 4)),
                 part(rr(10, 46, 80, 8, 4)), part(circle(66, 50, 11), circle(66, 50, 4)),
                 part(rr(10, 72, 80, 8, 4)), part(circle(42, 76, 11), circle(42, 76, 4))],
    "Quit": [part(poly([(12, 10), (56, 10), (56, 24), (24, 24), (24, 76), (56, 76), (56, 90), (12, 90)])),
             part(poly([(40, 43), (66, 43), (66, 28), (92, 50), (66, 72), (66, 57), (40, 57)]))],
    "Restart": [part(arc(50, 52, 38, 28, 40, 330)), part(poly([(34, 6), (64, 20), (36, 40)]))],
    "Shutdown": [part(arc(50, 54, 38, 28, 28, 332)), part(rr(45, 8, 10, 44, 5))],
    "FastShutdown": [part(poly([(58, 4), (20, 56), (44, 56), (38, 96), (80, 40), (54, 40)]))],
    "Retroachievements": [part(poly([(28, 10), (72, 10), (72, 36), (62, 52), (56, 56), (56, 70), (70, 76), (70, 88),
                                     (30, 88), (30, 76), (44, 70), (44, 56), (38, 52), (28, 36)])),
                          part(arc(28, 22, 20, 12, 180, 360)), part(arc(72, 22, 20, 12, 0, 180))],
    "Manual": [part(poly([(10, 18), (46, 18), (46, 86), (10, 80)]), rr(18, 30, 20, 4, 2), rr(18, 42, 20, 4, 2), rr(18, 54, 20, 4, 2)),
               part(poly([(54, 18), (90, 18), (90, 80), (54, 86)]), rr(62, 30, 20, 4, 2), rr(62, 42, 20, 4, 2), rr(62, 54, 20, 4, 2))],
    "Netplay": [part(circle(50, 50, 40), circle(50, 50, 32)),
                part(rr(12, 46, 76, 8)), part(rr(46, 12, 8, 76)),
                part(arc(50, 50, 22, 14, 0, 360, 48))],
}


def no_cover():
    """A game without a cover: the controller, faint, on a square of the strip's color."""
    tokens = ET.parse(os.path.join(ROOT, "_inc", "variables.xml")).getroot().find("variables")
    color = "#" + tokens.findtext("homeStrip").strip()[:6]
    controller = ICONS["controller"][0][0]
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="400" height="400">\n'
            f'<rect width="100" height="100" fill="{color}"/>\n'
            f'<path fill="#FFFFFF" fill-opacity="0.22" fill-rule="evenodd" transform="translate(25 25) scale(0.5)" d="{controller}"/>\n</svg>\n')


def main():
    for name, (parts, view) in ICONS.items():
        with open(os.path.join(ROOT, "_inc", "icons", name + ".svg"), "w") as f:
            f.write(svg(parts, view))
    with open(os.path.join(ROOT, "_inc", "icons", "no-cover.svg"), "w") as f:
        f.write(no_cover())
    menu = os.path.join(ROOT, "_inc", "icons", "menu")
    os.makedirs(menu, exist_ok=True)
    for name, parts in MENU.items():
        with open(os.path.join(menu, name.lower() + ".svg"), "w") as f:
            f.write(svg(parts))
    print(f"wrote {len(ICONS) + 1} icons in _inc/icons and {len(MENU)} in _inc/icons/menu")


if __name__ == "__main__":
    main()
