# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-xmlvalidate. See the LICENSE file for details.
"""Tests of py-xmlvalidate.py, py-xmlvalidate-all.sh and
py-xmlvalidate-install.py.

    python3 -m unittest discover -s tests -v

They run the real programs on small documents and schemas written for each
case.  Each test class works in a temporary folder with its own copy of the
scripts, so the download cache (.schema-cache/) and the harvested schemas
never land in the repository.  They need the Python running them to have
saxonche and lxml.  The ODD tests need the TEI stylesheets in odds/ and
common/ next to py-xmlvalidate.py (they are skipped otherwise), and the tests
of py-xmlvalidate-all.sh need jing (on the PATH, in ~/bin, or named by the
environment variable JING).
"""

import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEI = "http://www.tei-c.org/ns/1.0"
SCH = "http://purl.oclc.org/dsdl/schematron"


def find_jing():
    for j in (os.environ.get("JING"), shutil.which("jing"), str(Path.home() / "bin" / "jing")):
        if j and Path(j).is_file() and os.access(j, os.X_OK):
            return j
    return None


JING = find_jing()


def sch(body, ns=True):
    """An ISO Schematron schema with the tei prefix and BODY inside."""
    return (f'<schema xmlns="{SCH}" queryBinding="xslt2">\n'
            + (f'  <ns prefix="tei" uri="{TEI}"/>\n' if ns else '')
            + body + '\n</schema>\n')


def tei(body):
    """A TEI document with BODY inside <TEI>."""
    return f'<TEI xmlns="{TEI}">\n{body}\n</TEI>\n'


RNG_PI = '<?xml-model href="{href}" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>\n'


def rng(max_p=2, rules=True):
    """A RelaxNG schema for TEI with p (and note inside p), and, if RULES,
    an embedded Schematron rule allowing at most MAX_P p."""
    rule = (f'''      <sch:pattern id="max-p">
        <sch:rule context="tei:TEI">
          <sch:assert test="count(tei:p) le {max_p}">A <sch:name/> may contain at most {max_p} p, found <sch:value-of select="count(tei:p)"/></sch:assert>
        </sch:rule>
      </sch:pattern>
''' if rules else '')
    return f'''<grammar xmlns="http://relaxng.org/ns/structure/1.0" xmlns:sch="{SCH}" ns="{TEI}">
  {'<sch:ns prefix="tei" uri="' + TEI + '"/>' if rules else ''}
  <start>
    <element name="TEI">
{rule}      <oneOrMore><element name="p"><optional><attribute name="n"/></optional><zeroOrMore><choice><text/><element name="note"><text/></element></choice></zeroOrMore></element></oneOrMore>
    </element>
  </start>
</grammar>
'''


class Base(unittest.TestCase):
    """A temporary folder with copies of the scripts; helpers to run them."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="pyxv-tests-"))
        cls.bin = cls.tmp / "bin"
        cls.bin.mkdir()
        for name in ("py-xmlvalidate.py", "py-xmlvalidate-all.sh", "py-xmlvalidate-install.py"):
            shutil.copy2(REPO / name, cls.bin / name)
        cls.script = cls.bin / "py-xmlvalidate.py"
        # (the user's own settings must not change the results: no ODD2RNG
        # configuration, no TEI_STYLESHEETS, unless a test sets them)
        (cls.tmp / "no-config").mkdir()
        cls.env = {k: v for k, v in os.environ.items() if k != "TEI_STYLESHEETS"}
        cls.env["ODD2RNG_CONFIG"] = str(cls.tmp / "no-config")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="case-", dir=self.tmp))

    def write(self, name, text):
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_script(self, *args, cwd=None, env=None):
        """Run py-xmlvalidate.py; return (exit code, stdout, stderr).
        ENV adds to (or, with None values, removes from) the environment."""
        environ = dict(self.env)
        for k, v in (env or {}).items():
            if v is None:
                environ.pop(k, None)
            else:
                environ[k] = v
        p = subprocess.run([sys.executable, str(self.script), *map(str, args)],
                           capture_output=True, text=True, cwd=cwd or self.dir, timeout=120,
                           env=environ)
        return p.returncode, p.stdout, p.stderr

    def check(self, *args, cwd=None, env=None):
        """Run with --json; return (exit code, the report, stderr)."""
        code, out, err = self.run_script("--json", *args, cwd=cwd, env=env)
        self.assertTrue(out.strip().startswith("{"), f"no JSON (exit {code}):\n{err}")
        return code, json.loads(out), err

    def doc(self, report):
        return report["documents"][0]

    def texts(self, report):
        return sorted(v["text"] for v in self.doc(report)["violations"])


# --------------------------------------------------------------- the basics

class TestBasics(Base):

    def test_version(self):
        code, out, _ = self.run_script("--version")
        self.assertEqual(code, 0)
        self.assertRegex(out, r"^py-xmlvalidate\.py \d+\.\d+")

    def test_about(self):
        code, out, _ = self.run_script("--about")
        self.assertEqual(code, 0)
        self.assertRegex(out.splitlines()[0], r"^py-xmlvalidate\.py \d+\.\d+$")
        self.assertIn("TEI Stylesheets para -o:", out)
        for expected in ("Nicolas Vaughan <nicolasvaughan@proton.me>", "GNU General Public License",
                         "https://codeberg.org/nivaca/py-xmlvalidate", "Python:", "saxonche:", "lxml:",
                         str(self.script.resolve())):
            self.assertIn(expected, out)

    def test_valid_document_exits_0(self):
        s = self.write("s.sch", sch('<pattern><rule context="tei:p"><assert test="true()">never</assert></rule></pattern>'))
        d = self.write("d.xml", tei("<p>a</p>"))
        code, report, _ = self.check("-s", s, d)
        self.assertEqual(code, 0)
        self.assertEqual(self.doc(report)["violations"], [])
        self.assertEqual(self.doc(report)["xpath_errors"], [])
        self.assertEqual(report["source"]["type"], "sch")

    def test_violations_exit_1_with_lines_and_ids(self):
        s = self.write("s.sch", sch('<pattern id="pat"><rule context="tei:p">'
                                    '<assert test="string-length(.) lt 3">too long</assert></rule></pattern>'))
        d = self.write("d.xml", f'<TEI xmlns="{TEI}" xml:id="root">\n<p>ok</p>\n<p xml:id="x">far too long</p>\n</TEI>\n')
        code, report, _ = self.check("-s", s, d)
        self.assertEqual(code, 1)
        [v] = self.doc(report)["violations"]
        self.assertEqual((v["pattern"], v["type"], v["line"], v["xml_id"]), ("pat", "assert", 3, "x"))

    def test_text_report(self):
        s = self.write("s.sch", sch('<pattern><rule context="tei:p"><report test=". = \'b\'">p is b</report></rule></pattern>'))
        d = self.write("d.xml", tei('<p>a</p>\n<p xml:id="pb">b</p>'))
        code, out, _ = self.run_script("-v", "-s", s, d)
        self.assertEqual(code, 1)
        self.assertIn("1 infracciones", out)
        self.assertRegex(out, r"l\.\s+3\s+\[pb\]\s+p is b")


# ------------------------------------------------------------------- rules

class TestRules(Base):

    def test_assert_report_role_and_messages(self):
        s = self.write("s.sch", sch('''<pattern id="p1"><rule context="tei:p">
  <assert test="@n" role="warning"><name/> lacks @n</assert>
  <report test="@n = '2'">n is "<value-of select="@n"/>" on <name/></report>
</rule></pattern>'''))
        d = self.write("d.xml", tei('<p n="1">a</p>\n<p n="2">b</p>\n<p>c</p>'))
        code, report, _ = self.check("-s", s, d)
        vs = self.doc(report)["violations"]
        self.assertEqual(sorted((v["type"], v["role"], v["text"]) for v in vs),
                         [("assert", "warning", "p lacks @n"), ("report", "", 'n is "2" on p')])
        # the static message, for grouping, has … for what is interpolated
        self.assertIn('n is "…" on …', [v["message"] for v in vs])

    def test_several_tests_on_one_rule(self):
        s = self.write("s.sch", sch('''<pattern><rule context="tei:p">
  <assert test="@n">needs n</assert>
  <assert test="string-length(.) lt 5">too long</assert>
  <report test=". = 'x'">is x</report>
</rule></pattern>'''))
        d = self.write("d.xml", tei('<p>x</p>\n<p n="1">much too long</p>'))
        _, report, _ = self.check("-s", s, d)
        self.assertEqual(self.texts(report), ["is x", "needs n", "too long"])

    def test_first_match_shadowing(self):
        s = self.write("s.sch", sch('''<pattern id="a">
  <rule context="tei:p[@n]"><report test="true()">specific</report></rule>
  <rule context="tei:p"><report test="true()">general</report></rule>
</pattern>
<pattern id="b"><rule context="tei:p"><report test="true()">other pattern</report></rule></pattern>'''))
        d = self.write("d.xml", tei('<p n="1">a</p>\n<p>b</p>'))
        _, report, _ = self.check("-s", s, d)
        self.assertEqual(self.texts(report), ["general", "other pattern", "other pattern", "specific"])

    def test_rule_lets_and_current(self):
        s = self.write("s.sch", sch('''<pattern><rule context="tei:p">
  <let name="len" value="string-length(.)"/>
  <assert test="$len lt 4">length <value-of select="$len"/></assert>
  <assert test="count(//tei:p[@n = current()/@n]) le 1">n <value-of select="@n"/> repeated</assert>
</rule></pattern>'''))
        d = self.write("d.xml", tei('<p n="1">abcdef</p>\n<p n="1">ab</p>'))
        _, report, _ = self.check("-s", s, d)
        self.assertEqual(self.texts(report), ["length 6", "n 1 repeated", "n 1 repeated"])

    def test_schema_and_pattern_lets_use_the_root(self):
        """ISO Schematron: schema- and pattern-level variables are evaluated
        with the document's root as context, not with the rule's node."""
        s = self.write("s.sch", sch('''<let name="total" value="count(*/tei:p)"/>
<pattern>
  <let name="first" value="string(*/tei:p[1])"/>
  <rule context="tei:p">
    <assert test="$total = 3">total seen as <value-of select="$total"/></assert>
    <report test=". = $first">first: <value-of select="$first"/></report>
  </rule>
</pattern>'''))
        d = self.write("d.xml", tei("<p>a</p>\n<p>b</p>\n<p>c</p>"))
        code, report, _ = self.check("-s", s, d)
        # evaluated per p, count(*/tei:p) would be 0 and the assert would fail 3 times
        self.assertEqual(self.texts(report), ["first: a"])
        self.assertEqual(code, 1)

    def test_pattern_lets_in_the_rule_context(self):
        s = self.write("s.sch", sch('''<pattern><let name="w" value="'x'"/>
  <rule context="tei:p[. = $w]"><report test="true()">p is <value-of select="$w"/></report></rule>
</pattern>'''))
        d = self.write("d.xml", tei("<p>x</p>\n<p>y</p>"))
        _, report, _ = self.check("-s", s, d)
        self.assertEqual(self.texts(report), ["p is x"])

    def test_pattern_lets_do_not_leak(self):
        s = self.write("s.sch", sch('''<pattern><let name="v" value="'one'"/>
  <rule context="tei:TEI"><report test="true()">first <value-of select="$v"/></report></rule></pattern>
<pattern><let name="v" value="'two'"/>
  <rule context="tei:TEI"><report test="true()">second <value-of select="$v"/></report></rule></pattern>'''))
        d = self.write("d.xml", tei("<p>a</p>"))
        _, report, _ = self.check("-s", s, d)
        self.assertEqual(self.texts(report), ["first one", "second two"])


# --------------------------------------------------------- rules that fail

class TestBrokenRules(Base):

    def test_xpath_error_is_reported_and_exits_3(self):
        s = self.write("s.sch", sch('''<pattern id="good"><rule context="tei:p"><report test=". = 'b'">p is b</report></rule></pattern>
<pattern id="bad"><rule context="tei:p"><assert test="xs:integer(.) gt 0">not a number</assert></rule></pattern>'''))
        d = self.write("d.xml", tei("<p>a</p>\n<p>b</p>"))
        code, report, err = self.check("-s", s, d)
        self.assertEqual(code, 3)                 # the verdict is incomplete
        self.assertEqual(self.texts(report), ["p is b"])
        errors = self.doc(report)["xpath_errors"]
        # (grouped by error text, which names the value: one entry per p here)
        self.assertEqual({(e["message"], e["context"]) for e in errors}, {("not a number", "tei:p")})
        self.assertEqual(sum(e["nodes"] for e in errors), 2)

    def test_text_mode_also_exits_3(self):
        s = self.write("s.sch", sch('<pattern><rule context="tei:p"><assert test="xs:integer(.) gt 0">nan</assert></rule></pattern>'))
        d = self.write("d.xml", tei("<p>a</p>"))
        code, _, err = self.run_script("-s", s, d)
        self.assertEqual(code, 3)
        self.assertIn("ERROR XPath", err)

    def test_one_broken_test_does_not_hide_the_others(self):
        """The rule's single call fails; its tests are then evaluated one by
        one, so the good test still reports and the broken one is counted."""
        s = self.write("s.sch", sch('''<pattern><rule context="tei:p">
  <assert test="xs:integer(.) gt 0">nan</assert>
  <report test=". = 'b'">p is b</report>
</rule></pattern>'''))
        d = self.write("d.xml", tei("<p>1</p>\n<p>b</p>"))
        code, report, _ = self.check("-s", s, d)
        self.assertEqual(code, 3)
        self.assertEqual(self.texts(report), ["p is b"])
        self.assertEqual(self.doc(report)["xpath_errors"][0]["nodes"], 1)

    def test_error_on_a_shadowed_node_is_not_an_error(self):
        s = self.write("s.sch", sch('''<pattern>
  <rule context="tei:p[. = 'b']"/>
  <rule context="tei:p"><assert test="xs:integer(.) ge 0">negative</assert></rule>
</pattern>'''))
        d = self.write("d.xml", tei("<p>1</p>\n<p>b</p>\n<p>-2</p>"))
        code, report, _ = self.check("-s", s, d)
        self.assertEqual(self.doc(report)["xpath_errors"], [])
        self.assertEqual(self.texts(report), ["negative"])
        self.assertEqual(code, 1)


# ----------------------------------------------------- malformed documents

class TestMalformed(Base):

    def test_malformed_document(self):
        s = self.write("s.sch", sch('<pattern><rule context="tei:p"><assert test="true()">x</assert></rule></pattern>'))
        d = self.write("d.xml", f'<TEI xmlns="{TEI}">\n<p>a <notde>x\n</p>\n</TEI>\n')
        code, report, _ = self.check("-s", s, d)
        self.assertEqual(code, 3)
        doc = self.doc(report)
        self.assertIn("Opening and ending tag mismatch: notde line 2 and p", doc["error"])
        self.assertEqual(doc["error_line"], 3)


# ------------------------------------------------------- where rules come from

class TestSources(Base):

    def test_relaxng_with_embedded_rules(self):
        r = self.write("schema.rng", rng(2))
        d = self.write("d.xml", tei("<p>a</p>\n<p>b</p>\n<p>c</p>"))
        code, report, _ = self.check("-r", r, d)
        self.assertEqual(code, 1)
        self.assertEqual(self.texts(report), ["A TEI may contain at most 2 p, found 3"])
        self.assertTrue((self.dir / "schema.harvested.sch").is_file())

    def test_relaxng_without_rules_exits_3(self):
        r = self.write("schema.rng", rng(rules=False))
        d = self.write("d.xml", tei("<p>a</p>"))
        code, _, err = self.run_script("-r", r, d)
        self.assertEqual(code, 3)
        self.assertIn("no contiene anotaciones Schematron", err)

    def test_xml_model_detection(self):
        self.write("schemas/schema.rng", rng(1))
        d = self.write("d.xml", RNG_PI.format(href="schemas/schema.rng") + tei("<p>a</p>\n<p>b</p>"))
        code, report, _ = self.check(d)
        self.assertEqual(code, 1)
        self.assertEqual(report["source"]["type"], "rng")
        self.assertEqual(Path(report["source"]["path"]), self.dir / "schemas" / "schema.rng")

    def test_no_schema_exits_3(self):
        d = self.write("d.xml", tei("<p>a</p>"))
        code, _, _ = self.run_script(d)
        self.assertEqual(code, 3)

    def test_as_resolves_hrefs_from_the_real_place(self):
        """--as: a copy elsewhere is checked as if it were at PATH (relative
        xml-model hrefs, the name in the report); this is how the editors
        check unsaved text."""
        self.write("project/schema.rng", rng(1))
        real = self.dir / "project" / "d.xml"
        copy = self.write("elsewhere/copy.xml", RNG_PI.format(href="schema.rng") + tei("<p>a</p>\n<p>b</p>"))
        code, report, _ = self.check("--as", real, copy)
        self.assertEqual(code, 1)
        self.assertEqual(Path(self.doc(report)["file"]), real)

    ODD = f'''<TEI xmlns="{TEI}" xmlns:sch="{SCH}" xml:lang="en">
<teiHeader><fileDesc><titleStmt><title>t</title></titleStmt><publicationStmt><p>p</p></publicationStmt><sourceDesc><p>s</p></sourceDesc></fileDesc></teiHeader>
<text><body><schemaSpec ident="t" start="TEI">
  <constraintSpec ident="short-p" scheme="schematron">
    <constraint><sch:rule context="tei:p"><sch:assert test="string-length(.) lt 3">p too long</sch:assert></sch:rule></constraint>
  </constraintSpec>
</schemaSpec></body></text></TEI>
'''

    def odd_case(self, *args, env=None):
        """Check a document against a small ODD; return (code, report, stderr)."""
        if not (REPO / "odds" / "extract-isosch.xsl").is_file():
            self.skipTest("the TEI stylesheets are not in odds/ and common/")
        o = self.write("o.odd", self.ODD)
        d = self.write("d.xml", tei("<p>ok</p>\n<p>too long</p>"))
        return self.check("-o", o, d, *args, env=env)

    def assert_odd_ok(self, result, origin):
        code, report, err = result
        self.assertEqual(code, 1, err)
        self.assertEqual(self.texts(report), ["p too long"])
        self.assertIn(origin, err)

    def test_odd_with_stylesheets_option(self):
        self.assert_odd_ok(self.odd_case("--stylesheets", REPO), "(--stylesheets)")

    def test_odd_with_environment_variable(self):
        self.assert_odd_ok(self.odd_case(env={"TEI_STYLESHEETS": str(REPO)}), "(TEI_STYLESHEETS)")

    def test_odd_with_odd2rng_configuration(self):
        conf = self.dir / "conf"
        conf.mkdir()
        (conf / "config.toml").write_text(f'stylesheets = "{REPO}"\n', encoding="utf-8")
        self.assert_odd_ok(self.odd_case(env={"ODD2RNG_CONFIG": str(conf)}), "config.toml")

    def test_odd_with_stylesheets_next_to_the_script(self):
        for folder in ("odds", "common"):
            if (REPO / folder).is_dir() and not (self.bin / folder).exists():
                shutil.copytree(REPO / folder, self.bin / folder)
        try:
            self.assert_odd_ok(self.odd_case(), "(junto al script)")
        finally:
            for folder in ("odds", "common"):
                shutil.rmtree(self.bin / folder, ignore_errors=True)

    def test_odd_without_stylesheets_exits_3(self):
        o = self.write("o.odd", self.ODD)
        d = self.write("d.xml", tei("<p>ok</p>"))
        code, _, err = self.run_script("-o", o, d)
        self.assertEqual(code, 3)
        self.assertIn("No encuentro las TEI Stylesheets", err)
        code, _, err = self.run_script("-o", o, d, "--stylesheets", self.dir)
        self.assertEqual(code, 3)
        self.assertIn("no tiene odds/extract-isosch.xsl", err)


# ------------------------------------------------------------------ the cache

class TestCache(Base):

    def test_harvest_is_reused_and_redone(self):
        r = self.write("schema.rng", rng(5))
        d = self.write("d.xml", tei("<p>a</p>"))
        harvested = self.dir / "schema.harvested.sch"
        _, _, err = self.check("-r", r, d)
        self.assertIn("[cosecha]", err)
        _, _, err = self.check("-r", r, d)
        self.assertIn("[caché] schema.harvested.sch está al día", err)
        # a newer schema is harvested again, and its rules apply
        r.write_text(rng(0), encoding="utf-8")
        os.utime(r, (time.time() + 5, time.time() + 5))
        code, report, err = self.check("-r", r, d)
        self.assertIn("[cosecha]", err)
        self.assertEqual(code, 1)
        # a damaged cached copy is detected and made again
        harvested.write_text("<schema xmlns=", encoding="utf-8")
        os.utime(harvested, (time.time() + 10, time.time() + 10))
        code, report, err = self.check("-r", r, d)
        self.assertEqual(code, 1, err)
        self.assertEqual(len(self.doc(report)["violations"]), 1)


class TestRemote(Base):
    """A schema referenced by URL, served by a small web server here."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.served = cls.tmp / "served"
        cls.served.mkdir()
        (cls.served / "remote.rng").write_text(rng(2), encoding="utf-8")
        handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(cls.served), **kw)
        http.server.SimpleHTTPRequestHandler.log_message = lambda *a: None
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}/remote.rng"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        super().tearDownClass()

    def test_download_cache_and_refresh(self):
        d = self.write("d.xml", RNG_PI.format(href=self.url) + tei("<p>a</p>\n<p>b</p>"))
        code, _, err = self.check(d)
        self.assertEqual(code, 0)
        self.assertIn("[descarga]", err)
        self.assertTrue(any((self.bin / ".schema-cache").glob("*-remote.rng")))
        # the schema changes upstream: the cached copy still applies...
        (self.served / "remote.rng").write_text(rng(1), encoding="utf-8")
        code, _, err = self.check(d)
        self.assertEqual(code, 0)
        self.assertNotIn("[descarga]", err)
        # ...until --refresh
        code, report, err = self.check("--refresh", d)
        self.assertIn("[descarga]", err)
        self.assertEqual(code, 1)
        self.assertEqual(self.texts(report), ["A TEI may contain at most 1 p, found 2"])


# ------------------------------------------------------ py-xmlvalidate-all.sh

@unittest.skipUnless(JING, "jing not found")
class TestAllLayers(Base):
    """The two-layer wrapper: 0 clean, 1 RelaxNG, 2 Schematron, 3 both, 4 the
    validation could not be completed."""

    def all(self, *args):
        # (the wrapper runs python3: the one running these tests comes first,
        # before jing's folder, which may hold another, as /usr/bin does)
        env = dict(os.environ, PATH=os.pathsep.join(
            [str(Path(sys.executable).parent), str(Path(JING).parent), os.environ.get("PATH", "")]))
        p = subprocess.run([str(self.bin / "py-xmlvalidate-all.sh"), *map(str, args)],
                           capture_output=True, text=True, cwd=self.dir, env=env, timeout=120)
        return p.returncode, p.stdout + p.stderr

    def test_verdicts(self):
        r = self.write("schema.rng", rng(2))
        cases = {"clean.xml": ("<p>a</p>", 0), "relaxng.xml": ("<p>a<bogus/></p>", 1),
                 "schematron.xml": ("<p>a</p><p>b</p><p>c</p>", 2),
                 "both.xml": ("<p>a</p><p>b</p><p>c<bogus/></p>", 3)}
        for name, (body, expected) in cases.items():
            d = self.write(name, tei(body))
            code, out = self.all(r, d)
            self.assertEqual(code, expected, f"{name}:\n{out}")

    def test_incomplete_schematron_is_4(self):
        r = self.write("schema.rng", rng(2).replace("count(tei:p) le 2", "xs:integer(tei:p[1]) gt 0"))
        d = self.write("d.xml", tei("<p>a</p>"))
        code, out = self.all(r, d)
        self.assertEqual(code, 4, out)


# ------------------------------------------------- py-xmlvalidate-install.py

class TestInstaller(Base):

    def install(self, *args):
        p = subprocess.run([sys.executable, str(self.bin / "py-xmlvalidate-install.py"), *map(str, args)],
                           capture_output=True, text=True, timeout=120)
        return p.returncode, p.stdout + p.stderr

    def test_links_and_uninstall(self):
        target = self.dir / "mybin"
        code, out = self.install("--bin", target)
        self.assertEqual(code, 0, out)
        for name in ("py-xmlvalidate.py", "py-xmlvalidate-all.sh"):
            link = target / name
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), (self.bin / name).resolve())
        code, out = self.install("--bin", target, "--uninstall")
        self.assertEqual(code, 0, out)
        self.assertEqual(list(target.iterdir()), [])

    def test_a_file_is_left_alone(self):
        target = self.dir / "mybin"
        target.mkdir()
        (target / "py-xmlvalidate.py").write_text("mine")
        code, out = self.install("--bin", target, "--force")
        self.assertEqual(code, 1)
        self.assertEqual((target / "py-xmlvalidate.py").read_text(), "mine")


if __name__ == "__main__":
    unittest.main()
