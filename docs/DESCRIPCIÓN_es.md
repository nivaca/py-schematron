# py-xmlvalidate 1.16: descripción

## Análisis

py-xmlvalidate comprueba documentos TEI contra las reglas Schematron de su esquema, desde el terminal, e informa de cada infracción: cuántas veces se incumple cada regla y, para cada infracción, la línea y el `xml:id` del elemento identificable más cercano. Toma las reglas de un ODD, de un archivo ISO Schematron o de un esquema RelaxNG generado a partir de un ODD, que las lleva embebidas, y encuentra el esquema por sí solo en las instrucciones `<?xml-model?>` del documento. Su programa principal es py-xmlvalidate.py (hasta la versión 1.11 se llamó validate.py, y en la 1.12, xmlvalidate.py); otro, py-xmlvalidate-all.sh, comprueba además la estructura con RelaxNG, y una extensión para Visual Studio Code muestra los mismos resultados en el editor, subrayados mientras se escribe. Lo hizo Nicolas Vaughan en 2026, para las ediciones del proyecto SMTrad.

Se apoya en cuatro piezas ajenas: Saxon, a través de saxonche (Saxon C), que evalúa las reglas con XPath 3.1; lxml, que encuentra las líneas y los `xml:id`s; jing, de James Clark, que comprueba la estructura RelaxNG; y la hoja de estilo `extract-isosch.xsl` de las TEI Stylesheets, que extrae el Schematron de un ODD. py-xmlvalidate es software libre, bajo la Licencia Pública General de GNU, versión 3 o posterior.

Partí de oXygen, con el que se validaban los documentos del proyecto y que resultó fallar en silencio de tres maneras. Al estudiar esos fallos quedaron claros los requisitos. Lo primero era que el informe estuviera siempre completo, o dijera exactamente cuántas infracciones quedaban sin listar, y diera un recuento total verificable. Lo segundo, que las reglas se evaluaran igual que en oXygen, con XPath 3.1, respetando la semántica de ISO Schematron, y que un esquema sin reglas no aprobara nada en silencio.

Además, el programa tenía que servirle a cualquiera: desde el terminal, sobre muchos documentos a la vez, con los esquemas que de verdad usa el proyecto (un ODD propio y un RelaxNG publicado en GitHub), y sin tener que indicar el esquema cada vez. Más adelante se sumó otro requisito: ver los errores mientras se edita, en el editor, sin salir al terminal, con una instalación sencilla y sin tocar nunca los archivos del usuario.

## Diseño

py-xmlvalidate.py es un solo script, dividido en partes con un trabajo cada una. Las fuentes de reglas extraen el Schematron de un ODD o cosechan los patterns embebidos en un RelaxNG. La autodetección lee las instrucciones `<?xml-model?>`, descarga los esquemas remotos a un caché propio y clasifica cada esquema por su contenido. La lectura del esquema reúne patterns, reglas, asserts, reports y `let`s, y los mensajes con sus `<value-of>` y `<name/>`. La validación evalúa las reglas con Saxon y busca las líneas y los `xml:id`s con lxml. El informe sale en texto para el terminal o en JSON (`--json`) para otros programas.

py-xmlvalidate-all.sh valida en dos capas sobre el mismo RelaxNG: primero la estructura, con jing (o con lxml si jing no está), y luego las reglas, con py-xmlvalidate.py; combina los dos veredictos en su código de salida.

La extensión está en `vscode/`: `extension.ts` se ocupa de la integración con el editor (cuándo validar, los procesos, los diagnósticos, la barra de estado y las órdenes), y `parse.ts` de leer los informes de py-xmlvalidate.py y de jing, sin depender del editor, para poder probarla aparte. Al empaquetarse, la extensión lleva su propia copia de py-xmlvalidate.py.

El paquete de Emacs está en `emacs/`: `py-xmlvalidate.el` lee los mismos informes con funciones sin efectos, que se prueban aparte, y lanza los procesos desde un backend de Flymake. No lleva copia del script: se instala clonando el repositorio y usa el py-xmlvalidate.py de este. Straight arma el paquete con enlaces a su clon, y desde la versión 0.1.1 el paquete sigue el enlace de su propio archivo para encontrar el script.

Los archivos del proyecto son estos:

- `py-xmlvalidate.py`: el validador (662 líneas).
- `py-xmlvalidate-all.sh`: las dos capas, RelaxNG y Schematron (156 líneas).
- `vscode/`: la extensión (`src/extension.ts`, `src/parse.ts`), sus pruebas (`src/test/`), su icono (`images/`), su registro de cambios (`CHANGELOG.md`) y su README.
- `emacs/`: el paquete de Emacs (`py-xmlvalidate.el`), sus pruebas (`test/`) y su README.
- `py-xmlvalidate-install.py`: enlaza los dos scripts en `~/bin`, para llamarlos por su nombre desde cualquier carpeta.
- `tools/screenshots.py`: hace las capturas de los README.
- `tools/install-trang.py`: descarga trang de las versiones publicadas de jing-trang, comprueba su SHA-1 y lo instala en `~/bin` (o en `~/.local/bin` si no existe), para que el paquete de Emacs pueda darle a nxml el esquema.
- `tools/bundle-zip.py`: hace los archivos de cada versión en `dist/`: un zip de py-xmlvalidate.py con su documentación y el paquete de la extensión (`.vsix`).
- `.github/workflows/publish-vscode.yml`: prueba, empaqueta y publica la extensión con cada etiqueta de versión.
- `docs/`: las descripciones, las capturas (`img/`) y un ejemplo autónomo (`example/`): un texto TEI breve con errores deliberados y un esquema RelaxNG pequeño con reglas Schematron embebidas.

Las reglas se ejecutan tal como están en el esquema, con sus mensajes y sus `role`, para que quien conozca el esquema reconozca cada infracción sin aprender nada nuevo; el informe nombra el pattern de cada una.

Para que el programa responda rápido, lo que se extrae, se cosecha o se descarga se guarda en un caché, que se rehace solo cuando cambia el esquema o el propio script. La extensión guarda sus ajustes (el intérprete de Python, jing, el esquema, cuándo validar) en los ajustes de VS Code.

## Implementación

Está escrito en Python 3.15 o superior, con dos bibliotecas, saxonche y lxml; la extensión, en TypeScript. Son 12 archivos de código, unas 2450 líneas.

Antes se probaron implementaciones hechas. pyschematron tardaba minutos sobre el corpus, por las búsquedas `//*[@xml:id=…]` de las reglas; jing no admite `queryBinding="xslt2"`; SchXslt exigía administrar más archivos XSLT. Saxon, a través de saxonche, ya era una dependencia del proyecto, corre a la velocidad de C, y su XPath 3.1 es un superconjunto del de oXygen, de modo que `matches()`, `tokenize()`, `some`/`every` y `let` se comportan igual.

Los contextos relativos de las reglas se evalúan sobre todo el documento, y dentro de cada pattern cada nodo se compara solo con la primera regla cuyo contexto lo abarca, como prescribe ISO Schematron. Los `let` del esquema, del pattern y de la regla se traducen a `let $x := … return …` de XPath, y `current()`, que es de XSLT, se liga al nodo de contexto. Desde la versión 1.15, los tests de una regla se evalúan juntos, con sus variables calculadas una sola vez por nodo: la edición latina, de unas 26 000 líneas, pasó así de 13,9 a 3,5 segundos. La versión 1.16 encontró el resto del tiempo en otra parte: Saxon compila cada expresión que recibe, y el script lo llamaba una vez por nodo, de modo que la larga expresión de la regla de `<app>` se compilaba 2054 veces. Ahora cada regla se evalúa en una sola llamada para todos sus nodos; medidas una tras otra en la misma máquina, la edición latina pasó de 11,5 a 1,9 segundos, con resultados idénticos en 39 documentos. Los mensajes interpolan sus `<value-of>` (su valor de cadena) y sus `<name/>` para cada infracción. Una regla que no puede evaluarse se informa una sola vez, con el aviso de que el veredicto está incompleto, y un esquema sin reglas termina con un código de salida propio en lugar de aprobarlo todo.

### Caché

Al recargar VS Code, dos validaciones arrancaron a la vez, y una leyó el esquema descargado mientras la otra lo estaba escribiendo: "Premature end of data". Peor aún, la copia truncada quedaba en el caché, y todas las corridas siguientes fallaban igual.

Desde la versión 1.7, todo lo que se guarda en caché (esquemas descargados, reglas cosechadas y extraídas) se escribe en un archivo temporal que luego se renombra, de modo que quien lo lea ve o ningún archivo o uno completo. Una copia dañada que haya dejado una versión anterior se detecta y se reemplaza, y una descarga que no sea XML nunca se guarda. La comprobación de la cosecha se hace sobre los bytes, antes de escribir, así que un esquema mutilado nunca llega al caché.

Para probarlo, un proceso volvió a descargar el esquema durante 20 segundos mientras otros tres validaban: la versión anterior falló 88 veces de 635; la nueva, ninguna.

### Proceso y distribución

El trabajo pasó por ocho etapas: primero el informe sin tope, con el ODD del proyecto (versión 1.0); luego la cosecha de reglas del RelaxNG y las dos capas de py-xmlvalidate-all.sh (1.1); la detección del esquema por `<?xml-model?>` y los mensajes interpolados (1.2 y 1.3); la corrección de reglas que nunca se ejecutaban y de los mensajes (1.4 y 1.6); el informe JSON y la extensión de VS Code, con la elección del intérprete y la barra de estado (1.5; extensión 0.1 a 0.3); las escrituras atómicas del caché (1.7); la validación mientras se escribe (1.8; extensión 0.4 y 0.4.1), y por último la orden *Refresh Schema*, el icono, las capturas, la licencia GPL y los archivos de cada versión (extensión 0.4.2 a 0.5.3).

El código se gestiona con git, en un solo repositorio publicado en GitHub (https://github.com/nivaca/py-xmlvalidate) y en Codeberg (https://codeberg.org/nivaca/py-xmlvalidate). Cada versión se etiqueta (`vX.Y` cuando cambia py-xmlvalidate.py, `vscode-vA.B.C` cuando cambia solo la extensión) y se publica en las dos forjas, con el zip de py-xmlvalidate.py y el paquete de la extensión, que hace `tools/bundle-zip.py`. Con cada etiqueta, un flujo de trabajo de GitHub prueba y empaqueta la extensión, y puede publicarla en el Visual Studio Marketplace con Trusted Publishing, sin guardar ninguna clave.

## La extensión de VS Code

La extensión ejecuta `py-xmlvalidate.py --json`, y jing si el esquema es RelaxNG, al abrir un documento, al guardarlo y mientras se escribe, cuando la escritura se detiene (medio segundo por defecto, un ajuste). Las infracciones aparecen como diagnósticos: subrayadas en el texto, con el mensaje al pasar el puntero, y en el panel Problemas, con la capa que encontró cada una (Schematron, RelaxNG o XML). Una regla con `role="warning"` o `role="info"` se muestra con esa gravedad.

El texto sin guardar se escribe en una carpeta temporal privada, nunca junto al archivo del usuario, y py-xmlvalidate.py lo trata con `--as` como si fuera el archivo real, para que las rutas relativas de `<?xml-model?>` sigan funcionando. Mientras una etiqueta está a medio escribir, el error de buena formación aparece en su línea. Si el nombre de un elemento está mal escrito (`<notde>` por `<note>`), el analizador solo lo nota donde la etiqueta se cierra, a veces decenas de líneas después; por eso se marca también la línea donde se abrió, y jing, que sigue corriendo, señala el elemento. jing indica la posición justo después de la etiqueta, a menudo al final de la línea, lo que daba subrayados sin ancho que VS Code no dibuja; ahora se subraya la propia etiqueta.

Una barra de estado muestra el resultado del archivo actual: validando, limpio, el número de problemas o un fallo; sin ella, un archivo limpio parecía una extensión que no funcionaba. Si el Python configurado no tiene saxonche, la extensión dice cuál probó y ofrece elegir otro, comprobándolo antes de guardarlo. La orden *Refresh Schema* vuelve a descargar un esquema remoto que haya cambiado y valida de nuevo los archivos abiertos.

## El paquete de Emacs

Para Emacs 31 había cuatro diseños posibles: un backend de Flymake, un comprobador de Flycheck, un servidor de lenguaje usado con Eglot y una simple orden de informe. Elegí Flymake porque viene con Emacs y no pide nada más. La velocidad no justificaba un servidor: Python con sus bibliotecas arranca en unos 15 ms, y los segundos que tarda una edición grande se van en las reglas mismas, que es lo que la versión 1.15 acababa de reducir.

El backend trabaja como la extensión. Escribe el búfer en una copia temporal privada, ejecuta py-xmlvalidate.py con `--json` y `--as`, y jing si el esquema es RelaxNG, y convierte los dos informes en diagnósticos de Flymake con su capa y su pattern; una comprobación nueva mata la que sigue en marcha. `M-x py-xmlvalidate-report` muestra el informe de texto con enlaces a las líneas, y `M-x py-xmlvalidate-check-setup` dice si Python, saxonche, lxml, el script y jing están donde deben.

Emacs 31 solo deja que Flymake corra sobre los archivos de `trusted-content`, y el paquete respeta esa regla en lugar de declararse inofensivo: el `<?xml-model?>` de un documento elige el esquema, y Saxon ejecuta el XPath de ese esquema, que puede leer archivos y pedir URL. Basta poner ahí las carpetas de las ediciones propias.

En el uso real, un documento abierto desde la carpeta de descargas nunca se comprobaba mientras se escribía, y solo el informe mostraba sus errores Schematron: el archivo no era de confianza, y el paquete lo decía en un mensaje fugaz que nadie lee. La versión 0.1.2 lo hace difícil de pasar por alto: un aviso en el búfer `*Warnings*`, una vez por archivo, con la línea que hay que añadir al archivo de inicio; órdenes que explican por qué no pueden ejecutarse; una nota al final del informe; y `M-x py-xmlvalidate-trust-file`, que confía en el archivo o en su carpeta después de preguntar.

La versión 0.2.0 añadió dos cosas, después de mirar cómo uso Emacs de verdad. Compruebo el código con Flycheck, no con Flymake, así que los búferes de XML se veían y se comportaban distinto del resto; el paquete registra ahora también un comprobador de Flycheck, que se elige cuando Flycheck está instalado, con la misma regla de confianza que impone Flymake (Flycheck no tiene una propia). Y nxml-mode, el editor de XML, no tenía esquema: no sabe leer `<?xml-model?>`, así que usaba uno «vacío» que lo permite todo, y su completado no ofrecía nada. Después de cada comprobación, el paquete convierte ahora el esquema RelaxNG del documento a la sintaxis compacta con trang, lo guarda en un caché y se lo da a nxml, que entonces completa los elementos y atributos que el esquema permite y valida la estructura por sí mismo, al instante. Hubo que sortear dos cosas. La orden de nxml para poner un esquema ofrece escribir un `schemas.xml` junto al documento, así que el paquete usa la función que hay debajo. Y las tablas de nxml para las categorías Unicode `\p{P}` y `\p{S}` omiten puntuación corriente como `#`, de modo que rechazaba 94 atributos `ed="#U2"` de la edición latina que jing acepta; en la copia del esquema para nxml, el patrón de palabra de TEI enumera además esos caracteres. trang no estaba instalado y Fedora no lo empaqueta, así que `tools/install-trang.py` lo descarga de las versiones publicadas de jing-trang, comprueba su SHA-1 y lo instala en `~/bin`, como suele instalarse jing (o en `~/.local/bin` si no hay `~/bin`); para el esquema smed, su salida es idéntica a la de la copia que trae oXygen.

## Lo que vino de oXygen

oXygen falla en silencio de tres maneras: muestra como mucho 100 avisos de validación y descarta el resto sin decirlo; cuando dos reglas de un pattern comparten contexto, solo se ejecuta la primera (*first-match shadowing*); y una regla vacía por error puede invalidar el esquema entero. Un documento podía parecer limpio sin estarlo.

py-xmlvalidate.py elimina el primer fallo por diseño: el recuento por regla está siempre completo, y `--max` limita solo el detalle, nunca el recuento, y dice cuántas infracciones quedaron sin listar. Los otros dos se vuelven visibles con ese recuento total, y un esquema sin reglas termina con un error en lugar de aprobarlo todo. De oXygen viene también la decisión de evaluar con XPath 3.1, el mismo lenguaje de su binding, para que una regla dé el mismo resultado en los dos.

## Validación

La extensión tiene 11 pruebas automáticas (`npm test`), que corren con el ejecutor de pruebas de Node. Comprueban cómo los informes de py-xmlvalidate.py y de jing se convierten en diagnósticos, las gravedades, dónde empiezan y terminan los subrayados y los mensajes de error; una de ellas ejecuta py-xmlvalidate.py de principio a fin. Otra prueba (`npm run test:integration`) ejecuta la extensión dentro de un VS Code real, sin pantalla y con un perfil propio: comprueba que los errores caigan en las líneas correctas y se vean subrayados, que se encuentre un elemento mal escrito, que se valide el texto sin guardar y que *Refresh Schema* recoja un esquema cambiado en un pequeño servidor web. Las pruebas de la extensión corren también en GitHub Actions con cada etiqueta de versión.

El paquete de Emacs tiene 31 pruebas de ERT, que corren en un Emacs sin pantalla. Ocho no necesitan Python: leen los informes de py-xmlvalidate.py y de jing, buscan el script (también a través de un enlace como los de Straight) y adaptan el esquema compacto para nxml. Las otras veintitrés ejecutan los programas reales sobre documentos hechos para cada caso. Mediante Flymake comprueban las líneas y los subrayados, el elemento mal escrito, el texto sin guardar, la comprobación cancelada por otra más nueva, el esquema remoto refrescado desde un pequeño servidor web, el archivo fuera de `trusted-content` (su aviso, las órdenes que se niegan, la nota al final de su informe y la confianza concedida a petición), el búfer del informe con sus enlaces, y que no quede ningún proceso ni copia temporal. Mediante Flycheck, cargado de mi propia instalación, comprueban las mismas líneas, capas y subrayados, el texto sin guardar, la regla de confianza y que al apagar el modo Flycheck quede como estaba. Con trang, comprueban que nxml recibe el esquema y ofrece sus elementos, acepta `ed="#U2"`, encuentra un elemento fuera de lugar, reutiliza la conversión guardada, nunca reemplaza un esquema elegido a mano y recupera su esquema vacío. El paquete se probó también instalándolo con `package-vc-install` y con Straight en perfiles vacíos, y sobre la edición latina: la comprobación de Flycheck tardó 2,6 segundos, nxml tuvo el esquema 0,7 segundos después y no encontró errores, y dentro de un `<rdg>` ofreció los 123 elementos que el esquema permite allí.

py-xmlvalidate.py se comprueba con documentos y esquemas pequeños hechos para cada caso (*shadowing*, `let`s en cada nivel, espacios de nombres, atributos, texto mal formado, las tres fuentes de reglas), comparando el resultado antes y después de cada cambio, y con el ejemplo de `docs/example/`. Las capturas de los README se rehacen con `tools/screenshots.py` y se revisan a ojo, y el zip de cada versión se prueba descomprimiéndolo y ejecutándolo.

## Plataforma

Funciona en Linux. py-xmlvalidate.py necesita Python 3.15 o superior, con saxonche y lxml; jing es opcional, para la capa estructural, y la ruta del ODD necesita además `extract-isosch.xsl` y `common/functions.xsl` de las TEI Stylesheets junto al script. El paquete de Emacs necesita Emacs 31 o posterior. La extensión necesita Visual Studio Code 1.85 o posterior; en Linux conviene la versión nativa (RPM o deb) y no la Flatpak, que no ve el Python ni el jing del sistema.

Al ser Python y una extensión de VS Code, debería funcionar también en Windows y macOS, pero allí no se ha probado. Solo necesita internet para descargar los esquemas remotos la primera vez, o al refrescarlos, y nunca escribe en los documentos que valida.

## Ambiente

Lo desarrollé en Fedora Linux 45 con KDE Plasma, con Python 3.15, Node.js 22, Visual Studio Code y Emacs 31, y con git, con repositorios en GitHub y Codeberg. Las capturas se hacen con Xvfb, ImageMagick y Pillow.

Para usar py-xmlvalidate.py basta descomprimir el zip de una versión publicada, instalar saxonche y lxml (`pip install saxonche lxml`, mejor en un entorno virtual) y ejecutar `python3 py-xmlvalidate.py documento.xml`. Para la extensión, se descarga el `.vsix` de la misma versión y se instala con `code --install-extension`; en sus ajustes, `schematron.pythonPath` indica el Python que tiene saxonche y lxml. El paquete de Emacs se instala con `package-vc-install`, como explica `emacs/README.md`. Las descargas de esquemas quedan en `.schema-cache/`, junto al script.
