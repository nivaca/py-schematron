# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-schematron. See the LICENSE file for details.
"""Tests of tools/corpus-check.py, on a small corpus made here."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "tools" / "corpus-check.py"
SCH = "http://purl.oclc.org/dsdl/schematron"
TEI = "http://www.tei-c.org/ns/1.0"

SCHEMA = f"""<schema xmlns="{SCH}" queryBinding="xslt2">
  <ns prefix="tei" uri="{TEI}"/>
  <pattern id="one-p"><rule context="tei:TEI">
    <assert test="count(tei:p) le 1">at most one p</assert>
  </rule></pattern>
</schema>
"""

PI = ('<?xml-model href="../schemas/s.sch" type="application/xml" '
      'schematypens="http://purl.oclc.org/dsdl/schematron"?>\n')

# An "old version" that finds nothing anywhere: it prints an empty report.
FAKE_OLD = """import json, sys
print(json.dumps({"version": "0", "schema": "", "source": {"path": "", "type": "sch"},
                  "documents": [{"file": sys.argv[-1], "violations": [], "xpath_errors": []}]}))
"""


class TestCorpusCheck(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="pysch-corpus-test-")
        self.dir = Path(self._tmp.name)
        corpus = self.dir / "corpus"
        (corpus / "schemas").mkdir(parents=True)
        (corpus / "texts").mkdir()
        (corpus / "schemas" / "s.sch").write_text(SCHEMA, encoding="utf-8")
        self.docs = {
            "good.xml": PI + f'<TEI xmlns="{TEI}"><p>a</p></TEI>\n',
            "bad.xml": PI + f'<TEI xmlns="{TEI}">\n<p>a</p>\n<p>b</p>\n</TEI>\n',
            "no-schema.xml": f'<TEI xmlns="{TEI}"><p>a</p></TEI>\n',      # (not in the corpus)
        }
        for name, text in self.docs.items():
            (corpus / "texts" / name).write_text(text, encoding="utf-8")
        self.corpus = corpus
        self.stamps = {p: (p.stat().st_mtime_ns, p.read_bytes()) for p in corpus.rglob("*.xml")}

    def tearDown(self):
        # the documents are only read, never written
        for p, (mtime, data) in self.stamps.items():
            self.assertEqual((p.stat().st_mtime_ns, p.read_bytes()), (mtime, data), p)
        self._tmp.cleanup()

    def run_tool(self, *args, env=None):
        p = subprocess.run([sys.executable, str(TOOL), *map(str, args)], capture_output=True,
                           text=True, timeout=300, env={**os.environ, **(env or {})})
        return p.returncode, p.stdout + p.stderr

    def test_the_same_version_gives_the_same_results(self):
        code, out = self.run_tool("--corpus", self.corpus, "--old", REPO / "py-schematron.py",
                                  "--jobs", "2", "--verbose")
        self.assertEqual(code, 0, out)
        self.assertIn("2 documents;", out)                    # (no-schema.xml left out)
        self.assertIn("2 of 2 documents give the same result; 0 changed.", out)

    def test_a_changed_result_is_reported(self):
        old = self.dir / "old.py"
        old.write_text(FAKE_OLD, encoding="utf-8")
        code, out = self.run_tool("--old", old, env={"PY_SCHEMATRON_CORPUS": str(self.corpus)})
        self.assertEqual(code, 1, out)
        self.assertIn("CHANGED", out)
        self.assertIn("bad.xml", out)
        self.assertIn("violations: 0 -> 1", out)
        self.assertIn("+ line 2: at most one p", out)        # (the TEI element)
        self.assertIn("1 of 2 documents give the same result; 1 changed.", out)

    def test_no_corpus(self):
        code, out = self.run_tool("--old", REPO / "py-schematron.py",
                                  env={"PY_SCHEMATRON_CORPUS": ""})
        self.assertEqual(code, 2)
        self.assertIn("no corpus", out)


if __name__ == "__main__":
    unittest.main()
