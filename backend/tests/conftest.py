"""Rutas para que las pruebas corran igual desde la raíz del repo o desde backend/."""

import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
for ruta in (RAIZ, os.path.join(RAIZ, 'backend')):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)
