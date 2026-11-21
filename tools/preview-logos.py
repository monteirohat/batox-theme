#!/usr/bin/env python3
"""Previews the home's tiles: every system logo of Batocera's Carbon theme as this theme draws
it, in white (_inc/shaders/white.glsl), to find the ones that need a dark cut or their name
instead (logoCutDark, logoCutGray and logoAsName in _inc/variables.xml).

The logos aren't in this repository: copy them from a console first.

    scp -r root@CONSOLE:/usr/share/emulationstation/themes/es-theme-carbon/art/logos /tmp/logos
    python3 tools/preview-logos.py /tmp/logos        # writes dist/logos.html; open it in a browser

A tile shows the logo as the home does; under it, the same logo with each other treatment, to
compare. The browser's filters stand for the shader: the result on the console is the same.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUTS = {"logoCutDark": 0.25, "logoCutGray": 0.45}
# Translated and white-background variants of a logo: the home uses <system>.svg or .png only
VARIANT = re.compile(r"-(w|ca|cs|de|el|en|en_GB|engb|es|fr|hu|it|ja|nl|pl|pt|pt_BR|ro_RO|ru)$")


def lists():
    variables = ET.parse(os.path.join(ROOT, "_inc", "variables.xml")).getroot().find("variables")
    return {name: (variables.findtext(name) or "").split() for name in (*CUTS, "logoAsName")}


def cut_filter(level):
    """The shader's cutDark as an SVG filter: white, the alpha times a ramp on the brightness."""
    slope = 1 / 0.16
    return (f'<filter id="cut{int(level * 100)}" color-interpolation-filters="sRGB">'
            '<feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  '
            '0.299 0.587 0.114 0 0" result="luma"/>'
            f'<feComponentTransfer in="luma" result="mask"><feFuncA type="linear" slope="{slope:.3f}" '
            f'intercept="{-(level - 0.08) * slope:.3f}"/></feComponentTransfer>'
            '<feComposite in="SourceGraphic" in2="mask" operator="in" result="kept"/>'
            '<feColorMatrix in="kept" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1 0"/>'
            '</filter>')


def style(level):
    return f"filter:url(#cut{int(level * 100)})" if level else "filter:brightness(0) invert(1)"


def main():
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        sys.exit(__doc__)
    folder = os.path.abspath(sys.argv[1])
    chosen = lists()
    logos = {}
    for f in sorted(os.listdir(folder)):
        name, ext = os.path.splitext(f)
        if ext in (".svg", ".png") and not VARIANT.search(name):
            logos.setdefault(name, f)  # .png sorts before .svg, but the home prefers .svg
            if ext == ".svg":
                logos[name] = f
    cards = []
    for name, f in logos.items():
        src = "file://" + os.path.join(folder, f)
        level = next((CUTS[k] for k in CUTS if name in chosen[k]), 0)
        as_name = name in chosen["logoAsName"]
        tile = (f'<b>{name}</b>' if as_name else f'<img style="{style(level)}" src="{src}">')
        others = "".join(f'<i><img style="{style(l)}" src="{src}"></i>' for l in (0, *CUTS.values()) if l != level or as_name)
        label = "name" if as_name else f"cut {level}" if level else ""
        cards.append(f'<figure class="{"set" if label else ""}"><div>{tile}</div><p>{others}</p>'
                     f'<figcaption>{name} <u>{label}</u></figcaption></figure>')
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    out = os.path.join(ROOT, "dist", "logos.html")
    with open(out, "w") as page:
        page.write(
            "<!doctype html><meta charset=utf-8><title>Logos</title><style>"
            "body{background:#0B1A33;font:12px sans-serif;color:#A9B7CC;display:flex;flex-wrap:wrap;gap:8px;padding:16px}"
            "figure{margin:0;width:202px}div{height:202px;background:#15306B;display:grid;place-items:center}"
            "div img{max-width:86%;max-height:50%}b{color:#fff;font-size:20px;text-transform:uppercase;text-align:center}"
            "p{display:flex;gap:2px;margin:2px 0}i{flex:1;height:44px;background:#15306B;display:grid;place-items:center}"
            "i img{max-width:86%;max-height:60%}.set figcaption{color:#fff}u{color:#3B8CFF;text-decoration:none}"
            "</style><svg width=0 height=0 style='position:absolute'>"
            + "".join(cut_filter(l) for l in CUTS.values()) + "</svg>" + "".join(cards))
    print(f"wrote {out}: {len(logos)} logos")


if __name__ == "__main__":
    main()
