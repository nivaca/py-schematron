#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Nicolas Vaughan <nicolasvaughan@proton.me>
# This file is part of py-schematron. See the LICENSE file for details.
#
# py-schematron-all.sh: el nombre de py-schematron-all.py hasta la versión
# 2.1, cuando la validación bicapa era este script de bash. Sigue
# funcionando: llama a py-schematron-all.py, que está junto al archivo real
# de este (si se lo llama desde un enlace simbólico, se sigue el enlace),
# con el Python de $PY_SCHEMATRON_PYTHON o, si no, python3. Los argumentos
# y los códigos de salida son los mismos; véase py-schematron-all.py.
here="$(dirname "$(readlink -f "$0")")"
exec "${PY_SCHEMATRON_PYTHON:-python3}" "$here/py-schematron-all.py" "$@"
