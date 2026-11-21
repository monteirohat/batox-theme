#!/usr/bin/env python3
"""Draws the theme's own icons, flat and white: the top bar's controller, gun and wheel and the
down arrow under the selected tile (_inc/icons/). The systems' tiles show their brand logos
instead (views/system.xml).

    python3 tools/render-icons.py

Every icon is drawn on a 100 x 100 grid from a few shapes; each part is one path whose holes
(fill-rule evenodd) show the background through it.
"""

import os

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
    # Under the selected tile
    "arrow-down": ([part(poly([(44, 20), (56, 20), (56, 58), (70, 58), (50, 82), (30, 58), (44, 58)]))],
                   "0 0 100 100"),
}


def main():
    for name, (parts, view) in ICONS.items():
        with open(os.path.join(ROOT, "_inc", "icons", name + ".svg"), "w") as f:
            f.write(svg(parts, view))
    print(f"wrote {len(ICONS)} icons in _inc/icons")


if __name__ == "__main__":
    main()
