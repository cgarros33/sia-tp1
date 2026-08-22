"""Verdad externa: costo y empujes contra los récords publicados.

QUÉ CUBRE
    Que los métodos óptimos —BFS, IDDFS y A* con heurística admisible— devuelven
    exactamente los números que jugadores humanos publicaron en
    game-sokoban.com. Esos números NO salen de nuestro código. Si uno de estos
    tests falla, hay un bug y no hay otra explicación posible: o el motor está
    mal, o la heurística no es admisible, o el nivel se rompió.

    Que coincidan los DOS números —movimientos y empujes— es lo que da confianza
    en la transcripción. Con una sola pared mal puesta, el óptimo daría distinto.

EL TEST QUE HAY QUE CORRER PRIMERO CUANDO ALGO NO CIERRA
    `test_control_del_motor`: A*(h0) tiene que ser BFS. Con h = 0, A* degenera en
    búsqueda de costo uniforme, y con costo unitario la búsqueda de costo
    uniforme ES BFS. Si difieren, el bug está en el MOTOR —orden de la frontera,
    control de repetidos, o el momento en que se verifica la condición de meta— y
    no en ninguna heurística. Es lo que separa un problema de un lado del otro
    antes de empezar a mirar código.
"""

import pytest

from .conftest import ESPERADO, parametros_niveles

#: Los niveles donde IDDFS termina dentro del límite de nodos. En N4 y N5 agota
#: los 3.000.000 y eso ES un resultado del TP, no un fallo de implementación:
#: por eso no se testea ahí, se reporta en la Fase 6.
NIVELES_CON_IDDFS = ('n1_micro', 'n2_akk04', 'n3_caminata')

#: IDDFS en N2 y N3 tarda ~2,9 s y ~2,3 s: solos se comerían la mitad del
#: presupuesto de 10 segundos de la suite rápida.
NIVELES_CON_IDDFS_LENTOS = ('n2_akk04', 'n3_caminata')


def _parametros_iddfs():
    return [
        pytest.param(n, marks=pytest.mark.lento) if n in NIVELES_CON_IDDFS_LENTOS
        else pytest.param(n)
        for n in NIVELES_CON_IDDFS
    ]


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_bfs_reproduce_el_record_publicado(resultado, nivel):
    """BFS da el costo y los empujes de game-sokoban.com. NO SE NEGOCIA."""
    esperado = ESPERADO[nivel]
    r = resultado(nivel, 'bfs')
    assert r.exito, f'BFS no encontró solución en {nivel} ({r.motivo_fin})'
    assert r.costo == esperado['costo']
    assert r.empujes == esperado['empujes']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_control_del_motor_astar_h0_es_bfs(resultado, nivel):
    """A*(h0) coincide con BFS en costo, en nodos expandidos EXACTOS y en memoria.

    No es "parecido": es idéntico. Con h = 0 los dos métodos extraen los nodos en
    el mismo orden, así que expanden el mismo conjunto y en la misma secuencia.
    Que además coincida `memoria_maxima` prueba que también coinciden instante a
    instante y no sólo al final.

    Si este test falla, NO hay que mirar las heurísticas.
    """
    r_bfs = resultado(nivel, 'bfs')
    r_h0 = resultado(nivel, 'astar_h0')
    assert r_h0.exito
    assert r_h0.costo == r_bfs.costo
    assert r_h0.nodos_expandidos == r_bfs.nodos_expandidos
    assert r_h0.memoria_maxima == r_bfs.memoria_maxima


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_astar_con_heuristica_admisible_es_optimo(resultado, nivel):
    """A*(h1) reproduce el óptimo publicado.

    h1 es admisible —cada caja fuera de meta necesita al menos un empuje, y cada
    empuje es un movimiento—, así que A* con h1 tiene que ser óptimo. Si diera
    más que el récord, la que está mal es la demostración de admisibilidad.
    """
    esperado = ESPERADO[nivel]
    r = resultado(nivel, 'astar_h1')
    assert r.exito
    assert r.costo == esperado['costo']
    assert r.empujes == esperado['empujes']


@pytest.mark.parametrize('nivel', parametros_niveles())
@pytest.mark.parametrize('metodo', ('bfs', 'astar_h0', 'astar_h1', 'dfs', 'greedy_h1'))
def test_la_solucion_es_ejecutable(problema, resultado, nivel, metodo):
    """Aplicar la secuencia de acciones desde el inicial termina en meta.

    Atrapa errores en la reconstrucción del camino, que el costo por sí solo NO
    detecta: un `padre` mal enganchado puede dar un número correcto y devolver un
    camino que no se puede caminar. Y `costo + 1` estados es la comprobación de
    que no se perdió ni se duplicó ningún paso.

    Se corre sobre los cinco métodos y no sólo sobre los óptimos: la
    reconstrucción es código compartido, pero el camino que reconstruye no lo es.
    """
    p = problema(nivel)
    r = resultado(nivel, metodo)
    assert r.exito
    estados = p.reconstruir_estados(r.acciones)
    assert p.es_meta(estados[-1])
    assert len(estados) == r.costo + 1
    assert estados[0] == p.inicial


@pytest.mark.parametrize('nivel', _parametros_iddfs())
def test_iddfs_es_optimo_donde_termina(resultado, nivel):
    """IDDFS devuelve el óptimo en los niveles donde termina.

    Es óptimo con costo uniforme por la misma razón que BFS: la primera solución
    que aparece está a la mínima profundidad posible, porque el límite se sube de
    a uno.
    """
    esperado = ESPERADO[nivel]
    r = resultado(nivel, 'iddfs')
    assert r.exito, f'IDDFS no terminó en {nivel} ({r.motivo_fin})'
    assert r.costo == esperado['costo']
    assert r.empujes == esperado['empujes']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_el_estado_inicial_no_es_meta(problema, nivel):
    """Ningún nivel de la suite arranca resuelto.

    Suena trivial y no lo es: si `es_meta()` tuviera la comparación invertida,
    todos los métodos devolverían costo 0 y varios tests de arriba fallarían con
    mensajes que apuntarían al motor.
    """
    p = problema(nivel)
    assert not p.es_meta(p.inicial)
