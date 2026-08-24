"""Regresión interna: el comportamiento congelado de nuestra implementación."""

import shutil

import pytest

from src.busqueda import bfs
from src.modelo import Problema, leer_archivo

from .conftest import (COLUMNAS_BFS, ESPERADO, MAX_NODOS, NIVELES,
                       cargar_problema, parametros_niveles)


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_columnas_congeladas_de_bfs(resultado, nivel):
    """Las cinco columnas de BFS, exactas."""
    r = resultado(nivel, 'bfs')
    medido = {columna: getattr(r, columna) for columna in COLUMNAS_BFS}
    assert medido == ESPERADO[nivel]['bfs']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_memoria_maxima_es_el_pico_de_la_suma(resultado, nivel):
    """`memoria_maxima` está entre el pico de la frontera y la suma de los picos."""
    r = resultado(nivel, 'bfs')
    assert r.memoria_maxima >= r.frontera_maxima
    assert r.memoria_maxima >= r.estados_visitados
    assert r.memoria_maxima <= r.frontera_maxima + r.estados_visitados


def test_en_n1_la_suma_da_exacto_y_en_n2_no(resultado):
    """El caso concreto que alguien va a mirar sumando las dos columnas a mano."""
    r1 = resultado('n1_micro', 'bfs')
    assert r1.memoria_maxima == r1.frontera_maxima + r1.estados_visitados == 62

    r2 = resultado('n2_akk04', 'bfs')
    assert r2.frontera_maxima + r2.estados_visitados == 49_470
    assert r2.memoria_maxima == 49_434


@pytest.mark.parametrize('nivel', ('n2_akk04', 'n3_caminata'))
@pytest.mark.parametrize('metodo', ('bfs', 'dfs', 'greedy_h2', 'astar_h2'))
def test_determinismo(nivel, metodo):
    """Dos corridas seguidas del mismo método sobre el mismo nivel son idénticas."""
    from .conftest import _lanzar
    p = cargar_problema(nivel)
    primera = _lanzar(p, metodo, nivel)
    segunda = _lanzar(p, metodo, nivel)
    assert primera.nodos_expandidos == segunda.nodos_expandidos
    assert primera.nodos_generados == segunda.nodos_generados
    assert primera.costo == segunda.costo
    assert primera.acciones == segunda.acciones


def test_determinismo_iddfs_n1():
    """El mismo test sobre el método que lo motivó, en el nivel donde es barato."""
    from .conftest import _lanzar
    p = cargar_problema('n1_micro')
    primera = _lanzar(p, 'iddfs', 'n1_micro')
    segunda = _lanzar(p, 'iddfs', 'n1_micro')
    assert primera.nodos_expandidos == segunda.nodos_expandidos
    assert primera.iteraciones == segunda.iteraciones


@pytest.mark.lento
def test_determinismo_iddfs_n2():
    """IDDFS en N2: el caso exacto donde el timeout daba 3.453.866 y 1.798.624."""
    from .conftest import _lanzar
    p = cargar_problema('n2_akk04')
    primera = _lanzar(p, 'iddfs', 'n2_akk04')
    segunda = _lanzar(p, 'iddfs', 'n2_akk04')
    assert primera.nodos_expandidos == segunda.nodos_expandidos


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_dfs_nunca_por_debajo_del_optimo(resultado, nivel):
    """DFS puede dar cualquier cosa MENOS un costo menor al óptimo."""
    r = resultado(nivel, 'dfs')
    assert r.exito
    assert r.costo >= ESPERADO[nivel]['costo']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_dfs_es_estrictamente_peor_salvo_en_n1(resultado, nivel):
    """DFS encuentra UNA solución, no la mejor. N1 es la excepción documentada."""
    esperado = ESPERADO[nivel]
    r = resultado(nivel, 'dfs')
    if esperado['dfs_estrictamente_peor']:
        assert r.costo > esperado['costo']
    else:
        assert r.costo == esperado['costo']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_greedy_es_mas_barato_y_no_mejor(resultado, nivel):
    """Greedy expande menos nodos que BFS y su costo es MAYOR O IGUAL al óptimo."""
    r_greedy = resultado(nivel, 'greedy_h2')
    r_bfs = resultado(nivel, 'bfs')
    assert r_greedy.exito
    assert r_greedy.nodos_expandidos < r_bfs.nodos_expandidos
    assert r_greedy.costo >= ESPERADO[nivel]['costo']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_astar_h2_domina_a_astar_h0(resultado, nivel):
    """A*(h2) no expande más nodos que A*(h0) y devuelve el mismo costo."""
    r_h0 = resultado(nivel, 'astar_h0')
    r_h2 = resultado(nivel, 'astar_h2')
    assert r_h2.costo == r_h0.costo
    assert r_h2.nodos_expandidos <= r_h0.nodos_expandidos


@pytest.mark.lento
@pytest.mark.parametrize('nivel', ('n2_akk04', 'n3_caminata'))
def test_iddfs_ahorra_frontera_pero_no_memoria(resultado, nivel):
    """LA AFIRMACIÓN CORREGIDA, y es el resultado más interesante de la Fase 2."""
    r_iddfs = resultado(nivel, 'iddfs')
    r_bfs = resultado(nivel, 'bfs')
    assert r_iddfs.exito

    assert r_iddfs.frontera_maxima < r_bfs.frontera_maxima / 2
    assert r_iddfs.nodos_expandidos > r_bfs.nodos_expandidos * 10
    assert 0.5 <= r_iddfs.memoria_maxima / r_bfs.memoria_maxima <= 1.2


def test_iddfs_puro_si_ahorra_memoria_de_verdad():
    """El contraste: sin estructura de visitados, IDDFS sí tiene memoria chica."""
    from src.busqueda import iddfs_puro
    p = cargar_problema('n1_micro')
    r_puro = iddfs_puro(p, max_nodos=MAX_NODOS, nivel='n1_micro')
    r_bfs = bfs(p, max_nodos=MAX_NODOS, nivel='n1_micro')
    assert r_puro.exito
    assert r_puro.costo == r_bfs.costo
    assert r_puro.estados_visitados == 0
    assert r_puro.memoria_maxima < r_bfs.memoria_maxima / 2
    assert r_puro.nodos_expandidos > r_bfs.nodos_expandidos


CELDAS_DE_PISO_N1 = (
    ((1, 1), False),
    ((1, 2), False),
    ((1, 3), True),
    ((1, 4), True),
    ((2, 2), True),
    ((2, 4), True),
    ((3, 4), True),
    ((4, 4), True),
    ((5, 4), True),
)


def _mutar_a_pared(origen, destino, fila_tablero, columna):
    """Copia un .sok cambiando una celda de piso por pared. NUNCA toca `niveles/`."""
    shutil.copy(origen, destino)
    lineas = destino.read_text(encoding='utf-8').splitlines()

    fila_actual = -1
    for i, linea in enumerate(lineas):
        if linea.lstrip().startswith(';'):
            continue
        fila_actual += 1
        if fila_actual == fila_tablero:
            assert linea[columna] == ' ', (
                f'la celda ({fila_tablero}, {columna}) es {linea[columna]!r} y '
                f'la mutación esperaba piso'
            )
            lineas[i] = linea[:columna] + '#' + linea[columna + 1:]
            break
    else:
        raise AssertionError(f'no existe la fila {fila_tablero} en {origen}')

    destino.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    return destino


def _optimo(ruta):
    tablero, inicial = leer_archivo(ruta)
    r = bfs(Problema(tablero, inicial), max_nodos=MAX_NODOS)
    return r.costo if r.exito else None


def test_la_suite_detecta_un_nivel_alterado(tmp_path):
    """El criterio de aceptación: alterar N1 hace que el óptimo deje de ser 8."""
    copia = _mutar_a_pared(NIVELES / 'n1_micro.sok', tmp_path / 'n1_mutado.sok', 2, 2)
    assert _optimo(copia) != 8
    intacta = tmp_path / 'n1_intacto.sok'
    shutil.copy(NIVELES / 'n1_micro.sok', intacta)
    assert _optimo(intacta) == 8


@pytest.mark.parametrize('celda,rompe', CELDAS_DE_PISO_N1,
                         ids=lambda v: str(v) if isinstance(v, tuple) else str(v))
def test_mutacion_de_cada_celda_de_piso_de_n1(tmp_path, celda, rompe):
    """El mapa completo: qué celdas de N1 son críticas y cuáles no."""
    fila, columna = celda
    copia = _mutar_a_pared(NIVELES / 'n1_micro.sok',
                           tmp_path / 'n1_mutado.sok', fila, columna)
    if rompe:
        assert _optimo(copia) != 8
    else:
        assert _optimo(copia) == 8
