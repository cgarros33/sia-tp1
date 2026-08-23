"""Lo que la Fase 1 verificaba a mano, ahora automatizado."""

import pytest

from src.modelo import NivelInvalido, Problema, leer_texto
from src.modelo.tablero import DESPLAZAMIENTO, DIRECCIONES, NOMBRE_DIR

from .conftest import ESPERADO, parametros_niveles


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_estructura_del_nivel(problema, nivel):
    """Cajas, metas y celdas transitables coinciden con la tabla."""
    esperado = ESPERADO[nivel]
    p = problema(nivel)
    assert len(p.inicial.cajas) == esperado['cajas']
    assert len(p.tablero.metas) == esperado['metas']
    assert len(p.tablero.transitables) == esperado['celdas']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_hay_tantas_cajas_como_metas(problema, nivel):
    """Sin esta igualdad el nivel no tiene solución posible, y además `es_meta()`"""
    p = problema(nivel)
    assert len(p.inicial.cajas) == len(p.tablero.metas)


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_ida_y_vuelta(problema, nivel):
    """dibujar(inicial) -> leer_texto() -> el mismo problema."""
    p = problema(nivel)
    tablero_vuelta, inicial_vuelta = leer_texto(p.tablero.dibujar(p.inicial), nivel)

    assert (tablero_vuelta.alto, tablero_vuelta.ancho) == (p.tablero.alto, p.tablero.ancho)
    assert tablero_vuelta.paredes == p.tablero.paredes
    assert tablero_vuelta.metas == p.tablero.metas
    assert tablero_vuelta.transitables == p.tablero.transitables
    assert inicial_vuelta == p.inicial
    assert tablero_vuelta.dibujar(inicial_vuelta) == p.tablero.dibujar(p.inicial)


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_sucesores_del_estado_inicial(problema, nivel):
    """Cuántos sucesores tiene el inicial y cuántos de ellos son empuje."""
    esperado = ESPERADO[nivel]
    sucesores = list(problema(nivel).sucesores(problema(nivel).inicial))
    assert len(sucesores) == esperado['sucesores']
    assert sum(1 for _, _, empuje in sucesores if empuje) == esperado['sucesores_empuje']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_ningun_sucesor_viola_las_reglas(problema, nivel):
    """Ni jugador ni cajas dentro de una pared, y nunca dos cajas en la misma celda."""
    p = problema(nivel)
    cantidad_cajas = len(p.inicial.cajas)

    def revisar(estado):
        assert estado.jugador in p.tablero.transitables
        assert estado.jugador not in p.tablero.paredes
        assert estado.jugador not in estado.cajas
        assert estado.cajas <= p.tablero.transitables
        assert len(estado.cajas) == cantidad_cajas

    for _, hijo, _ in p.sucesores(p.inicial):
        revisar(hijo)
        for _, nieto, _ in p.sucesores(hijo):
            revisar(nieto)


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_un_empuje_mueve_exactamente_una_caja(problema, nivel):
    """Un movimiento cambia el conjunto de cajas en una sola posición, o en ninguna."""
    p = problema(nivel)
    for _, hijo, hubo_empuje in p.sucesores(p.inicial):
        diferencia = p.inicial.cajas ^ hijo.cajas
        assert len(diferencia) == (2 if hubo_empuje else 0)


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_la_tabla_de_movimientos_esta_indexada_por_direccion(problema, nivel):
    """`mover[p][d]` tiene que ser la celda que da `DESPLAZAMIENTO[d]`, para todo d."""
    p = problema(nivel)
    for origen in p.tablero.transitables:
        fila, col = p.tablero.coordenadas(origen)
        for d in DIRECCIONES:
            df, dc = DESPLAZAMIENTO[d]
            nueva_fila, nueva_col = fila + df, col + dc
            dentro = (0 <= nueva_fila < p.tablero.alto
                      and 0 <= nueva_col < p.tablero.ancho)
            destino = p.tablero.indice(nueva_fila, nueva_col) if dentro else -1
            if destino in p.tablero.paredes:
                destino = -1
            assert p.tablero.mover[origen][d] == destino, (
                f'mover[{origen}][{d}] ({NOMBRE_DIR[d]}) debería ser {destino}'
            )


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_la_accion_devuelta_es_el_movimiento_que_ocurrio(problema, nivel):
    """El código de acción que devuelve `sucesores()` describe el movimiento real."""
    p = problema(nivel)
    for accion, hijo, _ in p.sucesores(p.inicial):
        fila0, col0 = p.tablero.coordenadas(p.inicial.jugador)
        fila1, col1 = p.tablero.coordenadas(hijo.jugador)
        assert (fila1 - fila0, col1 - col0) == DESPLAZAMIENTO[accion], (
            f'la acción {accion} ({NOMBRE_DIR[accion]}) movió al jugador '
            f'{(fila1 - fila0, col1 - col0)}'
        )


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_la_tabla_de_movimientos_es_simetrica(problema, nivel):
    """Si desde p se llega a q, desde q se vuelve a p con la dirección opuesta."""
    p = problema(nivel)
    opuesta = {0: 1, 1: 0, 2: 3, 3: 2}
    for origen in p.tablero.transitables:
        for d in DIRECCIONES:
            destino = p.tablero.mover[origen][d]
            if destino != -1:
                assert p.tablero.mover[destino][opuesta[d]] == origen


NIVELES_INVALIDOS = {
    'sin_jugador': (
        '#####\n'
        '#$. #\n'
        '#####'
    ),
    'dos_jugadores': (
        '######\n'
        '#@@$.#\n'
        '######'
    ),
    'sin_cajas': (
        '#####\n'
        '#@. #\n'
        '#####'
    ),
    'mas_cajas_que_metas': (
        '#######\n'
        '#@$$. #\n'
        '#######'
    ),
    'mas_metas_que_cajas': (
        '#######\n'
        '#@$.. #\n'
        '#######'
    ),
    'caracter_desconocido': (
        '#####\n'
        '#@$X#\n'
        '#####'
    ),
}


@pytest.mark.parametrize('caso', sorted(NIVELES_INVALIDOS))
def test_el_parser_rechaza_niveles_invalidos(caso):
    """Fallar temprano y con un mensaje concreto."""
    with pytest.raises(NivelInvalido):
        leer_texto(NIVELES_INVALIDOS[caso], caso)


def test_un_nivel_minimo_valido_si_se_parsea():
    """El contraste del test anterior: si TODO fuera inválido, no probaría nada."""
    tablero, inicial = leer_texto('#####\n#@$.#\n#####', 'minimo')
    p = Problema(tablero, inicial)
    assert len(inicial.cajas) == 1
    assert len(tablero.metas) == 1
    assert not p.es_meta(inicial)
