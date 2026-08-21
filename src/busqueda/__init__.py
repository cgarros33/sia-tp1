"""Motor de búsqueda genérico y los cinco métodos.

La regla de este paquete: `motor.py` no sabe qué es una pared y `modelo/` no
sabe qué es una frontera. Esa separación es lo que permite que los cinco
métodos corran exactamente el mismo código de expansión.
"""

from .nodo import Nodo
from .frontera import Frontera, FronteraFIFO, FronteraLIFO, FronteraPrioridad
from .motor import CAMINO, CERRADO, MEJOR_G, MOTIVOS, POLITICAS, Resultado, buscar
from .algoritmos import (
    METODOS, METODOS_INFORMADOS,
    a_estrella, bfs, dfs, greedy, hpa, iddfs, iddfs_puro, resolver,
)

__all__ = [
    'Nodo',
    'Frontera', 'FronteraFIFO', 'FronteraLIFO', 'FronteraPrioridad',
    'CAMINO', 'CERRADO', 'MEJOR_G', 'MOTIVOS', 'POLITICAS', 'Resultado', 'buscar',
    'METODOS', 'METODOS_INFORMADOS',
    'a_estrella', 'bfs', 'dfs', 'greedy', 'hpa', 'iddfs', 'iddfs_puro', 'resolver',
]
