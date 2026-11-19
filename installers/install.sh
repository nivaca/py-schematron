#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-schematron. See the LICENSE file for details.
#
# Installs py-schematron on Linux or macOS:
#
#   curl -LsSf https://raw.githubusercontent.com/nivaca/py-schematron/main/installers/install.sh | sh
#   sh install.sh [--version X] [--from ZIP-OR-FOLDER] [--no-tei-stylesheets] [--force] [--uninstall]
#   (with curl ... | sh -s -- --uninstall, the options go after "-s --")
#
# It finds Python 3.15 or later and runs install.py with it (the one next to
# this script, or else the one in the repository): see install.py for what
# is installed, and where.
set -eu

URL="https://raw.githubusercontent.com/nivaca/py-schematron/main/installers/install.py"

python=""
for candidate in python3.17 python3.16 python3.15 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 15))' 2>/dev/null; then
        python="$candidate"
        break
    fi
done
if [ -z "$python" ]; then
    echo "install.sh: py-schematron needs Python 3.15 or later, and none was found." >&2
    case "$(uname -s)" in
        Darwin) echo "Install it from https://www.python.org/downloads/macos/ (or: brew install python@3.15)." >&2 ;;
        *) echo "Install it with your system's packages (python3.15), or from https://www.python.org/downloads/." >&2 ;;
    esac
    exit 1
fi

here="$(cd "$(dirname "$0")" 2>/dev/null && pwd || true)"
if [ -n "$here" ] && [ -f "$here/install.py" ]; then
    exec "$python" "$here/install.py" "$@"
fi
script="$(mktemp "${TMPDIR:-/tmp}/py-schematron-install.XXXXXX")"
trap 'rm -f "$script"' EXIT
if command -v curl >/dev/null 2>&1; then
    curl -LsSf "$URL" -o "$script"
elif command -v wget >/dev/null 2>&1; then
    wget -q "$URL" -O "$script"
else
    "$python" -c "import sys, urllib.request; urllib.request.urlretrieve(sys.argv[1], sys.argv[2])" "$URL" "$script"
fi
"$python" "$script" "$@"
