"""Modelo del problema: la representación del mundo, sin nada de búsqueda.

La separación entre este paquete y el motor de búsqueda (Fase 2) es
deliberada: el modelo no sabe qué es una frontera ni un nodo, y el motor no
sabe qué es una pared. Así el motor es genérico y la comparación entre métodos
es justa por construcción, porque todos corren exactamente el mismo modelo.
"""

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
