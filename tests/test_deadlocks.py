"""La poda de deadlocks: que no rompa nada y que sirva."""

import pytest

from src.busqueda import bfs
from src.deadlocks import DETECTORES, construir
from src.modelo import Problema, leer_texto

from .conftest import (COLUMNAS_BFS, DETECTORES_A_VERIFICAR, ESPERADO,
                       MAX_NODOS, cargar_problema, parametros_niveles)

PASILLO = """\
#######
#     #
#@$ . #
#######"""

BLOQUE_DE_METAS = """\
#######
#@    #
# **  #
# **  #
#######"""


def _empujes(camino):
    """(cajas, caja_movida) de cada empuje del camino, como los ve el detector."""
    for anterior, siguiente in zip(camino, camino[1:]):
        movidas = siguiente.cajas - anterior.cajas
        if movidas:
            yield siguiente.cajas, next(iter(movidas))


@pytest.mark.parametrize('capa', DETECTORES_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_ninguna_capa_poda_el_camino_optimo(camino, nivel, capa):
    """Todos los estados de un camino óptimo tienen solución: podar uno es un bug."""
    detectar = construir(capa, cargar_problema(nivel).tablero)
    podados = [i for i, (cajas, movida) in enumerate(_empujes(camino(nivel)))
               if detectar(cajas, movida)]
    assert not podados, (
        f'{capa} en {nivel}: poda los empujes {podados} del camino óptimo, que '
        f'por definición tienen solución. Es un falso positivo.')


@pytest.mark.parametrize('capa', DETECTORES_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_la_poda_no_cambia_el_costo(resultado, nivel, capa):
    """El criterio de la fase: mismo costo y mismos empujes que sin poda."""
    esperado = ESPERADO[nivel]
    r = resultado(nivel, 'bfs', capa)
    assert r.exito
    assert r.costo == esperado['costo']
    assert r.empujes == esperado['empujes']


@pytest.mark.parametrize('capa', DETECTORES_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_la_poda_devuelve_la_misma_solucion(resultado, nivel, capa):
    """No sólo el mismo costo: exactamente la misma secuencia de movimientos."""
    assert resultado(nivel, 'bfs', capa).acciones == resultado(nivel, 'bfs').acciones


@pytest.mark.parametrize('capa', DETECTORES_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_la_poda_no_aumenta_los_nodos(resultado, nivel, capa):
    """Podar sólo saca sucesores, así que no puede agregar trabajo."""
    con_poda = resultado(nivel, 'bfs', capa)
    sin_poda = resultado(nivel, 'bfs')
    assert con_poda.nodos_expandidos <= sin_poda.nodos_expandidos
    assert con_poda.nodos_generados <= sin_poda.nodos_generados
    assert con_poda.memoria_maxima <= sin_poda.memoria_maxima


@pytest.mark.parametrize('capa', ('estaticos', 'congelados'))
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_completo_no_es_peor_que_ninguna_de_las_dos_capas(resultado, nivel, capa):
    """`completo` poda todo lo que poda cada regla suelta, así que expande menos."""
    assert (resultado(nivel, 'bfs', 'completo').nodos_expandidos
            <= resultado(nivel, 'bfs', capa).nodos_expandidos)


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_columnas_congeladas_de_bfs_con_poda_completa(resultado, nivel):
    """Las cinco columnas de BFS con la poda completa, exactas."""
    r = resultado(nivel, 'bfs', 'completo')
    medido = {columna: getattr(r, columna) for columna in COLUMNAS_BFS}
    assert medido == ESPERADO[nivel]['deadlocks']['bfs_completo']


@pytest.mark.parametrize('capa', ('estaticos', 'congelados'))
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_expandidos_congelados_por_capa(resultado, nivel, capa):
    """Los nodos de cada capa suelta. Son la tabla que compara las dos reglas."""
    esperado = ESPERADO[nivel]['deadlocks']['expandidos_por_capa'][capa]
    assert resultado(nivel, 'bfs', capa).nodos_expandidos == esperado


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_celdas_muertas_congeladas(problema, nivel):
    """Cuántas celdas muertas tiene cada nivel, y que ninguna caja arranque en una."""
    from src.heuristicas.distancias import celdas_muertas
    p = problema(nivel)
    muertas = celdas_muertas(p.tablero)
    assert len(muertas) == ESPERADO[nivel]['deadlocks']['celdas_muertas']
    assert not (p.inicial.cajas & muertas)


def test_una_caja_en_un_rincon_la_ven_las_dos_reglas():
    """El rincón es el deadlock de manual, y las dos reglas llegan por caminos"""
    tablero, _ = leer_texto(PASILLO)
    rincon = tablero.indice(1, 1)
    for capa in DETECTORES_A_VERIFICAR:
        detectar = construir(capa, tablero)
        assert detectar(frozenset({rincon}), rincon), capa


def test_una_celda_muerta_que_no_es_rincon_la_ve_solo_la_estatica():
    """Una caja sola en el pasillo de arriba: no se puede empujar salvo en"""
    tablero, _ = leer_texto(PASILLO)
    muerta = tablero.indice(1, 3)
    assert construir('estaticos', tablero)(frozenset({muerta}), muerta)
    assert not construir('congelados', tablero)(frozenset({muerta}), muerta)
    assert construir('completo', tablero)(frozenset({muerta}), muerta)


def test_dos_cajas_contra_la_pared_las_ve_solo_la_regla_de_2x2():
    """El caso que justifica que la regla dinámica exista."""
    tablero, _ = leer_texto(PASILLO)
    izquierda, derecha = tablero.indice(2, 2), tablero.indice(2, 3)
    juntas = frozenset({izquierda, derecha})

    assert not construir('estaticos', tablero)(juntas, derecha)
    assert construir('congelados', tablero)(juntas, derecha)
    for capa in DETECTORES_A_VERIFICAR:
        detectar = construir(capa, tablero)
        assert not detectar(frozenset({izquierda}), izquierda), capa
        assert not detectar(frozenset({derecha}), derecha), capa


def test_un_2x2_con_todas_las_cajas_en_meta_no_es_deadlock():
    """LA CLÁUSULA. Un cuadrado lleno de cajas, todas sobre metas, es el nivel"""
    tablero, _ = leer_texto(BLOQUE_DE_METAS)
    bloque = frozenset(tablero.indice(f, c) for f in (2, 3) for c in (2, 3))
    assert bloque == tablero.metas
    assert not construir('congelados', tablero)(bloque, tablero.indice(3, 3))


def test_el_mismo_2x2_con_una_caja_fuera_de_meta_si_lo_es():
    """El control del test anterior: el mismo cuadrado corrido una columna, con"""
    tablero, _ = leer_texto(BLOQUE_DE_METAS)
    corrido = frozenset(tablero.indice(f, c) for f in (2, 3) for c in (3, 4))
    assert construir('congelados', tablero)(corrido, tablero.indice(3, 4))


def test_sin_poda_devuelve_none_y_no_una_funcion():
    """`'ninguno'` tiene que devolver `None`, no una función que siempre dice que"""
    assert construir('ninguno', cargar_problema('n1_micro').tablero) is None


def test_construir_rechaza_un_detector_inexistente():
    """Un `"deadlocks": "estatico"` mal tipeado en `config.json` daría una corrida"""
    with pytest.raises(ValueError):
        construir('no_existe', cargar_problema('n1_micro').tablero)


def test_todos_los_detectores_del_registro_estan_verificados():
    """El guardián, igual que el de las heurísticas."""
    declarados = set(DETECTORES_A_VERIFICAR) | {'ninguno'}
    assert set(DETECTORES) == declarados, (
        f'Detectores sin declarar: {sorted(set(DETECTORES) - declarados)}. Van a '
        f'DETECTORES_A_VERIFICAR de tests/conftest.py, que es la lista que se '
        f'somete a los tests de falsos positivos.')


def test_reconstruir_un_camino_ignora_la_poda():
    """`reconstruir_estados()` pide los sucesores sin podar, a propósito."""
    original = cargar_problema('n1_micro')
    acciones = bfs(original, max_nodos=MAX_NODOS).acciones

    todo_es_deadlock = Problema(original.tablero, original.inicial,
                                detector_deadlocks=lambda cajas, movida: True)
    estados = todo_es_deadlock.reconstruir_estados(acciones)
    assert len(estados) == len(acciones) + 1
    assert todo_es_deadlock.es_meta(estados[-1])

    assert bfs(todo_es_deadlock, max_nodos=MAX_NODOS).motivo_fin == 'sin_solucion'
