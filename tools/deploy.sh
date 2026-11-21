#!/bin/sh
# Copies the theme to a Batocera console over SSH, replacing the copy there.
#   tools/deploy.sh [host]      (default: $CONSOLE, else batocera.local; user root, password linux)
# Then choose the theme on the console (User interface settings > Theme set), or restart
# EmulationStation if it is already chosen (BatoX's EmulationStation screen has the button).
set -eu
HOST="${1:-${CONSOLE:-batocera.local}}"
DEST=/userdata/themes/batox-theme
cd "$(dirname "$0")/.."
python3 tools/check.py
# COPYFILE_DISABLE keeps macOS from adding ._ files to the archive
COPYFILE_DISABLE=1 tar -cf - --exclude ./.git --exclude ./.github --exclude ./docs --exclude ./tools \
  --exclude ./dist --exclude .DS_Store . |
  ssh "root@$HOST" "rm -rf $DEST.new && mkdir -p $DEST.new && tar -xf - -C $DEST.new && rm -rf $DEST && mv $DEST.new $DEST"
echo "Copied to $HOST:$DEST"
