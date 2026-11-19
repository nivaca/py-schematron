#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-schematron. See the LICENSE file for details.
"""py-schematron-all.py — validación bicapa de documentos TEI desde el terminal:
  capa 1: estructura RelaxNG   (jing; si no está instalado, lxml)
  capa 2: reglas Schematron    (py-schematron.py -r, cosechadas del mismo .rng)

Uso:
  py-schematron-all.py [-v] [-m N] esquema.rng documento.xml [más.xml ...]
  py-schematron-all.py [-v] [-m N] documento.xml [más.xml ...]
    -v    modo detallado de la capa Schematron (líneas y xml:ids)
    -m N  máximo de infractores detallados (pasa --max N a py-schematron.py)

Si el primer argumento no es un esquema RelaxNG (se clasifica por
CONTENIDO, no por extensión), se asume que todo son documentos y el .rng se
AUTODETECTA de la PI <?xml-model?> del primero, con la resolución y el
caché de descargas (.schema-cache/) de py-schematron.py. La capa Schematron
corre entonces con la autodetección propia de py-schematron.py (que
converge en la misma fuente). Un único .rng alimenta ambas capas.

jing: la orden `jing` del PATH (o la que indique $JING); si no está, y hay
Java, `java -jar` con el jing.jar que indique $JING_JAR; si tampoco, el
RelaxNG de lxml, más lento en esquemas grandes.

Códigos de salida:
  0  ambas capas limpias
  1  infracciones solo en la capa RelaxNG
  2  infracciones solo en la capa Schematron
  3  infracciones en ambas
  4  error de entorno o de uso (mensaje por stderr), o validación
     Schematron incompleta: un documento mal formado, o reglas que no se
     pudieron evaluar (py-schematron.py terminó con 3)

Ambas capas se ejecutan SIEMPRE (sin cortocircuito): en una campaña de
corrección conviene ver el panorama completo de una vez.

Hasta la versión 2.1 era un script de bash, py-schematron-all.sh; ese
nombre sigue funcionando, y llama a este.
"""

import sys

if sys.version_info < (3, 15):
    print(f"py-schematron-all.py necesita Python 3.15 o posterior; este es Python "
          f"{sys.version.split()[0]}.", file=sys.stderr)
    sys.exit(4)

import importlib.util  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
from pathlib import Path  # noqa: E402

RELAXNG_NS = 'http://relaxng.org/ns/structure/1.0'


def fallar(msg: str):
    """Error de entorno o de uso: mensaje a stderr y código 4."""
    print(msg, file=sys.stderr)
    sys.exit(4)


def aviso(msg: str):
    print(msg, file=sys.stderr, flush=True)


def leer_argumentos(argv):
    """[-v] [-m N] y los archivos, como el getopts del script de bash: las
    opciones van antes de los archivos."""
    verbose, maximo, i = False, None, 0
    while i < len(argv) and argv[i].startswith('-') and argv[i] != '-':
        op = argv[i]
        if op == '--':
            i += 1
            break
        if op == '-v':
            verbose = True
        elif op.startswith('-m'):
            valor = op[2:] or (argv[i + 1] if i + 1 < len(argv) else None)
            if valor is None:
                fallar('La opción -m requiere un valor')
            if not op[2:]:
                i += 1
            maximo = valor
        elif op in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)
        else:
            fallar(f'Opción desconocida: {op}')
        i += 1
    return verbose, maximo, argv[i:]


def validador() -> Path:
    """py-schematron.py: junto a este script (siguiendo un enlace simbólico,
    como el que crea py-schematron-install.py en ~/bin), o en el PATH."""
    junto = Path(__file__).resolve().parent / 'py-schematron.py'
    if junto.is_file():
        return junto
    en_path = shutil.which('py-schematron.py')
    if en_path:
        return Path(en_path)
    fallar('No encuentro py-schematron.py (ni junto a este script ni en el PATH)')


def python_del_validador() -> str:
    """El Python que ejecuta py-schematron.py: $PY_SCHEMATRON_PYTHON (las
    órdenes del instalador lo fijan) o, si no, este mismo."""
    return os.environ.get('PY_SCHEMATRON_PYTHON') or sys.executable


def lxml_etree():
    try:
        from lxml import etree
        return etree
    except ImportError:
        fallar('py-schematron-all.py necesita lxml: python3 -m pip install lxml')


def es_rng(path: Path) -> bool:
    """¿Es un esquema RelaxNG? (clasificación por contenido)"""
    etree = lxml_etree()
    try:
        return etree.QName(etree.parse(str(path)).getroot()).namespace == RELAXNG_NS
    except Exception:
        return False


def autodetectar(validate: Path, doc: Path) -> Path:
    """El href RelaxNG de la PI xml-model del primer documento, resuelto o
    descargado con las funciones y el caché de py-schematron.py."""
    spec = importlib.util.spec_from_file_location('validate', validate)
    v = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(v)
        # preferencia: PI tipada RelaxNG; respaldo: cualquier PI con href
        href = v.href_xml_model(doc, preferencia=(v.RELAXNG_NS,))
        local = v.obtener_recurso(href, doc.parent)
    except SystemExit:                    # (py-schematron.py ya dijo por qué)
        sys.exit(4)
    if v.clasificar_esquema(local) != 'rng':
        fallar(f'El esquema detectado ({href}) no es RelaxNG; la capa estructural '
               f'necesita un .rng — pásalo explícitamente')
    return Path(local)


def orden_jing():
    """Cómo ejecutar jing: una lista para subprocess, o None si no hay."""
    for candidato in (os.environ.get('JING'), shutil.which('jing')):
        if candidato:
            return [candidato]
    jar = os.environ.get('JING_JAR')
    if jar and Path(jar).expanduser().is_file() and shutil.which('java'):
        return ['java', '-jar', str(Path(jar).expanduser())]
    return None


def capa_relaxng(rng: Path, docs) -> int:
    jing = orden_jing()
    if jing:
        rc = subprocess.run([*jing, str(rng), *map(str, docs)]).returncode
        # jing: 0 válido, 1 inválido, >1 error de entorno
        if rc > 1:
            fallar(f'jing terminó con error de entorno ({rc})')
        return rc
    aviso('[aviso] jing no está instalado; uso el RelaxNG de lxml (más lento\n'
          '        en esquemas grandes; para lo definitivo: apt/brew install jing)')
    etree = lxml_etree()
    esquema = etree.RelaxNG(etree.parse(str(rng)))
    malo = 0
    for doc in docs:
        try:
            ok = esquema.validate(etree.parse(str(doc)))
        except etree.XMLSyntaxError as e:
            print(f'{doc}: mal formado: {e}', flush=True)
            malo = 1
            continue
        if not ok:
            malo = 1
            for e in esquema.error_log:
                print(f'{doc}:{e.line}: {e.message}', flush=True)
    return malo


def main(argv=None) -> int:
    verbose, maximo, archivos = leer_argumentos(sys.argv[1:] if argv is None else argv)
    if not archivos:
        fallar(f'Uso: {Path(sys.argv[0]).name} [-v] [-m N] [esquema.rng] documento.xml [más.xml ...]')
    validate = validador()
    primero = Path(archivos[0])
    if not primero.is_file():
        fallar(f'No existe: {primero}')

    auto = not es_rng(primero)
    if auto:
        docs = [Path(a) for a in archivos]
        rng = autodetectar(validate, primero)
        aviso(f'[auto] esquema RelaxNG: {rng}')
    else:
        rng, docs = primero, [Path(a) for a in archivos[1:]]
        if not docs:
            fallar('Falta el documento a validar')
    for d in docs:
        if not d.is_file():
            fallar(f'No existe el documento: {d}')

    aviso(f'=== capa 1: estructura RelaxNG ({rng.name}) ===')
    sys.stdout.flush()
    rc1 = capa_relaxng(rng, docs)
    if rc1 == 0:
        aviso('(estructura limpia)')

    aviso('=== capa 2: reglas Schematron ===')
    opciones = (['-v'] if verbose else []) + (['--max', maximo] if maximo else [])
    fuente = [] if auto else ['-r', str(rng)]
    sys.stdout.flush()
    rc2 = subprocess.run([python_del_validador(), str(validate), *fuente, *opciones,
                          *map(str, docs)]).returncode
    # 3: un documento mal formado o reglas que no se pudieron evaluar (el
    # veredicto Schematron está incompleto); otro código: error de uso o de entorno
    if rc2 == 3:
        fallar('=== VEREDICTO: validación Schematron incompleta (documento mal formado '
               'o reglas que no se pudieron evaluar; véase arriba) ===')
    if rc2 >= 2:
        fallar(f'py-schematron.py terminó con error ({rc2})')

    # Síntesis y código de salida compuesto
    total = (1 if rc1 else 0) + (2 if rc2 else 0)
    aviso({0: '=== VEREDICTO: válido en ambas capas ===',
           1: '=== VEREDICTO: infracciones RelaxNG (estructura) ===',
           2: '=== VEREDICTO: infracciones Schematron ===',
           3: '=== VEREDICTO: infracciones en ambas capas ==='}[total])
    return total


if __name__ == '__main__':
    sys.exit(main())
