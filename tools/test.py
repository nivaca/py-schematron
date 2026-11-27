#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-schematron. See the LICENSE file for details.
"""Corre a la vez las pruebas de py-schematron: python3 tools/test.py [-j N] [-v] [NOMBRE ...]

Cada archivo de pruebas (tests/test_*.py) corre en un proceso de unittest propio, tantos a la vez como
procesadores tenga el computador (-j lo cambia), primero los más lentos; así, la suite entera tarda más o menos
lo que su archivo más lento, y no la suma de todos. Cada proceso descubre su archivo como lo haría
python3 -m unittest discover -s tests, con la misma carpeta en sys.path, y tiene su propia carpeta temporal.

Los NOMBRE eligen qué correr: un archivo (test_zenodo) o un patrón (test_*corpus*). Al final aparecen los
archivos que fallaron, con su salida, y los totales; -v muestra además cada archivo a medida que termina. El
código de salida es 1 si falló alguna prueba. (python3 -m unittest discover -s tests las sigue corriendo una tras
otra.) Así las corre también tools/release.py.
"""

import argparse
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
# Los archivos que más tardan, que arrancan primero (los demás siguen en orden alfabético): medidos con -v
# (2026-11-26: el primero, 16 s, es lo que tarda la suite entera)
SLOW = ("test_py_schematron.py", "test_zenodo.py", "test_corpus_check.py")


def files(names: list[str]) -> list[Path]:
    """The test files to run, the slowest first."""
    found = sorted(TESTS.glob("test_*.py"))
    if names:
        found = [p for p in found if any(fnmatch.fnmatch(p.name, n) or fnmatch.fnmatch(p.stem, n) for n in names)]
    return sorted(found, key=lambda p: SLOW.index(p.name) if p.name in SLOW else len(SLOW))


def run(path: Path, work: Path, env: dict) -> tuple[Path, int, str, float]:
    """PATH run by unittest in a process of its own: (path, exit status, output, seconds)."""
    own = work / path.stem
    own.mkdir(parents=True, exist_ok=True)
    # (una carpeta temporal para cada proceso: lo que deja uno no lo ve otro)
    env = {**env, "TMPDIR": str(own)}
    start = time.time()
    done = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(TESTS), "-t", str(TESTS),
                           "-p", path.name], cwd=ROOT, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, errors="replace")
    return path, done.returncode, done.stdout, time.time() - start


def counts(output: str) -> dict[str, int]:
    """{'tests': n, 'failures': n, 'errors': n, 'skipped': n} of unittest's summary ("Ran N tests in ...", then
    "OK (skipped=2)" or "FAILED (failures=1, errors=1)")."""
    found = {}
    ran = re.findall(r"^Ran (\d+) tests? in ", output, re.M)
    if ran:
        found["tests"] = int(ran[-1])
    verdicts = re.findall(r"^(?:OK|FAILED) \(([^)]*)\)", output, re.M)
    if verdicts:
        for k, n in re.findall(r"(\w+)=(\d+)", verdicts[-1]):
            found[k] = int(n)
    return found


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="tools/test.py",
                                     description="Run the tests of py-schematron, each file in a process of its "
                                                 "own, at once.")
    parser.add_argument("names", nargs="*", metavar="NAME", help="files or patterns to run (default: all)")
    parser.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 2,
                        help="how many at a time (default: the processors)")
    parser.add_argument("-v", "--verbose", action="store_true", help="show each file as it ends")
    args = parser.parse_args(argv)
    todo = files(args.names)
    if not todo:
        print("tools/test.py: no tests match " + " ".join(args.names), file=sys.stderr)
        return 2
    work = Path(tempfile.mkdtemp(prefix="py-schematron-tests-"))
    start = time.time()
    failed: list[tuple[Path, str]] = []
    totals: dict[str, int] = {}
    try:
        with ThreadPoolExecutor(max(1, args.jobs)) as pool:
            jobs = [pool.submit(run, path, work, dict(os.environ)) for path in todo]
            for n, job in enumerate(as_completed(jobs), 1):
                path, status, output, seconds = job.result()
                found = counts(output)
                for k, v in found.items():
                    totals[k] = totals.get(k, 0) + v
                # Un archivo sin pruebas no es un fallo (unittest sale con 5 desde 3.12)
                if status not in (0, 5):
                    failed.append((path, output))
                if args.verbose or status not in (0, 5):
                    mark = "ok" if status in (0, 5) else "FAILED"
                    print(f"[{n}/{len(todo)}] {path.name}: {found.get('tests', 0)} tests, {seconds:.1f}s, {mark}",
                          flush=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    for path, output in failed:
        print(f"\n{'=' * 70}\n{path.name}\n{'=' * 70}\n{output.rstrip()}")
    said = ", ".join(f"{v} {k}" for k, v in sorted(totals.items()))
    print(f"\n{said} ({len(todo)} files) in {time.time() - start:.1f}s: "
          + (f"FAILED ({len(failed)} files)" if failed else "OK"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
