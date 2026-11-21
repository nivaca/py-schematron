Open-source software used by py-schematron
==========================================

py-schematron is free software, under the GNU General Public License,
version 3 or later (GPL-3.0-or-later).  It is made of its own scripts only:
none of the programs below is copied into this repository or into the
release zip.  They are installed separately, by pip, by the installers in
`installers/`, or by the system's package manager, and each keeps its own
licence.

What the program runs with
--------------------------

| Software | What it is used for | Licence |
|---|---|---|
| [Python](https://www.python.org/) 3.15 or later, with its standard library | The language of every script | Python Software Foundation License (PSF-2.0) |
| [saxonche](https://pypi.org/project/saxonche/) (SaxonC-HE, by Saxonica) | Evaluates the Schematron rules with XPath 3.1, and runs the TEI stylesheet that extracts the rules of an ODD | Mozilla Public License 2.0 (MPL-2.0) |
| [lxml](https://lxml.de/) | Reads the documents and schemas, finds the line and the `xml:id` of each offence, and is the RelaxNG fallback of py-schematron-all when jing is missing | BSD-3-Clause |
| [libxml2](https://gitlab.gnome.org/GNOME/libxml2) and [libxslt](https://gitlab.gnome.org/GNOME/libxslt) | The C libraries under lxml (included in its wheels) | MIT |
| [jing](https://relaxng.org/jclark/jing.html), by James Clark (optional) | Checks the RelaxNG structure in py-schematron-all | BSD-3-Clause (Thai Open Source Software Center) |
| A Java runtime, such as [OpenJDK](https://openjdk.org/) (only with jing) | Runs jing | GPL-2.0 with the Classpath Exception (OpenJDK) |
| [TEI Stylesheets](https://github.com/TEIC/Stylesheets): `odds/extract-isosch.xsl` and `common/functions.xsl` (only for `-o`) | Extract the Schematron rules of an ODD.  They are not distributed with py-schematron: the user points to a copy of the TEI Stylesheets | Dual licence: BSD-2-Clause or Creative Commons Attribution-ShareAlike 3.0 (CC-BY-SA-3.0), at the user's choice |

The jing distributed by its project (the `jing.jar` used on Windows, or
through `JING_JAR`) carries some libraries of its own, such as Xerces and
Saxon 9; their licences are in the `doc/` folder of that distribution.

What is used to develop and test it
-----------------------------------

These are not needed to run py-schematron, and none of them is distributed
with it.

| Software | What it is used for | Licence |
|---|---|---|
| [Ruff](https://docs.astral.sh/ruff/) | Lint of the Python code (`ruff.toml`), in the tests on GitHub | MIT |
| [Pillow](https://python-pillow.github.io/) | Draws the screenshot of the terminal (`tools/screenshots.py`) | MIT-CMU |
| [Hack](https://sourcefoundry.org/hack/) font | The font of that screenshot | MIT, with the Bitstream Vera License for the glyphs it comes from |
| [Xvfb](https://www.x.org/) (X.Org) | The hidden display where VS Code runs for its screenshots | MIT/X11 |
| [ImageMagick](https://imagemagick.org/) | Takes those screenshots (`import`) | ImageMagick License |
| [Node.js](https://nodejs.org/) and npm | Compile the VS Code extension for its screenshots | MIT (Node.js), Artistic-2.0 (npm) |
| [Visual Studio Code](https://code.visualstudio.com/) | Shown in the screenshots of the extension | MIT (the Code - OSS source); Microsoft's builds have their own product licence |
| [GitHub Actions](https://github.com/features/actions): `actions/checkout`, `actions/setup-python` | Run the tests and the installers on Linux, macOS and Windows | MIT |

The VS Code extension and the Emacs package have repositories of their own
([py-schematron-vscode](https://github.com/nivaca/py-schematron-vscode),
[py-schematron.el](https://github.com/nivaca/py-schematron.el)), each with
its own list.
