"""El reproductor: que dibuje la solución que encontró la búsqueda, y no otra."""

import pytest
from PIL import Image

from src.modelo import Problema
from src.viz import generar_gif, generar_tira
from src.viz.reproductor import (encabezado_de, es_empuje, indices_de_la_tira)

from .conftest import ESPERADO, cargar_problema, correr, parametros_niveles

NIVELES_DEL_REPRODUCTOR = ('n1_micro', 'n3_caminata')


@pytest.fixture(scope='module')
def gif(tmp_path_factory):
    """Genera el GIF de un nivel una sola vez y lo comparte, como `correr()`."""
    salida = tmp_path_factory.mktemp('gifs')
    hechos = {}

    def generar(nivel):
        if nivel not in hechos:
            hechos[nivel] = generar_gif(cargar_problema(nivel),
                                        correr(nivel, 'bfs').acciones,
                                        salida / f'{nivel}.gif')
        return hechos[nivel]

    return generar


@pytest.mark.parametrize('nivel', NIVELES_DEL_REPRODUCTOR)
def test_un_fotograma_por_estado(gif, resultado, nivel):
    """El GIF tiene `costo + 1` fotogramas, y se cuentan releyendo el archivo."""
    generado = gif(nivel)
    with Image.open(generado.ruta) as abierto:
        assert abierto.n_frames == resultado(nivel, 'bfs').costo + 1
    assert generado.fotogramas == resultado(nivel, 'bfs').costo + 1


@pytest.mark.parametrize('nivel', NIVELES_DEL_REPRODUCTOR)
def test_los_empujes_marcados_son_los_del_motor(gif, resultado, nivel):
    """El reproductor deduce los empujes comparando conjuntos de cajas; el motor"""
    assert gif(nivel).empujes == resultado(nivel, 'bfs').empujes \
        == ESPERADO[nivel]['empujes']


@pytest.mark.parametrize('nivel', NIVELES_DEL_REPRODUCTOR)
def test_el_ultimo_fotograma_es_meta(gif, nivel):
    """Se comprueba sobre los estados, no sobre los píxeles: si el camino no"""
    assert gif(nivel).ultimo_es_meta


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_la_tira_por_empujes_elige_el_inicial_los_empujes_y_el_final(
        problema, resultado, camino, nivel):
    """La cantidad de fotogramas de empuje coincide con los empujes de la solución."""
    estados = camino(nivel)
    elegidos = indices_de_la_tira(estados, 'empujes')

    assert elegidos[0] == 0
    assert elegidos[-1] == len(estados) - 1
    assert len(elegidos) == ESPERADO[nivel]['empujes'] + 1
    assert all(es_empuje(estados[paso - 1], estados[paso]) for paso in elegidos[1:])


@pytest.mark.parametrize('nivel', NIVELES_DEL_REPRODUCTOR)
def test_la_tira_todos_es_la_solucion_completa(camino, nivel):
    assert indices_de_la_tira(camino(nivel), 'todos') == list(range(len(camino(nivel))))


def test_la_tira_rechaza_un_criterio_desconocido(camino):
    with pytest.raises(ValueError):
        indices_de_la_tira(camino('n1_micro'), 'los_lindos')


def test_la_tira_se_escribe_y_se_abre(problema, resultado, tmp_path):
    r = resultado('n1_micro', 'bfs')
    tira = generar_tira(problema('n1_micro'), r.acciones, tmp_path / 'tira.png',
                        criterio='todos', titulo='n1_micro')
    with Image.open(tira.ruta) as abierto:
        assert abierto.size[0] > 0 and abierto.size[1] > 0
    assert tira.fotogramas == r.costo + 1


def test_el_reproductor_ignora_la_poda_de_deadlocks(resultado, tmp_path):
    """El reproductor dibuja el camino entero aunque el detector pode todo."""
    original = cargar_problema('n1_micro')
    r = resultado('n1_micro', 'bfs')
    todo_es_deadlock = Problema(original.tablero, original.inicial,
                                detector_deadlocks=lambda cajas, movida: True)

    gif = generar_gif(todo_es_deadlock, r.acciones, tmp_path / 'podado.gif')
    assert gif.fotogramas == r.costo + 1
    assert gif.empujes == r.empujes
    assert gif.ultimo_es_meta


def test_es_empuje_mira_las_cajas_y_no_al_jugador(camino):
    """Un paso es empuje si cambió el conjunto de cajas. En N1, de los 8 pasos"""
    estados = camino('n1_micro')
    empujes = [paso for paso in range(1, len(estados))
               if es_empuje(estados[paso - 1], estados[paso])]
    assert len(empujes) == ESPERADO['n1_micro']['empujes']


def test_el_encabezado_dice_paso_total_y_empuje():
    assert encabezado_de(5, 8, True) == 'paso 5/8 · empuje'
    assert encabezado_de(5, 8, False) == 'paso 5/8'
    assert encabezado_de(0, 8, False, 'n1_micro') == 'n1_micro · paso 0/8'
