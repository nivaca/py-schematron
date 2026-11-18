#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-xmlvalidate. See the LICENSE file for details.
"""Copy py-xmlvalidate.py into the plugins: python3 tools/sync-plugins.py
[--check] [--emacs FOLDER] [--vscode FOLDER]

The VS Code extension (py-xmlvalidate-vscode) and the Emacs package
(py-xmlvalidate-emacs) each carry their own copy of py-xmlvalidate.py, at
the top of their repositories, so that each installs on its own.  This
script copies this repository's py-xmlvalidate.py there, by default into
the clones next to this one (../py-xmlvalidate-emacs and
../py-xmlvalidate-vscode), and says which copies changed and from which
version.  It does not commit anything: after a copy, commit it in the
plugin and say in its changelog which version it carries.

--check copies nothing: it only says whether the copies are the same as
this one, and exits with 1 if any is not (or is missing), for use before
a release.  A plugin folder that does not exist is reported and skipped.
"""

import sys

if sys.version_info < (3, 15):
    sys.exit(f"sync-plugins.py needs Python 3.15 or later; this is "
             f"Python {sys.version.split()[0]}.")

import argparse  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "py-xmlvalidate.py"
PLUGINS = {"emacs": "py-xmlvalidate-emacs", "vscode": "py-xmlvalidate-vscode"}


def version(path: Path) -> str:
    """The __version__ of a py-xmlvalidate.py, read without importing it."""
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else "?"


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="tools/sync-plugins.py",
        description="Copy py-xmlvalidate.py into the clones of the VS Code extension "
                    "and the Emacs package.")
    parser.add_argument("--check", action="store_true",
                        help="copy nothing; exit with 1 if a copy differs or is missing")
    for key, name in PLUGINS.items():
        parser.add_argument(f"--{key}", type=Path, default=ROOT.parent / name, metavar="FOLDER",
                            help=f"the clone of {name} (default: ../{name})")
    args = parser.parse_args(argv)

    ours = SCRIPT.read_bytes()
    print(f"py-xmlvalidate.py {version(SCRIPT)}")
    stale = 0
    for key, name in PLUGINS.items():
        folder = getattr(args, key).expanduser().resolve()
        target = folder / "py-xmlvalidate.py"
        if not (folder / ".git").exists():
            print(f"  {name}: no clone in {folder} (skipped)")
            stale += 1
            continue
        if target.is_file() and target.read_bytes() == ours:
            print(f"  {name}: up to date")
            continue
        before = version(target) if target.is_file() else "none"
        if args.check:
            print(f"  {name}: differs (it has {before})")
            stale += 1
            continue
        shutil.copyfile(SCRIPT, target)
        mode = target.stat().st_mode
        target.chmod(mode | 0o111)                       # (it can be run, as here)
        print(f"  {name}: copied ({before} -> {version(SCRIPT)}); commit it there")
    if args.check and stale:
        sys.exit(1)


if __name__ == "__main__":
    main()
