"""Verdad externa: costo y empujes contra los récords publicados."""

import pytest

from .conftest import ESPERADO, parametros_niveles

NIVELES_CON_IDDFS = ('n1_micro', 'n2_akk04', 'n3_caminata')

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
    """A*(h0) coincide con BFS en costo, en nodos expandidos EXACTOS y en memoria."""
    r_bfs = resultado(nivel, 'bfs')
    r_h0 = resultado(nivel, 'astar_h0')
    assert r_h0.exito
    assert r_h0.costo == r_bfs.costo
    assert r_h0.nodos_expandidos == r_bfs.nodos_expandidos
    assert r_h0.memoria_maxima == r_bfs.memoria_maxima


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_astar_con_heuristica_admisible_es_optimo(resultado, nivel):
    """A*(h2) reproduce el óptimo publicado."""
    esperado = ESPERADO[nivel]
    r = resultado(nivel, 'astar_h2')
    assert r.exito
    assert r.costo == esperado['costo']
    assert r.empujes == esperado['empujes']


@pytest.mark.parametrize('nivel', parametros_niveles())
@pytest.mark.parametrize('metodo', ('bfs', 'astar_h0', 'astar_h2', 'dfs', 'greedy_h2'))
def test_la_solucion_es_ejecutable(problema, resultado, nivel, metodo):
    """Aplicar la secuencia de acciones desde el inicial termina en meta."""
    p = problema(nivel)
    r = resultado(nivel, metodo)
    assert r.exito
    estados = p.reconstruir_estados(r.acciones)
    assert p.es_meta(estados[-1])
    assert len(estados) == r.costo + 1
    assert estados[0] == p.inicial


@pytest.mark.parametrize('nivel', _parametros_iddfs())
def test_iddfs_es_optimo_donde_termina(resultado, nivel):
    """IDDFS devuelve el óptimo en los niveles donde termina."""
    esperado = ESPERADO[nivel]
    r = resultado(nivel, 'iddfs')
    assert r.exito, f'IDDFS no terminó en {nivel} ({r.motivo_fin})'
    assert r.costo == esperado['costo']
    assert r.empujes == esperado['empujes']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_el_estado_inicial_no_es_meta(problema, nivel):
    """Ningún nivel de la suite arranca resuelto."""
    p = problema(nivel)
    assert not p.es_meta(p.inicial)
