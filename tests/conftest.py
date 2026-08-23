"""Fixtures y LA tabla de valores esperados. Un solo lugar para todos los números.

QUÉ REPRESENTA
    El estado congelado del proyecto al cerrar la Fase 2. Todos los tests leen de
    `ESPERADO`: cuando haya que revisar un número, se revisa una vez y acá.

LOS DOS NIVELES DE EXIGENCIA, QUE ES LO QUE ORGANIZA TODA LA FASE

    Verdad externa — NO SE NEGOCIA. `costo` y `empujes` son los récords
    publicados por jugadores humanos en game-sokoban.com. No dependen de nuestra
    implementación. Si un método óptimo devuelve otro número, hay un bug: o el
    motor está mal, o la heurística no es admisible, o el nivel se rompió.

    Regresión interna — SE CONGELA. Todo lo que está bajo la clave `bfs` son
    métricas de NUESTRA implementación: dependen del orden en que se generan los
    sucesores, del criterio de desempate de la frontera y de la política de
    estados repetidos. No hay verdad externa contra la cual compararlas. Se
    midieron una vez y sirven para detectar cambios de comportamiento.

    Si un valor de regresión cambia, NO se actualiza el número esperado. Se
    entiende primero por qué cambió: puede ser una mejora legítima o puede ser un
    bug, y el test no distingue. Esa parte la hace una persona.

LA DECISIÓN DE DISEÑO — las corridas se cachean por sesión
    `correr()` guarda el `Resultado` de cada par (nivel, método) y lo devuelve a
    todos los tests que lo pidan. No es una optimización cosmética: BFS en N5
    expande 2.028.239 nodos y tarda entre 8 y 47 segundos según la máquina, y hay
    cuatro archivos de tests que necesitan ese mismo resultado —optimalidad,
    regresión, camino ejecutable y heurísticas—. Sin caché la suite correría BFS
    de N5 media docena de veces y nadie la correría nunca.

    Es seguro porque `Resultado` no se muta y porque los cinco métodos son
    determinísticos: dos corridas del mismo par dan exactamente lo mismo. Eso
    último no se asume, se testea (`test_regresion.py::test_determinismo`).

QUÉ SE DESCARTÓ
    Fixtures parametrizadas con `params=NIVELES_SUITE` y `scope='session'`. Es lo
    idiomático de pytest y acá estorba: obliga a que cada test reciba el nivel por
    la fixture, y entonces marcar `lento` sólo N4 y N5 deja de ser posible, porque
    la marca se aplica al test y no a cada valor del parámetro. Con
    `parametros_niveles()` la marca viaja pegada al nivel, que es donde
    corresponde.
"""

import pytest

from main import RAIZ, cargar_config
from src.busqueda import a_estrella, bfs, dfs, greedy, iddfs
from src.heuristicas import construir
from src.modelo import Problema, leer_archivo

NIVELES = RAIZ / 'niveles'

#: El techo de nodos de todas las corridas. Sale de `config.json` y no de una
#: constante escondida acá: el número que corta las corridas del proyecto tiene
#: que ser un dato versionado y el mismo para todos los métodos.
MAX_NODOS = cargar_config(RAIZ / 'config.json')['max_nodos']

#: Los cinco niveles, en el orden de la narrativa de la presentación.
NIVELES_SUITE = ('n1_micro', 'n2_akk04', 'n3_caminata', 'n4_matching', 'n5_limite')

#: Los que llevan `@pytest.mark.lento`. N4 son 654.260 nodos y N5 son 2.028.239:
#: entre los dos se llevan casi toda la duración de la suite completa.
NIVELES_LENTOS = ('n4_matching', 'n5_limite')


# --- LA TABLA ---------------------------------------------------------------
#
# `costo` y `empujes` son verdad externa (game-sokoban.com). Todo lo demás es
# regresión interna medida al cerrar la Fase 2 con corte por `max_nodos` y sin
# ningún timeout.
#
# `informatividad` es h(s0)/óptimo y se escribe como fracción a propósito: el
# numerador es el valor de la heurística en el estado inicial —para h1, cuántas
# cajas arrancan fuera de meta— y el denominador es el óptimo publicado. Así el
# número es auditable de un vistazo en vez de ser un decimal caído del cielo.
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
            'h0': 0.0, 'h1': 1 / 8, 'h2': 5 / 8, 'h3': 5 / 8, 'h4': 5 / 8, 'h5': 6 / 8,
        },
        # N1 es la excepción documentada del test estricto de DFS: es un pasillo
        # de 12 celdas sin ramificación real, así que DFS cae en el óptimo sin
        # buscarlo. Corriendo DFS con los 24 órdenes posibles de DIRECCIONES, da
        # 8 en los 24.
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
            'h0': 0.0, 'h1': 4 / 45, 'h2': 11 / 45, 'h3': 14 / 45, 'h4': 18 / 45, 'h5': 18 / 45,
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
            'h0': 0.0, 'h1': 2 / 104, 'h2': 12 / 104, 'h3': 12 / 104, 'h4': 12 / 104, 'h5': 13 / 104,
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
            'h0': 0.0, 'h1': 4 / 70, 'h2': 16 / 70, 'h3': 20 / 70, 'h4': 22 / 70, 'h5': 24 / 70,
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
            'h0': 0.0, 'h1': 4 / 306, 'h2': 23 / 306, 'h3': 27 / 306, 'h4': 63 / 306, 'h5': 70 / 306,
        },
        # No está en la lista del test estricto porque N5 no se corre ahí: DFS
        # en N5 da 6.992 contra un óptimo de 306, o sea 22x, pero verificarlo
        # cuesta 6 segundos y no agrega nada a lo que ya muestran N2, N3 y N4.
        'dfs_estrictamente_peor': True,
    },
}

#: Las cinco columnas congeladas de BFS. Se listan acá para que el test compare
#: el dict entero de una y el mensaje de fallo muestre las cinco juntas.
COLUMNAS_BFS = ('nodos_expandidos', 'nodos_generados', 'frontera_maxima',
                'estados_visitados', 'memoria_maxima')

#: Las heurísticas ADMISIBLES. Son las que se someten a los tests de
#: admisibilidad, consistencia e informatividad. La Fase 4 va agregando acá cada
#: eslabón de la escalera, junto con una fila en la clave `informatividad` de
#: cada nivel, y no escribe ningún test nuevo.
HEURISTICAS_A_VERIFICAR = ('h0', 'h1', 'h2', 'h3', 'h4', 'h5')

#: Las heurísticas que se sabe que NO son admisibles y están en el registro a
#: propósito, para mostrar qué se rompe. Existe para que el guardián de
#: `test_heuristicas.py` distinga "no admisible a propósito" de "nadie la
#: verificó", que es exactamente la diferencia entre una decisión y un olvido.
#:
#: Son dos y no una porque dan resultados distintos: hna = 2*h4 devuelve el
#: óptimo en los cinco niveles a pesar de no ser admisible, y hna4 = 4*h4 devuelve
#: soluciones subóptimas en n2_akk04 (47 contra 45) y n4_matching (82 contra 70).
#: La primera muestra que se pierde la GARANTÍA, la segunda muestra qué pasa
#: cuando esa garantía hacía falta. Ver src/heuristicas/hna_sobreestimada.py.
HEURISTICAS_NO_ADMISIBLES = ('hna', 'hna4')


def parametros_niveles(niveles=NIVELES_SUITE):
    """Los niveles como parámetros de pytest, con `lento` pegado a N4 y N5.

    La marca viaja con el valor del parámetro y no con el test, que es lo que
    permite que `pytest -m "not lento"` corra el mismo test sobre N1, N2 y N3 y
    saltee N4 y N5.
    """
    return [
        pytest.param(n, marks=pytest.mark.lento) if n in NIVELES_LENTOS
        else pytest.param(n)
        for n in niveles
    ]


# --- construcción y corridas, cacheadas por sesión ---------------------------

_CACHE_PROBLEMA = {}
_CACHE_CORRIDA = {}


def cargar_problema(nombre):
    """El `Problema` de un nivel. Cacheado: construir el `Tablero` precalcula la
    tabla de movimientos completa, y hay decenas de tests por nivel."""
    if nombre not in _CACHE_PROBLEMA:
        tablero, inicial = leer_archivo(NIVELES / f'{nombre}.sok')
        _CACHE_PROBLEMA[nombre] = Problema(tablero, inicial)
    return _CACHE_PROBLEMA[nombre]


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


def correr(nivel, clave='bfs'):
    """El `Resultado` de (nivel, método), calculado una sola vez por sesión.

    `clave` es 'bfs', 'dfs', 'iddfs', 'astar_h0', 'astar_h1', 'greedy_h1'...
    Nunca se pasa `timeout_s`: el único corte es `max_nodos`, que es
    determinístico y por lo tanto reproducible entre máquinas.
    """
    entrada = (nivel, clave)
    if entrada not in _CACHE_CORRIDA:
        _CACHE_CORRIDA[entrada] = _lanzar(cargar_problema(nivel), clave, nivel)
    return _CACHE_CORRIDA[entrada]


def camino_optimo(nivel):
    """Los `costo + 1` estados de la solución óptima que encontró BFS.

    Es lo que consumen las verificaciones de admisibilidad y consistencia: sobre
    un camino óptimo el costo restante desde el estado i es exactamente L - i, y
    entonces comprobar h(s_i) <= L - i sale gratis. Ver el docstring de
    `test_heuristicas.py`.
    """
    resultado = correr(nivel, 'bfs')
    return cargar_problema(nivel).reconstruir_estados(resultado.acciones)


# --- las fixtures, que son sólo la puerta de entrada a lo de arriba ----------

@pytest.fixture(scope='session')
def problema():
    """Devuelve la FUNCIÓN `cargar_problema`, no un problema.

    Los tests están parametrizados por nombre de nivel, así que necesitan pedir
    el problema que les toca; una fixture que devolviera un problema concreto
    obligaría a parametrizar la fixture y rompería el marcado selectivo de
    `lento`. Ver "QUÉ SE DESCARTÓ" arriba.
    """
    return cargar_problema


@pytest.fixture(scope='session')
def resultado():
    """Devuelve la función `correr`, por el mismo motivo que `problema`."""
    return correr


@pytest.fixture(scope='session')
def camino():
    """Devuelve la función `camino_optimo`, por el mismo motivo que `problema`."""
    return camino_optimo
