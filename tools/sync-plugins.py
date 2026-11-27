#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-schematron. See the LICENSE file for details.
"""Copia py-schematron.py y tools/release.py en los complementos:
python3 tools/sync-plugins.py [--check] [--emacs FOLDER] [--vscode FOLDER]

La extensión de VS Code (py-schematron-vscode) y el paquete de Emacs
(py-schematron.el) llevan cada uno su propia copia de py-schematron.py, en la
raíz de su repositorio, para que cada uno se instale por sí solo.  Este script
copia allí el py-schematron.py de este repositorio, por omisión en los clones
vecinos de este (../py-schematron.el y ../py-schematron-vscode), y dice qué
copias cambiaron y desde qué versión.  Copia también tools/release.py y
tools/zenodo.py, el script de publicación y la herramienta de Zenodo que
comparten los tres repositorios.  No hace ningún commit: después de una copia,
hay que hacerlo en el complemento y decir en su registro de cambios qué versión
lleva.

--check no copia nada: solo dice si las copias son iguales a la de aquí, y sale
con 1 si alguna no lo es (o falta), para usarlo antes de publicar una versión.
Si la carpeta de un complemento no existe, lo dice y la salta.
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
SCRIPT = ROOT / "py-schematron.py"
FILES = ("py-schematron.py", "tools/release.py", "tools/zenodo.py")    # (copied to the same place)
PLUGINS = {"emacs": "py-schematron.el", "vscode": "py-schematron-vscode"}


def version(path: Path) -> str:
    """The __version__ of a py-schematron.py, read without importing it."""
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else "?"


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="tools/sync-plugins.py",
        description="Copy py-schematron.py into the clones of the VS Code extension "
                    "and the Emacs package.")
    parser.add_argument("--check", action="store_true",
                        help="copy nothing; exit with 1 if a copy differs or is missing")
    for key, name in PLUGINS.items():
        parser.add_argument(f"--{key}", type=Path, default=ROOT.parent / name, metavar="FOLDER",
                            help=f"the clone of {name} (default: ../{name})")
    args = parser.parse_args(argv)

    print(f"py-schematron.py {version(SCRIPT)}")
    stale = 0
    for key, name in PLUGINS.items():
        folder = getattr(args, key).expanduser().resolve()
        if not (folder / ".git").exists():
            print(f"  {name}: no clone in {folder} (skipped)")
            stale += 1
            continue
        for rel in FILES:
            source, target = ROOT / rel, folder / rel
            ours = source.read_bytes()
            if target.is_file() and target.read_bytes() == ours:
                print(f"  {name}/{rel}: up to date")
                continue
            before = (version(target) if rel == "py-schematron.py" else "an older copy") \
                if target.is_file() else "none"
            if args.check:
                print(f"  {name}/{rel}: differs (it has {before})")
                stale += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            target.chmod(target.stat().st_mode | 0o111)      # (it can be run, as here)
            after = version(SCRIPT) if rel == "py-schematron.py" else "this one"
            print(f"  {name}/{rel}: copied ({before} -> {after}); commit it there")
    if args.check and stale:
        sys.exit(1)


if __name__ == "__main__":
    main()
