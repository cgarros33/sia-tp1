"""Admisibilidad, consistencia e informatividad de las heurísticas.

ESTE ARCHIVO ES LA INFRAESTRUCTURA DE LA FASE 4
    Agregar h2, h3, h4, h5 o la no admisible es agregar un nombre a
    `HEURISTICAS_A_VERIFICAR` en `conftest.py` y una fila a la clave
    `informatividad` de cada nivel. No se escribe ningún test nuevo.

POR QUÉ ALCANZA CON EL CAMINO ÓPTIMO — el argumento que va a la presentación
    Verificar admisibilidad en general es caro: h(n) <= h*(n) exige conocer el
    costo óptimo restante DESDE CADA ESTADO, o sea resolver el nivel una vez por
    estado. Sobre un camino óptimo s0, s1, ..., sL ese costo se conoce gratis:

        si el camino completo es óptimo, el tramo que va de si a sL también lo
        es, y por lo tanto h*(si) = L - i EXACTAMENTE.

    (Si existiera un camino más corto de si a la meta, pegándolo al tramo s0..si
    daría una solución de menos de L movimientos, y L era el óptimo.)

    Entonces alcanza con comprobar h(si) <= L - i en cada uno de los L+1 estados
    del camino: son L+1 estados verificados por el precio de una búsqueda que
    igual había que hacer.

QUÉ NO ES ESTO
    No es una demostración. Es una condición NECESARIA: si falla, la heurística
    no es admisible, seguro; si pasa, sólo sabemos que no falla en los estados de
    ese camino. La demostración sigue siendo el argumento escrito de dos
    renglones que va en la diapositiva. Esto es la red que atrapa el error de
    IMPLEMENTACIÓN —un signo cambiado, un factor de más— que el argumento no
    puede atrapar, porque el argumento habla de la heurística ideal y no del
    código que escribimos.
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
    """h no puede bajar más de 1 en un solo movimiento.

    Con costo unitario, la desigualdad triangular h(n) <= c(n,n') + h(n') se
    reduce a eso. Es más fuerte que la admisibilidad: si vale en todo el espacio,
    A* nunca necesita reabrir un estado, porque el primer camino con el que lo
    alcanza ya es el óptimo. Se comprueba sobre los estados del camino óptimo y
    sus sucesores directos, no sobre todo el espacio.
    """
    p = problema(nivel)
    fallos = verificar_consistencia(p, construir(nombre_h, p), camino(nivel))
    assert not fallos, f'{nombre_h} en {nivel}: ' + '; '.join(fallos)


@pytest.mark.parametrize('nombre_h', HEURISTICAS_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_h_vale_cero_en_la_meta(problema, camino, nivel, nombre_h):
    """En la meta el costo restante es 0, así que toda h admisible y no negativa
    vale forzosamente 0 ahí.

    Se testea aparte de la admisibilidad porque un h(meta) distinto de 0 es el
    error más común y el más fácil de leer en la salida.
    """
    p = problema(nivel)
    h = construir(nombre_h, p)
    assert h(camino(nivel)[-1]) == 0


@pytest.mark.parametrize('nombre_h', HEURISTICAS_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_informatividad_no_baja(problema, camino, nivel, nombre_h):
    """h(s0)/óptimo no baja del valor medido al cerrar la Fase 2.

    Es la métrica que ordena la escalera de la Fase 4 y el eje horizontal del
    gráfico de dominancia empírica de la Fase 8: 0 es h0, que no informa nada, y
    1 sería la heurística perfecta. Los valores medidos son 0,000 en los cinco
    niveles para h0 y 0,125 / 0,089 / 0,019 / 0,057 / 0,013 para h1.

    La aserción es `>=` y no `==` a propósito: mejorar una heurística sin cambiar
    su nombre es legítimo, empeorarla en silencio no. La tolerancia de 1e-9 es
    ruido de punto flotante, no margen: los valores esperados están escritos como
    fracciones exactas en `conftest`.
    """
    p = problema(nivel)
    medida = informatividad(construir(nombre_h, p), camino(nivel))
    assert medida >= ESPERADO[nivel]['informatividad'][nombre_h] - 1e-9


@pytest.mark.parametrize('nombre_h', HEURISTICAS_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_h0_no_informa_y_h1_si(problema, camino, nivel, nombre_h):
    """h0 vale 0 en el inicial por definición; h1 vale la cantidad de cajas.

    Es el ancla que hace auditable la tabla de informatividad: el numerador de
    esas fracciones no es un decimal caído del cielo, es un número que se puede
    contar mirando el tablero.
    """
    p = problema(nivel)
    h = construir(nombre_h, p)
    esperado = 0 if nombre_h == 'h0' else ESPERADO[nivel]['cajas']
    # En los cinco niveles de la suite ninguna caja arranca sobre una meta, así
    # que h1 del inicial es la cantidad total de cajas. Si algún nivel futuro
    # arrancara con una caja ya colocada, este test lo haría notar.
    assert h(p.inicial) == esperado


def test_construir_rechaza_una_heuristica_inexistente():
    """El registro falla con un nombre desconocido en vez de devolver algo.

    Un `"heuristica": "h2"` mal tipeado en `config.json` daría una corrida
    perfectamente exitosa que no es la que se pidió.
    """
    with pytest.raises(ValueError):
        construir('h_que_no_existe', None)


def test_todas_las_heuristicas_del_registro_estan_verificadas():
    """El registro y las listas de tests no se pueden desincronizar.

    Es el guardián de la Fase 4: si alguien agrega h2 a `HEURISTICAS` y se olvida
    de declararla, la heurística nueva entraría a la presentación sin que nadie
    haya comprobado que es admisible. Este test falla con el nombre de la que
    falta y obliga a tomar la decisión explícitamente: o va a la lista de las que
    se verifican, o va a la de las que NO son admisibles a propósito.
    """
    declaradas = set(HEURISTICAS_A_VERIFICAR) | set(HEURISTICAS_NO_ADMISIBLES)
    sin_declarar = set(HEURISTICAS) - declaradas
    assert not sin_declarar, (
        f'Heurísticas en el registro sin declarar: {sorted(sin_declarar)}. '
        f'Van a HEURISTICAS_A_VERIFICAR de tests/conftest.py con su '
        f'informatividad medida en ESPERADO, o a HEURISTICAS_NO_ADMISIBLES si '
        f'no ser admisible es justamente el punto.'
    )
    # Al revés también: una heurística declarada que ya no está en el registro
    # deja tests parametrizados sobre algo que no existe.
    assert declaradas <= set(HEURISTICAS)
