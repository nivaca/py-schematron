#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-schematron. See the LICENSE file for details.
"""Compara dos versiones de py-schematron.py sobre un corpus de documentos:

    python3 tools/corpus-check.py --corpus FOLDER [--against TAG | --old FILE]
                                  [--jobs N] [--slower PERCENT] [--min-seconds S] [--verbose]

Cada documento XML de las carpetas del corpus (--corpus, que se puede repetir, o
$PY_SCHEMATRON_CORPUS, con las carpetas separadas por el separador de rutas del
sistema) que tenga una instrucción <?xml-model?> se valida con --json en dos
versiones del programa: la de la última versión publicada (la etiqueta v* más
reciente, o --against TAG, o --old FILE) y el py-schematron.py de esta carpeta.
Antes, los documentos se copian a una carpeta temporal y se validan allí con
--as, de modo que sus referencias relativas a los esquemas siguen resolviéndose
y los originales solo se leen, nunca se escriben.

De cada documento se comparan los dos resultados: las violaciones (patrón,
tipo, texto, línea, xml:id), las reglas que no se pudieron evaluar, el error de
un documento mal formado y el código de salida; los tiempos y los mensajes de
progreso quedan fuera, porque siempre difieren.  Escribe los documentos cuyo
resultado cambió y el tiempo total de cada versión, y sale con 1 si cambió
algún resultado, con 2 si el problema es suyo (no hay documentos, no hay
etiqueta) y con 0 en otro caso.

Compara también el tiempo de cada documento, y avisa de los que la versión
nueva valida claramente más despacio: más de --slower PERCENT (50) y de
--min-seconds S (0.25) a la vez, para que no cuente el ruido habitual de las
mediciones.  Los documentos se revisan en paralelo, así que cada uno señalado
se vuelve a medir solo, con las dos versiones, y se mantiene únicamente si
sigue siendo más lento.  Una lentitud es un aviso, no un fallo.
"""

import sys

if sys.version_info < (3, 15):
    sys.exit(f"corpus-check.py needs Python 3.15 or later; this is "
             f"Python {sys.version.split()[0]}.")

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from concurrent.futures import ThreadPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "py-schematron.py"
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".schema-cache"}


def documents(folders: list[Path]) -> list[Path]:
    """The XML documents under FOLDERS that name a schema with <?xml-model?>."""
    found = []
    for folder in folders:
        for dirpath, dirnames, filenames in os.walk(folder):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                if not name.lower().endswith(".xml"):
                    continue
                path = Path(dirpath) / name
                try:
                    with open(path, "rb") as f:
                        head = f.read(4096)
                except OSError:
                    continue
                if b"<?xml-model" in head:
                    found.append(path.resolve())
    return found


def last_tag() -> str:
    tags = subprocess.run(["git", "tag", "--list", "v[0-9]*", "--sort=-v:refname"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.split()
    if not tags:
        raise SystemExit("corpus-check.py: no v* tag to compare with; give --against or --old")
    return tags[0]


def script_of(tag: str, target: Path) -> None:
    """Write py-schematron.py as it was at TAG (py-xmlvalidate.py before 2.0)."""
    for name in ("py-schematron.py", "py-xmlvalidate.py"):
        result = subprocess.run(["git", "show", f"{tag}:{name}"], cwd=ROOT, capture_output=True)
        if result.returncode == 0:
            target.write_bytes(result.stdout)
            return
    raise SystemExit(f"corpus-check.py: {tag} has no py-schematron.py")


def summary(code: int, stdout: str) -> dict:
    """What is compared of one run: the exit code and the results, without
    times, paths or progress messages."""
    try:
        report = json.loads(stdout)
    except json.JSONDecodeError:
        return {"exit": code, "output": stdout.strip()[-300:]}
    if "error" in report and "documents" not in report:
        return {"exit": code, "fatal": report["error"]}
    docs = []
    for d in report.get("documents", []):
        docs.append({
            "error": d.get("error"),
            "violations": sorted(
                (v.get("pattern") or "", v.get("type"), v.get("text") or v.get("message") or "",
                 v.get("line"), v.get("xml_id")) for v in d.get("violations", [])),
            "xpath_errors": sorted(
                (e.get("message") or "", e.get("error") or "", e.get("nodes"))
                for e in d.get("xpath_errors", [])),
        })
    return {"exit": code, "documents": docs}


def validate(script: Path, copy: Path, original: Path) -> tuple[dict, float]:
    start = time.perf_counter()
    result = subprocess.run([sys.executable, str(script), "--json", "--as", str(original), str(copy)],
                            capture_output=True, text=True)
    return summary(result.returncode, result.stdout), time.perf_counter() - start


def describe(old: dict, new: dict) -> str:
    """A short account of how two summaries differ."""
    if old.get("exit") != new.get("exit"):
        lines = [f"exit code {old.get('exit')} -> {new.get('exit')}"]
    else:
        lines = []
    for key in ("fatal", "output"):
        if old.get(key) != new.get(key):
            lines.append(f"{key}: {old.get(key)!r} -> {new.get(key)!r}")
    for i, (a, b) in enumerate(zip(old.get("documents", []), new.get("documents", []))):
        if a["error"] != b["error"]:
            lines.append(f"malformed: {a['error']!r} -> {b['error']!r}")
        gone = [v for v in a["violations"] if v not in b["violations"]]
        came = [v for v in b["violations"] if v not in a["violations"]]
        if gone or came:
            lines.append(f"violations: {len(a['violations'])} -> {len(b['violations'])}")
            for v in gone[:3]:
                lines.append(f"  - line {v[3]}: {v[2][:90]}")
            for v in came[:3]:
                lines.append(f"  + line {v[3]}: {v[2][:90]}")
        if a["xpath_errors"] != b["xpath_errors"]:
            lines.append(f"broken rules: {len(a['xpath_errors'])} -> {len(b['xpath_errors'])}")
    return "\n".join(lines) or "the results differ"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="tools/corpus-check.py",
                                     description="Compare two versions of py-schematron.py on a corpus.")
    parser.add_argument("--corpus", action="append", type=Path, metavar="FOLDER",
                        help="a folder of documents (repeatable; default: $PY_SCHEMATRON_CORPUS)")
    which = parser.add_mutually_exclusive_group()
    which.add_argument("--against", metavar="TAG", help="the version to compare with (default: the newest v* tag)")
    which.add_argument("--old", type=Path, metavar="FILE", help="a py-schematron.py to compare with")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 4, help="documents checked at once")
    parser.add_argument("--slower", type=float, default=50, metavar="PERCENT",
                        help="warn about documents this much slower (default 50)")
    parser.add_argument("--min-seconds", type=float, default=0.25, metavar="S",
                        help="... and at least this many seconds slower (default 0.25)")
    parser.add_argument("--verbose", action="store_true", help="list every document checked")
    args = parser.parse_args(argv)

    folders = args.corpus or [Path(p).expanduser() for p in
                              os.environ.get("PY_SCHEMATRON_CORPUS", "").split(os.pathsep) if p]
    if not folders:
        print("corpus-check.py: no corpus: give --corpus FOLDER or set PY_SCHEMATRON_CORPUS",
              file=sys.stderr)
        return 2
    docs = documents([f.expanduser().resolve() for f in folders])
    if not docs:
        print(f"corpus-check.py: no document with <?xml-model?> in {', '.join(map(str, folders))}",
              file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="pysch-corpus-") as tmp:
        tmp = Path(tmp)
        scripts = {}
        for side in ("old", "new"):
            (tmp / side).mkdir()
            if (ROOT / ".schema-cache").is_dir():              # (fewer downloads)
                shutil.copytree(ROOT / ".schema-cache", tmp / side / ".schema-cache")
            scripts[side] = tmp / side / "py-schematron.py"
        if args.old:
            shutil.copyfile(args.old, scripts["old"])
            label = str(args.old)
        else:
            label = args.against or last_tag()
            script_of(label, scripts["old"])
        shutil.copyfile(SCRIPT, scripts["new"])
        copies = tmp / "docs"
        copies.mkdir()
        pairs = []
        for i, doc in enumerate(docs):
            copy = copies / f"{i:05d}-{doc.name}"
            shutil.copyfile(doc, copy)
            pairs.append((doc, copy))
        print(f"{len(docs)} documents; {label} against this folder's py-schematron.py", flush=True)

        def check(pair):
            doc, copy = pair
            old, t_old = validate(scripts["old"], copy, doc)
            new, t_new = validate(scripts["new"], copy, doc)
            return doc, old, new, t_old, t_new

        # (a first pass on one document fills each cache, so that parallel
        # runs do not download the same schema at once)
        results = [check(pairs[0])]
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            results += list(pool.map(check, pairs[1:]))

        def slower(t_old, t_new):
            return t_new - t_old >= args.min_seconds and t_new > t_old * (1 + args.slower / 100)
        copies_of = dict(pairs)
        slowdowns = []
        for doc, old, new, t_old, t_new in results:
            if old == new and slower(t_old, t_new):         # (timed again, alone)
                _, _, _, t_old2, t_new2 = check((doc, copies_of[doc]))
                if slower(t_old2, t_new2):
                    slowdowns.append((doc, t_old2, t_new2))

    changed = 0
    total_old = total_new = 0.0
    for doc, old, new, t_old, t_new in results:
        total_old += t_old
        total_new += t_new
        if old != new:
            changed += 1
            print(f"\nCHANGED  {doc}\n{describe(old, new)}")
        elif args.verbose:
            print(f"same     {doc}")
    for doc, t_old, t_new in slowdowns:
        print(f"\nSLOWER   {doc}\n{t_old:.2f} s -> {t_new:.2f} s "
              f"({(t_new - t_old) / t_old * 100:+.0f}%)" if t_old else f"\nSLOWER   {doc}")
    print(f"\n{len(results) - changed} of {len(results)} documents give the same result; "
          f"{changed} changed.")
    if slowdowns:
        print(f"{len(slowdowns)} document(s) validate clearly slower with this version "
              f"(over {args.slower:g}% and {args.min_seconds:g} s; see SLOWER above).")
    print(f"Time: {label} {total_old:.1f} s, this version {total_new:.1f} s "
          f"({(total_new - total_old) / total_old * 100:+.0f}%)." if total_old else "")
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
