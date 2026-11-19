#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-schematron. See the LICENSE file for details.
"""Install py-schematron on Linux, macOS or Windows (or remove it).

    python3 install.py [--version X] [--from ZIP-OR-FOLDER] [--no-tei-stylesheets]
                       [--force] [--uninstall]

It needs Python 3.15 or later, and only Python's standard library: install.sh
(Linux, macOS) and install.ps1 (Windows) find such a Python and run it.  It
needs no administrator rights, and leaves the system's Python alone.

* A folder of its own: ~/.local/share/py-schematron (Linux; $XDG_DATA_HOME
  if set), ~/Library/Application Support/py-schematron (macOS) or
  %LOCALAPPDATA%\\py-schematron (Windows), holding:
  - program/: the release, from the zip of the latest release on GitHub
    (or Codeberg, if GitHub can't be reached), of --version X, or the zip
    or folder (a clone) given with --from; with the two TEI stylesheets
    that -o needs (odds/extract-isosch.xsl and common/functions.xsl), from
    TEIC/Stylesheets, unless --no-tei-stylesheets;
  - venv/: a Python environment with saxonche and lxml, from pip.
* The commands, which run the program with that environment:
  - Linux and macOS: py-schematron.py and py-schematron-all.sh, in ~/bin if
    it exists, or else in ~/.local/bin;
  - Windows: py-schematron (py-schematron.cmd), in the folder's bin\\,
    which is added to the user's PATH.  py-schematron-all.sh, a shell
    script, does not run on Windows.

An existing command of the same name that this installer did not make (a
link made by py-schematron-install.py from a clone, say) is left alone,
unless --force.  Run it again to update to the latest release: the cache of
downloaded schemas is kept.  --uninstall removes the folder and the
commands, and nothing else.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

NAME = "py-schematron"
MINIMUM = (3, 15)
GITHUB = "https://github.com/nivaca/py-schematron"
CODEBERG = "https://codeberg.org/nivaca/py-schematron"
AGENT = {"User-Agent": "py-schematron-installer"}
# The program's files, in a release zip or a clone
PROGRAM_FILES = ("py-schematron.py", "py-schematron-all.sh", "LICENSE",
                 "README.md", "README_es.md")
TEI = "https://raw.githubusercontent.com/TEIC/Stylesheets/dev/"
TEI_FILES = ("odds/extract-isosch.xsl", "common/functions.xsl")
# The first line after the shebang of every command this installer makes
MARK = "made by py-schematron's installer"


def windows() -> bool:
    return sys.platform == "win32"


def say(text: str = "") -> None:
    print(text, flush=True)


# ------------------------------------------------------------------ where

def home_of_app() -> Path:
    """The installer's own folder."""
    if windows():
        return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / NAME
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / NAME


def python_of(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if windows() else "bin/python")


def bin_folder() -> Path:
    """Where the commands go: on Windows the folder's bin\\ (added to the
    PATH); elsewhere ~/bin if it exists, or else ~/.local/bin."""
    if windows():
        return home_of_app() / "bin"
    home_bin = Path.home() / "bin"
    return home_bin if home_bin.is_dir() else Path.home() / ".local" / "bin"


# ------------------------------------------------------------------ the release

def latest_version() -> str:
    """The latest release: GitHub's (where /releases/latest leads), or else Codeberg's."""
    errors = []
    try:
        request = urllib.request.Request(f"{GITHUB}/releases/latest", headers=AGENT, method="HEAD")
        with urllib.request.urlopen(request, timeout=30) as answer:
            tag = answer.geturl().rstrip("/").rsplit("/", 1)[-1]
        if tag.startswith("v"):
            return tag[1:]
        errors.append(f"GitHub: no release ({answer.geturl()})")
    except OSError as e:
        errors.append(f"GitHub: {e}")
    try:
        api = CODEBERG.replace("codeberg.org/", "codeberg.org/api/v1/repos/") + "/releases/latest"
        with urllib.request.urlopen(urllib.request.Request(api, headers=AGENT), timeout=30) as answer:
            return json.load(answer)["tag_name"].lstrip("v")
    except (OSError, ValueError, KeyError) as e:
        errors.append(f"Codeberg: {e}")
    raise SystemExit("install.py: the latest release could not be found (" + "; ".join(errors) + ")")


def zip_name(version: str) -> str:
    return f"{NAME}-v.{version}.zip"


def download(url: str, target: Path) -> None:
    with urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=120) as answer:
        target.write_bytes(answer.read())


def fetch_release(version: str, folder: Path) -> Path:
    """Download the zip of VERSION into FOLDER: from GitHub, or else Codeberg."""
    target = folder / zip_name(version)
    errors = []
    for site in (GITHUB, CODEBERG):
        url = f"{site}/releases/download/v{version}/{zip_name(version)}"
        try:
            download(url, target)
            say(f"py-schematron {version}: {url}")
            return target
        except OSError as e:
            errors.append(f"{site}: {e}")
    raise SystemExit(f"install.py: there is no release {version} ({'; '.join(errors)})")


def unpack(source: Path, program: Path) -> None:
    """Put the program's files from SOURCE (a release zip, or a folder such
    as a clone) into PROGRAM, which is made anew."""
    with tempfile.TemporaryDirectory(prefix="py-schematron-") as tmp:
        if source.is_dir():
            root = source
        elif zipfile.is_zipfile(source):
            with zipfile.ZipFile(source) as z:
                z.extractall(tmp)
            tops = [p for p in Path(tmp).iterdir() if p.is_dir()]
            root = tops[0] if len(tops) == 1 and not (Path(tmp) / PROGRAM_FILES[0]).exists() else Path(tmp)
        else:
            raise SystemExit(f"install.py: {source} is neither a zip nor a folder")
        if not (root / PROGRAM_FILES[0]).is_file():
            raise SystemExit(f"install.py: there is no {PROGRAM_FILES[0]} in {source}")
        if program.exists():
            shutil.rmtree(program)
        program.mkdir(parents=True)
        for name in PROGRAM_FILES:
            if (root / name).is_file():
                shutil.copy2(root / name, program / name)
        for name in ("odds", "common"):               # (a clone may have them)
            if (root / name).is_dir():
                shutil.copytree(root / name, program / name)


def fetch_tei_stylesheets(program: Path) -> str | None:
    """The two TEI stylesheets that -o needs, next to the program; None, or
    what went wrong (a warning: everything else works without them)."""
    try:
        for name in TEI_FILES:
            target = program / name
            if not target.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                download(TEI + name, target)
        return None
    except OSError as e:
        return (f"the TEI stylesheets could not be downloaded ({e}); -o (rules from an ODD) "
                f"needs them, or a clone of TEIC/Stylesheets named with --stylesheets")


# ------------------------------------------------------------------ Python

def run(*command) -> None:
    say("+ " + " ".join(str(c) for c in command))
    result = subprocess.run([str(c) for c in command])
    if result.returncode:
        raise SystemExit(f"install.py: this failed (exit code {result.returncode})")


def make_venv(venv: Path) -> Path:
    """The environment (made anew, so that an update starts clean); its Python."""
    if venv.exists():
        shutil.rmtree(venv)
    try:
        import venv as venv_module  # (some Linux systems leave it out: python3-venv)
        venv_module.EnvBuilder(with_pip=True, upgrade_deps=False).create(venv)
    except (ImportError, subprocess.CalledProcessError, OSError) as e:
        raise SystemExit(f"install.py: a Python environment could not be made ({e}). On Debian "
                         f"and Ubuntu, install python3-venv (or python3.15-venv) and try again.") from None
    python = python_of(venv)
    if not python.exists():
        raise SystemExit(f"install.py: the environment has no Python ({python})")
    return python


def install_libraries(python: Path) -> None:
    run(python, "-m", "pip", "install", "--disable-pip-version-check", "saxonche", "lxml")


# ------------------------------------------------------------------ the commands

def commands(program: Path, python: Path) -> dict[str, str]:
    """The commands to write: {file name: text}."""
    if windows():
        return {"py-schematron.cmd":
                f'@echo off\r\nrem {MARK}\r\n"{python}" "{program / "py-schematron.py"}" %*\r\n'}
    return {
        "py-schematron.py":
            f'#!/bin/sh\n# {MARK}\nexec "{python}" "{program / "py-schematron.py"}" "$@"\n',
        "py-schematron-all.sh":
            f'#!/bin/sh\n# {MARK}\nPY_SCHEMATRON_PYTHON="{python}" exec /bin/bash '
            f'"{program / "py-schematron-all.sh"}" "$@"\n',
    }


def ours(path: Path) -> bool:
    """Whether PATH is a command this installer made."""
    if path.is_symlink() or not path.is_file():
        return False
    try:
        return MARK in path.read_text(encoding="utf-8", errors="replace")[:300]
    except OSError:
        return False


def write_commands(folder: Path, texts: dict[str, str], force: bool) -> list[str]:
    """Write the commands into FOLDER; the notes for the user."""
    folder.mkdir(parents=True, exist_ok=True)
    notes = []
    for name, text in texts.items():
        target = folder / name
        if (target.exists() or target.is_symlink()) and not ours(target):
            if not force:
                what = f"a link to {os.readlink(target)}" if target.is_symlink() else "a file"
                notes.append(f"{target} is {what}, not made by this installer: left alone "
                             f"(--force replaces it).")
                continue
            target.unlink()
        target.write_text(text, encoding="utf-8", newline="")
        if not windows():
            target.chmod(0o755)
        say(f"  {target}")
    return notes


def on_path(folder: Path) -> bool:
    norm = lambda p: os.path.normcase(os.path.realpath(p)).rstrip("\\/")
    return any(norm(p) == norm(folder) for p in os.environ.get("PATH", "").split(os.pathsep) if p)


def add_to_user_path(folder: str) -> bool:
    """Add FOLDER to the user's PATH (Windows); whether it wasn't there."""
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0,
                        winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            value, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            value, kind = "", winreg.REG_EXPAND_SZ
        parts = [p for p in value.split(";") if p]
        if any(os.path.normcase(p.rstrip("\\")) == os.path.normcase(folder.rstrip("\\")) for p in parts):
            return False
        winreg.SetValueEx(key, "Path", 0, kind, ";".join(parts + [folder]))
    return True


def remove_from_user_path(folder: str) -> None:
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0,
                        winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            value, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            return
        parts = [p for p in value.split(";")
                 if p and os.path.normcase(p.rstrip("\\")) != os.path.normcase(folder.rstrip("\\"))]
        winreg.SetValueEx(key, "Path", 0, kind, ";".join(parts))


def jing_hint() -> str | None:
    """How to get jing, for py-schematron-all.sh and the plugins, if it is missing."""
    if shutil.which("jing"):
        return None
    if windows():
        return ("jing (optional: the RelaxNG layer of the VS Code extension and the Emacs "
                "package) is not on the PATH; it needs Java and jing.jar, see the README.")
    if sys.platform == "darwin":
        return "jing (optional, for the RelaxNG layer) is not installed: brew install jing-trang"
    return ("jing (optional, for the RelaxNG layer) is not installed: sudo dnf install jing, "
            "or sudo apt install jing")


# ------------------------------------------------------------------ install, uninstall

def install(args) -> None:
    home = home_of_app()
    home.mkdir(parents=True, exist_ok=True)
    program, venv = home / "program", home / "venv"
    cache = home / ".schema-cache-kept"
    if (program / ".schema-cache").is_dir():                # (kept across updates)
        shutil.rmtree(cache, ignore_errors=True)
        shutil.move(program / ".schema-cache", cache)
    with tempfile.TemporaryDirectory(prefix="py-schematron-") as tmp:
        if args.source:
            source = Path(args.source).expanduser().resolve()
        else:
            source = fetch_release(args.version or latest_version(), Path(tmp))
        unpack(source, program)
    if cache.is_dir():
        shutil.move(cache, program / ".schema-cache")
    notes = []
    if not args.no_tei_stylesheets:
        warning = fetch_tei_stylesheets(program)
        if warning:
            notes.append(warning)
    python = make_venv(venv)
    install_libraries(python)
    folder = bin_folder()
    say(f"The commands, in {folder}:")
    notes += write_commands(folder, commands(program, python), args.force)
    if windows():
        if add_to_user_path(str(folder)):
            notes.append(f"{folder} was added to your PATH: open a new terminal to use py-schematron.")
        else:
            notes.append("Windows has no py-schematron-all.sh: run py-schematron, and jing apart.")
    elif not on_path(folder):
        notes.append(f'{folder} is not on your PATH: add it, for instance with the line '
                     f'export PATH="{folder}:$PATH" in ~/.profile (bash) or ~/.zshrc (zsh), '
                     f'and open a new terminal.')
    hint = jing_hint()
    if hint:
        notes.append(hint)
    result = subprocess.run([str(python), str(program / "py-schematron.py"), "--version"],
                            capture_output=True, text=True)
    say()
    say(f"{result.stdout.strip() or 'py-schematron'} is installed in {home}.")
    say(f"Try it: {'py-schematron' if windows() else 'py-schematron.py'} --about")
    for note in notes:
        say(f"- {note}")


def uninstall() -> None:
    home = home_of_app()
    folder = bin_folder()
    for name in commands(home / "program", python_of(home / "venv")):
        target = folder / name
        if ours(target):
            target.unlink()
            say(f"  removed {target}")
        elif target.exists() or target.is_symlink():
            say(f"  {target} was not made by this installer: left alone")
    if windows():
        remove_from_user_path(str(folder))
    if home.exists():
        shutil.rmtree(home)
        say(f"  removed {home}")
    say("py-schematron is removed.")


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < MINIMUM:
        raise SystemExit("install.py: py-schematron needs Python %d.%d or later; this is %s (%s)"
                         % (MINIMUM + (sys.version.split()[0], sys.executable)))
    parser = argparse.ArgumentParser(prog="install.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--version", help="this release instead of the latest (e.g. 2.0)")
    parser.add_argument("--from", dest="source", metavar="ZIP-OR-FOLDER",
                        help="install this release zip, or this folder (a clone), instead of downloading")
    parser.add_argument("--no-tei-stylesheets", action="store_true",
                        help="don't download the two TEI stylesheets that -o needs")
    parser.add_argument("--force", action="store_true",
                        help="replace commands of the same name that this installer did not make")
    parser.add_argument("--uninstall", action="store_true", help="remove what this installed")
    args = parser.parse_args(argv)
    if args.uninstall:
        uninstall()
    else:
        install(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
