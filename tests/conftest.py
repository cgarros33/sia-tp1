"""Fixtures y LA tabla de valores esperados. Un solo lugar para todos los números."""

import pytest

from main import RAIZ, cargar_config
from src.busqueda import a_estrella, bfs, dfs, greedy, iddfs
from src.deadlocks import construir as construir_detector
from src.heuristicas import construir
from src.modelo import Problema, leer_archivo

NIVELES = RAIZ / 'niveles'

MAX_NODOS = cargar_config(RAIZ / 'config.json')['max_nodos']

NIVELES_SUITE = ('n1_micro', 'n2_akk04', 'n3_caminata', 'n4_matching', 'n5_limite')

NIVELES_LENTOS = ('n4_matching', 'n5_limite')


ESPERADO = {
    'n1_micro': {
        'lid': 37953,
        'cajas': 1, 'metas': 1, 'celdas': 12,
        'costo': 8, 'empujes': 5,
        'sucesores': 2, 'sucesores_empuje': 0,
        'bfs': {
            'nodos_expandidos': 38,
            'nodos_generados': 94,
            'frontera_maxima': 12,
            'estados_visitados': 50,
            'memoria_maxima': 62,
        },
        'informatividad': {
            'h0': 0.0, 'h1': 1 / 8, 'h2': 1 / 8, 'h3': 5 / 8,
            'h4': 5 / 8, 'h5': 5 / 8, 'h6': 6 / 8,
        },
        'deadlocks': {
            'celdas_muertas': 5,
            'expandidos_por_capa': {'estaticos': 35, 'congelados': 35},
            'bfs_completo': {
                'nodos_expandidos': 35,
                'nodos_generados': 85,
                'frontera_maxima': 10,
                'estados_visitados': 44,
                'memoria_maxima': 53,
            },
        },
        'dfs_estrictamente_peor': False,
    },
    'n2_akk04': {
        'lid': 29619,
        'cajas': 4, 'metas': 4, 'celdas': 32,
        'costo': 45, 'empujes': 18,
        'sucesores': 2, 'sucesores_empuje': 1,
        'bfs': {
            'nodos_expandidos': 44_124,
            'nodos_generados': 112_849,
            'frontera_maxima': 2_691,
            'estados_visitados': 46_779,
            'memoria_maxima': 49_434,
        },
        'informatividad': {
            'h0': 0.0, 'h1': 1 / 45, 'h2': 4 / 45, 'h3': 11 / 45,
            'h4': 14 / 45, 'h5': 18 / 45, 'h6': 18 / 45,
        },
        'deadlocks': {
            'celdas_muertas': 13,
            'expandidos_por_capa': {'estaticos': 14_178, 'congelados': 9_839},
            'bfs_completo': {
                'nodos_expandidos': 9_839,
                'nodos_generados': 24_719,
                'frontera_maxima': 661,
                'estados_visitados': 10_475,
                'memoria_maxima': 11_111,
            },
        },
        'dfs_estrictamente_peor': True,
    },
    'n3_caminata': {
        'lid': 953,
        'cajas': 2, 'metas': 2, 'celdas': 35,
        'costo': 104, 'empujes': 22,
        'sucesores': 3, 'sucesores_empuje': 0,
        'bfs': {
            'nodos_expandidos': 6_360,
            'nodos_generados': 15_594,
            'frontera_maxima': 220,
            'estados_visitados': 6_491,
            'memoria_maxima': 6_622,
        },
        'informatividad': {
            'h0': 0.0, 'h1': 1 / 104, 'h2': 2 / 104, 'h3': 12 / 104,
            'h4': 12 / 104, 'h5': 12 / 104, 'h6': 13 / 104,
        },
        'deadlocks': {
            'celdas_muertas': 23,
            'expandidos_por_capa': {'estaticos': 2_002, 'congelados': 2_944},
            'bfs_completo': {
                'nodos_expandidos': 1_816,
                'nodos_generados': 4_353,
                'frontera_maxima': 79,
                'estados_visitados': 1_826,
                'memoria_maxima': 1_836,
            },
        },
        'dfs_estrictamente_peor': True,
    },
    'n4_matching': {
        'lid': 29617,
        'cajas': 4, 'metas': 4, 'celdas': 31,
        'costo': 70, 'empujes': 22,
        'sucesores': 2, 'sucesores_empuje': 0,
        'bfs': {
            'nodos_expandidos': 654_260,
            'nodos_generados': 1_728_078,
            'frontera_maxima': 21_345,
            'estados_visitados': 662_769,
            'memoria_maxima': 671_278,
        },
        'informatividad': {
            'h0': 0.0, 'h1': 1 / 70, 'h2': 4 / 70, 'h3': 16 / 70,
            'h4': 20 / 70, 'h5': 22 / 70, 'h6': 24 / 70,
        },
        'deadlocks': {
            'celdas_muertas': 12,
            'expandidos_por_capa': {'estaticos': 73_813, 'congelados': 214_466},
            'bfs_completo': {
                'nodos_expandidos': 60_410,
                'nodos_generados': 155_205,
                'frontera_maxima': 2_028,
                'estados_visitados': 61_358,
                'memoria_maxima': 62_306,
            },
        },
        'dfs_estrictamente_peor': True,
    },
    'n5_limite': {
        'lid': 8602,
        'cajas': 4, 'metas': 4, 'celdas': 41,
        'costo': 306, 'empujes': 99,
        'sucesores': 1, 'sucesores_empuje': 0,
        'bfs': {
            'nodos_expandidos': 2_028_239,
            'nodos_generados': 5_010_835,
            'frontera_maxima': 20_365,
            'estados_visitados': 2_028_469,
            'memoria_maxima': 2_028_699,
        },
        'informatividad': {
            'h0': 0.0, 'h1': 1 / 306, 'h2': 4 / 306, 'h3': 23 / 306,
            'h4': 27 / 306, 'h5': 63 / 306, 'h6': 70 / 306,
        },
        'deadlocks': {
            'celdas_muertas': 13,
            'expandidos_por_capa': {'estaticos': 608_999, 'congelados': 508_669},
            'bfs_completo': {
                'nodos_expandidos': 429_817,
                'nodos_generados': 1_064_551,
                'frontera_maxima': 4_917,
                'estados_visitados': 429_917,
                'memoria_maxima': 430_017,
            },
        },
        'dfs_estrictamente_peor': True,
    },
}

COLUMNAS_BFS = ('nodos_expandidos', 'nodos_generados', 'frontera_maxima',
                'estados_visitados', 'memoria_maxima')

HEURISTICAS_A_VERIFICAR = ('h0', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6')

HEURISTICAS_NO_ADMISIBLES = ('hna', 'hna4')

DETECTORES_A_VERIFICAR = ('estaticos', 'congelados', 'completo')


def parametros_niveles(niveles=NIVELES_SUITE):
    """Los niveles como parámetros de pytest, con `lento` pegado a N4 y N5."""
    return [
        pytest.param(n, marks=pytest.mark.lento) if n in NIVELES_LENTOS
        else pytest.param(n)
        for n in niveles
    ]


_CACHE_PROBLEMA = {}
_CACHE_CORRIDA = {}


def cargar_problema(nombre, deadlocks='ninguno'):
    """El `Problema` de un nivel, con la capa de poda pedida. Cacheado."""
    entrada = (nombre, deadlocks)
    if entrada not in _CACHE_PROBLEMA:
        tablero, inicial = leer_archivo(NIVELES / f'{nombre}.sok')
        _CACHE_PROBLEMA[entrada] = Problema(
            tablero, inicial,
            detector_deadlocks=construir_detector(deadlocks, tablero))
    return _CACHE_PROBLEMA[entrada]


def _lanzar(problema, clave, nivel):
    if clave == 'bfs':
        return bfs(problema, max_nodos=MAX_NODOS, nivel=nivel)
    if clave == 'dfs':
        return dfs(problema, max_nodos=MAX_NODOS, nivel=nivel)
    if clave == 'iddfs':
        return iddfs(problema, max_nodos=MAX_NODOS, nivel=nivel)
    if clave.startswith('astar_'):
        nombre_h = clave.split('_', 1)[1]
        return a_estrella(problema, construir(nombre_h, problema), nombre_h,
                          max_nodos=MAX_NODOS, nivel=nivel)
    if clave.startswith('greedy_'):
        nombre_h = clave.split('_', 1)[1]
        return greedy(problema, construir(nombre_h, problema), nombre_h,
                      max_nodos=MAX_NODOS, nivel=nivel)
    raise ValueError(f'Corrida desconocida: {clave!r}')


def correr(nivel, clave='bfs', deadlocks='ninguno'):
    """El `Resultado` de (nivel, método, capa de poda), una sola vez por sesión."""
    entrada = (nivel, clave, deadlocks)
    if entrada not in _CACHE_CORRIDA:
        _CACHE_CORRIDA[entrada] = _lanzar(
            cargar_problema(nivel, deadlocks), clave, nivel)
    return _CACHE_CORRIDA[entrada]


def camino_optimo(nivel):
    """Los `costo + 1` estados de la solución óptima que encontró BFS."""
    resultado = correr(nivel, 'bfs')
    return cargar_problema(nivel).reconstruir_estados(resultado.acciones)


@pytest.fixture(scope='session')
def problema():
    """Devuelve la FUNCIÓN `cargar_problema`, no un problema."""
    return cargar_problema


@pytest.fixture(scope='session')
def resultado():
    """Devuelve la función `correr`, por el mismo motivo que `problema`."""
    return correr


@pytest.fixture(scope='session')
def camino():
    """Devuelve la función `camino_optimo`, por el mismo motivo que `problema`."""
    return camino_optimo
