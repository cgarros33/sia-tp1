"""Modelo del problema: la representación del mundo, sin nada de búsqueda."""

from .tablero import (
    ARRIBA, ABAJO, IZQUIERDA, DERECHA,
    DIRECCIONES, NOMBRE_DIR, DESPLAZAMIENTO,
    Tablero,
)
from .estado import Estado
from .parser_xsb import NivelInvalido, leer_texto, leer_archivo
from .problema import Problema

__all__ = [
    'ARRIBA', 'ABAJO', 'IZQUIERDA', 'DERECHA',
    'DIRECCIONES', 'NOMBRE_DIR', 'DESPLAZAMIENTO',
    'Tablero', 'Estado',
    'NivelInvalido', 'leer_texto', 'leer_archivo',
    'Problema',
]
