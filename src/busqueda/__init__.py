"""Motor de búsqueda genérico y los cinco métodos."""

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
