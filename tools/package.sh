#!/bin/sh
# Builds dist/batox-theme.zip from the last commit, with only the theme's files (see
# .gitattributes). The ZIP's name is the theme's name on the console, so it never carries the
# version: the release does.
set -eu
cd "$(dirname "$0")/.."
python3 tools/check.py
mkdir -p dist
git archive --format=zip --prefix=batox-theme/ -o dist/batox-theme.zip HEAD
echo "Wrote dist/batox-theme.zip ($(du -k dist/batox-theme.zip | cut -f1) KB)"
