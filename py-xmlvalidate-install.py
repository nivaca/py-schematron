#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-xmlvalidate. See the LICENSE file for details.
"""Install the commands of py-xmlvalidate: python3 py-xmlvalidate-install.py
[--bin FOLDER] [--force | --uninstall]

Makes symbolic links in ~/bin (or FOLDER) to the two scripts in this
folder, so they can be run from anywhere by their names:

    py-xmlvalidate.py document.xml
    py-xmlvalidate-all.sh document.xml

The links point to this folder, so the scripts keep finding what lives
next to them (odds/ and common/ for ODDs, and the .schema-cache/ of
downloaded schemas), and a `git pull` here updates the commands at once.
Run it again after moving this folder.

Nothing else is touched: an existing file of the same name in FOLDER is
left alone (and reported), and so is a link that points somewhere else,
unless --force is given.  --uninstall removes only the links that point to
this folder.

The scripts run with the `python3` they find first on the PATH, which needs
the saxonche and lxml libraries.  The installer checks that, and says how
to install them if they are missing.  Everything goes into the user's own
folders: no administrator rights are needed.
"""

import sys

if sys.version_info < (3, 15):
    sys.exit(f"py-xmlvalidate-install.py needs Python 3.15 or later; this is "
             f"Python {sys.version.split()[0]}.")

import argparse  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import stat  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
SCRIPTS = ("py-xmlvalidate.py", "py-xmlvalidate-all.sh")


def say(text: str = ""):
    print(text, flush=True)


def ours(link: Path) -> bool:
    """Whether LINK is a symbolic link to one of this folder's scripts."""
    return link.is_symlink() and Path(os.path.realpath(link)).parent == HERE


def make_executable(path: Path):
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def install(folder: Path, force: bool) -> bool:
    folder.mkdir(parents=True, exist_ok=True)
    ok = True
    for name in SCRIPTS:
        target, link = HERE / name, folder / name
        make_executable(target)
        if ours(link) and os.path.realpath(link) == str(target):
            say(f"  {link} already points here")
            continue
        if link.is_symlink() and (force or not link.exists()):
            link.unlink()                          # (another or a broken link)
        elif link.exists() or link.is_symlink():
            what = "a link to " + os.readlink(link) if link.is_symlink() else "a file"
            say(f"  {link} is {what}: left alone (--force replaces a link, never a file)")
            ok = False
            continue
        link.symlink_to(target)
        say(f"  {link} -> {target}")
    return ok


def uninstall(folder: Path):
    for name in SCRIPTS:
        link = folder / name
        if ours(link):
            link.unlink()
            say(f"  removed {link}")
        elif link.exists() or link.is_symlink():
            say(f"  {link} does not point here: left alone")


def check_path(folder: Path):
    dirs = [Path(p).resolve() for p in os.environ.get("PATH", "").split(os.pathsep) if p]
    if folder.resolve() not in dirs:
        say(f"\nNote: {folder} is not on your PATH, so the commands need their full path.")
        say(f"  Add it, e.g. in bash: export PATH=\"{folder}:$PATH\" (in ~/.bashrc);")
        say(f"  in fish: fish_add_path {folder}")


def check_python():
    """The interpreter the scripts' first line (#!/usr/bin/env python3) finds."""
    python = shutil.which("python3")
    if not python:
        say("\nNote: there is no python3 on the PATH; the scripts need one (3.15 or later).")
        return
    probe = subprocess.run([python, "-c", "import sys, saxonche, lxml; "
                            "print(sys.version.split()[0])"], capture_output=True, text=True)
    if probe.returncode == 0:
        say(f"\nThe scripts will run with {python} (Python {probe.stdout.strip()}), "
            f"which has saxonche and lxml.")
        return
    missing = "saxonche" if "saxonche" in probe.stderr else ("lxml" if "lxml" in probe.stderr else "")
    say(f"\nNote: the scripts will run with {python}, which "
        + (f"does not have the '{missing}' library." if missing else "cannot run them yet:\n"
           + probe.stderr.strip()))
    say(f"  Install the libraries for it:  {python} -m pip install --user saxonche lxml")
    say("  or put first on your PATH a Python that has them (such as a virtual\n"
        "  environment's bin/ folder).")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="py-xmlvalidate-install.py",
        description="Link the commands py-xmlvalidate.py and py-xmlvalidate-all.sh "
                    "into ~/bin (or another folder).")
    parser.add_argument("--bin", type=Path, default=Path.home() / "bin", metavar="FOLDER",
                        help="where to put the links (default: ~/bin)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--force", action="store_true",
                       help="replace existing links that point elsewhere (never files)")
    group.add_argument("--uninstall", action="store_true",
                       help="remove the links that point to this folder")
    args = parser.parse_args(argv)
    folder = args.bin.expanduser()
    if args.uninstall:
        say(f"Removing the links in {folder}:")
        uninstall(folder)
        return
    say(f"Linking the commands into {folder}:")
    ok = install(folder, args.force)
    check_path(folder)
    check_python()
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
