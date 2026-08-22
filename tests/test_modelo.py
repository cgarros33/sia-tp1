"""Lo que la Fase 1 verificaba a mano, ahora automatizado.

QUÉ CUBRE
    Que el nivel que lee el parser es el que está escrito en el archivo, y que
    el modelo de transición respeta las reglas de Sokoban. Es la capa de abajo:
    si algo de acá falla, todo lo que mide la búsqueda mide otro juego.

EL TEST QUE MÁS PAGA — la ida y vuelta
    Dibujar el estado inicial, volver a parsear el dibujo y obtener el mismo
    problema. Cierra el círculo entre el lector y el escritor: un error en
    cualquiera de los dos rompe la igualdad. Y no es un test de laboratorio,
    porque el reproductor estado por estado de la Fase 7 usa exactamente
    `dibujar()`: si esto falla, ese reproductor va a mostrar tableros mal en la
    presentación.

LOS NIVELES INVÁLIDOS SE CONSTRUYEN COMO TEXTO, NUNCA COMO ARCHIVOS
    `niveles/` está verificado contra los récords publicados y no se toca. Un
    nivel roto guardado ahí sería, además, una invitación a que alguien lo use
    por error.
"""

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
    """Sin esta igualdad el nivel no tiene solución posible, y además `es_meta()`
    se apoya en ella: compara conjuntos, y eso sólo equivale a "todas las cajas
    están en meta" si los tamaños coinciden."""
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
    # Y la vuelta completa: el dibujo del problema reparseado tiene que ser
    # idéntico carácter a carácter al original.
    assert tablero_vuelta.dibujar(inicial_vuelta) == p.tablero.dibujar(p.inicial)


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_sucesores_del_estado_inicial(problema, nivel):
    """Cuántos sucesores tiene el inicial y cuántos de ellos son empuje.

    Es la prueba más barata de que el modelo de transición y la geometría del
    nivel son los que creemos: cambiar una sola pared del archivo cambia estos
    dos números en la mayoría de los casos.
    """
    esperado = ESPERADO[nivel]
    sucesores = list(problema(nivel).sucesores(problema(nivel).inicial))
    assert len(sucesores) == esperado['sucesores']
    assert sum(1 for _, _, empuje in sucesores if empuje) == esperado['sucesores_empuje']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_ningun_sucesor_viola_las_reglas(problema, nivel):
    """Ni jugador ni cajas dentro de una pared, y nunca dos cajas en la misma celda.

    Se comprueba sobre los sucesores del inicial y sobre los de esos sucesores:
    dos niveles alcanzan para ejercitar empujes, porque en varios niveles el
    inicial todavía no tiene ninguno disponible.
    """
    p = problema(nivel)
    cantidad_cajas = len(p.inicial.cajas)

    def revisar(estado):
        assert estado.jugador in p.tablero.transitables
        assert estado.jugador not in p.tablero.paredes
        assert estado.jugador not in estado.cajas
        assert estado.cajas <= p.tablero.transitables
        # `cajas` es un frozenset, así que dos cajas superpuestas se colapsarían
        # en una sola entrada: la cuenta es la que detecta el error.
        assert len(estado.cajas) == cantidad_cajas

    for _, hijo, _ in p.sucesores(p.inicial):
        revisar(hijo)
        for _, nieto, _ in p.sucesores(hijo):
            revisar(nieto)


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_un_empuje_mueve_exactamente_una_caja(problema, nivel):
    """Un movimiento cambia el conjunto de cajas en una sola posición, o en ninguna.

    Es la regla del juego que sostiene la admisibilidad de h1 —"un movimiento
    cambia la cuenta de cajas fuera de meta a lo sumo en 1"—, así que conviene
    tenerla testeada acá abajo y no darla por sabida allá arriba.
    """
    p = problema(nivel)
    for _, hijo, hubo_empuje in p.sucesores(p.inicial):
        diferencia = p.inicial.cajas ^ hijo.cajas
        assert len(diferencia) == (2 if hubo_empuje else 0)


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_la_tabla_de_movimientos_esta_indexada_por_direccion(problema, nivel):
    """`mover[p][d]` tiene que ser la celda que da `DESPLAZAMIENTO[d]`, para todo d.

    Suena a tautología y NO lo es: `_construir_tabla_de_movimientos()` arma cada
    fila con `append` recorriendo `DIRECCIONES`, así que la fila queda indexada
    por la POSICIÓN dentro de esa tupla y no por la constante de dirección. Hoy
    coinciden porque `DIRECCIONES` es (0, 1, 2, 3); si alguien la reordena, la
    tabla queda permutada y `mover[p][ARRIBA]` devuelve la celda de otra
    dirección.

    Lo insidioso es que la búsqueda seguiría dando los mismos números, porque
    `sucesores()` recorre la misma tupla permutada y las dos permutaciones se
    cancelan. Lo que se rompe en silencio es el CÓDIGO DE ACCIÓN que se devuelve:
    `sucesores()` hace `yield d`, y ese `d` es el que `NOMBRE_DIR` traduce a la
    letra U/D/L/R de la solución. O sea que la solución impresa —y el GIF de la
    Fase 7— mostrarían movimientos que no son los que hizo la búsqueda, con todos
    los tests en verde. Éste es el test que lo impide.
    """
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
    """El código de acción que devuelve `sucesores()` describe el movimiento real.

    Es la otra mitad del test anterior, y la que se ve en la presentación: si
    `sucesores()` devuelve la acción ARRIBA para un movimiento que fue a la
    derecha, la cadena de letras que imprime `main.py` es una mentira prolija.
    """
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
    """Si desde p se llega a q, desde q se vuelve a p con la dirección opuesta.

    Atrapa el error clásico de las posiciones linealizadas: moverse a la
    izquierda desde la columna 0 da p-1, que es una celda existente pero de la
    fila anterior. Si `mover` no controlara las dos coordenadas por separado, el
    tablero tendría teletransportes de borde a borde y esta simetría se rompería.
    """
    p = problema(nivel)
    opuesta = {0: 1, 1: 0, 2: 3, 3: 2}
    for origen in p.tablero.transitables:
        for d in DIRECCIONES:
            destino = p.tablero.mover[origen][d]
            if destino != -1:
                assert p.tablero.mover[destino][opuesta[d]] == origen


# --- el parser tiene que rechazar lo que no es un nivel jugable -------------

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
    """Fallar temprano y con un mensaje concreto.

    Un nivel mal transcripto que igual se parsea no da un error: da una búsqueda
    que se comporta raro y que se depura durante horas creyendo que el bug está
    en el motor.
    """
    with pytest.raises(NivelInvalido):
        leer_texto(NIVELES_INVALIDOS[caso], caso)


def test_un_nivel_minimo_valido_si_se_parsea():
    """El contraste del test anterior: si TODO fuera inválido, no probaría nada."""
    tablero, inicial = leer_texto('#####\n#@$.#\n#####', 'minimo')
    p = Problema(tablero, inicial)
    assert len(inicial.cajas) == 1
    assert len(tablero.metas) == 1
    assert not p.es_meta(inicial)
