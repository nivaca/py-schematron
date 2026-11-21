Software libre que usa py-schematron
====================================

py-schematron es software libre, bajo la Licencia Pública General de GNU,
versión 3 o posterior (GPL-3.0-or-later).  Lo forman solo sus propios
scripts: ninguno de los programas de abajo está copiado en este repositorio
ni en el zip de las versiones.  Se instalan aparte, con pip, con los
instaladores de `installers/` o con el gestor de paquetes del sistema, y
cada uno conserva su licencia.

Con qué corre el programa
-------------------------

| Software | Para qué se usa | Licencia |
|---|---|---|
| [Python](https://www.python.org/) 3.15 o posterior, con su biblioteca estándar | El lenguaje de todos los scripts | Python Software Foundation License (PSF-2.0) |
| [saxonche](https://pypi.org/project/saxonche/) (SaxonC-HE, de Saxonica) | Evalúa las reglas Schematron con XPath 3.1 y ejecuta la hoja de estilo de TEI que extrae las reglas de un ODD | Mozilla Public License 2.0 (MPL-2.0) |
| [lxml](https://lxml.de/) | Lee los documentos y los esquemas, halla la línea y el `xml:id` de cada infracción, y es el RelaxNG de reserva de py-schematron-all cuando falta jing | BSD-3-Clause |
| [libxml2](https://gitlab.gnome.org/GNOME/libxml2) y [libxslt](https://gitlab.gnome.org/GNOME/libxslt) | Las bibliotecas en C bajo lxml (incluidas en sus wheels) | MIT |
| [jing](https://relaxng.org/jclark/jing.html), de James Clark (opcional) | Revisa la estructura RelaxNG en py-schematron-all | BSD-3-Clause (Thai Open Source Software Center) |
| Un entorno de Java, como [OpenJDK](https://openjdk.org/) (solo con jing) | Ejecuta jing | GPL-2.0 con la Classpath Exception (OpenJDK) |
| [TEI Stylesheets](https://github.com/TEIC/Stylesheets): `odds/extract-isosch.xsl` y `common/functions.xsl` (solo para `-o`) | Extraen las reglas Schematron de un ODD.  No se distribuyen con py-schematron: el usuario indica una copia de las TEI Stylesheets | Doble licencia: BSD-2-Clause o Creative Commons Atribución-CompartirIgual 3.0 (CC-BY-SA-3.0), a elección del usuario |

El jing que distribuye su proyecto (el `jing.jar` que se usa en Windows o
con `JING_JAR`) trae algunas bibliotecas propias, como Xerces y Saxon 9;
sus licencias están en la carpeta `doc/` de esa distribución.

Con qué se desarrolla y se prueba
---------------------------------

Nada de esto hace falta para usar py-schematron, y nada se distribuye con
él.

| Software | Para qué se usa | Licencia |
|---|---|---|
| [Ruff](https://docs.astral.sh/ruff/) | Revisión del código Python (`ruff.toml`), en las pruebas de GitHub | MIT |
| [Pillow](https://python-pillow.github.io/) | Dibuja la captura del terminal (`tools/screenshots.py`) | MIT-CMU |
| La fuente [Hack](https://sourcefoundry.org/hack/) | La letra de esa captura | MIT, con la Bitstream Vera License para los glifos de los que procede |
| [Xvfb](https://www.x.org/) (X.Org) | La pantalla oculta donde corre VS Code para sus capturas | MIT/X11 |
| [ImageMagick](https://imagemagick.org/) | Toma esas capturas (`import`) | ImageMagick License |
| [Node.js](https://nodejs.org/) y npm | Compilan la extensión de VS Code para sus capturas | MIT (Node.js), Artistic-2.0 (npm) |
| [Visual Studio Code](https://code.visualstudio.com/) | Aparece en las capturas de la extensión | MIT (el código de Code - OSS); las compilaciones de Microsoft tienen su propia licencia de producto |
| [GitHub Actions](https://github.com/features/actions): `actions/checkout`, `actions/setup-python` | Ejecutan las pruebas y los instaladores en Linux, macOS y Windows | MIT |

La extensión de VS Code y el paquete de Emacs tienen repositorios propios
([py-schematron-vscode](https://github.com/nivaca/py-schematron-vscode),
[py-schematron.el](https://github.com/nivaca/py-schematron.el)), cada uno
con su lista.
