How py-xmlvalidate was made
===========================

py-xmlvalidate checks TEI documents against the Schematron rules of
their schema, from the terminal, and reports every offence: how many
times each rule is broken and, for each offence, the line and the
`xml:id` of the nearest identifiable element.  It takes the rules from
an ODD, from an ISO Schematron file, or from a RelaxNG schema generated
from an ODD, which carries them embedded; it finds the schema by itself
in the document's `<?xml-model?>` instructions.  Its main program is
py-xmlvalidate.py (called validate.py until version 1.11, and
xmlvalidate.py in 1.12); a companion script, py-xmlvalidate-all.sh, also
checks the structure with RelaxNG, and an extension for Visual Studio
Code shows the same results in the editor, underlined as you type.
Nicolas Vaughan made it in 2026, for the editions of the SMTrad project.
Here I explain how it was made, in eight stages.

It stands on four pieces of other people's work: Saxon, through saxonche
(Saxon C), which evaluates the rules with XPath 3.1; lxml, which finds
the lines and the `xml:id`s; jing, by James Clark, which checks the
RelaxNG structure; and the stylesheet `extract-isosch.xsl` of the TEI
Stylesheets, which extracts the Schematron of an ODD.  py-xmlvalidate is
free software, under the GNU General Public License, version 3 or later.

Nicolas Vaughan is Associate Professor of Literature at the School of Arts
and Humanities of the Universidad de los Andes, Bogotá, Colombia.

1. A report without a cap
-------------------------

The project's documents were validated in oXygen, which turned out to
fail silently in three ways.  It shows at most 100 validation highlights
and drops the rest without a word; when two rules of a pattern share a
context, only the first one runs (first-match shadowing); and a rule
that is empty by mistake can invalidate the whole schema.  A document
could look clean when it was not.

The first version (1.0, July 2026) answered the first of these by
design.  It extracts the Schematron of the project's ODD with the TEI
stylesheet `extract-isosch.xsl`, keeps the result in a cache that is
renewed when the ODD changes, and runs the rules itself: patterns,
rules, asserts, reports and `let`s, with first-match shadowing inside
each pattern, as ISO Schematron prescribes.  The report gives a count
per rule, always complete; `-v` lists the offences with their line and
`xml:id`, and `--max` limits only that list, never the count, and says
how many offences were left out.

Ready-made implementations were tried first.  pyschematron took minutes
on the corpus, because of the `//*[@xml:id=…]` searches of the rules;
jing does not support `queryBinding="xslt2"`; SchXslt needed more XSLT
files to manage.  Saxon, through saxonche, was already a dependency of
the project, runs at the speed of C, and its XPath 3.1 is a superset of
oXygen's, so `matches()`, `tokenize()`, `some`/`every` and `let` behave
the same way.

2. RelaxNG, and two layers
--------------------------

Version 1.1 (July 2026) added a second source of rules: a RelaxNG schema
generated from an ODD carries the Schematron patterns embedded in it, the
very rules that jing ignores.  py-xmlvalidate.py harvests them, without
duplicates, into a Schematron file of its own.  Harvesting had a subtle
bug: copied out of their context, the patterns could be written with
the wrong namespace and come back as nothing.  The fix cleans up the
namespace declarations, and a self-check reads the harvested file back
and compares the number of patterns before using it.

The same version added `current()` (the TEI Guidelines' rules use it),
guards against documents that are not well-formed and against schemas
without rules (which would approve anything), an exit code of its own
for problems of the environment, and a cache that is renewed when either
the schema or the script changes.  py-xmlvalidate-all.sh runs the two
layers on the same RelaxNG file: the structure with jing (or lxml,
without it), then the rules with py-xmlvalidate.py, and combines their
verdicts in its exit code.

3. Finding the schema
---------------------

From version 1.2 (July 2026) no schema has to be given:
py-xmlvalidate.py reads the document's `<?xml-model?>` instructions,
prefers a Schematron one, then a RelaxNG one, and downloads a remote
schema once, to a cache, until `--refresh` asks for it again.  What a
file is (ODD, Schematron or RelaxNG) is decided by its content, not by
its name.  py-xmlvalidate-all.sh gained the same detection.  Version 1.3
made the messages more useful: the `<value-of>`s inside them are
evaluated for each offence, so a message names, for example, the exact
sigla that are missing.

4. Rules that never ran
-----------------------

A review of the code in November 2026 found the most serious kind of
problem: rules that silently did nothing.  Only the `let`s of a rule
were read, not those of its schema or its pattern, so a rule that used a
pattern's variable failed to evaluate on every node and was skipped, and
a document could pass with exit code 0.  Version 1.4 adds those `let`s,
and reports rules that fail to evaluate once each, with a warning that
the verdict is incomplete.  The same version found the lines of elements
without a namespace, and of offences on attributes.

Version 1.6 corrected the messages: `<name/>`, which the project's schema
uses 96 times, had been dropped ("Error: has corresp…"); a `<value-of>`
of an attribute printed the whole attribute, `corresp=" corresp="#" "`,
instead of its value; and the spaces around an inserted value were
changed.

5. A Visual Studio Code extension
---------------------------------

Version 1.5 gave py-xmlvalidate.py a `--json` report, with every
offence, its line, `xml:id`, pattern and `role`, and the rules that
failed.  On it stands an extension for Visual Studio Code (`vscode/`),
which runs py-xmlvalidate.py, and jing for RelaxNG schemas, when a
document is opened or saved, and shows the offences as diagnostics:
underlined in the text, with the message on hover, and listed in the
Problems panel.  The extension carries its own copy of
py-xmlvalidate.py.

The next versions made it easier to set up and to read.  When the Python
it uses lacks saxonche, it says which Python it tried, and offers to
choose another, checking it before saving the setting (0.2).  A status
bar item shows the result of the current file: a spinner while it
works, a tick when the file is clean, the number of problems, or a red
"failed" when it cannot run (0.3).  Without it, a clean file looked
exactly like an extension that did not work.

6. Two validations at once
--------------------------

After a reload, VS Code validated two files at the same moment, and one
of them read the downloaded schema while the other was still writing it:
"Premature end of data".  Worse, the truncated copy stayed in the cache,
and every later run failed in the same way.  Version 1.7 writes every
cached file (downloaded schemas, harvested and extracted rules) to a
temporary file and renames it into place, so a reader sees either no file
or a whole one; a damaged copy left by an older version is detected and
replaced, and a download that is not XML is never kept.  In a test that
re-downloaded the schema for 20 seconds while three other processes
validated, the old version failed 88 times in 635; the new one, never.

7. Validating as you type
-------------------------

Version 0.4 of the extension validates the text being edited, unsaved
changes included, once typing pauses (half a second by default, a
setting).  The text is written to a private temporary folder, never next
to the user's file, and py-xmlvalidate.py 1.8 has `--as`, which treats
that copy as if it were the real file, so relative `<?xml-model?>` paths
still work.  While a tag is half typed, the document is not well-formed
for a moment; py-xmlvalidate.py now reports that as an ordinary error on
its line, not as a failure.

Testing the extension inside a real VS Code showed two problems that
tests against a simulated editor had missed.  A misspelt element, such
as `<notde>` for `<note>`, was reported where the parser noticed it,
dozens of lines later; now the line where the unclosed tag was opened is
flagged too, and jing, which still runs, points straight at it.  And
jing reports the position just after a start tag, often at the end of a
line, which gave underlines of no width that VS Code does not draw; now
the tag itself is underlined (0.4.1).

8. Finishing touches
--------------------

A remote schema is downloaded once, so a new version of it was not seen
until the cache was emptied by hand; the extension's *Refresh Schema*
command downloads it again and validates the open files (0.5).  The
extension has an icon: an XML tag whose slash is a tick, above the red
underline it draws.  `tools/screenshots.py` makes the screenshots of the
READMEs, as in my other projects: a real session in the terminal, drawn
like Konsole, and a real VS Code on a hidden display, with a profile of
its own, so nothing appears on the screen and the user's settings are
not touched.  Both use `docs/example/`, a short TEI text with deliberate
mistakes and a small RelaxNG schema with Schematron rules embedded in it.

Last, the project changed from the MIT licence to the GPL, version 3 or
later (0.5.2), like my other projects.  Each release now carries two
files, which `tools/bundle-zip.py` makes in `dist/`: a zip of
py-xmlvalidate.py with its documentation, made from the files that git
tracks, and the extension's package.  The extension has a changelog, and
a GitHub workflow tests and packages it with each release tag and can
publish it in the Visual Studio Marketplace with Trusted Publishing,
without storing any key (0.5.3).  The repositories are now called
py-xmlvalidate.

Version 1.15 made the checks faster.  Each test of a rule used to be
evaluated on its own, computing the rule's `<let>` variables again every
time; now all the tests of a rule are evaluated in one call per node, with
the variables computed once, as ISO Schematron intends.  On the Latin
edition, about 26,000 lines, the check went from 13.9 to 3.5 seconds,
with the same results; a rule whose combined call fails is still evaluated
test by test, so that a broken test is reported on its own.

Version 1.16 found the rest of that time somewhere else.  Saxon compiles
every expression it is given, and the script still called it once per
node, so the `<app>` rule's long expression was compiled 2,054 times:
9 of its 9.6 seconds.  Now each rule is evaluated in a single call over
all its context nodes, which returns each node's path, for shadowing,
and its test results.  Measured one after the other on the same machine,
the Latin edition went from 11.5 to 1.9 seconds, and 39 documents gave
identical results.  A rule whose single call fails is evaluated node by
node, as before.

Then came an Emacs package, `emacs/py-xmlvalidate.el`, for Emacs 31.  I
weighed four designs: a Flymake backend, a Flycheck checker, a language
server used through Eglot, and a mere report command.  Flymake won
because it is part of Emacs and asks for nothing else.  Speed was not an
argument for a server: Python with its libraries starts in about 15 ms,
and the seconds a large edition takes go into the rules themselves,
which is what version 1.15 had just reduced.  The backend works like
the extension: it writes the buffer to a private temporary copy, runs
py-xmlvalidate.py with `--json` and `--as`, and jing for RelaxNG
schemas, and turns both reports into Flymake diagnostics with their
layer and pattern; a new check kills the one still running.  Emacs 31
lets Flymake run only on files listed in `trusted-content`, and the
package keeps that rule: a document's `<?xml-model?>` chooses the
schema, and Saxon runs the schema's XPath, which can read files and
fetch URLs.  The package installs from the repository with
`package-vc-install` and uses the repository's own py-xmlvalidate.py.
Version 0.1.1 added Straight, which builds a package from links to its
clone; the package now follows the link to its own file to find the
script.  In real use, a document opened from the downloads folder was
never checked as I typed, and only the report showed its Schematron
errors: the file was not trusted, and the package said so in a passing
message that nobody reads.  Version 0.1.2 makes this hard to miss: a
warning in the `*Warnings*` buffer, once per file, with the line to add
to the init file; commands that explain why they cannot run; a note at
the end of the report; and `M-x py-xmlvalidate-trust-file`, which trusts
the file or its folder after asking.

Version 0.2.0 added two things, after looking at how I actually use
Emacs.  I check code with Flycheck, not Flymake, so XML buffers looked
and behaved unlike the rest; the package now registers a Flycheck checker
as well, chosen when Flycheck is installed, with the same trust rule that
Flymake imposes (Flycheck has none of its own).  And nxml-mode, the XML
editor, had no schema at all: it cannot read `<?xml-model?>`, so it used
a "vacuous" schema that allows anything, and its completion offered
nothing.  After each check, the package now converts the document's
RelaxNG schema to the compact syntax with trang, keeps it in a cache and
gives it to nxml, which then completes the elements and attributes the
schema allows and validates the structure itself, at once.  Two things
had to be worked around.  nxml's command for setting a schema offers to
write a `schemas.xml` next to the document, so the package uses the
function underneath it.  And nxml's tables for the Unicode categories
`\p{P}` and `\p{S}` leave out ordinary punctuation such as `#`, so it
rejected 94 `ed="#U2"` attributes in the Latin edition that jing accepts;
in nxml's copy of the schema, TEI's word pattern also lists those
characters explicitly.  trang was not installed, and Fedora does not
package it, so `tools/install-trang.py` downloads it from the jing-trang
releases, checks its SHA-1 and installs it in `~/bin`, as jing usually
is (or in `~/.local/bin` when there is no `~/bin`); for the smed
schema its output is identical to that of the copy inside oXygen.

Version 1.17 moved the two plugins out.  They had lived in the `vscode/`
and `emacs/` folders of this repository, and both depended on it: the
extension copied `../py-xmlvalidate.py` when it was packaged, and the
Emacs package ran the copy in the folder above its own.  Each now has a
repository of its own, py-xmlvalidate-vscode and py-xmlvalidate-emacs, on
GitHub and Codeberg, with its history extracted from this one and its
tags renamed (`vscode-v0.5.9` became `v0.5.9`; the extension versions
released only inside py-xmlvalidate releases got tags of their own).  I
weighed git submodules and chose against them: the dependency runs from
the plugins to the script, not the other way, and submodules would have
cost two commits for every change and broken the Emacs install.  Instead
each plugin carries a copy of `py-xmlvalidate.py` at the top of its
repository, and `tools/sync-plugins.py` copies each new version there, or
says whether the copies are the same.  The Emacs recipes became simpler
(no `:files`, no `:lisp-dir`), the trang installer went with the Emacs
package, and the publishing workflow with the extension.

Testing
-------

The tests of the plugins now live in their repositories.  The extension
has 11 automated tests (`npm test`), run with Node's own
test runner.  They check how the reports of py-xmlvalidate.py and of
jing become diagnostics, the severities, where the underlines start and
end, and the error messages; one of them runs py-xmlvalidate.py from
beginning to end.  Another test (`npm run test:integration`) runs the
extension inside a real VS Code, without a screen and with a profile of
its own: it checks that the errors land on the right lines and are
visibly underlined, that a misspelt element is found, that unsaved
changes are validated, and that *Refresh Schema* picks up a schema
changed on a small web server.  The tests of the extension also run on
GitHub Actions with each release tag.

The Emacs package has 31 ERT tests, run in a batch Emacs.  Eight need no
Python: they read the reports of py-xmlvalidate.py and jing, find the
script (also through a link like Straight's), and adapt the compact
schema for nxml.  The other twenty-three run the real programs on
documents made for each case.  Through Flymake they check the lines and
underlines, the typo, unsaved changes, a check cancelled by a newer one,
a remote schema refreshed from a small web server, a file outside
`trusted-content` (its warning, the commands that refuse, the note at
the end of its report, and trusting it on request), the report buffer
and its links, and that no process or temporary copy is left behind.
Through Flycheck, loaded from my own installation, they check the same
lines, layers and underlines, unsaved text, the trust rule, and that
turning the mode off leaves Flycheck as it found it.  With trang, they
check that nxml gets the schema and offers its elements, accepts
`ed="#U2"`, finds a misplaced element, reuses the cached conversion,
never replaces a schema chosen by hand, and gets its vacuous schema back.
The package was also installed with `package-vc-install` and with
Straight into empty profiles, and tried on the Latin edition: Flycheck's
check took 2.6 seconds, nxml had the schema 0.7 seconds later and found
no errors, and inside an `<rdg>` it offered the 123 elements the schema
allows there.

py-xmlvalidate.py is checked on small documents and schemas made for each
case (shadowing, `let`s at every level, namespaces, attributes,
malformed text, the three sources of rules), compared before and after
each change, and on the example in `docs/example/`; the cache was
checked with the test of concurrent runs described above.  The zip of
each release is tried by unzipping it and running it.  The program has
now 12 files of code, around 2,450 lines.
