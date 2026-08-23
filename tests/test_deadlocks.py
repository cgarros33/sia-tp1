"""La poda de deadlocks: que no rompa nada y que sirva.

LA ASIMETRÍA QUE ORGANIZA ESTE ARCHIVO
    Un falso negativo —no ver un deadlock que existe— cuesta nodos y nada más.
    Un falso positivo —declarar muerto un estado que sí tenía solución— rompe la
    optimalidad. Los dos errores no cuestan lo mismo, así que casi todos los
    tests de acá apuntan al segundo.

POR QUÉ ALCANZA CON EL CAMINO ÓPTIMO — el mismo truco que la Fase 3
    Comprobar que un detector no tiene falsos positivos en general exigiría saber
    qué estados tienen solución, o sea resolver el nivel desde cada uno. Sobre el
    camino óptimo se sabe gratis: TODOS sus estados tienen solución, por
    definición. Entonces, si una capa marca uno de ellos, tiene un falso positivo
    seguro.

    Es una condición necesaria, no una demostración: si pasa, sólo sabemos que no
    falla en los estados de ese camino. La demostración sigue siendo el argumento
    escrito en el docstring de cada regla en `src/deadlocks.py`. Esto es la red
    que atrapa el error de implementación que el argumento no puede atrapar.

LOS TABLEROS DE ACÁ SE CONSTRUYEN COMO TEXTO, NUNCA EN `niveles/`
    Y las configuraciones de cajas con las que se los interroga no tienen por qué
    ser alcanzables ni tener la misma cantidad de cajas que el nivel: un detector
    es una función de la geometría y de un conjunto de cajas, y se lo testea como
    tal.
"""

import pytest

from src.busqueda import bfs
from src.deadlocks import DETECTORES, construir
from src.modelo import Problema, leer_texto

from .conftest import (COLUMNAS_BFS, DETECTORES_A_VERIFICAR, ESPERADO,
                       MAX_NODOS, cargar_problema, parametros_niveles)

# Un pasillo contra la pared de arriba y una fila de abajo con la única meta.
# Las celdas vivas son exactamente (2,2), (2,3) y (2,4): una caja en la fila 1
# sólo se puede empujar en horizontal —arriba hay pared y para empujarla hacia
# abajo el jugador tendría que pararse en esa pared— y en la fila 1 no hay
# ninguna meta.
PASILLO = """\
#######
#     #
#@$ . #
#######"""

# Las cuatro metas forman un bloque de 2x2, como en n4_matching. El estado meta
# de este tablero ES un cuadrado de 2x2 lleno de cajas.
BLOQUE_DE_METAS = """\
#######
#@    #
# **  #
# **  #
#######"""


def _empujes(camino):
    """(cajas, caja_movida) de cada empuje del camino, como los ve el detector.

    El motor consulta al detector sólo después de un empuje y le pasa la caja
    recién movida. Acá se reconstruye exactamente esa llamada: la caja movida es
    la que aparece en el conjunto de cajas del estado siguiente y no estaba en el
    anterior.
    """
    for anterior, siguiente in zip(camino, camino[1:]):
        movidas = siguiente.cajas - anterior.cajas
        if movidas:
            yield siguiente.cajas, next(iter(movidas))


# --- lo que no se puede romper: falsos positivos -----------------------------

@pytest.mark.parametrize('capa', DETECTORES_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_ninguna_capa_poda_el_camino_optimo(camino, nivel, capa):
    """Todos los estados de un camino óptimo tienen solución: podar uno es un bug.

    En `n4_matching` este test es además el que cuida la cláusula "al menos una
    caja fuera de meta" de la regla de 2x2: sus cuatro metas son un bloque de
    2x2, así que el último estado del camino es un cuadrado lleno. Sin la
    cláusula se podan 4 de los 71 estados y BFS declara el nivel irresoluble.
    """
    detectar = construir(capa, cargar_problema(nivel).tablero)
    podados = [i for i, (cajas, movida) in enumerate(_empujes(camino(nivel)))
               if detectar(cajas, movida)]
    assert not podados, (
        f'{capa} en {nivel}: poda los empujes {podados} del camino óptimo, que '
        f'por definición tienen solución. Es un falso positivo.')


@pytest.mark.parametrize('capa', DETECTORES_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_la_poda_no_cambia_el_costo(resultado, nivel, capa):
    """El criterio de la fase: mismo costo y mismos empujes que sin poda.

    Es verdad externa: son los récords publicados en game-sokoban.com. Si la
    poda cambiara el costo, el detector estaría sacando estados que sí tenían
    solución.
    """
    esperado = ESPERADO[nivel]
    r = resultado(nivel, 'bfs', capa)
    assert r.exito
    assert r.costo == esperado['costo']
    assert r.empujes == esperado['empujes']


@pytest.mark.parametrize('capa', DETECTORES_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_la_poda_devuelve_la_misma_solucion(resultado, nivel, capa):
    """No sólo el mismo costo: exactamente la misma secuencia de movimientos.

    Es más fuerte que el test anterior y sale del mismo argumento. Un estado sin
    solución tiene todos sus sucesores sin solución, así que ningún estado del
    camino a la meta puede haber sido descubierto a través de uno podado. Los
    nodos que llevan a la meta conservan su padre y su orden de descubrimiento,
    y BFS devuelve el mismo camino.
    """
    assert resultado(nivel, 'bfs', capa).acciones == resultado(nivel, 'bfs').acciones


# --- lo que la poda tiene que comprar ---------------------------------------

@pytest.mark.parametrize('capa', DETECTORES_A_VERIFICAR)
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_la_poda_no_aumenta_los_nodos(resultado, nivel, capa):
    """Podar sólo saca sucesores, así que no puede agregar trabajo.

    Sacar elementos de la frontera no reordena a los que quedan —el contador de
    inserción es monótono—, de modo que lo que se expande con poda es un
    subconjunto de lo que se expandía sin ella. Es `<=` y no `<` porque en un
    nivel donde la capa no encontrara nada que podar, las dos corridas serían la
    misma búsqueda.
    """
    con_poda = resultado(nivel, 'bfs', capa)
    sin_poda = resultado(nivel, 'bfs')
    assert con_poda.nodos_expandidos <= sin_poda.nodos_expandidos
    assert con_poda.nodos_generados <= sin_poda.nodos_generados
    assert con_poda.memoria_maxima <= sin_poda.memoria_maxima


@pytest.mark.parametrize('capa', ('estaticos', 'congelados'))
@pytest.mark.parametrize('nivel', parametros_niveles())
def test_completo_no_es_peor_que_ninguna_de_las_dos_capas(resultado, nivel, capa):
    """`completo` poda todo lo que poda cada regla suelta, así que expande menos.

    Lo que NO se testea es que una capa domine a la otra, porque es falso: en
    `n2_akk04` la regla de 2x2 expande 9.839 nodos y la estática 14.178, y en
    `n4_matching` es al revés, 214.466 contra 73.813. Por eso son dos capas
    medibles por separado y no una sola.
    """
    assert (resultado(nivel, 'bfs', 'completo').nodos_expandidos
            <= resultado(nivel, 'bfs', capa).nodos_expandidos)


# --- regresión interna: los números congelados de la fase -------------------

@pytest.mark.parametrize('nivel', parametros_niveles())
def test_columnas_congeladas_de_bfs_con_poda_completa(resultado, nivel):
    """Las cinco columnas de BFS con la poda completa, exactas.

    Mismo estatus que las de la Fase 3: son métricas de NUESTRA implementación,
    no verdad externa. Si una cambia, no se actualiza el número esperado hasta
    entender por qué cambió.
    """
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
    """Cuántas celdas muertas tiene cada nivel, y que ninguna caja arranque en una.

    Lo segundo es un control cruzado contra la Fase 2: si una caja del estado
    inicial cayera en una celda muerta el nivel sería irresoluble, y BFS
    encuentra el óptimo publicado en los cinco. O sea que si esto saltara, el
    detector estaría mal, no el nivel.
    """
    from src.heuristicas.distancias import celdas_muertas
    p = problema(nivel)
    muertas = celdas_muertas(p.tablero)
    assert len(muertas) == ESPERADO[nivel]['deadlocks']['celdas_muertas']
    assert not (p.inicial.cajas & muertas)


# --- las dos reglas, sobre tableros armados a mano ---------------------------

def test_una_caja_en_un_rincon_la_ven_las_dos_reglas():
    """El rincón es el deadlock de manual, y las dos reglas llegan por caminos
    distintos: para la estática es una celda de la que no se sale a empujones,
    para la de 2x2 es un cuadrado con tres paredes."""
    tablero, _ = leer_texto(PASILLO)
    rincon = tablero.indice(1, 1)
    for capa in DETECTORES_A_VERIFICAR:
        detectar = construir(capa, tablero)
        assert detectar(frozenset({rincon}), rincon), capa


def test_una_celda_muerta_que_no_es_rincon_la_ve_solo_la_estatica():
    """Una caja sola en el pasillo de arriba: no se puede empujar salvo en
    horizontal y en esa fila no hay ninguna meta, así que no llega nunca. Ningún
    cuadrado de 2x2 está lleno, así que la regla dinámica no la ve."""
    tablero, _ = leer_texto(PASILLO)
    muerta = tablero.indice(1, 3)
    assert construir('estaticos', tablero)(frozenset({muerta}), muerta)
    assert not construir('congelados', tablero)(frozenset({muerta}), muerta)
    assert construir('completo', tablero)(frozenset({muerta}), muerta)


def test_dos_cajas_contra_la_pared_las_ve_solo_la_regla_de_2x2():
    """El caso que justifica que la regla dinámica exista.

    Las dos celdas son vivas: desde cualquiera de las dos, una caja sola llega a
    la meta. Muertas quedan JUNTAS, y eso depende de dónde está la otra caja, que
    es exactamente lo que una tabla precalculada por celda no puede saber.
    """
    tablero, _ = leer_texto(PASILLO)
    izquierda, derecha = tablero.indice(2, 2), tablero.indice(2, 3)
    juntas = frozenset({izquierda, derecha})

    assert not construir('estaticos', tablero)(juntas, derecha)
    assert construir('congelados', tablero)(juntas, derecha)
    # Y cada una por su cuenta no es deadlock para ninguna de las dos reglas.
    for capa in DETECTORES_A_VERIFICAR:
        detectar = construir(capa, tablero)
        assert not detectar(frozenset({izquierda}), izquierda), capa
        assert not detectar(frozenset({derecha}), derecha), capa


def test_un_2x2_con_todas_las_cajas_en_meta_no_es_deadlock():
    """LA CLÁUSULA. Un cuadrado lleno de cajas, todas sobre metas, es el nivel
    resuelto: las cajas no se mueven más y no hace falta que se muevan.

    Sin este caso el detector podaría el estado meta de `n4_matching`, cuyas
    cuatro metas son un bloque de 2x2, y el nivel devolvería "sin solución".
    """
    tablero, _ = leer_texto(BLOQUE_DE_METAS)
    bloque = frozenset(tablero.indice(f, c) for f in (2, 3) for c in (2, 3))
    assert bloque == tablero.metas
    assert not construir('congelados', tablero)(bloque, tablero.indice(3, 3))


def test_el_mismo_2x2_con_una_caja_fuera_de_meta_si_lo_es():
    """El control del test anterior: el mismo cuadrado corrido una columna, con
    dos de sus cuatro celdas fuera de meta, sí es un deadlock."""
    tablero, _ = leer_texto(BLOQUE_DE_METAS)
    corrido = frozenset(tablero.indice(f, c) for f in (2, 3) for c in (3, 4))
    assert construir('congelados', tablero)(corrido, tablero.indice(3, 4))


# --- el registro -------------------------------------------------------------

def test_sin_poda_devuelve_none_y_no_una_funcion():
    """`'ninguno'` tiene que devolver `None`, no una función que siempre dice que
    no: es lo que hace que la corrida sin poda sea EXACTAMENTE la de las Fases 2
    a 4 y no una equivalente."""
    assert construir('ninguno', cargar_problema('n1_micro').tablero) is None


def test_construir_rechaza_un_detector_inexistente():
    """Un `"deadlocks": "estatico"` mal tipeado en `config.json` daría una corrida
    perfectamente exitosa que no es la que se pidió."""
    with pytest.raises(ValueError):
        construir('no_existe', cargar_problema('n1_micro').tablero)


def test_todos_los_detectores_del_registro_estan_verificados():
    """El guardián, igual que el de las heurísticas.

    Si alguien agrega una regla nueva a `DETECTORES` y se olvida de declararla,
    entraría a la presentación sin que nadie haya comprobado que no poda estados
    con solución. Este test falla con el nombre de la que falta.
    """
    declarados = set(DETECTORES_A_VERIFICAR) | {'ninguno'}
    assert set(DETECTORES) == declarados, (
        f'Detectores sin declarar: {sorted(set(DETECTORES) - declarados)}. Van a '
        f'DETECTORES_A_VERIFICAR de tests/conftest.py, que es la lista que se '
        f'somete a los tests de falsos positivos.')


def test_reconstruir_un_camino_ignora_la_poda():
    """`reconstruir_estados()` pide los sucesores sin podar, a propósito.

    La poda es una optimización de la búsqueda, no una regla del juego. Si un
    detector tuviera un bug y descartara un estado legal, con la poda activada el
    reproductor de la Fase 7 cortaría el camino a la mitad con un error de
    "acción no legal", que apunta al lugar equivocado.

    Se comprueba con un detector que poda TODO: la búsqueda queda sin solución y
    aun así el camino que había encontrado antes se reconstruye entero.
    """
    original = cargar_problema('n1_micro')
    acciones = bfs(original, max_nodos=MAX_NODOS).acciones

    todo_es_deadlock = Problema(original.tablero, original.inicial,
                                detector_deadlocks=lambda cajas, movida: True)
    estados = todo_es_deadlock.reconstruir_estados(acciones)
    assert len(estados) == len(acciones) + 1
    assert todo_es_deadlock.es_meta(estados[-1])

    assert bfs(todo_es_deadlock, max_nodos=MAX_NODOS).motivo_fin == 'sin_solucion'
