#!/usr/bin/env python3
"""Draws the systems' backgrounds (systems/<name>/background.jpg): the machine, inked and lit
from behind, on a pier in front of a coastal city at sunset. Saturated pinks, oranges and
purples over the theme's navy, with the left kept dark for the texts and the very top for the
top bar; the sky keeps its color behind the home's row of tiles, which are translucent.

    python3 tools/render-system-backgrounds.py            # every system, and the loading screen
    python3 tools/render-system-backgrounds.py snes nes   # only these
    python3 tools/render-system-backgrounds.py splash     # only the loading screen's picture
    python3 tools/render-system-backgrounds.py --svg snes # also keeps dist/backgrounds/snes.svg

Each picture is an SVG written by this script and turned into a 1920 x 1080 JPEG by a headless
Chrome or Chromium (set CHROME to its path if it isn't found). Everything is drawn here: no
photo, no logo, no artwork from a game or a console maker.

A machine is a few boxes (a body, its raised parts, a cartridge...) seen from the same corner:
x runs along its front, y from its back to the viewer, z up. The sun is behind it, to the right.
"""

import base64
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1920, 1080
HORIZON = 0.64 * H
INK = "#0E0620"
NAVY = "#050B1A"

# One unit along x and along y, on the screen (z is straight up)
EX, EY = (0.95, 0.14), (-0.55, 0.28)
SUN = (0.55, -0.83)  # towards the sun, on the ground


# --- colors -----------------------------------------------------------------

def rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(a[i] + (b[i] - a[i]) * t))) for i in range(3))


def dim(c, keep):
    return mix("#000000", c, keep)


# Sky from the top to the horizon (fractions of the height), sun, light and shadow of each mood
MOODS = {
    "vice": dict(
        sky=[(0, "#040816"), (.14, "#0B1238"), (.33, "#3A1466"), (.50, "#9A1F85"), (.565, "#F03C72"),
             (.61, "#FF7F4F"), (.64, "#FFCB66")],
        sun=("#FFE9A0", "#FF6F61"), glow="#FF5E8A", rim="#FFB07A", shadow="#2B1250", city="#27104D",
        cloud=("#5A1C78", "#FF8E7A"), water=("#C24A6E", "#45155C", "#080A1E")),
    "miami": dict(
        sky=[(0, "#040816"), (.14, "#071A3A"), (.33, "#0F4A80"), (.50, "#6A55B8"), (.565, "#F0629F"),
             (.61, "#FF9F7A"), (.64, "#FFDDA6")],
        sun=("#FFF1C1", "#FF8FB1"), glow="#FF8FBF", rim="#FFC2A0", shadow="#1B2A5E", city="#1D2A63",
        cloud=("#3F4FA0", "#FFA9B8"), water=("#D46A98", "#2C3A86", "#060C22")),
    "gold": dict(
        sky=[(0, "#040816"), (.14, "#101040"), (.33, "#43207A"), (.50, "#B23F74"), (.56, "#F6774C"),
             (.61, "#FFAA3F"), (.64, "#FFE680")],
        sun=("#FFF4B8", "#FFA23D"), glow="#FF9A3D", rim="#FFD08A", shadow="#3A1848", city="#33154A",
        cloud=("#6B2A6E", "#FFB05E"), water=("#D9763F", "#5A1E55", "#0A0A1E")),
    "night": dict(
        sky=[(0, "#03050F"), (.14, "#070B26"), (.36, "#1F1152"), (.54, "#62188C"), (.60, "#CC2585"),
             (.64, "#FF6494")],
        sun=("#FFF3FF", "#F0B7FF"), glow="#C13CFF", rim="#FF6AD5", shadow="#150C3A", city="#120A33",
        cloud=("#2A1560", "#D94BB0"), water=("#8A2A86", "#2A1160", "#05061A")),
}


# --- the page: gradients and filters shared by everything --------------------

class Page:
    def __init__(self):
        self.defs, self.body, self.n = [], [], 0

    def new_id(self):
        self.n += 1
        return f"g{self.n}"

    def gradient(self, stops, x1=0, y1=0, x2=0, y2=1, user=False):
        """A linear gradient; stops are (offset, color) or (offset, color, opacity)."""
        i = self.new_id()
        units = ' gradientUnits="userSpaceOnUse"' if user else ""
        body = "".join(f'<stop offset="{s[0]}" stop-color="{s[1]}"'
                       + (f' stop-opacity="{s[2]}"' if len(s) > 2 else "") + "/>" for s in stops)
        self.defs.append(f'<linearGradient id="{i}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"{units}>{body}</linearGradient>')
        return f"url(#{i})"

    def radial(self, stops):
        i = self.new_id()
        body = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
        self.defs.append(f'<radialGradient id="{i}">{body}</radialGradient>')
        return f"url(#{i})"

    def add(self, *parts):
        self.body.extend(parts)

    def svg(self):
        filters = (
            '<filter id="blur3" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>'
            '<filter id="blur8" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="8"/></filter>'
            '<filter id="blur20" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="20"/></filter>'
            '<filter id="blur45" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="45"/></filter>'
            # Brush: bends shapes along long horizontal strokes, like paint
            '<filter id="brush" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" '
            'baseFrequency="0.004 0.03" numOctaves="3" seed="7" result="n"/><feDisplacementMap in="SourceGraphic" '
            'in2="n" scale="46" xChannelSelector="R" yChannelSelector="G"/></filter>'
            '<filter id="ragged" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" '
            'baseFrequency="0.02" numOctaves="3" seed="3" result="n"/><feDisplacementMap in="SourceGraphic" '
            'in2="n" scale="16"/><feGaussianBlur stdDeviation="1.2"/></filter>'
            '<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="5"/>'
            '<feColorMatrix type="saturate" values="0"/></filter>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
                f'<defs>{filters}{"".join(self.defs)}</defs>{"".join(self.body)}</svg>')


def poly(points, fill, stroke="none", sw=0, extra=""):
    d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in points) + "Z"
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" {extra}/>'


def hull(points):
    pts = sorted(set((round(x, 1), round(y, 1)) for x, y in points))
    if len(pts) < 3:
        return pts

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out[:-1]
    return half(pts) + half(reversed(pts))


# --- details drawn flat on a face (in the box's own units) -------------------

def rect(x, y, w, h, fill, r=0, stroke=INK, sw=.5, op=1):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}" opacity="{op}"/>')


def circ(cx, cy, r, fill, stroke=INK, sw=.5, op=1):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>'


def line(x1, y1, x2, y2, stroke, sw=.7, op=1):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linecap="round" opacity="{op}"/>')


def path(d, fill="none", stroke=INK, sw=.5, op=1, extra=""):
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" '
            f'stroke-linecap="round" opacity="{op}" {extra}/>')


def dpad(cx, cy, size, arm, fill):
    a, b = size / 2, arm / 2
    return (rect(cx - a, cy - b, size, arm, fill, r=1) + rect(cx - b, cy - a, arm, size, fill, r=1)
            + rect(cx - b, cy - b, arm, arm, fill, stroke="none"))


def grid(x, y, cols, rows, kw, kh, gap, fill, stroke=INK):
    return "".join(rect(x + c * (kw + gap), y + r * (kh + gap), kw, kh, fill, r=.6, stroke=stroke, sw=.3)
                   for r in range(rows) for c in range(cols))


def lines(x, y, w, n, gap, stroke, sw=.7, op=1):
    return "".join(line(x, y + i * gap, x + w, y + i * gap, stroke, sw, op) for i in range(n))


def neon(d, color, sw=2.2):
    """A neon tube: a wide glow, the tube and its white core."""
    return (path(d, stroke=color, sw=sw * 3.2, op=.55, extra='filter="url(#blur3)"')
            + path(d, stroke=color, sw=sw) + path(d, stroke="#FFFFFF", sw=sw * .35, op=.9))


# --- a box of a machine ------------------------------------------------------

class Box:
    """x, y: its back left corner on the ground; w along x, d along y, h up from z; r rounds its
    corners; rot turns it around its middle. top, front and right are details drawn on those
    faces (front and right: from the face's top left corner, down). screens are (face, x, y, w,
    h, color) and glow."""

    def __init__(self, x, y, w, d, h, color, z=0, r=0, rot=0, top=(), front=(), right=(), screens=(),
                 top_color=None):
        self.x, self.y, self.w, self.d, self.h, self.z = x, y, w, d, h, z
        self.color, self.top_color = color, top_color or color
        self.r, self.rot = min(r, w / 2, d / 2), math.radians(rot)
        self.top, self.front, self.right, self.screens = top, front, right, screens

    def loc(self, u, v):
        cx, cy = self.x + self.w / 2, self.y + self.d / 2
        du, dv = u - self.w / 2, v - self.d / 2
        c, s = math.cos(self.rot), math.sin(self.rot)
        return cx + du * c - dv * s, cy + du * s + dv * c

    def outline(self):
        w, d, r = self.w, self.d, self.r
        if r <= 0:
            return [(0, 0), (w, 0), (w, d), (0, d)]
        pts = []
        for cx, cy, a0 in ((r, r, 180), (w - r, r, 270), (w - r, d - r, 0), (r, d - r, 90)):
            for k in range(7):
                a = math.radians(a0 + 15 * k)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts

    def corners(self):
        return [self.loc(u, v) + (z,) for u, v in self.outline() for z in (self.z, self.z + self.h)]


class View:
    """Places a machine on the page: fits its boxes in a rectangle and projects them."""

    def __init__(self, boxes, center_x, base_y, max_w, max_h):
        self.s, self.ox, self.oy = 1, 0, 0
        pts = [self.p(*c) for b in boxes for c in b.corners()]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        self.s = min(max_w / (max(xs) - min(xs)), max_h / (max(ys) - min(ys)))
        self.ox = center_x - self.s * (max(xs) + min(xs)) / 2
        self.oy = base_y - self.s * max(ys)

    def p(self, x, y, z=0):
        return (self.ox + self.s * (x * EX[0] + y * EY[0]), self.oy + self.s * (x * EX[1] + y * EY[1] - z))

    def matrix(self, p0, pu, pv):
        return (f'matrix({pu[0] - p0[0]:.4f} {pu[1] - p0[1]:.4f} {pv[0] - p0[0]:.4f} {pv[1] - p0[1]:.4f} '
                f'{p0[0]:.2f} {p0[1]:.2f})')


def draw_box(page, view, box, mood, glows):
    pts = [box.loc(u, v) for u, v in box.outline()]
    n = len(pts)
    cx, cy = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
    zt = box.z + box.h
    top = [view.p(x, y, zt) for x, y in pts]
    bottom = [view.p(x, y, box.z) for x, y in pts]
    out, edges = [], []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        nx, ny = b[1] - a[1], a[0] - b[0]
        length = math.hypot(nx, ny) or 1
        nx, ny = nx / length, ny / length
        if nx * ((a[0] + b[0]) / 2 - cx) + ny * ((a[1] + b[1]) / 2 - cy) < 0:
            nx, ny = -nx, -ny
        edges.append((nx * EX[1] + ny * EY[1] > 1e-6 and box.h > 0, nx * SUN[0] + ny * SUN[1]))
    # The sides the viewer sees, each shaded by how much it faces the sun
    for i, (visible, lit) in enumerate(edges):
        if not visible:
            continue
        j = (i + 1) % n
        if lit > 0:
            color = mix(dim(box.color, .74), mood["rim"], .30 * lit)
        else:
            color = mix(dim(box.color, .50 + .14 * (1 + lit)), mood["shadow"], .34)
        out.append(poly([top[i], top[j], bottom[j], bottom[i]], color, color, .8))
    # Ink: the silhouette of the sides, and a crease where they turn sharply
    for i, (visible, lit) in enumerate(edges):
        if not visible:
            continue
        j, before = (i + 1) % n, edges[i - 1]
        out.append(f'<path d="M{bottom[i][0]:.1f},{bottom[i][1]:.1f}L{bottom[j][0]:.1f},{bottom[j][1]:.1f}" '
                   f'stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>')
        if not before[0] or abs(before[1] - lit) > .45:
            out.append(f'<path d="M{top[i][0]:.1f},{top[i][1]:.1f}L{bottom[i][0]:.1f},{bottom[i][1]:.1f}" '
                       f'stroke="{INK}" stroke-width="{2.4 if not before[0] else 1.5}" stroke-linecap="round"/>')
        if not edges[j][0]:
            out.append(f'<path d="M{top[j][0]:.1f},{top[j][1]:.1f}L{bottom[j][0]:.1f},{bottom[j][1]:.1f}" '
                       f'stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>')
    # The top: cooler near the viewer, warm towards the sun
    near, far = max(top, key=lambda p: p[1]), min(top, key=lambda p: p[1])
    fill = page.gradient([(0, mix(dim(box.top_color, .80), mood["shadow"], .20)),
                          (1, mix(mix(box.top_color, "#FFFFFF", .06), mood["rim"], .22))],
                         near[0], near[1], far[0], far[1], user=True)
    out.append(poly(top, fill, INK, 2.4))
    p0 = view.p(*box.loc(0, 0), zt)
    if box.top:
        m = view.matrix(p0, view.p(*box.loc(1, 0), zt), view.p(*box.loc(0, 1), zt))
        out.append(f'<g transform="{m}">{"".join(box.top)}</g>')
    f0 = view.p(*box.loc(0, box.d), zt)
    mf = view.matrix(f0, view.p(*box.loc(1, box.d), zt), view.p(*box.loc(0, box.d), zt - 1))
    r0 = view.p(*box.loc(box.w, box.d), zt)
    mr = view.matrix(r0, view.p(*box.loc(box.w, box.d - 1), zt), view.p(*box.loc(box.w, box.d), zt - 1))
    if box.front:
        out.append(f'<g transform="{mf}">{"".join(box.front)}</g>')
    if box.right:
        out.append(f'<g transform="{mr}">{"".join(box.right)}</g>')
    # The light of the sun along the edges that face it
    for i, (visible, lit) in enumerate(edges):
        if lit > .2:
            j = (i + 1) % n
            a = (top[i][0] + (view.p(cx, cy, zt)[0] - top[i][0]) * .02, top[i][1] + (view.p(cx, cy, zt)[1] - top[i][1]) * .02)
            b = (top[j][0] + (view.p(cx, cy, zt)[0] - top[j][0]) * .02, top[j][1] + (view.p(cx, cy, zt)[1] - top[j][1]) * .02)
            out.append(f'<path d="M{a[0]:.1f},{a[1]:.1f}L{b[0]:.1f},{b[1]:.1f}" stroke="{mood["rim"]}" '
                       f'stroke-width="2.6" stroke-linecap="round" opacity="{min(1, .35 + lit * .7):.2f}"/>')
    for face, x, y, w, h, color in box.screens:
        m = {"top": None, "front": mf, "right": mr}[face] or view.matrix(
            p0, view.p(*box.loc(1, 0), zt), view.p(*box.loc(0, 1), zt))
        glows.append(f'<g transform="{m}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/></g>')
    page.add(*out)


def draw_machine(page, boxes, mood, center_x=1390, base_y=940):
    view = View(boxes, center_x, base_y, 940, 540)
    # The pier it stands on, running out of the picture to the right and to the viewer
    ground = [b for b in boxes if b.z == 0]
    xs = [c[0] for b in ground for c in b.corners()]
    ys = [c[1] for b in ground for c in b.corners()]
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    x0, y0, x1, y1 = min(xs) - span * .30, min(ys) - span * .34, max(xs) + 4000, max(ys) + 4000
    deck = [view.p(x0, y0), view.p(x1, y0), view.p(x1, y1), view.p(x0, y1)]
    far = view.p(x0, y0)
    fill = page.gradient([(0, mix(mood["shadow"], mood["glow"], .42)), (.35, mix(mood["shadow"], "#0A0718", .35)),
                          (1, "#07060F")], far[0], far[1], far[0] - 80, far[1] + 420, user=True)
    page.add(poly(deck, fill))
    planks = []
    step = span * .14
    k = 0
    while y0 + k * step < y1 and k < 60:
        a, b = view.p(x0, y0 + k * step), view.p(x1, y0 + k * step)
        planks.append(f'<path d="M{a[0]:.1f},{a[1]:.1f}L{b[0]:.1f},{b[1]:.1f}" stroke="#05040C" stroke-width="2" opacity=".55"/>')
        k += 1
    page.add("".join(planks))
    a, b, c = view.p(x0, y1), view.p(x0, y0), view.p(x1, y0)
    page.add(f'<path d="M{a[0]:.1f},{a[1]:.1f}L{b[0]:.1f},{b[1]:.1f}L{c[0]:.1f},{c[1]:.1f}" fill="none" '
             f'stroke="{mood["rim"]}" stroke-width="3" opacity=".8" stroke-linejoin="round"/>')
    # The glow of the sunset on the wet boards, and the machine's shadow, which falls to the viewer
    page.add(f'<ellipse cx="{far[0] + 420:.0f}" cy="{far[1] + 70:.0f}" rx="520" ry="70" fill="{mood["glow"]}" '
             f'opacity=".20" filter="url(#blur20)"/>')
    for b in ground:
        base = [view.p(c[0], c[1]) for c in b.corners()]
        cast = [view.p(c[0] - SUN[0] * b.h * 1.1, c[1] - SUN[1] * b.h * 1.1) for c in b.corners()]
        page.add(poly(hull(base + cast), "#03020A", extra='opacity=".62" filter="url(#blur8)"'))
    glows = []
    for b in boxes:
        draw_box(page, view, b, mood, glows)
    if glows:
        page.add(f'<g filter="url(#blur20)" opacity=".55" style="mix-blend-mode:screen">{"".join(glows)}</g>')
    return view


# --- the scene ---------------------------------------------------------------

def palm(page, x, y, height, lean, color, rnd):
    """A palm's silhouette: a bent trunk and drooping fronds."""
    tx, ty = x + lean, y - height
    out = [f'<path d="M{x - height * .028:.1f},{y:.1f}Q{x + lean * .2:.1f},{y - height * .55:.1f} {tx - height * .012:.1f},{ty:.1f}'
           f'L{tx + height * .012:.1f},{ty:.1f}Q{x + lean * .2 + height * .04:.1f},{y - height * .55:.1f} {x + height * .028:.1f},{y:.1f}Z" fill="{color}"/>']
    for k in range(11):
        angle = math.radians(-205 + k * 23 + rnd.uniform(-7, 7))
        length = height * rnd.uniform(.34, .46)
        ex, ey = tx + math.cos(angle) * length, ty + math.sin(angle) * length * .75 + length * .34
        mx, my = tx + math.cos(angle) * length * .55, ty + math.sin(angle) * length * .75 - length * .10
        out.append(f'<path d="M{tx:.1f},{ty:.1f}Q{mx:.1f},{my:.1f} {ex:.1f},{ey:.1f}" fill="none" stroke="{color}" '
                   f'stroke-width="{height * .016:.1f}" stroke-linecap="round"/>')
        leaves = []
        for i in range(1, 15):
            t = i / 15
            px = (1 - t) ** 2 * tx + 2 * (1 - t) * t * mx + t * t * ex
            py = (1 - t) ** 2 * ty + 2 * (1 - t) * t * my + t * t * ey
            drop = length * .30 * math.sin(math.pi * min(1, t * 1.15)) + 2
            leaves.append(f"M{px:.1f},{py:.1f}l{math.cos(angle) * drop * .35:.1f},{drop:.1f}")
        out.append(f'<path d="{"".join(leaves)}" fill="none" stroke="{color}" stroke-width="{height * .011:.1f}" stroke-linecap="round"/>')
    page.add("".join(out))


def scene(page, mood, rnd, centered=False):
    """The sky, the city, the palms and the water. The sun and the city sit to the right, where
    the machine is; centered, for the loading screen, they take the whole width."""
    sun_x = 960 if centered else rnd.uniform(1380, 1560)
    # Sky, brushed
    sky = page.gradient([(o / .64, c) for o, c in mood["sky"]], 0, 0, 0, HORIZON, user=True)
    page.add(f'<rect width="{W}" height="{H}" fill="{mood["sky"][-1][1]}"/>')
    page.add(f'<g filter="url(#brush)"><rect x="-120" y="-80" width="{W + 240}" height="{HORIZON + 120:.0f}" fill="{sky}"/>')
    halo = page.radial([(0, mood["sun"][0], .95), (.25, mood["glow"], .55), (1, mood["glow"], 0)])
    page.add(f'<ellipse cx="{sun_x:.0f}" cy="{HORIZON - 30:.0f}" rx="760" ry="330" fill="{halo}"/></g>')
    disc = page.gradient([(0, mood["sun"][0]), (1, mood["sun"][1])])
    radius = 92 if mood is MOODS["night"] else 128
    page.add(f'<circle cx="{sun_x:.0f}" cy="{HORIZON - (150 if mood is MOODS["night"] else 46):.0f}" r="{radius}" fill="{disc}"/>')
    # Clouds lit from below
    shade, lit = mood["cloud"]
    cloud = page.gradient([(0, shade), (.55, mix(shade, lit, .55)), (1, lit)])
    clouds = []
    for _ in range(7):
        cx, cy = rnd.uniform(40 if centered else 720, 1900), rnd.uniform(HORIZON - 440, HORIZON - 70)
        w = rnd.uniform(220, 520)
        for i in range(9):
            t = i / 8 - .5
            clouds.append(f'<ellipse cx="{cx + t * w:.0f}" cy="{cy - (1 - 4 * t * t) * w * .035 + rnd.uniform(-5, 5):.0f}" '
                          f'rx="{w * rnd.uniform(.13, .2):.0f}" ry="{w * rnd.uniform(.035, .06) + 6:.0f}"/>')
    page.add(f'<g fill="{cloud}" opacity=".82" filter="url(#ragged)">{"".join(clouds)}</g>')
    for _ in range(9):
        cx, cy = rnd.uniform(0 if centered else 800, 1920), rnd.uniform(HORIZON - 120, HORIZON - 22)
        page.add(f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rnd.uniform(140, 380):.0f}" ry="{rnd.uniform(3, 7):.1f}" '
                 f'fill="{lit}" opacity="{rnd.uniform(.35, .7):.2f}" filter="url(#blur3)"/>')
    # The city across the water: a hazy far row, then a darker near one with lit windows
    for layer, (base, height, fog) in enumerate(((HORIZON + 2, 120, .50), (HORIZON + 6, 185, .16))):
        color = mix(mood["city"], mood["glow"], fog)
        tower = page.gradient([(0, color), (1, mix(color, mood["glow"], .30))])
        x, out, windows = (-40.0 if centered else 640.0), [], []
        while x < W + 40:
            bw = rnd.uniform(26, 84)
            bh = rnd.uniform(.18, 1) ** 1.6 * height + 16
            out.append(f'<rect x="{x:.0f}" y="{base - bh:.0f}" width="{bw:.0f}" height="{bh + 4:.0f}"/>')
            if rnd.random() < .3:
                out.append(f'<rect x="{x + bw * .3:.0f}" y="{base - bh - bh * .14:.0f}" width="{bw * .4:.0f}" height="{bh * .14 + 2:.0f}"/>')
            if rnd.random() < .16:
                out.append(f'<rect x="{x + bw / 2 - 1:.0f}" y="{base - bh - 30:.0f}" width="2" height="30"/>')
            if layer:
                for wy in range(int(base - bh + 7), int(base - 8), 9):
                    for wx in range(int(x + 5), int(x + bw - 6), 8):
                        if rnd.random() < .22:
                            windows.append(f'<rect x="{wx}" y="{wy}" width="3" height="4" fill="{rnd.choice((mood["sun"][0], mood["rim"], "#9FE8FF"))}"/>')
            x += bw + rnd.uniform(-6, 14)
        page.add(f'<g fill="{tower}">{"".join(out)}</g><g opacity=".85">{"".join(windows)}</g>')
    # An island with palms, far to the right
    dark = mix(mood["city"], "#04030C", .55)
    page.add(f'<ellipse cx="1800" cy="{HORIZON + 14:.0f}" rx="270" ry="20" fill="{dark}"/>')
    for x, hgt, lean in ((1700, 330, -40), (1822, 410, 30), (1895, 280, -20), (1608, 190, 16)):
        palm(page, x, HORIZON + 8, hgt * rnd.uniform(.92, 1.06), lean, dark, rnd)
    if centered:
        page.add(f'<ellipse cx="130" cy="{HORIZON + 14:.0f}" rx="250" ry="20" fill="{dark}"/>')
        for x, hgt, lean in ((210, 320, 36), (96, 400, -28), (30, 270, 18), (300, 180, -14)):
            palm(page, x, HORIZON + 8, hgt * rnd.uniform(.92, 1.06), lean, dark, rnd)
    page.add(f'<rect x="{0 if centered else 600}" y="{HORIZON - 26:.0f}" width="{W}" height="34" fill="{mood["glow"]}" opacity=".22" filter="url(#blur8)"/>')
    # The water: the sky upside down, darker, with the sun's streak
    w1, w2, w3 = mood["water"]
    water = page.gradient([(0, w1), (.22, w2), (1, w3)])
    page.add(f'<rect x="0" y="{HORIZON:.0f}" width="{W}" height="{H - HORIZON:.0f}" fill="{water}"/>')
    ripples = []
    for i in range(46):
        y = HORIZON + 6 + (i / 46) ** 1.5 * 300
        spread = 30 + (y - HORIZON) * .9
        ripples.append(f'<ellipse cx="{sun_x + rnd.uniform(-spread, spread):.0f}" cy="{y:.0f}" rx="{rnd.uniform(24, 60 + spread * .5):.0f}" '
                       f'ry="{1.6 + (y - HORIZON) * .012:.1f}" fill="{mood["sun"][0]}" opacity="{rnd.uniform(.25, .7) * (1 - i / 60):.2f}"/>')
    for _ in range(60):
        y = HORIZON + rnd.uniform(4, 330)
        ripples.append(f'<ellipse cx="{rnd.uniform(0 if centered else 500, 1920):.0f}" cy="{y:.0f}" rx="{rnd.uniform(30, 150):.0f}" ry="{1.2 + (y - HORIZON) * .008:.1f}" '
                       f'fill="{rnd.choice((mood["glow"], w3, mood["rim"]))}" opacity="{rnd.uniform(.12, .4):.2f}"/>')
    page.add("".join(ripples))


def finish(page, splash=False):
    """Keeps the left, the very top and the bottom dark for the texts, and adds a grain of paint.
    The loading screen has no texts but its bottom line: only its top and bottom are shaded."""
    grain = f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity=".07" style="mix-blend-mode:overlay"/>'
    if splash:
        top = page.gradient([(0, NAVY, .92), (.16, NAVY, .55), (.34, NAVY, 0)])
        bottom = page.gradient([(.72, "#03040C", 0), (.86, "#03040C", .55), (1, "#03040C", .86)])
        page.add(f'<rect width="{W}" height="{H}" fill="{top}"/><rect width="{W}" height="{H}" fill="{bottom}"/>{grain}')
        return
    left = page.gradient([(0, NAVY, .97), (.26, NAVY, .90), (.46, NAVY, .50), (.64, NAVY, 0)], 0, 0, 1, 0)
    top = page.gradient([(0, NAVY, .95), (.11, NAVY, .84), (.19, NAVY, .34), (.30, NAVY, 0)])
    bottom = page.gradient([(.84, "#03040C", 0), (1, "#03040C", .70)])
    # A soft shade behind the system's name, which may run far to the right over the bright sky
    page.add(f'<ellipse cx="960" cy="478" rx="560" ry="84" fill="{NAVY}" opacity=".42" filter="url(#blur45)"/>')
    page.add(f'<rect width="{W}" height="{H}" fill="{left}"/><rect width="{W}" height="{H}" fill="{top}"/>'
             f'<rect width="{W}" height="{H}" fill="{bottom}"/>{grain}')


# --- the machines ------------------------------------------------------------

def label(page, a, b):
    return page.gradient([(0, a), (1, b)], 0, 0, 1, 1)


def screen(page, a, b):
    return page.gradient([(0, mix(a, "#FFFFFF", .35)), (.5, a), (1, b)], 0, 0, 1, 1)


def pad(x, y, w, d, color, buttons, rot=0, face=None, r=None, cross="#22222A"):
    """A controller lying on the pier: a cross on the left, round buttons on the right."""
    details = [rect(w * .06, d * .12, w * .88, d * .76, face, r=d * .12)] if face else []
    details.append(dpad(w * .22, d * .5, d * .46, d * .16, cross))
    for i, c in enumerate(buttons):
        details.append(circ(w * (.86 - .14 * i), d * (.42 + .16 * (i % 2)), d * .12, c))
    details.append(rect(w * .42, d * .56, w * .07, d * .08, "#3A3A44", r=1) + rect(w * .52, d * .56, w * .07, d * .08, "#3A3A44", r=1))
    return Box(x, y, w, d, 8, color, r=d * .22 if r is None else r, rot=rot, top=details)


def cart(page, x, y, w, d, h, color, z, c1, c2):
    """A cartridge standing in its slot, a colored label on its front."""
    return Box(x, y, w, d, h, color, z=z, r=1.5, front=[rect(w * .1, h * .12, w * .8, h * .62, label(page, c1, c2), r=1.5)])


def snes(page):
    gray, purple = "#C9C7D0", "#6A4FB0"
    return [
        Box(0, 0, 200, 150, 36, gray, r=12,
            top=[lines(14, 16, 22, 5, 6, "#8F8D9A"), lines(164, 16, 22, 5, 6, "#8F8D9A")],
            front=[rect(18, 13, 42, 14, "#2A2933", r=3), rect(68, 13, 42, 14, "#2A2933", r=3), circ(176, 20, 3, "#D9363E")]),
        Box(40, 12, 120, 98, 7, "#B9B7C3", z=36, r=8, top=[rect(18, 30, 84, 20, "#1C1B23", r=3)]),
        cart(page, 62, 44, 76, 14, 36, "#A3A1AD", 43, "#FF5E8A", "#3B8CFF"),
        Box(20, 118, 38, 14, 5, purple, z=36, r=3),
        Box(84, 116, 32, 18, 4, "#93919E", z=36, r=3),
        Box(142, 118, 38, 14, 5, purple, z=36, r=3),
        pad(-92, 176, 104, 46, "#C9C7D0", ("#6A4FB0", "#9A86D6", "#6A4FB0", "#9A86D6"), rot=-14),
    ]


def nes(page):
    gray, dark = "#D8D6D1", "#3A3A42"
    return [
        Box(0, 0, 210, 170, 58, gray, r=3,
            top=[lines(150, 18, 46, 9, 7, "#A9A7A2"), line(0, 118, 210, 118, "#A9A7A2", .8)],
            front=[rect(0, 30, 210, 28, dark, stroke="none"), rect(8, 4, 150, 22, "#CBC9C4", r=2),
                   circ(18, 44, 2.6, "#E0303A"), rect(28, 39, 26, 10, "#8E2B33", r=1.5), rect(60, 39, 26, 10, "#8E2B33", r=1.5),
                   rect(126, 37, 28, 15, "#101014", r=2), rect(164, 37, 28, 15, "#101014", r=2)],
            right=[rect(0, 30, 170, 28, dark, stroke="none", op=.9)]),
        pad(-96, 196, 110, 48, "#D8D6D1", ("#D9303A", "#D9303A"), rot=-12, face="#26262C", r=3, cross="#111116"),
    ]


def n64(page):
    body, hump = "#3A3B42", "#44454D"
    return [
        Box(0, 0, 210, 150, 32, body, r=30,
            top=[circ(34, 104, 9, "#2A2B31"), circ(176, 104, 9, "#2A2B31"), rect(76, 104, 58, 26, "#303138", r=4)],
            front=[rect(24 + i * 42, 12, 28, 13, "#121216", r=5) for i in range(4)]),
        Box(52, 10, 106, 84, 11, hump, z=32, r=12, top=[rect(14, 30, 78, 20, "#121216", r=3)]),
        cart(page, 68, 42, 74, 14, 34, "#8E8E98", 43, "#FFC25E", "#3B8CFF"),
        Box(16, 112, 40, 34, 34, body, r=16),
        Box(154, 112, 40, 34, 34, body, r=16),
        pad(-100, 190, 104, 50, "#8E8E98", ("#F2C230", "#F2C230", "#2E7BD9", "#3FA65A"), rot=-12),
    ]


def megadrive(page):
    black = "#1C1C21"
    return [
        Box(0, 0, 214, 152, 28, black, r=16,
            top=['<circle cx="107" cy="68" r="62" fill="none" stroke="#B9BCC8" stroke-width="2.4" stroke-dasharray="150 400" transform="rotate(200 107 68)"/>',
                 rect(18, 124, 28, 10, "#D12B33", r=2), rect(58, 126, 18, 7, "#D5D5DC", r=2), circ(92, 130, 2.6, "#FF4650"),
                 rect(14, 92, 6, 22, "#2E2E36", r=2), lines(168, 104, 30, 5, 6, "#33333C")],
            front=[rect(24, 9, 36, 13, "#08080A", r=3), rect(70, 9, 36, 13, "#08080A", r=3), circ(180, 15, 3.4, "#08080A")]),
        Box(49, 10, 116, 116, 6, "#26262D", z=28, r=58, top=[rect(26, 48, 64, 20, "#08080A", r=3)]),
        cart(page, 78, 60, 58, 14, 34, "#131316", 34, "#FF5E8A", "#FFC25E"),
        pad(-104, 192, 110, 50, "#1C1C21", ("#3A3A44", "#3A3A44", "#3A3A44"), rot=-12, cross="#C9C9D2"),
    ]


def mastersystem(page):
    black, red = "#1B1B20", "#C4161C"
    return [
        Box(0, 0, 224, 142, 26, black, r=4,
            top=[path("M8,134L8,96L58,78L96,78L96,134Z", fill=red), lines(112, 96, 100, 4, 9, "#D9D9E0", .9, .8),
                 rect(112, 78, 30, 9, "#8D8D97", r=1.5), rect(150, 78, 30, 9, "#8D8D97", r=1.5), circ(196, 82, 2.6, "#FF4650")],
            front=[rect(18, 7, 74, 5, "#050506", r=1), rect(128, 8, 32, 12, "#08080A", r=2), rect(170, 8, 32, 12, "#08080A", r=2)]),
        Box(56, 8, 112, 58, 8, "#25252B", z=26, r=3, top=[rect(14, 18, 84, 18, "#08080A", r=2), line(14, 44, 98, 44, red, 1.2)]),
        cart(page, 74, 28, 76, 12, 30, "#17171B", 34, "#F03C72", "#FFFFFF"),
        pad(-92, 184, 96, 46, "#1B1B20", ("#C4161C", "#C4161C"), rot=-12, r=4, cross="#3A3A44"),
    ]


def sg1000(page):
    white = "#E7E5DF"
    return [
        Box(0, 0, 196, 134, 30, white, r=6,
            top=[rect(10, 10, 176, 74, "#1A1A1F", r=3), rect(46, 30, 96, 18, "#050506", r=2),
                 rect(18, 100, 34, 13, "#2C5FBF", r=2), rect(60, 100, 34, 13, "#D9A62E", r=2), lines(134, 98, 46, 4, 7, "#9D9B95")],
            front=[rect(18, 10, 40, 12, "#111114", r=2)]),
        cart(page, 52, 32, 84, 13, 30, "#17171B", 30, "#FFC25E", "#2C5FBF"),
        Box(-104, 150, 66, 60, 12, "#222228", r=6, rot=-14, top=[circ(52, 14, 6, "#D9303A")]),
        Box(-80, 170, 13, 13, 44, "#111114", z=12, r=6.5),
        Box(-86, 164, 25, 25, 16, "#D9303A", z=50, r=12.5),
    ]


def pcengine(page):
    white = "#EFEDE6"
    return [
        Box(0, 0, 150, 150, 26, white, r=7,
            top=[rect(24, 118, 102, 9, "#25252B", r=2), rect(8, 54, 10, 30, "#C9C7C0", r=2), rect(112, 16, 24, 7, "#E2542C", r=2),
                 lines(30, 20, 60, 6, 7, "#C4C2BB"), rect(30, 70, 90, 34, "#E4E2DB", r=3)],
            front=[rect(34, 8, 82, 5, "#0C0C0F", r=1)]),
        Box(40, 144, 70, 34, 2.5, "#17171B", z=12, r=2, top=[rect(6, 5, 58, 18, label(page, "#FF7F4F", "#6A55B8"), r=1.5)]),
        Box(-122, 150, 104, 48, 9, white, r=8, rot=-14,
            top=[dpad(24, 24, 24, 8, "#2A2A31"), circ(72, 26, 7, "#E2542C"), circ(90, 22, 7, "#E2542C"),
                 rect(44, 34, 9, 4, "#8D8B85", r=1), rect(56, 34, 9, 4, "#8D8B85", r=1)]),
    ]


def game_cart(page, x, y, color, c1, c2, rot, z=0):
    """A small cartridge lying on the pier."""
    return Box(x, y, 48, 54, 6, color, z=z, r=3, rot=rot,
               top=[rect(6, 12, 36, 32, label(page, c1, c2), r=2), lines(8, 4, 32, 2, 3, mix(color, "#000000", .35))])


def gameboy(page, body, buttons, glass, lit):
    return [
        Box(0, 0, 100, 166, 15, body, r=11,
            top=[rect(8, 9, 84, 74, "#2B2B34", r=5), rect(19, 18, 62, 54, screen(page, *lit), r=1.5), circ(13, 42, 1.8, "#FF4650", stroke="none"),
                 dpad(27, 114, 28, 9.5, "#1E1E25"), circ(66, 120, 8, buttons), circ(84, 110, 8, buttons),
                 path("M34,146l12,-4", stroke="#55555F", sw=4.4), path("M52,146l12,-4", stroke="#55555F", sw=4.4),
                 path("M72,150l12,-10M77,154l12,-10M82,158l10,-8", stroke=mix(body, "#000000", .4), sw=1.6)],
            screens=[("top", 19, 18, 62, 54, lit[0])]),
        game_cart(page, 150, 40, glass, "#FF5E8A", "#FFC25E", 22),
        game_cart(page, 176, 112, "#8E8E98", "#3B8CFF", "#7BE0C3", -16),
    ]


def gbc(page):
    return gameboy(page, "#1FA39B", "#2A2A32", "#6A4FB0", ("#B8F27A", "#2E9E6B"))


def gb(page):
    return gameboy(page, "#C6C4BA", "#A6245C", "#8E8E98", ("#B5C96A", "#5E7A32"))


def gba(page):
    body = "#5A4FD6"
    return [
        Box(10, -5, 44, 10, 11, "#9C97C9", r=4), Box(146, -5, 44, 10, 11, "#9C97C9", r=4),
        Box(0, 0, 200, 108, 15, body, r=30,
            top=[rect(52, 16, 96, 70, "#22222B", r=7), rect(62, 25, 76, 52, screen(page, "#7BE0FF", "#3B5BD9"), r=1.5),
                 dpad(27, 52, 28, 9.5, "#1E1E25"), circ(160, 60, 8.5, "#1E1E25"), circ(178, 46, 8.5, "#1E1E25"),
                 circ(34, 86, 3.4, "#8F8AC2"), circ(46, 92, 3.4, "#8F8AC2"), circ(150, 14, 1.8, "#7CFF8A", stroke="none"),
                 path("M160,84l14,-6M164,90l14,-6M168,96l12,-5", stroke=mix(body, "#000000", .4), sw=1.6)],
            screens=[("top", 62, 25, 76, 52, "#7BE0FF")]),
        game_cart(page, 250, 30, "#3A3B42", "#FF5E8A", "#FFC25E", 18),
    ]


def nds(page, silver="#DADDE5"):
    return [
        Box(0, -11, 168, 11, 88, silver, r=3,
            front=['<g transform="scale(1 .72)">' + rect(9, 8, 150, 104, "#1D1E26", r=5) + rect(36, 22, 96, 72, screen(page, "#9FE8FF", "#3B5BD9"), r=1.5)
                   + "".join(circ(x, y, 1.4, "#55565F", stroke="none") for x in (20, 148) for y in (50, 58, 66)) + "</g>"],
            screens=[("front", 36, 16, 96, 52, "#9FE8FF")]),
        Box(0, 0, 168, 120, 14, silver, r=9,
            top=[rect(30, 14, 108, 84, "#1D1E26", r=3), rect(36, 20, 96, 72, screen(page, "#FFD9A0", "#F0629F"), r=1.5),
                 dpad(15, 56, 22, 7.5, "#3A3B44"), circ(153, 46, 5, "#3A3B44"), circ(153, 66, 5, "#3A3B44"),
                 circ(144, 56, 5, "#3A3B44"), circ(162, 56, 5, "#3A3B44"), rect(140, 86, 9, 4, "#8A8D96", r=2), rect(152, 86, 9, 4, "#8A8D96", r=2)],
            screens=[("top", 36, 20, 96, 72, "#FFB0C8")]),
        Box(196, 60, 6, 96, 5, "#EDEDF2", r=2.5, rot=28),
    ]


def gamegear(page):
    black = "#1D1D22"
    return [
        Box(0, 0, 214, 114, 23, black, r=27,
            top=[rect(58, 15, 98, 78, "#0F0F13", r=9), rect(71, 26, 72, 56, screen(page, "#8EF0C0", "#2C8FD9"), r=1.5),
                 circ(30, 56, 18, "#2A2A32"), dpad(30, 56, 24, 8, "#15151A"), circ(168, 64, 8.5, "#2A2A32"), circ(186, 50, 8.5, "#2A2A32"),
                 rect(170, 22, 18, 6, "#2B5FD9", r=3), circ(194, 80, 2, "#FF4650", stroke="none"),
                 path("M22,88l14,6M18,94l14,6", stroke="#33333C", sw=1.6)],
            screens=[("top", 71, 26, 72, 56, "#8EF0C0")]),
        game_cart(page, 262, 26, "#17171B", "#FF5E8A", "#3B8CFF", 16),
    ]


def neogeo_pocket(page, body, lit):
    return [
        Box(0, 0, 184, 102, 17, body, r=20,
            top=[rect(50, 13, 84, 70, "#18181F", r=5), rect(60, 22, 64, 52, screen(page, *lit), r=1.5),
                 circ(27, 52, 17, mix(body, "#000000", .3)), circ(150, 60, 8.5, "#2A2A32"), circ(168, 46, 8.5, "#2A2A32"),
                 rect(146, 82, 16, 5, mix(body, "#000000", .45), r=2.5)],
            screens=[("top", 60, 22, 64, 52, lit[0])]),
        Box(17, 42, 20, 20, 6, "#25252C", z=17, r=10),
        Box(13, 38, 28, 28, 5, "#34343E", z=23, r=14),
        game_cart(page, 232, 22, "#25252C", "#FFC25E", "#F03C72", 18),
    ]


def ngp(page):
    return neogeo_pocket(page, "#9BA1B6", ("#D4DEC0", "#7F8F74"))


def ngpc(page):
    return neogeo_pocket(page, "#2743B8", ("#FFD36E", "#F03C72"))


def joystick(x, y, rot=-14):
    """A one-button joystick of the 80s, next to a home computer."""
    return [Box(x, y, 66, 62, 12, "#1C1C21", r=6, rot=rot, top=[circ(52, 13, 6.5, "#D9303A")]),
            Box(x + 24, y + 26, 13, 13, 42, "#111114", z=12, r=6.5),
            Box(x + 18.5, y + 20.5, 24, 24, 15, "#2A2A32", z=54, r=12)]


def c64(page):
    beige, well, key = "#C9B99B", "#4A3C34", "#3A2E28"
    return [
        Box(0, 0, 236, 136, 26, beige, r=7,
            top=[rect(13, 40, 182, 78, well, r=2), grid(18, 45, 15, 4, 9.4, 13, 2, key, stroke="#221A16"),
                 rect(60, 103, 92, 11, key, r=1.5, stroke="#221A16", sw=.3), grid(202, 45, 1, 4, 22, 13, 4, "#8F8473"),
                 circ(214, 24, 2.6, "#FF4650"), lines(14, 12, 90, 4, 6, "#A99A7E"),
                 "".join(rect(150 + i * 5, 14, 4, 12, c, stroke="none") for i, c in enumerate(("#D9303A", "#F28C28", "#F2C230", "#3FA65A", "#2E7BD9")))],
            front=[rect(0, 0, 236, 6, "#B6A688", stroke="none")]),
    ] + joystick(-120, 120)


def msx2(page):
    body = "#24252C"
    return [
        Box(0, 0, 244, 144, 26, body, r=5,
            top=[rect(12, 54, 176, 78, "#111216", r=2), grid(17, 59, 14, 4, 10, 13.5, 2, "#CFCFD6"),
                 rect(56, 119, 96, 10, "#CFCFD6", r=1.5, sw=.3), grid(17, 36, 5, 1, 22, 10, 4, "#8E8E99"),
                 rect(196, 86, 36, 36, "#3C5A9A", r=5), dpad(214, 104, 26, 8, "#27375F"),
                 rect(148, 10, 78, 16, "#08080A", r=2), line(12, 30, 232, 30, "#D9303A", 1.2), circ(206, 62, 2.6, "#7CFF8A")],
            front=[rect(20, 8, 30, 10, "#08080A", r=2), rect(60, 8, 30, 10, "#08080A", r=2)]),
        cart(page, 156, 12, 62, 11, 28, "#EDEDF2", 26, "#F03C72", "#3B8CFF"),
    ] + joystick(-118, 126)


def cabinet(page, body, accent, glass, sign, stripes):
    """An upright arcade cabinet: base, control panel, screen and lit marquee."""
    def side(depth, drop=0):
        return ["".join(path(f"M0,{y - drop}L{depth},{y - drop + depth * .3:.1f}L{depth},{y - drop + depth * .3 + w:.1f}L0,{y - drop + w}Z",
                             fill=c, stroke="none", op=.9) for y, w, c in stripes)]
    return [
        Box(0, 0, 100, 84, 96, body, r=2,
            front=[rect(0, 0, 100, 14, accent, stroke="none"), rect(30, 36, 40, 42, mix(body, "#000000", .35), r=2),
                   rect(40, 46, 8, 12, "#FFC25E", r=1), rect(52, 46, 8, 12, "#FFC25E", r=1)],
            right=side(84, -30)),
        Box(0, 0, 100, 52, 116, body, z=96, r=2,
            front=[rect(7, 8, 86, 96, "#08080E", r=4), rect(13, 14, 74, 82, screen(page, *glass), r=3),
                   rect(24, 30, 10, 7, "#FFFFFF", stroke="none", op=.85), rect(44, 44, 10, 7, "#FFFFFF", stroke="none", op=.85),
                   rect(62, 28, 10, 7, "#FFFFFF", stroke="none", op=.85), path("M46,84l5,-9l5,9Z", fill="#FFE27A", stroke="none"),
                   rect(49.5, 62, 2, 8, "#FFE27A", stroke="none")],
            right=side(52), screens=[("front", 13, 14, 74, 82, glass[0])]),
        Box(-4, 46, 108, 54, 11, "#1A1A21", z=96, r=2,
            top=[circ(26, 26, 7, "#2A2A33")] + [circ(52 + (i % 3) * 16, 18 + (i // 3) * 16 + (i % 3) * 2, 5.4, c)
                                               for i, c in enumerate((accent, "#FFC25E", "#7BE0FF", accent, "#FFC25E", "#7BE0FF"))]),
        Box(19, 69, 6, 6, 16, "#C9C9D2", z=107, r=3),
        Box(15, 65, 14, 14, 11, "#D9303A", z=123, r=7),
        Box(-3, -3, 106, 60, 28, body, z=212, r=2,
            front=[rect(6, 5, 94, 18, label(page, *sign), r=2), path("M16,14h20M44,14h34M84,14h8", stroke="#FFFFFF", sw=3, op=.9)],
            screens=[("front", 6, 5, 94, 18, sign[0])]),
    ]


def mame(page):
    return cabinet(page, "#16224F", "#3B8CFF", ("#3B2A8C", "#0B0B2A"), ("#3B8CFF", "#7BE0FF"),
                   ((20, 14, "#FFC25E"), (40, 8, "#3B8CFF")))


def fbneo(page):
    return cabinet(page, "#3A1014", "#F2542C", ("#5A1680", "#12071F"), ("#F2542C", "#FFC25E"),
                   ((16, 12, "#F2542C"), (34, 8, "#FFC25E"), (48, 5, "#F2542C")))


def naomi(page):
    """A sit-down cabinet, white, with a stool."""
    white = "#ECECF2"
    return [
        Box(0, 0, 130, 100, 68, white, r=8, front=[rect(40, 22, 50, 34, "#D4D4DC", r=3), rect(52, 30, 8, 12, "#F0629F", r=1), rect(68, 30, 8, 12, "#F0629F", r=1)]),
        Box(6, 0, 118, 58, 112, white, z=68, r=10,
            front=[rect(8, 8, 102, 92, "#0A0A10", r=8), rect(15, 15, 88, 78, screen(page, "#7BE0FF", "#3B2A8C"), r=5),
                   path("M30,70l14,-22l12,14l10,-8l18,16Z", fill="#FFFFFF", stroke="none", op=.8), circ(80, 34, 6, "#FFE27A", stroke="none")],
            screens=[("front", 15, 15, 88, 78, "#7BE0FF")]),
        Box(-5, 52, 140, 58, 12, "#DCDCE4", z=68, r=6,
            top=[circ(30, 28, 8, "#2A2A33")] + [circ(64 + (i % 3) * 20, 20 + (i // 3) * 18 + (i % 3) * 2, 6.4, c)
                                               for i, c in enumerate(("#F0629F", "#F0629F", "#F0629F", "#3FA65A", "#3FA65A", "#3FA65A"))]),
        Box(22, 77, 6, 6, 16, "#C9C9D2", z=80, r=3),
        Box(18, 73, 14, 14, 11, "#2743B8", z=96, r=7),
        Box(10, -2, 110, 56, 20, white, z=180, r=8, front=[rect(8, 4, 94, 12, label(page, "#7BE0FF", "#F0629F"), r=3)],
            screens=[("front", 8, 4, 94, 12, "#7BE0FF")]),
        Box(48, 150, 12, 12, 34, "#2A2A33", r=6),
        Box(30, 132, 48, 48, 9, "#D9303A", z=34, r=24),
    ]


def computer(page, case, glass, picture):
    """A desktop computer of the 90s: the case, the monitor on it, keyboard and mouse."""
    key = mix(case, "#FFFFFF", .25)
    return [
        Box(0, 0, 190, 150, 30, case, r=3,
            front=[rect(108, 7, 66, 6, "#2E2E36", r=1), rect(108, 17, 66, 4, "#2E2E36", r=1), circ(20, 15, 2.6, "#7CFF8A"),
                   rect(30, 11, 16, 8, mix(case, "#000000", .25), r=1.5), lines(60, 9, 34, 4, 4, mix(case, "#000000", .3))]),
        Box(24, 22, 142, 110, 112, case, z=30, r=7,
            front=[rect(9, 8, 124, 92, "#22222A", r=7), rect(17, 15, 108, 78, screen(page, *glass), r=4)] + picture,
            screens=[("front", 17, 15, 108, 78, glass[0])]),
        Box(8, 176, 172, 58, 8, case, r=3, top=[grid(6, 6, 15, 4, 8.6, 9.6, 2, key), rect(46, 49, 76, 6, key, r=1, sw=.3)]),
        Box(204, 190, 24, 34, 8, case, r=10, top=[line(12, 3, 12, 14, mix(case, "#000000", .4))]),
    ]


def ports(page):
    return computer(page, "#D5D0C2", ("#3FB8C9", "#1B3F8C"),
                    [rect(26, 24, 56, 40, "#E9ECF2", r=1.5, sw=.4), rect(26, 24, 56, 7, "#3B5BD9", r=1.5, sw=.4),
                     rect(58, 46, 54, 38, "#E9ECF2", r=1.5, sw=.4), rect(58, 46, 54, 7, "#F0629F", r=1.5, sw=.4)])


def pygame(page):
    snake = "".join(rect(x, y, 9, 9, c, r=1.5, sw=.4) for x, y, c in
                    ((30, 30, "#FFD43B"), (40, 30, "#FFD43B"), (50, 30, "#FFD43B"), (50, 40, "#FFD43B"), (50, 50, "#FFD43B"),
                     (60, 50, "#4B8BBE"), (70, 50, "#4B8BBE"), (80, 50, "#4B8BBE"), (80, 60, "#4B8BBE"), (80, 70, "#4B8BBE")))
    return computer(page, "#3A3B44", ("#27375F", "#0B0F24"), [snake, circ(104, 36, 4.5, "#F0629F", sw=.4)])


def allgames(page):
    """A pile of cartridges of every shape and color."""
    def big(x, y, color, c1, c2, rot, z=0):
        return Box(x, y, 96, 74, 13, color, z=z, r=4, rot=rot,
                   top=[rect(12, 12, 72, 40, label(page, c1, c2), r=2), lines(14, 60, 68, 2, 4, mix(color, "#000000", .4))])
    return [
        big(0, 0, "#A3A1AD", "#FF5E8A", "#3B8CFF", -8),
        big(120, 10, "#17171B", "#FFC25E", "#F03C72", 12),
        big(40, 6, "#D8D6D1", "#7BE0C3", "#3B5BD9", 6, z=13),
        game_cart(page, 236, 60, "#8E8E98", "#FFC25E", "#F2542C", 24),
        big(-70, 96, "#C4161C", "#FFE27A", "#FF7F4F", -20),
        big(70, 104, "#3A3B42", "#B8F27A", "#2E9E6B", 4),
        game_cart(page, 206, 132, "#6A4FB0", "#FF5E8A", "#FFC25E", -14),
        big(78, 100, "#F2C230", "#F0629F", "#6A55B8", -10, z=13),
        game_cart(page, 96, 26, "#1FA39B", "#FFFFFF", "#7BE0FF", 14, z=26),
    ]


def sign(page, tubes):
    """A neon sign on two posts."""
    return [
        Box(26, 2, 8, 8, 48, "#191428", r=2), Box(166, 2, 8, 8, 48, "#191428", r=2),
        Box(0, 0, 200, 12, 170, "#141026", z=48, r=3,
            front=[rect(6, 6, 188, 158, "#0C0918", r=4, stroke="#3A2A66", sw=1)] + tubes,
            screens=[("front", 40, 30, 120, 110, "#6A2A9C")]),
    ]


def favorites(page):
    star = "M" + "L".join(f"{100 + (62 if i % 2 == 0 else 26) * math.sin(math.pi * i / 5):.1f},{88 - (62 if i % 2 == 0 else 26) * math.cos(math.pi * i / 5):.1f}"
                          for i in range(10)) + "Z"
    return sign(page, [neon(star, "#FF4F9A", 3), neon("M36,152h128", "#FFD36E", 2.2), neon("M20,24h22M158,24h22", "#7BE0FF", 2)])


def lastplayed(page):
    ticks = "".join(f"M{100 + 56 * math.sin(a):.1f},{84 - 56 * math.cos(a):.1f}L{100 + 64 * math.sin(a):.1f},{84 - 64 * math.cos(a):.1f}"
                    for a in (math.pi * k / 6 for k in range(12)))
    circle = "M100,14a70,70 0 1 0 0.1,0Z"
    return sign(page, [neon(circle, "#5FE0FF", 3), neon(ticks, "#5FE0FF", 1.6), neon("M100,84L100,42M100,84L132,100", "#FF4F9A", 3),
                       neon("M40,160h120", "#FFD36E", 2.2)])


# --- families: one drawing, many machines ------------------------------------

RAINBOW = ("#D9303A", "#F28C28", "#F2C230", "#3FA65A", "#2E7BD9")


def raised(boxes, dz, keep=1):
    """Lifts a machine onto a base: every box but its last `keep` (its controller) goes up."""
    for b in boxes[:len(boxes) - keep]:
        b.z += dz
    return boxes


def on_base(page, machine, color, w, d, h=22, keep=1, tray=True):
    """A console on the unit sold to sit under it (a CD or disk drive)."""
    front = [rect(w * .5, h * .3, w * .34, h * .3, mix(color, "#000000", .45), r=1), circ(w * .12, h * .5, 2.6, "#7CFF8A")] if tray else []
    return [Box(-(w - 200) / 2 - 4, -8, w, d, h, color, r=6, front=front)] + raised(machine, h, keep)


def disc_console(page, body, lid, accent, pad_color, pad_buttons, w=200, d=170, h=34, r=8, tray=False, ridges=False,
                 led="#7CFF8A", pad_face=None, cross="#22222A"):
    """A console that plays discs: a round lid on top, or a tray at the front."""
    dark = mix(body, "#000000", .4)
    top = [lines(14, 14, w - 28, 8, 6, mix(body, "#000000", .3))] if ridges else []
    front = [rect(w * .08, h * .3, w * .19, h * .38, "#08080A", r=3), rect(w * .31, h * .3, w * .19, h * .38, "#08080A", r=3),
             circ(w * .92, h * .5, 2.8, led)]
    if tray:
        front.append(rect(w * .56, h * .22, w * .3, h * .24, dark, r=1))
    boxes = [Box(0, 0, w, d, h, body, r=r, top=top, front=front)]
    if not tray:
        radius = min(w, d) * .36
        boxes.append(Box(w / 2 - radius, d * .44 - radius, 2 * radius, 2 * radius, 5, lid, z=h, r=radius,
                         top=[circ(radius, radius, radius * .3, mix(lid, "#000000", .22))]))
    boxes += [Box(w * .07, d * .85, 28, 14, 4, accent, z=h, r=5), Box(w * .79, d * .85, 28, 14, 4, accent, z=h, r=5)]
    boxes.append(pad(-w * .5, d + 26, 112, 50, pad_color, pad_buttons, rot=-12, face=pad_face, cross=cross))
    return boxes


def cart_console(page, body, panel, accent, cart_color="#17171B", labels=("#FF5E8A", "#3B8CFF"), w=210, d=140, h=30, r=5,
                 wood=False, switches=0, pad_args=None, stick=False):
    """A console that takes cartridges on top: a dark panel, a slot, a few switches."""
    top = [rect(10, 10, w - 20, d * .52, panel, r=3), rect(w * .24, d * .2, w * .52, d * .14, "#050506", r=2)]
    if switches:
        top += [rect(18 + i * (w - 50) / max(1, switches - 1) - 5, d * .74, 12, 18, accent, r=2) for i in range(switches)]
    else:
        top += [rect(18, d * .74, 34, 13, accent, r=2), rect(60, d * .74, 34, 13, mix(accent, "#FFFFFF", .4), r=2)]
    front = [rect(0, h * .42, w, h * .58, "#7A4E24", stroke="none"), lines(0, h * .56, w, 3, h * .14, "#5E3A18", .6)] if wood \
        else [rect(18, h * .3, 40, h * .4, "#111114", r=2), rect(66, h * .3, 40, h * .4, "#111114", r=2)]
    boxes = [Box(0, 0, w, d, h, body, r=r, top=top, front=front)]
    if cart_color:
        boxes.append(cart(page, w * .26, d * .21, w * .48, d * .1, 30, cart_color, h, *labels))
    if stick:
        boxes += joystick(-112, d + 6)
    elif pad_args:
        boxes.append(pad(-100, d + 40, *pad_args, rot=-12))
    return boxes


def docked_console(page, body, panel, pads, w=230, d=150, h=30):
    """A console of the first years: its two keypad controllers rest in wells on top."""
    boxes = [Box(0, 0, w, d, h, body, r=4,
                 top=[rect(10, 10, w - 20, d * .34, panel, r=3), rect(w * .3, d * .14, w * .4, d * .12, "#050506", r=2),
                      rect(14, d * .5, w * .36, d * .44, "#0B0B0E", r=3), rect(w * .64 - 14, d * .5, w * .36, d * .44, "#0B0B0E", r=3)],
                 front=[rect(18, h * .3, 44, h * .4, "#111114", r=2)])]
    for x in (20, w * .64 - 8):
        boxes.append(Box(x, d * .53, w * .36 - 12, d * .38, 8, pads, z=h - 4, r=4,
                         top=[circ((w * .36 - 12) / 2, 14, 9, mix(pads, "#000000", .35)),
                              grid(8, 28, 3, 3, (w * .36 - 34) / 3, 5, 2, mix(pads, "#FFFFFF", .3))]))
    return boxes


def tower(page, body, accent, w=70, d=170, h=200, pad_color=None):
    """A console that stands upright."""
    boxes = [Box(-8, -4, w + 16, d + 8, 8, mix(body, "#000000", .2), r=4),
             Box(0, 0, w, d, h, body, z=8, r=5,
                 front=[rect(w * .34, h * .1, w * .16, h * .6, "#2A2A30", r=3), rect(w * .36, h * .3, w * .12, h * .3, accent, stroke="none"),
                        circ(w * .42, h * .84, 5, mix(body, "#000000", .12)), rect(w * .6, h * .14, w * .26, 8, mix(body, "#000000", .12), r=2)],
                 screens=[("front", w * .34, h * .3, w * .16, h * .3, accent)])]
    if pad_color:
        boxes.append(pad(-150, d + 10, 112, 50, pad_color, ("#D9303A", "#3FA65A", "#2E7BD9", "#F2C230"), rot=-12))
    return boxes


def handheld(page, body, lit, w=184, d=102, r=20, h=16, left="dpad", buttons=2, btn="#2A2A32", wide=.36, cart_color="#25252C"):
    """A handheld held sideways: a control at the left, the screen, buttons at the right."""
    sw, sh = w * wide, d * .52
    sx, sy = (w - sw) / 2, d * .2
    top = [rect(sx - 9, sy - 8, sw + 18, sh + 16, "#18181F", r=5), rect(sx, sy, sw, sh, screen(page, *lit), r=1.5)]
    if left == "dpad":
        top.append(dpad(w * .14, d * .5, d * .3, d * .1, "#1E1E25"))
    elif left == "two":
        top += [dpad(w * .1, d * .34, d * .2, d * .07, "#1E1E25"), dpad(w * .17, d * .68, d * .2, d * .07, "#1E1E25")]
    else:
        top.append(circ(w * .14, d * .5, d * .17, mix(body, "#000000", .3)))
    spots = ((.82, .6), (.91, .46), (.79, .34), (.88, .2))
    top += [circ(w * x, d * y, d * .085, btn) for x, y in spots[:buttons]]
    boxes = [Box(0, 0, w, d, h, body, r=r, top=top, screens=[("top", sx, sy, sw, sh, lit[0])])]
    if left == "stick":
        boxes += [Box(w * .14 - 10, d * .5 - 10, 20, 20, 6, "#25252C", z=h, r=10), Box(w * .14 - 14, d * .5 - 14, 28, 28, 5, "#34343E", z=h + 6, r=14)]
    if cart_color:
        boxes.append(game_cart(page, w + 48, 22, cart_color, "#FFC25E", "#F03C72", 18))
    return boxes


def linked(page, body, buttons, lit):
    """Two handhelds joined by a cable, for two players."""
    first = gameboy(page, body, buttons, "#8E8E98", lit)[:1]
    second = gameboy(page, mix(body, "#FFFFFF", .25), buttons, "#8E8E98", lit)[:1]
    second[0].x, second[0].y, second[0].rot = 150, 30, math.radians(14)
    return first + [Box(96, 60, 60, 6, 4, "#1A1A1E", r=3, rot=10)] + second


def game_watch(page, body, plate):
    """A pocket game with an LCD: a wide screen between two round buttons."""
    return [Box(0, 0, 190, 104, 10, body, r=10,
                top=[rect(10, 10, 170, 84, plate, r=6), rect(52, 20, 86, 58, "#C9D2B8", r=2),
                     path("M64,66h62M72,66v-10h8v10M96,66v-18h8v18M112,56a6,6 0 1 0 0.1,0Z", fill="none", stroke="#3A4032", sw=2),
                     circ(28, 62, 11, "#D9303A"), circ(162, 62, 11, "#D9303A"), rect(18, 20, 20, 7, mix(plate, "#000000", .3), r=3),
                     rect(152, 20, 20, 7, mix(plate, "#000000", .3), r=3)])]


def keyboard(page, body, well, keys, fkeys=None, w=236, d=136, h=26, r=7, stripe=False, deck=None, led="#FF4650", stick=True):
    """A home computer in its keyboard. deck: a "tape" recorder beside the keys, a "floppy" slot
    in its right side, or a "cart" slot behind them."""
    cols = 12 if deck == "tape" else 15
    kw, kh = (w - 60) / 15 - 2, (d - 70) / 4 - 2
    edge = mix(keys, "#000000", .5)
    top = [rect(13, 40, w - 54, d - 58, well, r=2), grid(18, 45, cols, 4, kw, kh, 2, keys, stroke=edge),
           rect(w * .25, d - 27, w * .36, 10, keys, r=1.5, stroke=edge, sw=.3), circ(w - 22, 24, 2.6, led),
           lines(14, 12, 90, 4, 6, mix(body, "#000000", .18))]
    if fkeys:
        top.append(grid(w - 34, 45, 1, 4, 22, kh, 2, fkeys))
    if stripe:
        top.append("".join(rect(w - 86 + i * 5, 14, 4, 12, c, stroke="none") for i, c in enumerate(RAINBOW)))
    if deck == "tape":
        top += [rect(w - 92, 44, 50, d - 66, mix(body, "#000000", .3), r=2), rect(w - 86, 52, 38, 24, "#111114", r=2),
                grid(w - 86, d - 44, 5, 1, 6, 10, 2, keys, stroke=edge)]
    if deck == "cart":
        top.append(rect(w - 96, 10, 78, 16, "#08080A", r=2))
    right = [rect(22, 9, 64, 5, "#111114", r=1), rect(92, 8, 10, 7, mix(body, "#000000", .3), r=1)] if deck == "floppy" else []
    boxes = [Box(0, 0, w, d, h, body, r=r, top=top, front=[rect(0, 0, w, 6, mix(body, "#000000", .1), stroke="none")], right=right)]
    if deck == "cart":
        boxes.append(cart(page, w - 88, 12, 62, 11, 28, "#EDEDF2", h, "#F03C72", "#3B8CFF"))
    return boxes + (joystick(-120, d - 16) if stick else [])


def allinone(page, case, glass, keys=None, w=150, d=150, h=170):
    """A computer with its monitor in the same case, and its keyboard in front."""
    return [
        Box(0, 0, w, d, h, case, r=6,
            front=[rect(w * .1, h * .08, w * .8, h * .52, "#22222A", r=6), rect(w * .16, h * .13, w * .68, h * .42, screen(page, *glass), r=4),
                   rect(w * .58, h * .74, w * .28, 5, "#2E2E36", r=1), lines(w * .14, h * .72, w * .3, 4, 5, mix(case, "#000000", .25))],
            screens=[("front", w * .16, h * .13, w * .68, h * .42, glass[0])]),
        Box(-8, d + 16, w + 16, 56, 8, case, r=3, top=[grid(6, 6, 13, 4, (w + 4) / 13 - 2, 9.6, 2, keys or mix(case, "#FFFFFF", .25))]),
        Box(w + 26, d + 30, 24, 34, 8, case, r=10),
    ]


def text_screen(*colors):
    """Lines of text on a monitor, for a system that has no picture of its own."""
    return ["".join(rect(26, 24 + i * 9, w, 4, c, stroke="none", op=.9) for i, (w, c) in enumerate(colors))]


def pinball(page, body, glass, sign):
    """A pinball table: the slanted playfield on four legs, the lit backbox behind."""
    legs = [Box(x, y, 8, 8, 64, "#C9C9D2", r=2) for x, y in ((4, 6), (88, 6), (4, 186), (88, 186))]
    return legs + [
        Box(0, 0, 100, 60, 150, body, z=64, r=3,
            front=[rect(8, 10, 84, 78, "#08080E", r=3), rect(13, 15, 74, 68, label(page, *sign), r=2),
                   circ(50, 49, 17, "#FFFFFF", stroke="none", op=.85), rect(20, 100, 60, 22, mix(body, "#000000", .3), r=2)],
            screens=[("front", 13, 15, 74, 68, sign[0])]),
        Box(0, 50, 100, 150, 46, body, z=64, r=3,
            top=[rect(8, 6, 84, 136, screen(page, *glass), r=3), circ(34, 44, 9, "#FFE27A"), circ(64, 36, 9, "#F03C72"), circ(52, 72, 9, "#7BE0FF"),
                 path("M30,128l16,-10M70,128l-16,-10", stroke="#FFFFFF", sw=4), rect(84, 90, 5, 46, "#C9C9D2", r=2)],
            front=[rect(36, 14, 28, 16, mix(body, "#000000", .35), r=2), circ(16, 22, 4, "#D9303A"), circ(84, 22, 4, "#FFE27A")],
            screens=[("top", 8, 6, 84, 136, glass[0])]),
    ]


# --- machines of their own ----------------------------------------------------

def psx(page):
    return disc_console(page, "#BDBEC6", "#C9CAD2", "#A9AAB3", "#BDBEC6", ("#3FA65A", "#D9303A", "#2E7BD9", "#F06AA8"))


def ps2(page):
    return disc_console(page, "#17171B", None, "#2B2B33", "#17171B", ("#3FA65A", "#D9303A", "#2E7BD9", "#F06AA8"),
                        w=220, d=170, h=38, r=3, tray=True, ridges=True, led="#3B8CFF", cross="#3A3A44")


def ps3(page):
    return disc_console(page, "#101014", None, "#C9C9D2", "#101014", ("#3FA65A", "#D9303A", "#2E7BD9", "#F06AA8"),
                        w=226, d=176, h=44, r=22, tray=True, led="#D9303A", cross="#3A3A44")


def ps4(page):
    boxes = disc_console(page, "#15151A", None, "#2B2B33", "#15151A", ("#3FA65A", "#D9303A", "#2E7BD9", "#F06AA8"),
                         w=220, d=180, h=30, r=2, tray=True, led="#FFFFFF", cross="#3A3A44")
    boxes[0].top = [rect(0, 84, 220, 5, "#5FC8FF", stroke="none")]
    boxes[0].screens = [("top", 0, 82, 220, 9, "#5FC8FF")]
    return boxes


def saturn(page):
    return disc_console(page, "#2A2A30", "#34343C", "#3B5BD9", "#2A2A30", ("#3FA65A", "#F2C230", "#2E7BD9"), w=210, d=176, h=38, r=10,
                        cross="#55565F")


def dreamcast(page):
    boxes = disc_console(page, "#EDEDF0", "#E2E2E8", "#D5D5DC", "#EDEDF0", ("#D9303A", "#F2C230", "#3FA65A", "#2E7BD9"), w=190, d=190, h=38,
                         r=14, led="#F28C28", cross="#8E8E98")
    boxes[0].front = [rect(14 + i * 42, 12, 30, 14, "#C4C4CC", r=3) for i in range(4)] + [circ(176, 19, 2.8, "#F28C28")]
    return boxes


def threedo(page):
    return disc_console(page, "#1B1B20", None, "#3A3A44", "#1B1B20", ("#D9303A", "#3FA65A", "#2E7BD9"), w=230, d=170, h=40, r=4, tray=True,
                        cross="#55565F")


def gamecube(page):
    purple = "#5B4FB0"
    return [
        Box(30, -10, 70, 12, 26, "#3A3A44", z=30, r=5),
        Box(0, 0, 130, 130, 100, purple, r=9,
            top=[circ(65, 60, 46, mix(purple, "#000000", .18)), circ(65, 60, 12, mix(purple, "#000000", .35)),
                 rect(16, 110, 26, 10, "#B9B7C6", r=4), rect(88, 110, 26, 10, "#B9B7C6", r=4)],
            front=[rect(8, 52, 114, 30, "#8E8AA8", r=4)] + [circ(26 + i * 26, 67, 9, "#3A3A44") for i in range(4)]),
        pad(-140, 150, 112, 54, purple, ("#3FA65A", "#D9303A", "#B9B7C6", "#F2C230"), rot=-12),
    ]


def wii(page):
    white = "#F2F2F5"
    return tower(page, white, "#5FC8FF", w=56, d=170, h=190) + [
        Box(-130, 150, 36, 124, 12, white, r=8, rot=-20,
            top=[dpad(18, 24, 16, 5.5, "#D8D8DE"), circ(18, 52, 7, "#D8D8DE"), circ(18, 98, 4, "#D8D8DE"), circ(18, 110, 4, "#D8D8DE")])]


def wiiu(page):
    return [Box(0, 0, 250, 118, 14, "#16161B", r=24,
                top=[rect(60, 14, 130, 84, "#08080A", r=4), rect(66, 20, 118, 72, screen(page, "#7BE0FF", "#3B5BD9"), r=2),
                     circ(30, 34, 11, "#2A2A32"), circ(220, 34, 11, "#2A2A32"), dpad(30, 76, 24, 8, "#2A2A32"),
                     circ(212, 70, 6, "#2A2A32"), circ(228, 70, 6, "#2A2A32"), circ(220, 60, 6, "#2A2A32"), circ(220, 80, 6, "#2A2A32")],
                screens=[("top", 66, 20, 118, 72, "#7BE0FF")])]


def switch(page):
    def joycon(x, color, stick_y, left):
        dots = [circ(18, 62, 3.6, "#17171B"), circ(18, 78, 3.6, "#17171B"), circ(10, 70, 3.6, "#17171B"), circ(26, 70, 3.6, "#17171B")]
        return Box(x, 0, 36, 100, 10, color, r=14, top=[circ(18, stick_y, 8, "#17171B")] + [d if left else d for d in dots])
    return [joycon(-38, "#00B7EB", 28, True),
            Box(0, 0, 170, 100, 9, "#1B1B20", r=4, top=[rect(8, 8, 154, 84, screen(page, "#FF8FB1", "#6A55B8"), r=2)],
                screens=[("top", 8, 8, 154, 84, "#FF8FB1")]),
            joycon(172, "#FF4554", 60, False)]


def xbox(page):
    return [Box(0, 0, 230, 180, 62, "#16161A", r=6,
                top=[path("M20,16L210,164M210,16L20,164", stroke="#0A0A0C", sw=14), circ(115, 90, 34, "#0A0A0C"), circ(115, 90, 24, "#6FD93A"),
                     lines(20, 16, 40, 5, 7, "#0A0A0C", 2)],
                front=[rect(60, 10, 110, 14, "#0A0A0C", r=2), circ(30, 46, 6, "#2A2A30"), circ(48, 46, 3, "#6FD93A")]
                + [rect(98 + i * 30, 38, 22, 14, "#0A0A0C", r=3) for i in range(4)],
                screens=[("top", 91, 66, 48, 48, "#6FD93A")]),
            pad(-150, 196, 124, 58, "#16161A", ("#3FA65A", "#D9303A", "#2E7BD9", "#F2C230"), rot=-12, cross="#3A3A44")]


def xbox360(page):
    return [Box(0, 0, 230, 170, 52, "#EDEDF0", r=14,
                top=[lines(18, 20, 194, 6, 9, "#D5D5DC", 1.2)],
                front=[rect(22, 12, 120, 12, "#C9C9D2", r=3), circ(196, 26, 13, "#C9C9D2"), circ(196, 26, 8, "#6FD93A"), rect(22, 32, 44, 10, "#D5D5DC", r=3)],
                screens=[("front", 186, 16, 20, 20, "#6FD93A")]),
            pad(-150, 186, 124, 58, "#EDEDF0", ("#3FA65A", "#D9303A", "#2E7BD9", "#F2C230"), rot=-12, cross="#8E8E98")]


def virtualboy(page):
    red, black = "#B8242B", "#17171B"
    return [Box(46, 60, 8, 8, 72, black, r=3, rot=20), Box(118, 60, 8, 8, 72, black, r=3, rot=-20), Box(30, 40, 112, 60, 8, black, r=6),
            Box(0, 0, 172, 116, 74, red, z=70, r=16,
                front=[rect(14, 12, 144, 50, black, r=12), circ(56, 37, 14, "#2A0A0C"), circ(116, 37, 14, "#2A0A0C"),
                       circ(56, 37, 8, "#FF3B3B", stroke="none"), circ(116, 37, 8, "#FF3B3B", stroke="none")],
                screens=[("front", 44, 25, 84, 24, "#FF3B3B")]),
            pad(-130, 150, 112, 54, black, ("#B8242B", "#B8242B"), rot=-12, cross="#B8242B")]


def atari2600(page):
    return cart_console(page, "#1C1A1A", "#141212", "#C9C9D2", "#3A2A1A", ("#F28C28", "#F2C230"), w=230, d=150, h=32, wood=True,
                        switches=6, stick=True)


def neogeo(page):
    black = "#17171B"
    return [Box(0, 0, 250, 150, 28, black, r=4,
                top=[rect(40, 14, 170, 56, "#0A0A0C", r=3), rect(60, 30, 130, 22, "#050506", r=2), rect(20, 112, 36, 12, "#C9C9D2", r=2),
                     rect(64, 112, 36, 12, "#C9C9D2", r=2), line(120, 118, 230, 118, "#C9A227", 1.4)],
                front=[rect(20, 8, 44, 13, "#08080A", r=2), rect(72, 8, 44, 13, "#08080A", r=2)]),
            cart(page, 64, 32, 122, 18, 40, "#101014", 28, "#F2C230", "#D9303A"),
            Box(-190, 150, 170, 86, 18, black, r=6, rot=-12,
                top=[circ(40, 44, 16, "#2A2A32")] + [circ(84 + i * 22, 50 - i * 6, 9, c) for i, c in enumerate(("#D9303A", "#F2C230", "#3FA65A", "#2E7BD9"))]),
            Box(-162, 184, 12, 12, 26, "#C9C9D2", z=18, r=6),
            Box(-170, 176, 28, 28, 18, "#D9303A", z=44, r=14)]


def vectrex(page):
    return [Box(0, 0, 120, 130, 180, "#17171B", r=6,
                front=[rect(12, 12, 96, 118, "#050506", r=6),
                       path("M30,96L60,36L90,96ZM44,70h32M24,112h72", stroke="#B8F27A", sw=1.6, extra='filter="url(#blur3)"'),
                       path("M30,96L60,36L90,96ZM44,70h32M24,112h72", stroke="#EFFFD0", sw=.8), rect(16, 144, 88, 26, "#2A2A32", r=3),
                       circ(34, 157, 6, "#17171B")] + [circ(60 + i * 12, 157, 4, "#17171B") for i in range(4)],
                screens=[("front", 20, 30, 80, 90, "#B8F27A")])]


def famicom(page):
    white, red = "#EFEDE6", "#8E1F2B"
    side = lambda x: Box(x, 34, 22, 96, 10, red, z=22, r=3, top=[dpad(11, 22, 14, 5, "#17171B"), circ(11, 62, 4, "#17171B"), circ(11, 76, 4, "#17171B")])
    return [Box(0, 0, 200, 150, 30, white, r=5,
                top=[rect(34, 16, 132, 110, red, r=4), rect(50, 30, 100, 20, "#17171B", r=2), rect(46, 100, 30, 12, "#D8D6D0", r=2),
                     rect(124, 100, 30, 12, "#D8D6D0", r=2), rect(84, 98, 32, 16, "#C92A36", r=2)],
                front=[rect(60, 10, 80, 12, "#17171B", r=2)]),
            cart(page, 58, 32, 84, 16, 34, "#F2C230", 30, "#D9303A", "#FFFFFF"), side(4), side(174)]


def fds(page):
    boxes = famicom(page)
    return [Box(-6, -6, 212, 162, 34, "#B8242B", r=5, front=[rect(40, 10, 132, 10, "#17171B", r=2), rect(86, 22, 40, 6, "#F2C230", stroke="none")])] \
        + raised(boxes, 34, keep=0)


def sega32x(page):
    boxes = megadrive(page)
    boxes[2] = Box(62, 40, 90, 56, 30, "#1C1C21", z=34, r=18, top=[rect(14, 20, 62, 16, "#08080A", r=3), circ(45, 46, 3, "#D12B33")])
    return boxes


def nintendo3ds(page):
    return nds(page, "#17171B")


def psp(page):
    return handheld(page, "#101014", ("#7BE0FF", "#3B5BD9"), w=240, d=102, r=42, h=14, buttons=4, btn="#2A2A32", wide=.5, cart_color=None)


def psvita(page):
    return handheld(page, "#101014", ("#FF8FB1", "#3B5BD9"), w=250, d=110, r=46, h=12, left="stick", buttons=4, btn="#2A2A32", wide=.54,
                    cart_color=None)


# --- signs for the collections --------------------------------------------------

def person(x, y):
    return f"M{x - 14},{y + 34}a14,16 0 0 1 28,0M{x},{y - 6}a9,9 0 1 0 0.1,0Z"


SIGNS = {
    "players2": lambda: [neon(person(74, 70) + person(126, 70), "#5FE0FF", 3), neon("M40,150h120", "#FFD36E", 2.2)],
    "players4": lambda: [neon(person(46, 66) + person(82, 66) + person(118, 66) + person(154, 66), "#FF4F9A", 2.6), neon("M30,150h140", "#FFD36E", 2.2)],
    "gun": lambda: [neon("M100,34a50,50 0 1 0 0.1,0ZM100,18v36M100,114v36M34,84h36M130,84h36", "#FF4F9A", 3), neon("M100,84h0.1", "#FFD36E", 5)],
    "new": lambda: [neon("M100,24l14,46l46,14l-46,14l-14,46l-14,-46l-46,-14l46,-14Z", "#FFD36E", 3), neon("M40,152h120", "#5FE0FF", 2.2)],
    "trophy": lambda: [neon("M66,28h68v36a34,34 0 0 1 -68,0ZM66,40h-22a22,22 0 0 0 22,26M134,40h22a22,22 0 0 1 -22,26M100,98v26M74,136h52", "#FFD36E", 3)],
    "vertical": lambda: [neon("M62,20h76v130h-76Z", "#5FE0FF", 3), neon("M100,120v-70M82,68l18,-20l18,20", "#FF4F9A", 3)],
    "wheel": lambda: [neon("M100,22a62,62 0 1 0 0.1,0ZM100,70a14,14 0 1 0 0.1,0Z", "#5FE0FF", 3), neon("M42,76l44,6M158,76l-44,6M100,98v46", "#FF4F9A", 3)],
    "folder": lambda: [neon("M30,44h50l14,16h76v84h-140Z", "#FFD36E", 3), neon("M56,96h88M56,118h60", "#5FE0FF", 2.4)],
    "book": lambda: [neon("M100,40c-20,-12 -44,-12 -64,-4v96c20,-8 44,-8 64,4c20,-12 44,-12 64,-4v-96c-20,-8 -44,-8 -64,4Zv96", "#5FE0FF", 3)],
    "moon": lambda: [neon("M124,26a60,60 0 1 0 30,96a50,50 0 0 1 -30,-96Z", "#FFD36E", 3), neon("M52,44h0.1M40,96h0.1M70,140h0.1", "#5FE0FF", 4)],
    "record": lambda: [neon("M100,30a54,54 0 1 0 0.1,0Z", "#FF4F9A", 3), neon("M100,62a22,22 0 1 0 0.1,0Z", "#FF4F9A", 8)],
    "camera": lambda: [neon("M30,54h36l10,-16h48l10,16h36v86h-140Z", "#5FE0FF", 3), neon("M100,70a26,26 0 1 0 0.1,0Z", "#FF4F9A", 3)],
    "picture": lambda: [neon("M30,30h140v110h-140Z", "#5FE0FF", 3), neon("M44,124l34,-40l22,24l18,-16l38,32", "#FF4F9A", 3), neon("M136,58h0.1", "#FFD36E", 8)],
    "globe": lambda: [neon("M100,24a60,60 0 1 0 0.1,0ZM40,84h120M100,24c-34,36 -34,84 0,120M100,24c34,36 34,84 0,120", "#5FE0FF", 2.6)],
    "pad": lambda: [neon("M52,54h96a30,30 0 0 1 0,60h-96a30,30 0 0 1 0,-60Z", "#FF4F9A", 3), neon("M62,84h24M74,72v24", "#5FE0FF", 3),
                    neon("M126,76h0.1M142,92h0.1", "#FFD36E", 6)],
    "store": lambda: [neon("M36,62h128l-12,62h-104ZM36,62l-10,-28h-12", "#FFD36E", 3), neon("M66,142h0.1M134,142h0.1", "#5FE0FF", 7)],
}


def neon_sign(symbol):
    return lambda page: sign(page, SIGNS[symbol]())


def wordmark(page, text="BatoX"):
    """The theme's name over the loading screen's sky, in a brush script, pink and leaning, as
    on a poster of the eighties. The font is Mr Dafoe (SIL Open Font License,
    tools/fonts/MrDafoe-LICENSE.txt); it goes into the picture, not into the theme."""
    with open(os.path.join(ROOT, "tools", "fonts", "MrDafoe-Regular.ttf"), "rb") as f:
        font = base64.b64encode(f.read()).decode()
    page.defs.append(f'<style>@font-face{{font-family:"Wordmark";src:url(data:font/ttf;base64,{font})}}</style>')
    fill = page.gradient([(0, "#FFA3D4"), (.55, "#FF4F9A"), (1, "#E0237A")])
    words = (f'<text x="960" y="372" text-anchor="middle" font-family="Wordmark" font-size="300" {{}}>{text}</text>')
    page.add('<g transform="rotate(-7 960 300)">'
             + words.format('fill="#FF4F9A" opacity=".55" filter="url(#blur20)"')
             + words.format('fill="#1A0626" transform="translate(9 11)" opacity=".85"')
             + words.format(f'fill="{fill}" stroke="#2A0A3A" stroke-width="5" paint-order="stroke" stroke-linejoin="round"')
             + '</g>')


def loading(page):
    """The loading screen's picture: cartridges and a controller, for no system in particular."""
    return allgames(page) + [pad(-150, 210, 124, 54, "#C9C7D0", ("#F03C72", "#FFC25E", "#3B8CFF", "#7BE0C3"), rot=-14)]


# The loading screen's picture goes to _inc/backgrounds/splash.jpg (splash.xml)
SPLASH = "splash"

# Each system's machine and the mood of its sky
SYSTEMS = {
    "snes": (snes, "vice"), "snes-msu1": (snes, "miami"), "nes": (nes, "gold"), "n64": (n64, "miami"),
    "gb": (gb, "gold"), "gbc": (gbc, "vice"), "gba": (gba, "gold"), "nds": (nds, "night"),
    "megadrive": (megadrive, "night"), "mastersystem": (mastersystem, "vice"), "gamegear": (gamegear, "miami"),
    "sg-1000": (sg1000, "gold"), "pcengine": (pcengine, "miami"), "ngp": (ngp, "gold"), "ngpc": (ngpc, "vice"),
    "c64": (c64, "gold"), "msx2": (msx2, "night"),
    "mame": (mame, "night"), "fbneo": (fbneo, "vice"), "naomi": (naomi, "miami"),
    "ports": (ports, "vice"), "pygame": (pygame, "miami"),
    "auto-allgames": (allgames, "vice"), "auto-favorites": (favorites, "night"), "auto-lastplayed": (lastplayed, "night"),
}


def put(names, model, mood=None):
    """Gives these systems (their theme names, separated by spaces) a drawing; without a mood,
    each takes one of the four by its name, so a family doesn't look the same everywhere."""
    for name in names.split():
        SYSTEMS.setdefault(name, (model, mood))


BEIGE, CREAM, GRAY, DARK, BLACK, WHITE = "#C9B99B", "#DDD6C2", "#B9BAC2", "#3A3B44", "#1B1B20", "#EDEDF0"
PADS = ("#D9303A", "#3FA65A", "#2E7BD9", "#F2C230")
GREEN_LIT, BLUE_LIT, AMBER_LIT, GRAY_LIT = ("#B8F27A", "#2E9E6B"), ("#7BE0FF", "#3B5BD9"), ("#FFD36E", "#F03C72"), ("#D4DEC0", "#7F8F74")

# Nintendo
put("snesh snes-msu snesmsu1 snesmini sfc sufami sgb sgb-msu1", snes)
put("satellaview snescd", lambda p: on_base(p, snes(p), "#B9B7C3", 216, 166))
put("nesh", nes)
put("famicom", famicom)
put("fds", fds)
put("64dd n64dd", lambda p: on_base(p, n64(p), "#34353B", 226, 166, tray=False))
put("gbh", gb)
put("gbch", gbc)
put("gbah", gba)
put("gb2players", lambda p: linked(p, "#C6C4BA", "#A6245C", ("#B5C96A", "#5E7A32")))
put("gbc2players", lambda p: linked(p, "#6A4FB0", "#2A2A32", GREEN_LIT))
put("3ds 3dsen", nintendo3ds)
put("gc", gamecube)
put("wii", wii)
put("wiiu", wiiu)
put("switch", switch)
put("virtualboy", virtualboy)
put("gameandwatch gw", lambda p: game_watch(p, "#C9A227", "#8E1F2B"))
put("lcdgames", lambda p: game_watch(p, "#C9C9D2", "#2743B8"))
put("pokemini", lambda p: gameboy(p, "#2E7BD9", "#F2C230", "#8E8E98", GRAY_LIT))

# Sega
put("genesis megadrive-japan megadrive-msu msu-md genh", megadrive)
put("megacd segacd", lambda p: on_base(p, megadrive(p), "#1C1C21", 240, 170))
put("sega32x", sega32x)
put("saturn", saturn)
put("dreamcast", dreamcast)
put("ggh", gamegear)
put("sc-3000", lambda p: keyboard(p, BLACK, "#0B0B0E", "#C9C9D2", fkeys="#C4161C", deck="cart"))
put("pico beena", lambda p: cart_console(p, "#F2C230", "#2E7BD9", "#D9303A", "#D9303A", ("#FFFFFF", "#7BE0C3"), pad_args=None))
put("segaai", lambda p: keyboard(p, WHITE, "#D5D5DC", "#8E8E98", fkeys="#2E7BD9"))

# Sony, Microsoft
put("psx psxmini", psx)
put("ps2", ps2)
put("ps3", ps3)
put("ps4", ps4)
put("psp pspminis", psp)
put("psvita", psvita)
put("xbox chihiro", xbox)
put("xbox360", xbox360)

# NEC, SNK, Atari, others with discs
put("tg16", pcengine)
put("pce-cd pcenginecd tg16cd", lambda p: on_base(p, pcengine(p), "#EFEDE6", 190, 180))
put("supergrafx", lambda p: cart_console(p, "#3A3B44", "#2A2A30", "#8E8E98", "#EFEDE6", ("#FF7F4F", "#6A55B8"), w=220, d=160, h=44,
                                         pad_args=(104, 48, "#3A3B44", ("#8E8E98", "#8E8E98"))))
put("pcfx", lambda p: tower(p, WHITE, "#7CFF8A", pad_color=WHITE))
put("neogeo neogeox neogeomini", neogeo)
put("neogeocd", lambda p: disc_console(p, BLACK, "#25252B", "#C9A227", BLACK, PADS, w=220, d=180, cross="#3A3A44"))
put("3do", threedo)
put("cdi", lambda p: disc_console(p, "#2A2A30", None, "#55565F", "#2A2A30", PADS[:2], w=240, d=170, h=38, r=4, tray=True))
put("amigacd32", lambda p: disc_console(p, "#3A3B44", "#2A2A30", "#8E8E98", "#3A3B44", PADS, w=200, d=180, r=6))
put("amigacdtv vis fmtownsmarty", lambda p: disc_console(p, "#17171B", None, "#3A3A44", "#17171B", PADS[:2], w=250, d=180, h=40, r=3, tray=True))
put("atari2600", atari2600)
put("atari5200", lambda p: cart_console(p, BLACK, "#101014", "#C9C9D2", BLACK, ("#F28C28", "#D9303A"), w=250, d=170, h=34, stick=True))
put("atari7800", lambda p: cart_console(p, BLACK, "#C9C9D2", "#D9303A", BLACK, ("#F2C230", "#2E7BD9"), w=220, d=140, h=28, stick=True))
put("atarijaguar", lambda p: cart_console(p, BLACK, "#101014", "#D9303A", BLACK, ("#D9303A", "#F2C230"), w=220, d=160, h=34,
                                           pad_args=(118, 62, BLACK, ("#D9303A", "#D9303A", "#D9303A"))))
put("atarijaguarcd", lambda p: on_base(p, cart_console(p, BLACK, "#101014", "#D9303A", None, w=200, d=150, h=30, pad_args=(118, 62, BLACK, ("#D9303A",) * 3)),
                                       BLACK, 220, 170))
put("atarilynx", lambda p: handheld(p, "#3A3B44", AMBER_LIT, w=240, d=100, r=18, buttons=4, wide=.3, cart_color=BLACK))
put("colecovision", lambda p: docked_console(p, BLACK, "#C9C9D2", "#17171B"))
put("intellivision", lambda p: docked_console(p, "#6B4426", "#C9A227", "#2A2118"))
put("vectrex", vectrex)

# Consoles with cartridges, most of them from the first years
put("channelf", lambda p: cart_console(p, "#3A2A1A", "#C9A227", "#F2C230", "#F2C230", stick=True, wood=True))
put("odyssey2 videopac videopacplus", lambda p: keyboard(p, "#C9C9D2", BLACK, "#3A3B44", fkeys="#D9303A", w=220, d=130, deck="cart"))
put("astrocade", lambda p: cart_console(p, "#3A2A1A", BLACK, "#C9A227", BLACK, wood=True, switches=4, stick=True))
put("arcadia apfm1000 vc4000 sv8000 pv1000 pv2000", lambda p: docked_console(p, "#D8D6D1", BLACK, "#3A3B44"))
put("cassettevision scv multivision ctvboy", lambda p: cart_console(p, "#D8D6D1", "#C4161C", "#2E7BD9", BLACK, ("#F2C230", "#D9303A"), switches=4))
put("creativision", lambda p: docked_console(p, "#EFEDE6", "#6B4426", "#D9303A"))
put("advision", lambda p: allinone(p, BLACK, ("#FF3B3B", "#2A0A0C"), keys="#D9303A", w=130, d=120, h=130))
put("gx4000", lambda p: cart_console(p, "#D8D6D1", "#B9BAC2", "#3A3B44", "#D8D6D1", ("#3FA65A", "#2E7BD9"), r=30,
                                      pad_args=(104, 48, "#D8D6D1", ("#3A3B44", "#3A3B44"))))
put("supracan loopy", lambda p: cart_console(p, "#D5D5DC", "#8E8E98", "#D9303A", "#3A3B44", pad_args=(104, 48, "#D5D5DC", PADS)))
put("vsmile socrates", lambda p: cart_console(p, "#F28C28", "#6A55B8", "#3FA65A", "#F2C230", ("#D9303A", "#FFFFFF"), r=24,
                                              pad_args=(110, 56, "#6A55B8", ("#F2C230", "#3FA65A"))))
put("tvgames plugnplay", lambda p: [pad(0, 0, 220, 96, "#D9303A", ("#F2C230", "#3FA65A", "#2E7BD9", "#FFFFFF"), face="#17171B", r=30),
                                    game_cart(p, 260, 30, "#17171B", "#FFC25E", "#F03C72", 16)])
put("uzebox actionmax", lambda p: cart_console(p, BLACK, "#2A2A30", "#3FA65A", None, pad_args=(104, 48, "#C9C7D0", ("#6A4FB0",) * 2)))

# Handhelds
put("wonderswan", lambda p: handheld(p, "#E8E6E0", GRAY_LIT, left="two", cart_color="#E8E6E0"))
put("wonderswancolor", lambda p: handheld(p, "#2E7BD9", BLUE_LIT, left="two", cart_color="#2E7BD9"))
put("gamate megaduck supervision gmaster", lambda p: gameboy(p, "#3A3B44", "#D9303A", "#8E8E98", GREEN_LIT))
put("gamepock arduboy", lambda p: gameboy(p, "#EDEDF0", "#3A3B44", "#8E8E98", GRAY_LIT))
put("gamecom", lambda p: handheld(p, "#2A2A30", GRAY_LIT, w=220, d=110, buttons=4, wide=.4))
put("gp32 ngage", lambda p: handheld(p, "#EDEDF0", BLUE_LIT, left="stick", buttons=2, btn="#8E8E98", wide=.4, cart_color=None))

# Arcade
put("arcade hbmame mess projectarcade zinc", mame)
put("fba fba_libretro fbn", fbneo)
put("naomi2 atomiswave systemsp hikaru triforce lindbergh namco2x6 teknoparrot", naomi)
put("cps1 cps2 cps3 capcom", lambda p: cabinet(p, "#16224F", "#F2C230", ("#3B2A8C", "#0B0B2A"), ("#F2C230", "#D9303A"), ((20, 14, "#F2C230"), (40, 8, "#D9303A"))))
put("model2 model3 segastv", lambda p: cabinet(p, "#EDEDF0", "#2743B8", ("#3B5BD9", "#0B0B2A"), ("#2743B8", "#7BE0FF"), ((20, 14, "#2743B8"), (40, 8, "#7BE0FF"))))
put("namco22 gaelco igs irem cave", lambda p: cabinet(p, "#2A1A3A", "#F03C72", ("#5A1680", "#12071F"), ("#F03C72", "#FFC25E"), ((18, 12, "#F03C72"), (36, 8, "#7BE0FF"))))
put("neogeo64 mugen ikemen", lambda p: cabinet(p, "#8E1F2B", "#F2C230", ("#3B2A8C", "#0B0B2A"), ("#D9303A", "#F2C230"), ((20, 14, "#F2C230"),)))
put("daphne singe dice", lambda p: cabinet(p, "#1B2A1B", "#3FA65A", ("#2E9E6B", "#06120A"), ("#3FA65A", "#B8F27A"), ((20, 14, "#3FA65A"), (40, 8, "#B8F27A"))))
put("lightgun", lambda p: cabinet(p, "#3A1014", "#F28C28", ("#5A1680", "#12071F"), ("#F28C28", "#FFC25E"), ((20, 14, "#F28C28"),)))
put("fpinball vpinball pinballfx pinballfx2 pinballfx3 pinballm zaccariapinball", lambda p: pinball(p, "#16224F", ("#3B2A8C", "#0B0B2A"), ("#F03C72", "#FFC25E")))

# Home computers in their keyboard
put("c128", lambda p: keyboard(p, CREAM, "#B9B29E", "#55504A", fkeys="#8F8473", w=260, d=140, h=22))
put("c20 vic20", lambda p: keyboard(p, "#E6DEC8", "#4A3C34", "#3A2E28", fkeys="#C98A3A", stripe=True))
put("c16 cplus4", lambda p: keyboard(p, DARK, "#25252B", "#D8D6D1", fkeys="#8E8E98"))
put("msx msx1 msx2+ msxturbor", msx2)
put("zxspectrum", lambda p: keyboard(p, BLACK, "#101014", "#55565F", w=200, d=120, h=16, stripe=True, led="#17171B"))
put("zx81", lambda p: keyboard(p, BLACK, "#101014", "#2A2A30", w=170, d=120, h=14, led="#17171B", stick=False))
put("amstradcpc", lambda p: keyboard(p, "#3A3B44", "#25252B", "#55565F", w=280, d=136, deck="tape"))
put("atari800 atari8bit", lambda p: keyboard(p, "#C9B99B", "#3A2E28", "#6B5A4A", fkeys="#F2C230", deck="cart"))
put("xegs", lambda p: keyboard(p, "#D8D6D1", "#B9BAC2", "#EDEDF0", fkeys="#F0A6B8", deck="cart"))
put("atarist", lambda p: keyboard(p, "#C4C4C0", "#A9A9A6", "#EDEDEA", fkeys="#8E8E98", w=260, d=150, deck="floppy"))
put("amiga amiga500 amiga1200 amiga4000", lambda p: keyboard(p, "#D8D2C0", "#B9B29E", "#EDE8DA", fkeys="#8F8A7A", w=260, d=150, deck="floppy"))
put("apple2 apple2gs", lambda p: keyboard(p, "#D5CDB6", "#3A2E28", "#55504A", w=230, d=160, h=40, led="#3FA65A"))
put("bbcmicro electron atom", lambda p: keyboard(p, "#DDD6C2", "#17171B", "#2A2A30", fkeys="#C4161C"))
put("oric", lambda p: keyboard(p, "#17171B", "#101014", "#D8D6D1", fkeys="#C4161C", w=210, d=124, h=18))
put("coco dragon32 dragon64 mc10", lambda p: keyboard(p, "#C9C9D2", "#17171B", "#2A2A30", fkeys="#D9303A", deck="cart"))
put("ti99", lambda p: keyboard(p, "#C9C9D2", "#17171B", "#2A2A30", deck="cart", w=250))
put("trs80 tandy1k", lambda p: keyboard(p, "#B9BAC2", "#17171B", "#2A2A30", fkeys="#8E8E98"))
put("spectravideo", lambda p: keyboard(p, "#EDEDF0", "#D5D5DC", "#8E8E98", fkeys="#D9303A", deck="cart"))
put("thomson", lambda p: keyboard(p, "#8E8E98", "#3A3B44", "#D8D6D1", fkeys="#2E7BD9"))
put("laser310 cgenie camplynx tutor tvc bk rx78 p2000t vg5k", lambda p: keyboard(p, "#D8D6D1", "#3A3B44", "#EDEDF0", fkeys="#F28C28"))
put("enterprise", lambda p: keyboard(p, "#17171B", "#101014", "#3A3B44", fkeys="#3FA65A", stripe=True))
put("samcoupe", lambda p: keyboard(p, "#EDEDF0", "#D5D5DC", "#8E8E98", fkeys="#2E7BD9", deck="floppy"))
put("fm7 pc60 pc80 mz700 mz800 adam", lambda p: keyboard(p, "#D8D2C0", "#3A3B44", "#EDE8DA", fkeys="#3FA65A", w=260, d=146))
put("commanderx16", lambda p: keyboard(p, "#EDEDF0", "#3A3B44", "#D8D6D1", fkeys="#6A4FB0", stripe=True))

# Computers with a monitor
put("pc", lambda p: computer(p, "#D5D0C2", ("#2743B8", "#0B0F24"), text_screen((40, "#FFFFFF"), (70, "#FFFFFF"), (24, "#FFFFFF"), (56, "#FFD36E"), (30, "#FFFFFF"))))
put("pc88 pc98 x1 fmtowns archimedes pcw", lambda p: computer(p, "#D8D2C0", ("#0B0F24", "#050816"), text_screen((60, "#B8F27A"), (36, "#B8F27A"), (70, "#B8F27A"), (22, "#B8F27A"))))
put("x68000", lambda p: computer(p, "#3A3B44", ("#3B2A8C", "#0B0B2A"), [rect(34, 28, 22, 22, "#F03C72", r=1, sw=.4), rect(70, 46, 22, 22, "#7BE0FF", r=1, sw=.4)]))
put("macintosh", lambda p: allinone(p, "#DDD6C2", ("#F4F4F0", "#B9BAC2")))
put("pet mz80k mz2000 mz2500", lambda p: allinone(p, "#EDEDF0", GREEN_LIT, keys="#3A3B44", w=160, d=160, h=180))
put("pdp1", lambda p: allinone(p, "#8E9AA8", ("#B8F27A", "#06120A"), keys="#D8D6D1", w=170, d=150, h=200))
put("scummvm residualvm", lambda p: computer(p, "#D5D0C2", ("#3FA65A", "#0B2A1A"), [path("M30,70l20,-30l16,18l12,-10l22,22Z", fill="#0B2A1A", stroke="none"), circ(96, 34, 6, "#FFD36E", stroke="none")]))
put("windows windows_installers steam gog epic eagames amazon heroic lutris flatpak linux android j2me",
    lambda p: computer(p, "#3A3B44", ("#3B8CFF", "#1B3F8C"), [rect(26, 24, 56, 40, "#E9ECF2", r=1.5, sw=.4), rect(26, 24, 56, 7, "#17171B", r=1.5, sw=.4), rect(88, 30, 24, 24, "#FFD36E", r=2, sw=.4)]))
put("flash bennugd lutro solarus easyrpg vgmplay", pygame)
put("pico8 tic80 lowresnx vircon32 wasm4 pyxel", lambda p: computer(p, "#F03C72", ("#1D2B53", "#0B0F24"),
    ["".join(rect(x, y, 9, 9, c, r=1, sw=.4) for x, y, c in ((34, 34, "#FFEC27"), (44, 34, "#FFEC27"), (44, 44, "#FF77A8"), (54, 44, "#FF77A8"), (64, 54, "#29ADFF"), (74, 54, "#29ADFF"), (84, 44, "#00E436")))]))

# Games ported to Batocera: a computer of their time, the screen in a color of their own
for i, names in enumerate(("abuse bstone cannonball cavestory cdogs cgenius corsixth devilutionx dxx-rebirth ecwolf eduke32 etlegacy",
                           "fallout1-ce fallout2-ce fury gzdoom halflife hcl hurrican jazz2 odcommander openbor openjazz prboom mrboom",
                           "quake quake2 quake3 raze reminiscence rott rtcw sdlpop sonic-mania sonic3-air sonicretro superbroswar",
                           "thextech traider1 traider2 tyrian xrick zeldac boom3 dinothawr gemrb iortcw opengoal openlara pdark",
                           "powerbomberman starship theforceengine tyrquake vitaquake2 xash3d_fwgs retrobat")):
    glass = (("#F2542C", "#3A1014"), ("#3FB8C9", "#1B3F8C"), ("#F03C72", "#3B2A8C"), ("#B8F27A", "#0B2A1A"), ("#FFD36E", "#5A1E55"))[i]
    put(names, lambda p, glass=glass: computer(p, "#D5D0C2", glass, [path("M30,74l18,-34l14,20l12,-12l26,26Z", fill="#0B0F24", stroke="none", op=.75)]))

# Collections and Batocera's own entries: a neon sign
put("auto-at2players", neon_sign("players2"), "night")
put("auto-at4players", neon_sign("players4"), "night")
put("auto-lightgun", neon_sign("gun"), "night")
put("auto-neverplayed", neon_sign("new"), "night")
put("auto-retroachievements", neon_sign("trophy"), "night")
put("auto-verticalarcade", neon_sign("vertical"), "night")
put("auto-wheel", neon_sign("wheel"), "night")
put("collections custom-collections", neon_sign("folder"), "night")
put("favorites", favorites, "night")
put("library", neon_sign("book"), "night")
put("moonlight", neon_sign("moon"), "night")
put("recordings", neon_sign("record"), "night")
put("screenshots", neon_sign("camera"), "night")
put("imageviewer", neon_sign("picture"), "night")
put("internet", neon_sign("globe"), "night")
put("openbor mugen", neon_sign("pad"), "night")

MOOD_NAMES = sorted(MOODS)


# --- output ------------------------------------------------------------------

def chrome():
    for name in (os.environ.get("CHROME"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium", "chromium", "chromium-browser", "google-chrome"):
        found = name and (name if os.path.exists(name) else shutil.which(name))
        if found:
            return found
    sys.exit("Chrome or Chromium not found: set CHROME to its path")


def render(name, keep_svg, browser, work):
    splash = name == SPLASH
    model, mood_name = (loading, "vice") if splash else SYSTEMS[name]
    mood = MOODS[mood_name or MOOD_NAMES[zlib.crc32(name.encode()) % len(MOOD_NAMES)]]
    rnd = random.Random(zlib.crc32(name.encode()))
    page = Page()
    scene(page, mood, rnd, centered=splash)
    # On the loading screen, the picture's subject stays clear of the progress line (at 945)
    draw_machine(page, model(page), mood, *((960, 890) if splash else (1390, 940)))
    finish(page, splash)
    if splash:
        wordmark(page)
    svg = page.svg()
    if keep_svg:
        os.makedirs(os.path.join(ROOT, "dist", "backgrounds"), exist_ok=True)
        with open(os.path.join(ROOT, "dist", "backgrounds", name + ".svg"), "w") as f:
            f.write(svg)
    html = os.path.join(work, name + ".html")
    with open(html, "w") as f:
        f.write(f'<!doctype html><meta charset="utf-8"><body style="margin:0;background:{NAVY};overflow:hidden">{svg}')
    folder = os.path.join(ROOT, "_inc", "backgrounds") if splash else os.path.join(ROOT, "systems", name)
    os.makedirs(folder, exist_ok=True)
    out = os.path.join(folder, "splash.jpg" if splash else "background.jpg")
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={work}/profile",
                    f"--window-size={W},{H}", "--force-device-scale-factor=1", "--virtual-time-budget=4000",
                    f"--screenshot={out}", "file://" + html],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if shutil.which("xattr"):
        subprocess.run(["xattr", "-c", out], check=False)
    print(f"{name}: {os.path.getsize(out) >> 10} KB")


def main():
    args = [a for a in sys.argv[1:] if a != "--svg"]
    unknown = [a for a in args if a not in SYSTEMS and a != SPLASH]
    if unknown:
        sys.exit(f"unknown system: {' '.join(unknown)} (known: {' '.join(sorted(SYSTEMS))}, {SPLASH})")
    browser = chrome()
    with tempfile.TemporaryDirectory() as work:
        for name in args or sorted(SYSTEMS) + [SPLASH]:
            render(name, "--svg" in sys.argv, browser, work)


if __name__ == "__main__":
    main()
