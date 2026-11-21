#!/usr/bin/env python3
"""Checks the theme before it reaches a console. EmulationStation only logs these
mistakes, so they are easy to miss:

- every XML file is well formed and declares formatVersion 7;
- every <include> and every referenced file exists;
- every ${variable} a view uses is defined (or comes from the engine);
- every element of a view is one the engine knows (the names are case sensitive: <webImage> is
  skipped, <webimage> is drawn);
- images stay small enough for a Raspberry Pi.

    python3 tools/check.py        # exit status 1 when something is wrong
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", ".github", "docs", "tools", "dist"}
# Variables EmulationStation provides itself
ENGINE_VARS = re.compile(r"^(themePath|lang|screen\.|system\.|global\.|systemview\.|systembackground\.)")
VAR = re.compile(r"\$\{([^}]+)\}")
# Text that names a file of the theme
FILE_REF = re.compile(r"^(\$\{themePath\}|\.)/[^{}$]*\.(png|jpe?g|svg|ttf|otf|xml|glsl|wav|ogg|mp4)$", re.I)
# The element types of Batocera's EmulationStation (ThemeData::sElementMap), and what may sit in a view
ELEMENTS = {
    "splash", "control", "stackpanel", "rectangle", "screenshader", "shader", "image", "imagegrid",
    "gridtile", "clock", "networkIcon", "webimage", "batteryText", "batteryIcon", "text", "textlist",
    "container", "ninepatch", "datetime", "rating", "sound", "gameextras", "controllerActivity",
    "batteryIndicator", "helpsystem", "video", "carousel", "menuText", "menuTextSmall", "menuGroup",
    "menuBackground", "menuIcons", "menuGrid",
}
VIEW_CHILDREN = ELEMENTS | {"include"}
MAX_IMAGE = {".png": 600 << 10, ".jpg": 400 << 10, ".jpeg": 400 << 10, ".svg": 200 << 10}


def xml_files():
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if f.endswith(".xml"):
                yield os.path.join(root, f)


def resolve(ref, xml_path):
    if ref.startswith("${themePath}/"):
        return os.path.join(ROOT, ref[len("${themePath}/"):])
    return os.path.normpath(os.path.join(os.path.dirname(xml_path), ref))


def main():
    errors, warnings = [], []
    defined, used = set(), []
    for path in xml_files():
        rel = os.path.relpath(path, ROOT)
        try:
            tree = ET.parse(path)
        except ET.ParseError as e:
            errors.append(f"{rel}: {e}")
            continue
        root = tree.getroot()
        if root.tag != "theme" or (root.findtext("formatVersion") or "").strip() != "7":
            errors.append(f"{rel}: expected <theme> with <formatVersion>7</formatVersion>")
        for view in list(root.iter("view")) + list(root.iter("customView")):
            for child in view:
                if isinstance(child.tag, str) and child.tag not in VIEW_CHILDREN:
                    errors.append(f"{rel}: <{child.tag}> is not an element the engine knows")
        for variables in root.iter("variables"):
            defined.update(child.tag for child in variables)
        for el in root.iter():
            text = (el.text or "").strip()
            for value in [text] + list(el.attrib.values()):
                used.extend((rel, name) for name in VAR.findall(value))
            if el.tag == "include" and text:
                if not os.path.exists(resolve(text, path)):
                    errors.append(f"{rel}: include {text} doesn't exist")
            elif FILE_REF.match(text) and not os.path.exists(resolve(text, path)):
                errors.append(f"{rel}: <{el.tag}> {text} doesn't exist")
    for rel, name in used:
        if name not in defined and not ENGINE_VARS.match(name):
            errors.append(f"{rel}: ${{{name}}} is not defined")
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            limit = MAX_IMAGE.get(os.path.splitext(f)[1].lower())
            p = os.path.join(root, f)
            if limit and os.path.getsize(p) > limit:
                warnings.append(f"{os.path.relpath(p, ROOT)}: {os.path.getsize(p) >> 10} KB, over {limit >> 10} KB")
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("error:", e)
    print(f"{len(list(xml_files()))} XML files, {len(defined)} variables: "
          f"{len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
