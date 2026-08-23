"""Admisibilidad, consistencia e informatividad de las heurísticas.

Sobre un camino óptimo el costo real restante desde el estado i es exactamente
L - i, así que comprobar h(si) <= L - i verifica admisibilidad en todo el camino
sin resolver nada de nuevo.
"""

import pytest

from src.heuristicas import HEURISTICAS, construir
from verificaciones.admisibilidad import (informatividad, verificar_admisibilidad,
                                          verificar_consistencia)

from .conftest import (ESPERADO, HEURISTICAS_A_VERIFICAR,
                       HEURISTICAS_NO_ADMISIBLES, parametros_niveles)


@pytest.mark.parametrize('nombre_h', HEURISTICAS_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_admisible_sobre_el_camino_optimo(problema, camino, nivel, nombre_h):
    """h(si) <= L - i en los L+1 estados del camino óptimo, y h nunca negativa."""
    p = problema(nivel)
    fallos = verificar_admisibilidad(p, construir(nombre_h, p), camino(nivel))
    assert not fallos, f'{nombre_h} en {nivel}: ' + '; '.join(fallos)


@pytest.mark.parametrize('nombre_h', HEURISTICAS_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_consistente_sobre_el_camino_optimo(problema, camino, nivel, nombre_h):
    """h no puede bajar más de 1 en un solo movimiento."""
    p = problema(nivel)
    fallos = verificar_consistencia(p, construir(nombre_h, p), camino(nivel))
    assert not fallos, f'{nombre_h} en {nivel}: ' + '; '.join(fallos)


@pytest.mark.parametrize('nombre_h', HEURISTICAS_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_h_vale_cero_en_la_meta(problema, camino, nivel, nombre_h):
    """En la meta el costo restante es 0, así que toda h admisible y no negativa"""
    p = problema(nivel)
    h = construir(nombre_h, p)
    assert h(camino(nivel)[-1]) == 0


@pytest.mark.parametrize('nombre_h', HEURISTICAS_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_informatividad_no_baja(problema, camino, nivel, nombre_h):
    """h(s0)/óptimo no baja del valor medido al cerrar la Fase 2."""
    p = problema(nivel)
    medida = informatividad(construir(nombre_h, p), camino(nivel))
    assert medida >= ESPERADO[nivel]['informatividad'][nombre_h] - 1e-9


@pytest.mark.parametrize('nombre_h', ('h0', 'h1'))
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_h0_no_informa_y_h1_si(problema, camino, nivel, nombre_h):
    """h0 vale 0 en el inicial por definición; h1 vale la cantidad de cajas."""
    p = problema(nivel)
    h = construir(nombre_h, p)
    esperado = 0 if nombre_h == 'h0' else ESPERADO[nivel]['cajas']
    assert h(p.inicial) == esperado


def test_construir_rechaza_una_heuristica_inexistente():
    """El registro falla con un nombre desconocido en vez de devolver algo."""
    with pytest.raises(ValueError):
        construir('h_que_no_existe', None)


def test_todas_las_heuristicas_del_registro_estan_verificadas():
    """El registro y las listas de tests no se pueden desincronizar."""
    declaradas = set(HEURISTICAS_A_VERIFICAR) | set(HEURISTICAS_NO_ADMISIBLES)
    sin_declarar = set(HEURISTICAS) - declaradas
    assert not sin_declarar, (
        f'Heurísticas en el registro sin declarar: {sorted(sin_declarar)}. '
        f'Van a HEURISTICAS_A_VERIFICAR de tests/conftest.py con su '
        f'informatividad medida en ESPERADO, o a HEURISTICAS_NO_ADMISIBLES si '
        f'no ser admisible es justamente el punto.'
    )
    assert declaradas <= set(HEURISTICAS)
