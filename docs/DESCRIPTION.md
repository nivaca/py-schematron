How py-schematron was made
===========================

py-schematron checks TEI documents against the Schematron rules of
their schema, from the terminal, and reports every offence: how many
times each rule is broken and, for each offence, the line and the
`xml:id` of the nearest identifiable element.  It takes the rules from
an ODD, from an ISO Schematron file, or from a RelaxNG schema generated
from an ODD, which carries them embedded; it finds the schema by itself
in the document's `<?xml-model?>` instructions.  Its main program is
py-schematron.py (called validate.py until version 1.11, xmlvalidate.py
in 1.12, and py-xmlvalidate.py from 1.13 to 1.21, when the project was
py-xmlvalidate); a companion script, py-schematron-all.py, also
checks the structure with RelaxNG, and an extension for Visual Studio
Code shows the same results in the editor, underlined as you type.
Nicolas Vaughan made it in 2026, for the editions of the SMTrad project.
Here I explain how it was made, in nine stages.

It stands on four pieces of other people's work: Saxon, through saxonche
(Saxon C), which evaluates the rules with XPath 3.1; lxml, which finds
the lines and the `xml:id`s; jing, by James Clark, which checks the
RelaxNG structure; and the stylesheet `extract-isosch.xsl` of the TEI
Stylesheets, which extracts the Schematron of an ODD.  py-schematron is
free software, under the GNU General Public License, version 3 or later;
the software it uses, and the licence of each, are listed in
`docs/THIRD-PARTY.md`.

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
very rules that jing ignores.  py-schematron.py harvests them, without
duplicates, into a Schematron file of its own.  Harvesting had a subtle
bug: copied out of their context, the patterns could be written with
the wrong namespace and come back as nothing.  The fix cleans up the
namespace declarations, and a self-check reads the harvested file back
and compares the number of patterns before using it.

The same version added `current()` (the TEI Guidelines' rules use it),
guards against documents that are not well-formed and against schemas
without rules (which would approve anything), an exit code of its own
for problems of the environment, and a cache that is renewed when either
the schema or the script changes.  py-schematron-all.py runs the two
layers on the same RelaxNG file: the structure with jing (or lxml,
without it), then the rules with py-schematron.py, and combines their
verdicts in its exit code.  (It was a bash script, py-schematron-all.sh,
until 2.1; version 2.2 rewrote it in Python, so that it runs on Windows
too, where it can run jing with Java, and kept the old name as a
wrapper.)

3. Finding the schema
---------------------

From version 1.2 (July 2026) no schema has to be given:
py-schematron.py reads the document's `<?xml-model?>` instructions,
prefers a Schematron one, then a RelaxNG one, and downloads a remote
schema once, to a cache, until `--refresh` asks for it again.  What a
file is (ODD, Schematron or RelaxNG) is decided by its content, not by
its name.  py-schematron-all.py gained the same detection.  Version 1.3
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

Version 1.5 gave py-schematron.py a `--json` report, with every
offence, its line, `xml:id`, pattern and `role`, and the rules that
failed.  On it stands an extension for Visual Studio Code (`vscode/`),
which runs py-schematron.py, and jing for RelaxNG schemas, when a
document is opened or saved, and shows the offences as diagnostics:
underlined in the text, with the message on hover, and listed in the
Problems panel.  The extension carries its own copy of
py-schematron.py.

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
to the user's file, and py-schematron.py 1.8 has `--as`, which treats
that copy as if it were the real file, so relative `<?xml-model?>` paths
still work.  While a tag is half typed, the document is not well-formed
for a moment; py-schematron.py now reports that as an ordinary error on
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
py-schematron.py with its documentation, made from the files that git
tracks, and the extension's package.  The extension has a changelog, and
a GitHub workflow tests and packages it with each release tag and can
publish it in the Visual Studio Marketplace with Trusted Publishing,
without storing any key (0.5.3).  The repositories are now called
py-schematron.

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

Then came an Emacs package, `emacs/py-schematron.el`, for Emacs 31.  I
weighed four designs: a Flymake backend, a Flycheck checker, a language
server used through Eglot, and a mere report command.  Flymake won
because it is part of Emacs and asks for nothing else.  Speed was not an
argument for a server: Python with its libraries starts in about 15 ms,
and the seconds a large edition takes go into the rules themselves,
which is what version 1.15 had just reduced.  The backend works like
the extension: it writes the buffer to a private temporary copy, runs
py-schematron.py with `--json` and `--as`, and jing for RelaxNG
schemas, and turns both reports into Flymake diagnostics with their
layer and pattern; a new check kills the one still running.  Emacs 31
lets Flymake run only on files listed in `trusted-content`, and the
package keeps that rule: a document's `<?xml-model?>` chooses the
schema, and Saxon runs the schema's XPath, which can read files and
fetch URLs.  The package installs from the repository with
`package-vc-install` and uses the repository's own py-schematron.py.
Version 0.1.1 added Straight, which builds a package from links to its
clone; the package now follows the link to its own file to find the
script.  In real use, a document opened from the downloads folder was
never checked as I typed, and only the report showed its Schematron
errors: the file was not trusted, and the package said so in a passing
message that nobody reads.  Version 0.1.2 makes this hard to miss: a
warning in the `*Warnings*` buffer, once per file, with the line to add
to the init file; commands that explain why they cannot run; a note at
the end of the report; and `M-x py-schematron-trust-file`, which trusts
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
extension copied `../py-schematron.py` when it was packaged, and the
Emacs package ran the copy in the folder above its own.  Each now has a
repository of its own, py-schematron-vscode and py-schematron.el, on
GitHub and Codeberg, with its history extracted from this one and its
tags renamed (`vscode-v0.5.9` became `v0.5.9`; the extension versions
released only inside py-schematron releases got tags of their own).  I
weighed git submodules and chose against them: the dependency runs from
the plugins to the script, not the other way, and submodules would have
cost two commits for every change and broken the Emacs install.  Instead
each plugin carries a copy of `py-schematron.py` at the top of its
repository, and `tools/sync-plugins.py` copies each new version there, or
says whether the copies are the same.  The Emacs recipes became simpler
(no `:files`, no `:lisp-dir`), the trang installer went with the Emacs
package, and the publishing workflow with the extension.

Version 1.18 did three things that had waited.  The program got a test
suite of its own, with Python's unittest: until then each change was
checked by hand, by comparing the output before and after on small cases
and on the editions.  `let`s at schema and pattern level are now
evaluated with the document's root as context, as ISO Schematron says;
they used to be computed again for each node, with the node as context,
which is slower and gives a different answer for a variable written with
a relative path.  None of my schemas declares variables at those levels,
so no result changed.  And a rule that cannot be evaluated now makes the
script exit 3, since the verdict is incomplete; the question had been
open since version 1.4, when such rules started to be reported instead of
failing silently.  Version 1.19 added `--about`, which says what the
program is, who made it, its licence and repositories, and what it runs
with: Python, saxonche, lxml, Saxon, the cache.  The two plugins have an
About command of their own, which shows that output too, so a bug report
can say at once which versions were involved.  In 1.20, `-o` stopped
requiring copies of two TEI stylesheets next to the script: it takes the
folder of a full clone of the TEI Stylesheets from `--stylesheets`, from
`TEI_STYLESHEETS`, or from the configuration of ODD2RNG, the companion
script that makes the RelaxNG from an ODD, so that both programs use the
same stylesheets.  Version 1.21 made the JSON report the plugins' only
source: the progress messages that went to stderr in Spanish are also
events in the report, with stable English kinds, a fatal error gives
JSON with its message, and each violation says where its assert or
report is written.  That location is in the file one edits, the ODD or
the RelaxNG, not in the `.sch` made from it: the program finds the n-th
rule with the same test there, since extraction and harvest keep the
order.  On the five schemas of the editions every rule was found.  Both
plugins use it to jump from an error to its rule.

Version 2.0 renamed the project py-schematron, and 2.1 gave it
installers for Linux, macOS and Windows, on the model of py-foliation's:
a shell script and a PowerShell script find Python 3.15 or later and run
a common install.py, which downloads the latest release, makes a Python
environment of its own with saxonche and lxml, fetches the two TEI
stylesheets, and writes the commands.  Until then the program assumed a
Linux machine with a suitable python3 on the PATH.  Since I have no Mac
or Windows machine at hand, a job of the GitHub workflow installs it for
real on the three systems at every push, and validates a document with
the installed command.

9. Windows, and checks before each release
------------------------------------------

The installers made Windows a real target, and Windows was where the
remaining problems were.  py-schematron-all.sh was a shell script, so in
2.2 I rewrote it in Python as py-schematron-all.py; it finds jing as a
command, or as a `jing.jar` run with Java, which is how jing comes on
Windows.  The plugins could not do that yet: they ran a command called
`jing`, which Windows does not have.  The Emacs package (0.10.0) and the
extension (0.12.0) now accept a `jing.jar` in their settings, or take it
from the variable `JING_JAR`, and run it with `java -jar`.

The tests of the Emacs package on Windows found more.  Emacs there reads
the output of a process in the system's code page, so the accents in
the messages came out garbled; the package now reads it as UTF-8.  More
serious was that Flymake on Windows calls the backend for a file outside
`trusted-content`, where on Linux and macOS it does not: a document I
had not trusted was checked, and its schema run.  The backend relied on
Flymake for that rule, which the Flycheck checker did not, so now it
refuses such a file itself (0.10.1).  Its test calls the backend
directly, as Flymake does on Windows, and fails without the fix.

The other changes are checks.  `tools/corpus-check.py` validates all
the documents of my editions, 210 of them, with the last released
version and with the new one, and compares the results;
`tools/release.py` runs it before each release.  Since 2.4 it also
compares the time of each document, and warns about those the new
version validates clearly slower (by more than half, and by a quarter of
a second at least).  As the documents are validated in parallel, the
timings are noisy, so each document flagged is timed again alone before
it is reported.  In 2.5 the GitHub workflow began to run ruff on the
Python code, with only the rules that find real errors, and package-lint
on the Emacs package.  ruff found six small things in the program;
package-lint objected that the package changed nxml as soon as it was
loaded, so the fixes for nxml's datatypes now go in when the mode starts
in an nxml buffer.  Finally, 2.6 added `--jobs N`, which validates
several documents at once in separate processes, each with its own
Saxon (one cannot be shared between threads) and the rules already read.
The results come back in the order of the documents, so the report is
the same as with one; on 32 editions, eight processes took 0.28 seconds
instead of 0.65.

Testing
-------

The tests of the plugins now live in their repositories.  The extension
has 18 automated tests (`npm test`), run with Node's own
test runner.  They check how the reports of py-schematron.py and of
jing become diagnostics, the severities, where the underlines start and
end, and the error messages; one of them runs py-schematron.py from
beginning to end.  Another test (`npm run test:integration`) runs the
extension inside a real VS Code, without a screen and with a profile of
its own: it checks that the errors land on the right lines and are
visibly underlined, that a misspelt element is found, that unsaved
changes are validated, that *Refresh Schema* picks up a schema changed
on a small web server, that *Go to Rule* opens the schema at the
assert, and what *About* shows.  The unit tests also run on GitHub
Actions at every push, on Linux and Windows.

The Emacs package has 46 ERT tests, run in a batch Emacs.  Some need no
Python: they read the reports of py-schematron.py and jing, find the
script (also through a link like Straight's), and check the mending of
nxml's XSD datatypes in a fresh Emacs.  The others run the real programs on
documents made for each case.  Through Flymake they check the lines and
underlines, the typo, unsaved changes, a check cancelled by a newer one,
a remote schema refreshed from a small web server, a file outside
`trusted-content` (its warning, the commands that refuse, the note at
the end of its report, trusting it on request, and that the backend
itself refuses it), how jing is run (a program, a `jing.jar`, or the one
in `JING_JAR`), the report buffer
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

py-schematron.py has 56 tests (`python3 -m unittest discover -s
tests`), which run it, py-schematron-all.py and the installer on small
documents and schemas made for each case, in a temporary folder: rules
and messages, shadowing, `let`s at every level and `current()`, broken
rules and the exit codes, malformed text, the sources of rules (`-s`,
`-r`, an ODD, `<?xml-model?>`, `--as`), the cache and a damaged cached
copy, and a remote schema served by a small web server.  Run against
version 1.17, exactly the six tests of what 1.18 changed fail.  Each
change is also compared before and after on the editions and on the
example in `docs/example/`; the cache was
checked with the test of concurrent runs described above, and before
each release `tools/corpus-check.py` compares the results and the times
of the new version with those of the last one on the 210 documents of
my editions.  On GitHub, ruff checks the Python code and package-lint
the Emacs package before the tests, and the tests of both plugins run on
Windows as well as Linux, and on macOS for each release.  The zip of
each release is tried by unzipping it and running it, and a job of the
GitHub workflow installs the program with `installers/` and validates a
document with the installed command, on Linux and Windows at every push
and on macOS for each release.  The program has now around 2,700 lines
of Python and shell; the extension, around 800 of TypeScript, and the
Emacs package, around 1,550 of Emacs Lisp.
