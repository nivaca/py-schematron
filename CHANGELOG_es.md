# Registro de cambios

Los cambios notables de py-schematron, que se llamó py-xmlvalidate hasta
la 2.0. Las versiones publicadas, con sus archivos zip, están en
[Codeberg](https://codeberg.org/nivaca/py-schematron/releases) y
[GitHub](https://github.com/nivaca/py-schematron/releases).

Este registro cubre solo el programa principal. Las etiquetas
`vscode-v…` y `emacs-v…` de este repositorio pertenecen a la extensión de
VS Code y al paquete de Emacs, que vivieron aquí hasta la 1.17; ahora
tienen repositorio propio, cada uno con su registro de cambios:
[py-schematron-vscode](https://github.com/nivaca/py-schematron-vscode)
y [py-schematron.el](https://github.com/nivaca/py-schematron.el).

El programa principal se llamó `validate.py` hasta la 1.11,
`xmlvalidate.py` en la 1.12, `py-xmlvalidate.py` de la 1.13 a la 1.21, y
`py-schematron.py` desde la 2.0. Cada entrada usa los nombres de su
momento.

## 2.7 — 2026-11-21

- **`docs/THIRD-PARTY_es.md`** (y `docs/THIRD-PARTY.md`, en inglés): el
  software libre que usa py-schematron, y la licencia de cada uno: aquello
  con lo que corre (Python, saxonche, lxml, jing, las TEI Stylesheets) y
  lo que se usa para desarrollarlo y probarlo. Nada de eso se distribuye
  con el programa.
- Las descripciones de `docs/` se ponen al día con la 2.6.
- La validación es la misma.

## 2.6 — 2026-11-19

- **`--jobs N` valida varios documentos en paralelo**, N a la vez, en
  procesos separados, cada uno con su propio Saxon y las reglas ya
  leídas; 0 significa uno por procesador. Los resultados vuelven en el
  orden de los documentos, así que el JSON y el informe de texto son los
  mismos que con un solo proceso. Con 32 ediciones: 0,28 s en lugar de
  0,65 s, con 8.
- Esta versión trae también la 2.3 a la 2.5, que no se etiquetaron.

## 2.5 — 2026-11-19

- ruff corre en GitHub antes de las pruebas, con `ruff.toml` (solo sus
  reglas por omisión: errores reales, no estilo). Se corrigen sus seis
  hallazgos: cuatro lambdas asignadas a nombres y dos variables llamadas
  `l`.

## 2.4 — 2026-11-19

- `tools/corpus-check.py` compara también el tiempo de cada documento, y
  avisa de los que la nueva versión valida claramente más despacio (más
  de `--slower PERCENT` y de `--min-seconds S` a la vez, confirmado por
  una segunda medición). Una lentitud es solo un aviso.

## 2.3 — 2026-11-19

- Se eliminan `pyproject.toml` y `src/py_schematron/`: un esqueleto de
  paquete del comienzo del proyecto que nunca se usó. El programa son sus
  scripts, instalados con `installers/` o desde un clon.

## 2.2 — 2026-11-19

- **`py-schematron-all.py`** hace en Python lo que hacía el script de
  bash `py-schematron-all.sh`, con los mismos argumentos, mensajes y
  códigos de salida, así que las dos capas corren también en Windows.
  Ejecuta jing, o el `jing.jar` que indique `JING_JAR`, con Java, o si
  no lxml. `py-schematron-all.sh` se queda como envoltorio suyo.
- Los instaladores crean `py-schematron-all.py` (y el nombre antiguo) en
  Linux y macOS, y `py-schematron-all.cmd` en Windows.
- `tools/corpus-check.py` valida cada documento de un corpus con la
  última versión publicada y con la actual, y enumera los documentos
  cuyos resultados cambiaron. `tools/release.py` lo ejecuta cuando está
  definida `PY_SCHEMATRON_CORPUS`.
- 53 pruebas.

## 2.1 — 2026-11-19

- **Instaladores para Linux, macOS y Windows**: `installers/install.sh`
  e `installers/install.ps1` buscan un Python adecuado y ejecutan
  `installers/install.py`, que descarga la última versión publicada,
  crea un entorno de Python con saxonche y lxml, trae las dos hojas de
  estilo de TEI para `-o` y escribe las órdenes en `~/bin` o
  `~/.local/bin` (o `py-schematron.cmd` en el PATH del usuario en
  Windows). Si se ejecuta de nuevo, actualiza y conserva la caché de
  esquemas; `--uninstall` lo desinstala.
- `py-schematron-all.sh` toma su Python de `PY_SCHEMATRON_PYTHON`.
- La sección de instalación del README se reescribe, en inglés y en
  español.
- `install.ps1` ya no se detiene cuando al lanzador `py` le falta una de
  las versiones de Python que prueba.
- 45 pruebas; un trabajo en GitHub instala el programa en Linux, macOS y
  Windows.

## 2.0 — 2026-11-19

- **El proyecto pasa a llamarse py-schematron.** Los scripts son
  `py-schematron.py`, `py-schematron-all.sh` y
  `py-schematron-install.py`; el zip de cada versión es
  `py-schematron-v.X.Y.zip`. El instalador quita los enlaces de los
  nombres anteriores.
- La validación no cambia.

## 1.21 — 2026-11-18

- Con `--json`, los mensajes de progreso (descarga, caché, extracción,
  cosecha…) son también `events` en el informe, con clases estables y
  sus datos, y un error fatal sigue dando JSON con su mensaje. Los
  complementos leen esto en lugar de los mensajes en español de stderr.
- Cada infracción y cada error XPath dicen dónde está su regla (`rule`:
  archivo y línea del assert o del report, en el ODD, el RelaxNG o el
  archivo Schematron de donde viene).
- Las pruebas corren también todos los lunes en GitHub. 35 pruebas.

## 1.20 — 2026-11-18

- `-o` encuentra las TEI Stylesheets mediante `--stylesheets DIR`, la
  variable `TEI_STYLESHEETS` o el ajuste `stylesheets` del `config.toml`
  de ODD2RNG, antes que `odds/` y `common/` junto al script.
- Las pruebas corren en GitHub con cada push, con jing y las dos hojas
  de estilo. 33 pruebas.
- `tools/release.py` publica una versión con una sola orden:
  comprobaciones, pruebas, el zip, la etiqueta, el push a Codeberg y
  GitHub, y las dos publicaciones.

## 1.19 — 2026-11-18

- `--about` dice qué es el programa, quién lo hizo, su licencia y sus
  repositorios, y con qué corre: Python, saxonche, lxml, Saxon, la
  carpeta de la caché y las hojas de estilo de TEI para `-o`.

## 1.18 — 2026-11-18

- **Un conjunto de pruebas**: `tests/test_py_xmlvalidate.py`, 28 pruebas
  con unittest, sobre documentos y esquemas pequeños en una carpeta
  temporal.
- Los `let` de nivel de esquema y de pattern se evalúan con la raíz del
  documento como contexto, como manda ISO Schematron. Los `let` de nivel
  de regla conservan el nodo de la regla.
- Una regla que no puede evaluarse hace que el script salga con el
  código 3, porque el veredicto queda incompleto;
  `py-xmlvalidate-all.sh` lo informa con el código de salida 4.

## 1.17 — 2026-11-18

- La extensión de VS Code y el paquete de Emacs pasan a repositorios
  propios, cada uno con su copia del script. `tools/sync-plugins.py`
  copia en ellos cada nueva versión del script. El script mismo no
  cambia.

## 1.16 — 2026-11-17

- **Cada regla se evalúa en una sola llamada a Saxon** para todos sus
  nodos de contexto, en lugar de una llamada (y una compilación) por
  nodo. Si esa llamada falla, la regla se evalúa nodo por nodo, como
  antes. La edición latina de smed pasó de 11,5 s a 1,9 s, con
  resultados idénticos en 39 documentos.

## 1.15 — 2026-11-17

- Las pruebas de una regla se evalúan juntas, en una expresión por nodo,
  con sus variables `let` calculadas una sola vez, como pretende ISO
  Schematron; una prueba rota se sigue informando por separado. La
  edición latina de smed pasó de 13,9 s a 3,5 s, con resultados
  idénticos en 35 documentos.

## 1.14 — 2026-11-17

- `py-xmlvalidate-install.py` enlaza los scripts en `~/bin` (`--bin`
  para otra carpeta, `--force` para reemplazar otro enlace,
  `--uninstall`) y comprueba que python3 tenga saxonche y lxml.
- `py-xmlvalidate-all.sh` encuentra `py-xmlvalidate.py` aunque se lo
  llame mediante un enlace simbólico.

## 1.13 — 2026-11-17

- Los scripts toman el nombre del proyecto: `py-xmlvalidate.py` y
  `py-xmlvalidate-all.sh`. La validación no cambia.

## 1.12 — 2026-11-17

- El script pasa a llamarse `xmlvalidate.py` (y `validate-all.sh`,
  `xmlvalidate-all.sh`), por el nuevo nombre del proyecto,
  py-xmlvalidate. La validación no cambia.

## 1.11 — 2026-11-14

- El script comprueba que su Python sea 3.15 o posterior, y lo dice con
  claridad si no lo es.

## 1.10 — 2026-11-14

- Hace falta Python 3.15 o posterior (antes, 3.13).

## 1.9 — 2026-11-14

- Hace falta Python 3.13 o posterior (antes, 3.11).

## 1.8 — 2026-11-12

- `--as PATH` valida un documento como si estuviera en PATH (para las
  referencias relativas de `xml-model` y el nombre del informe), de modo
  que un editor pueda validar texto sin guardar a partir de una copia
  temporal.
- Las instrucciones `xml-model` se leen con tolerancia, así que un
  documento que aún no está bien formado recibe un error normal de "not
  well-formed" con su línea.

## 1.7 — 2026-11-12

- **Los archivos de la caché se escriben de forma atómica**, en un
  archivo temporal que luego se renombra. Dos ejecuciones simultáneas
  (como en VS Code después de recargar) podían leer un esquema que aún se
  estaba escribiendo, y en la caché quedaba una copia truncada. Las
  copias dañadas se detectan ahora y se descargan de nuevo, y una
  descarga que no es XML bien formado nunca entra en la caché.

## 1.6 — 2026-11-12

- `<name/>` en los mensajes ahora se interpola (antes se descartaba).
- `<value-of>` de un atributo da su valor, no el atributo entero
  (`corresp=" corresp="#" "`).
- Se conservan los espacios alrededor de un valor insertado.

## 1.5 — 2026-11-12

- **`--json`**: cada infracción con su pattern, contexto, rol, mensaje,
  línea y `xml:id`, los errores XPath por regla y la fuente del esquema.
  Un documento mal formado se convierte en una entrada de error.
- Una primera versión de la extensión de VS Code, que lee este informe.

## 1.4 — 2026-11-12

- **Se leen los `let` de nivel de esquema y de pattern.** Solo se leían
  los de nivel de regla, así que una prueba que usaba una variable
  declarada más arriba fallaba y se omitía, y un documento podía pasar
  con el código de salida 0.
- Se encuentran las líneas y los `xml:id` de los elementos sin espacio
  de nombres y de las infracciones en atributos y en texto.
- Los errores XPath se informan una vez por regla, con un recuento de
  nodos, y el resumen dice que el veredicto está incompleto.

## 1.0 a 1.3 — 2026-07-11 a 2026-07-20

Estas versiones no se etiquetaron.

- Primera versión (1.0): `validate.py` comprueba documentos TEI con las
  reglas Schematron de un ODD, extraídas con la hoja de estilo de TEI
  `extract-isosch.xsl` y ejecutadas con Saxon (saxonche), con
  first-match shadowing en cada pattern. El informe da un recuento
  completo por regla; `-v` enumera las infracciones con su línea y su
  `xml:id`, y `--max` limita solo esa lista.
- 1.1: se cosechan y se ejecutan las reglas embebidas en un esquema
  RelaxNG generado a partir de un ODD; `current()`; protecciones contra
  documentos mal formados y esquemas sin reglas. `validate-all.sh`
  comprueba la estructura RelaxNG con jing, y luego las reglas.
- 1.2: el esquema se encuentra en las instrucciones `<?xml-model?>` del
  documento, y un esquema remoto se descarga una vez a una caché, hasta
  `--refresh`.
- 1.3: los `<value-of>` de los mensajes se evalúan para cada infracción.
