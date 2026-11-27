#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-schematron. See the LICENSE file for details.
"""Hace el zip de la versión en build/release/: python3 tools/bundle-zip.py

build/release/py-schematron-v.VERSION.zip (la versión de py-schematron.py), con
el programa en una carpeta del mismo nombre: py-schematron.py,
py-schematron-all.sh, py-schematron-install.py, los README, la licencia
y docs/ (las descripciones, las capturas y el ejemplo).  Se hace con los
archivos que git sigue, así que no entra nada que solo exista en esta carpeta
(las hojas de estilo de TEI en odds/ y common/, las cachés de esquemas, los
documentos de prueba, los archivos de bloqueo del editor...).  Quedan fuera
también lo que no es parte del programa (tools/, con los scripts que hacen el
zip, las capturas y las copias de los complementos; packaging/, con la clave
pública que firma las versiones) y los archivos ocultos.  Los scripts conservan
su permiso de ejecución.  La extensión de VS Code y el paquete de Emacs tienen
repositorios y versiones propios (py-schematron-vscode, py-schematron.el).

build/release se crea en la carpeta del programa si hace falta (tools/release.py
lo publica desde allí y lo borra al final; dist/ no se usa); --output da otra
carpeta.  Si alguno de los archivos del zip tiene cambios que aún no están en un
commit, lo advierte, porque el zip toma los archivos tal como están ahora.
"""

import argparse
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # (above tools/)
DIST = os.path.join(HERE, "build", "release")  # (not dist/: see tools/release.py)
NAME = "py-schematron"

#  What is in the repository but not part of the program
NOT_PART = ("tools/", "packaging/")


def version() -> str:
    """py-schematron.py's __version__, read without importing it (that would
    need saxonche and lxml)."""
    with open(os.path.join(HERE, "py-schematron.py"), encoding="utf-8") as f:
        m = re.search(r'^__version__\s*=\s*"([^"]+)"', f.read(), re.M)
    if not m:
        sys.exit("bundle-zip.py: no __version__ in py-schematron.py")
    return m.group(1)


def name() -> str:
    """The name of the zip, without .zip: py-schematron-v.1.12."""
    return f"{NAME}-v.{version()}"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=HERE, capture_output=True, text=True, check=True).stdout


def files() -> list[str]:
    """The files of the distribution, relative to the program's folder."""
    out = []
    for f in git("ls-files", "-z").split("\0"):
        if not f or f.startswith(NOT_PART) or any(p.startswith(".") for p in f.split("/")):
            continue
        if os.path.isfile(os.path.join(HERE, f)):  # (tracked but deleted: left out)
            out.append(f)
    return sorted(out)


def uncommitted(paths: list[str]) -> list[str]:
    status = git("status", "--porcelain", "--", *paths)
    return [line[3:] for line in status.splitlines()]


def bundle_zip(folder: str) -> str:
    """Writes the zip into FOLDER; returns its path."""
    path = os.path.join(folder, name() + ".zip")
    tmp = path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files():
            src = os.path.join(HERE, f)
            info = zipfile.ZipInfo.from_file(src, name() + "/" + f)
            #  (ordinary permissions, whatever this folder has: rw-r--r--, or
            #  rwxr-xr-x for what can be run, as py-schematron-all.sh)
            mode = 0o755 if os.access(src, os.X_OK) else 0o644
            info.external_attr = (0o100000 | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(src, "rb") as data:
                z.writestr(info, data.read())
    os.replace(tmp, path)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="tools/bundle-zip.py",
        description=f"Make the release bundle: {name()}.zip.")
    parser.add_argument("-o", "--output", metavar="FOLDER", default=None,
                        help="the folder to write it in (default: build/release, in the program's folder)")
    parser.add_argument("-l", "--list", action="store_true",
                        help="only list the files the zip would have")
    parser.add_argument("--no-vsix", action="store_true", help=argparse.SUPPRESS)  # (no .vsix any more)
    args = parser.parse_args(argv)
    if args.list:
        print("\n".join(files()))
        return
    if args.output is None:
        args.output = DIST
        os.makedirs(DIST, exist_ok=True)
    elif not os.path.isdir(args.output):
        sys.exit(f"bundle-zip.py: there is no folder {args.output}")
    changed = uncommitted(files())
    if changed:
        print("Note: not committed yet, bundled as they are now: " + ", ".join(changed))
    try:
        path = bundle_zip(args.output)
    except OSError as e:
        sys.exit(f"bundle-zip.py: {e}")
    with zipfile.ZipFile(path) as z:
        count = len(z.namelist())
    print(f"Wrote {path} ({count} files, {os.path.getsize(path) / 1e6:.1f} MB).")


if __name__ == "__main__":
    main()
