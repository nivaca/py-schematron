# Changelog

All notable changes to py-schematron, which was named py-xmlvalidate
until 2.0. The releases, with their zip files, are on
[Codeberg](https://codeberg.org/nivaca/py-schematron/releases) and
[GitHub](https://github.com/nivaca/py-schematron/releases).

This changelog covers the main program only. The tags `vscode-v…` and
`emacs-v…` of this repository belong to the VS Code extension and the
Emacs package, which lived here until 1.17; they now have repositories
of their own, with their own changelogs:
[py-schematron-vscode](https://github.com/nivaca/py-schematron-vscode)
and [py-schematron.el](https://github.com/nivaca/py-schematron.el).

The main program was called `validate.py` until 1.11, `xmlvalidate.py`
in 1.12, `py-xmlvalidate.py` from 1.13 to 1.21, and `py-schematron.py`
since 2.0. Each entry uses the names of its time.

## 2.7 — 2026-11-21

- **`docs/THIRD-PARTY.md`** (and `docs/THIRD-PARTY_es.md`, in Spanish):
  the open-source software py-schematron uses, and the licence of each:
  what it runs with (Python, saxonche, lxml, jing, the TEI Stylesheets)
  and what is used to develop and test it. None of it is distributed
  with the program.
- The descriptions in `docs/` are brought up to date with 2.6.
- The validation is the same.

## 2.6 — 2026-11-19

- **`--jobs N` validates several documents in parallel**, N at a time,
  in separate processes, each with its own Saxon and the rules already
  read; 0 means one per processor. The results come back in the order
  of the documents, so the JSON and the text report are the same as
  with one process. On 32 editions: 0.28 s instead of 0.65 s, with 8.
- This release also carries 2.3 to 2.5, which were not tagged.

## 2.5 — 2026-11-19

- ruff runs on GitHub before the tests, with `ruff.toml` (its default
  rules only: real errors, not style). Its six findings are fixed: four
  lambdas assigned to names and two variables called `l`.

## 2.4 — 2026-11-19

- `tools/corpus-check.py` also compares the time of each document, and
  warns about those the new version validates clearly slower (more than
  `--slower PERCENT` and `--min-seconds S` at once, confirmed by a
  second timing). A slowdown is only a warning.

## 2.3 — 2026-11-19

- `pyproject.toml` and `src/py_schematron/` are removed: a package
  scaffold from the start of the project, never used. The program is
  its scripts, installed with `installers/` or from a clone.

## 2.2 — 2026-11-19

- **`py-schematron-all.py`** does in Python what the bash script
  `py-schematron-all.sh` did, with the same arguments, messages and exit
  codes, so the two layers run on Windows too. It runs jing, or the
  `jing.jar` named by `JING_JAR` with Java, or else lxml.
  `py-schematron-all.sh` remains as a wrapper of it.
- The installers make `py-schematron-all.py` (and the old name) on Linux
  and macOS, and `py-schematron-all.cmd` on Windows.
- `tools/corpus-check.py` validates every document of a corpus with the
  last release and with the current version, and lists the documents
  whose results changed. `tools/release.py` runs it when
  `PY_SCHEMATRON_CORPUS` is set.
- 53 tests.

## 2.1 — 2026-11-19

- **Installers for Linux, macOS and Windows**: `installers/install.sh`
  and `installers/install.ps1` find a suitable Python and run
  `installers/install.py`, which downloads the latest release, makes a
  Python environment with saxonche and lxml, fetches the two TEI
  stylesheets for `-o`, and writes the commands in `~/bin` or
  `~/.local/bin` (or `py-schematron.cmd` on the user's PATH on Windows).
  Run again, it updates and keeps the schema cache; `--uninstall`
  removes it.
- `py-schematron-all.sh` takes its Python from `PY_SCHEMATRON_PYTHON`.
- The README's installation section is rewritten, in English and
  Spanish.
- `install.ps1` no longer stops when the `py` launcher lacks one of the
  Python versions it tries.
- 45 tests; a job on GitHub installs the program on Linux, macOS and
  Windows.

## 2.0 — 2026-11-19

- **The project is renamed py-schematron.** The scripts are
  `py-schematron.py`, `py-schematron-all.sh` and
  `py-schematron-install.py`; the release zip is
  `py-schematron-v.X.Y.zip`. The installer removes the links of the
  former names.
- The validation does not change.

## 1.21 — 2026-11-18

- With `--json`, the progress messages (download, cache, extraction,
  harvest…) are also `events` in the report, with stable kinds and
  their data, and a fatal error still gives JSON with its message. The
  plugins read these instead of the Spanish messages on stderr.
- Each violation and XPath error says where its rule is (`rule`: file
  and line of the assert or report, in the ODD, RelaxNG or Schematron
  file it came from).
- The tests also run every Monday on GitHub. 35 tests.

## 1.20 — 2026-11-18

- `-o` finds the TEI Stylesheets through `--stylesheets DIR`, the
  variable `TEI_STYLESHEETS` or the `stylesheets` setting of ODD2RNG's
  `config.toml`, before `odds/` and `common/` next to the script.
- The tests run on GitHub at every push, with jing and the two
  stylesheets. 33 tests.
- `tools/release.py` makes a release in one command: checks, tests, the
  zip, the tag, the push to Codeberg and GitHub, both releases.

## 1.19 — 2026-11-18

- `--about` says what the program is, who made it, its licence and
  repositories, and what it runs with: Python, saxonche, lxml, Saxon,
  the cache folder and the TEI stylesheets for `-o`.

## 1.18 — 2026-11-18

- **A test suite**: `tests/test_py_xmlvalidate.py`, 28 tests with
  unittest, on small documents and schemas in a temporary folder.
- Schema- and pattern-level `let`s are bound with the document's root
  as context, as ISO Schematron says. Rule-level `let`s keep the rule's
  node.
- A rule that cannot be evaluated makes the script exit with code 3,
  since the verdict is incomplete; `py-xmlvalidate-all.sh` reports it
  with exit code 4.

## 1.17 — 2026-11-18

- The VS Code extension and the Emacs package move to repositories of
  their own, each with its own copy of the script.
  `tools/sync-plugins.py` copies each new version of the script into
  them. The script itself does not change.

## 1.16 — 2026-11-17

- **Each rule is evaluated in one Saxon call** for all its context
  nodes, instead of one call (and one compilation) per node. If that
  call fails, the rule is evaluated node by node as before. The Latin
  edition of smed went from 11.5 s to 1.9 s, with identical results on
  39 documents.

## 1.15 — 2026-11-17

- A rule's tests are evaluated together, in one expression per node,
  with its `let` variables computed once, as ISO Schematron intends; a
  broken test is still reported on its own. The Latin edition of smed
  went from 13.9 s to 3.5 s, with identical results on 35 documents.

## 1.14 — 2026-11-17

- `py-xmlvalidate-install.py` links the scripts into `~/bin` (`--bin`
  for another folder, `--force` to replace another link, `--uninstall`)
  and checks that python3 has saxonche and lxml.
- `py-xmlvalidate-all.sh` finds `py-xmlvalidate.py` through a symbolic
  link.

## 1.13 — 2026-11-17

- The scripts take the project's name: `py-xmlvalidate.py` and
  `py-xmlvalidate-all.sh`. The validation does not change.

## 1.12 — 2026-11-17

- The script is renamed `xmlvalidate.py` (and `validate-all.sh`
  `xmlvalidate-all.sh`), for the project's new name, py-xmlvalidate.
  The validation does not change.

## 1.11 — 2026-11-14

- The script checks that its Python is 3.15 or later, and says so
  clearly if it is not.

## 1.10 — 2026-11-14

- Python 3.15 or later is needed (it was 3.13).

## 1.9 — 2026-11-14

- Python 3.13 or later is needed (it was 3.11).

## 1.8 — 2026-11-12

- `--as PATH` validates a document as if it were at PATH (for relative
  `xml-model` references and the report's name), so that an editor can
  validate unsaved text from a temporary copy.
- The `xml-model` instructions are read tolerantly, so a document that
  is not yet well-formed gets a normal "not well-formed" error with its
  line.

## 1.7 — 2026-11-12

- **Cached files are written atomically**, to a temporary file renamed
  into place. Two runs at once (as in VS Code after a reload) could read
  a schema still being written, and a truncated copy stayed in the
  cache. Damaged copies are now detected and downloaded again, and a
  download that is not well-formed XML is never cached.

## 1.6 — 2026-11-12

- `<name/>` in messages is now interpolated (it was dropped).
- `<value-of>` of an attribute gives its value, not the whole
  attribute (`corresp=" corresp="#" "`).
- The spaces around an inserted value are kept.

## 1.5 — 2026-11-12

- **`--json`**: every violation with its pattern, context, role,
  message, line and `xml:id`, the XPath errors per rule and the source
  of the schema. A malformed document becomes an error entry.
- A first version of the VS Code extension, which reads this report.

## 1.4 — 2026-11-12

- **Schema- and pattern-level `let`s are read.** Only rule-level ones
  were, so a test that used a variable declared higher up failed and
  was skipped, and a document could pass with exit code 0.
- Lines and `xml:id`s are found for elements without a namespace and
  for offences on attributes and text.
- XPath errors are reported once per rule, with a node count, and the
  summary says that the verdict is incomplete.

## 1.0 to 1.3 — 2026-07-11 to 2026-07-20

These versions were not tagged.

- First version (1.0): `validate.py` checks TEI documents against the
  Schematron rules of an ODD, extracted with the TEI stylesheet
  `extract-isosch.xsl` and run with Saxon (saxonche), with
  first-match shadowing in each pattern. The report gives a complete
  count per rule; `-v` lists the offences with their line and
  `xml:id`, and `--max` limits only that list.
- 1.1: the rules embedded in a RelaxNG schema generated from an ODD are
  harvested and run; `current()`; guards against malformed documents and
  schemas without rules. `validate-all.sh` checks the RelaxNG structure
  with jing, then the rules.
- 1.2: the schema is found in the document's `<?xml-model?>`
  instructions, and a remote schema is downloaded once to a cache, until
  `--refresh`.
- 1.3: the `<value-of>`s in messages are evaluated for each offence.
