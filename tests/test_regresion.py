"""Regresión interna: el comportamiento congelado de nuestra implementación.

LA DISTINCIÓN QUE ORGANIZA ESTE ARCHIVO
    Nodos expandidos, generados, frontera máxima, visitados y memoria son
    métricas de NUESTRO código, no verdad externa. Dependen del orden en que se
    generan los sucesores, del criterio de desempate de la frontera y de la
    política de estados repetidos. No hay ningún récord publicado contra el cual
    compararlos: se midieron una vez al cerrar la Fase 2 y viven en `conftest`.

    SI UN VALOR DE ACÁ CAMBIA, NO SE ACTUALIZA EL NÚMERO ESPERADO. Un número que
    cambia después de un refactor es la señal de que el refactor cambió el
    comportamiento. Puede ser una mejora legítima o puede ser un bug, y el test
    no distingue: esa parte la hace una persona.

POR QUÉ `memoria_maxima` NO ES LA SUMA DE LAS OTRAS DOS COLUMNAS
    Alguien va a sumar frontera máxima más visitados y no le va a dar. En N2:
    2.691 + 46.779 = 49.470, y la tabla dice 49.434.

    `memoria_maxima` es el PICO DE LA SUMA, no la suma de los picos. La frontera
    de BFS alcanza su máximo en el medio de la corrida —en N2, en la expansión
    40.180 de 44.124— y para entonces la estructura de visitados todavía va por
    42.871. Cuando la suma alcanza su máximo, en la última expansión, la frontera
    ya bajó a 2.655. De ahí los 36 de diferencia.

    En N1 la suma da exacto por un motivo de tamaño, no por una propiedad: la
    frontera llega a 12 en la expansión 27 y se queda en 12 hasta la última, la
    38, que es justo cuando visitados llega a su valor final de 50. En un pasillo
    de 12 celdas no hay lugar para que la frontera decrezca antes del final.

    Segundo detalle: la columna "visitados" ni siquiera es un pico, es el valor
    FINAL de la estructura. Con política 'cerrado' sólo crece, así que final =
    máximo, pero se está sumando un pico de mitad de corrida con un valor de
    cierre. Ver `Resultado.memoria_maxima` en `src/busqueda/motor.py`.
"""

import shutil

import pytest

from src.busqueda import bfs
from src.modelo import Problema, leer_archivo

from .conftest import (COLUMNAS_BFS, ESPERADO, MAX_NODOS, NIVELES,
                       cargar_problema, parametros_niveles)


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_columnas_congeladas_de_bfs(resultado, nivel):
    """Las cinco columnas de BFS, exactas.

    Se comparan como un dict entero y no con cinco aserciones sueltas: cuando
    falla, el mensaje muestra las cinco juntas, y ver cuáles se movieron y cuáles
    no es la mitad del diagnóstico. Si cambian expandidos y generados pero no la
    frontera, el orden de sucesores es sospechoso; si cambia sólo la memoria, lo
    que cambió es la política de repetidos.
    """
    r = resultado(nivel, 'bfs')
    medido = {columna: getattr(r, columna) for columna in COLUMNAS_BFS}
    assert medido == ESPERADO[nivel]['bfs']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_memoria_maxima_es_el_pico_de_la_suma(resultado, nivel):
    """`memoria_maxima` está entre el pico de la frontera y la suma de los picos.

    Es la comprobación de que se mide lo que decimos que se mide, y deja el
    hecho escrito como test y no sólo como comentario. Las dos cotas:

      - No puede ser MENOR que ninguno de los dos picos por separado, porque en
        el instante de cada pico el otro sumando es no negativo.
      - No puede ser MAYOR que la suma de los picos, porque cada sumando está
        acotado por su propio máximo en todo instante.

    La igualdad con la cota de arriba sólo se da cuando los dos picos caen en el
    mismo instante, que es lo que pasa en N1 y no en los demás.
    """
    r = resultado(nivel, 'bfs')
    assert r.memoria_maxima >= r.frontera_maxima
    assert r.memoria_maxima >= r.estados_visitados
    assert r.memoria_maxima <= r.frontera_maxima + r.estados_visitados


def test_en_n1_la_suma_da_exacto_y_en_n2_no(resultado):
    """El caso concreto que alguien va a mirar sumando las dos columnas a mano.

    Está escrito como test para que la explicación del docstring del módulo no
    quede como una afirmación sin respaldo.
    """
    r1 = resultado('n1_micro', 'bfs')
    assert r1.memoria_maxima == r1.frontera_maxima + r1.estados_visitados == 62

    r2 = resultado('n2_akk04', 'bfs')
    assert r2.frontera_maxima + r2.estados_visitados == 49_470
    assert r2.memoria_maxima == 49_434


# --- determinismo -----------------------------------------------------------

@pytest.mark.parametrize('nivel', ('n2_akk04', 'n3_caminata'))
@pytest.mark.parametrize('metodo', ('bfs', 'dfs', 'greedy_h1', 'astar_h1'))
def test_determinismo(nivel, metodo):
    """Dos corridas seguidas del mismo método sobre el mismo nivel son idénticas.

    ESTE TEST EXISTE POR UNA RAZÓN CONCRETA. En la Fase 2, con corte por reloj,
    IDDFS daba 3.453.866 nodos en una corrida y 1.798.624 en la siguiente: el
    timeout cortaba en un punto distinto según cómo venía la máquina. El corte
    por límite de nodos lo arregló, y este test está para que nadie reintroduzca
    un timeout sin darse cuenta.

    No usa la caché de `conftest.correr()` a propósito: acá justamente hay que
    lanzar la búsqueda dos veces de verdad.
    """
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
    """IDDFS en N2: el caso exacto donde el timeout daba 3.453.866 y 1.798.624.

    Va marcado `lento` porque son 1.261.013 nodos por corrida y hay dos.
    """
    from .conftest import _lanzar
    p = cargar_problema('n2_akk04')
    primera = _lanzar(p, 'iddfs', 'n2_akk04')
    segunda = _lanzar(p, 'iddfs', 'n2_akk04')
    assert primera.nodos_expandidos == segunda.nodos_expandidos


# --- los métodos no óptimos, con la afirmación precisa ----------------------

@pytest.mark.parametrize('nivel', parametros_niveles())
def test_dfs_nunca_por_debajo_del_optimo(resultado, nivel):
    """DFS puede dar cualquier cosa MENOS un costo menor al óptimo.

    Si diera menor, el "óptimo" publicado no sería óptimo o el costo estaría mal
    contado. Es la afirmación fuerte y vale en los cinco niveles.
    """
    r = resultado(nivel, 'dfs')
    assert r.exito
    assert r.costo >= ESPERADO[nivel]['costo']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_dfs_es_estrictamente_peor_salvo_en_n1(resultado, nivel):
    """DFS encuentra UNA solución, no la mejor. N1 es la excepción documentada.

    N1 es un pasillo de 12 celdas sin ramificación real: DFS cae en el óptimo sin
    buscarlo, y lo hace con los 24 órdenes posibles de `DIRECCIONES`. En N2 el
    rango de esos mismos 24 órdenes es 113-181 contra un óptimo de 45, y en N3 es
    164-448 contra 104: ahí el test estricto es seguro.

    La excepción está en la tabla de `conftest` y no escondida en un `if`, para
    que se lea junto al resto de los datos del nivel.
    """
    esperado = ESPERADO[nivel]
    r = resultado(nivel, 'dfs')
    if esperado['dfs_estrictamente_peor']:
        assert r.costo > esperado['costo']
    else:
        assert r.costo == esperado['costo']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_greedy_es_mas_barato_y_no_mejor(resultado, nivel):
    """Greedy expande menos nodos que BFS y su costo es MAYOR O IGUAL al óptimo.

    Documenta el compromiso velocidad contra optimalidad. Que en N1 y N2 dé
    exactamente el óptimo no contradice nada: Greedy no da garantía, y no dar
    garantía no es lo mismo que garantizar lo contrario.
    """
    r_greedy = resultado(nivel, 'greedy_h1')
    r_bfs = resultado(nivel, 'bfs')
    assert r_greedy.exito
    assert r_greedy.nodos_expandidos < r_bfs.nodos_expandidos
    assert r_greedy.costo >= ESPERADO[nivel]['costo']


@pytest.mark.parametrize('nivel', parametros_niveles())
def test_astar_h1_domina_a_astar_h0(resultado, nivel):
    """A*(h1) no expande más nodos que A*(h0) y devuelve el mismo costo.

    Es el primer escalón de la dominancia empírica que la Fase 4 va a extender a
    h2...h5: si h1 >= h0 en todo estado y las dos son admisibles, A*(h1) no puede
    expandir más. Acá vale el "no más" y no el "estrictamente menos", porque en un
    nivel donde h1 valiera 0 en todos lados las dos serían la misma búsqueda.
    """
    r_h0 = resultado(nivel, 'astar_h0')
    r_h1 = resultado(nivel, 'astar_h1')
    assert r_h1.costo == r_h0.costo
    assert r_h1.nodos_expandidos <= r_h0.nodos_expandidos


# --- IDDFS: la afirmación de los libros, corregida --------------------------

@pytest.mark.lento
@pytest.mark.parametrize('nivel', ('n2_akk04', 'n3_caminata'))
def test_iddfs_ahorra_frontera_pero_no_memoria(resultado, nivel):
    """LA AFIRMACIÓN CORREGIDA, y es el resultado más interesante de la Fase 2.

    Los libros dicen que IDDFS usa mucha menos memoria que BFS. En NUESTRA
    implementación eso es FALSO, y el test dice lo que sí es cierto:

      - Su FRONTERA es más chica, y CUÁNTO depende del nivel: 49 nodos contra
        2.691 en N2 son 55x, pero 53 contra 220 en N3 son apenas 4,2x. El
        ahorro de frontera no es una constante del método, es una consecuencia
        de la forma del árbol: en N3, con 2 cajas y una solución de 104
        movimientos, el factor de ramificación es tan bajo que ni BFS acumula
        mucha frontera. Por eso la aserción usa un factor 2 y los números
        medidos quedan acá escritos.
      - Expande muchísimos más nodos: 1.261.013 contra 44.124 en N2 (29x) y
        1.005.854 contra 6.360 en N3 (158x). Ése es el precio del trabajo
        repetido entre iteraciones.
      - Pero su MEMORIA TOTAL es COMPARABLE a la de BFS: 0,87x en N2 y 0,98x en
        N3. No ahorra nada apreciable.

    El motivo es que nuestro IDDFS mantiene estructura de visitados —política
    'mejor_g'—, porque sin ella, en Sokoban, las transposiciones lo hacen
    inviable. Al guardarlos, la ventaja de memoria se muda de la pila al
    diccionario y desaparece. La versión de manual es `iddfs_puro`, que
    efectivamente ahorra memoria y sólo termina en N1.

    Testear "IDDFS usa mucha menos memoria" habría sido testear el libro en vez
    de nuestro código, y habría fallado.
    """
    r_iddfs = resultado(nivel, 'iddfs')
    r_bfs = resultado(nivel, 'bfs')
    assert r_iddfs.exito

    assert r_iddfs.frontera_maxima < r_bfs.frontera_maxima / 2
    assert r_iddfs.nodos_expandidos > r_bfs.nodos_expandidos * 10
    # La cota de abajo es la que importa: prohíbe afirmar el ahorro de memoria.
    # La de arriba está para que el test siga siendo informativo si alguien
    # cambia la política y la memoria se dispara.
    assert 0.5 <= r_iddfs.memoria_maxima / r_bfs.memoria_maxima <= 1.2


def test_iddfs_puro_si_ahorra_memoria_de_verdad():
    """El contraste: sin estructura de visitados, IDDFS sí tiene memoria chica.

    Y paga el precio: 137 nodos expandidos contra 38 de BFS en N1, y en ningún
    otro nivel de la suite termina. Existe para poder MEDIR ese intercambio.
    """
    from src.busqueda import iddfs_puro
    p = cargar_problema('n1_micro')
    r_puro = iddfs_puro(p, max_nodos=MAX_NODOS, nivel='n1_micro')
    r_bfs = bfs(p, max_nodos=MAX_NODOS, nivel='n1_micro')
    assert r_puro.exito
    assert r_puro.costo == r_bfs.costo
    assert r_puro.estados_visitados == 0
    assert r_puro.memoria_maxima < r_bfs.memoria_maxima / 2
    assert r_puro.nodos_expandidos > r_bfs.nodos_expandidos


# --- el test de mutación deliberada ----------------------------------------
#
# Es la comprobación de que la suite realmente detecta un nivel alterado y no
# está pasando por casualidad. Sin esto, "los tests pasan" no dice nada.
#
# LA MUTACIÓN VA DE PISO A PARED, Y NO AL REVÉS. La especificación de la fase
# pedía cambiar una pared por piso, y ESO NO PUEDE FUNCIONAR EN N1: abrir una
# celda nunca elimina un camino que ya existía, así que el óptimo sólo puede
# quedarse en 8 o bajar, y en N1 ninguna apertura individual crea un atajo.
# Probamos las 33 mutaciones pared->piso posibles y ninguna cambia el óptimo.
#
# (Las cinco del borde derecho parecen cambiarlo, pero es un artefacto: el
# parser hace rstrip() de cada fila y rellena las filas cortas con pared, así que
# borrar el '#' final de '#    #' deja '#', que se rellena a '######' y TAPIA el
# pasillo. El test pasaría por la razón contraria a la que dice su nombre.)
#
# Cerrar una celda sí puede romper el óptimo, y en N1 lo rompe en 7 de las 9
# celdas de piso. Es la dirección honesta de la mutación.

#: (fila, columna) de las 9 celdas de piso vacío de n1_micro.sok, y si cerrarlas
#: rompe la solución. Las dos que no la rompen son los rincones de la fila 1 por
#: los que la solución óptima no pasa.
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

    # Las líneas de comentario ';' no cuentan como filas del tablero: hay que
    # saltearlas para que (fila, columna) signifique lo mismo que en el tablero.
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
    """El criterio de aceptación: alterar N1 hace que el óptimo deje de ser 8.

    Se cierra la celda (2,2), el hueco entre el jugador y la caja. Es el paso
    obligado de la solución: sin él el jugador no llega a empujar nada y el nivel
    queda sin solución.
    """
    copia = _mutar_a_pared(NIVELES / 'n1_micro.sok', tmp_path / 'n1_mutado.sok', 2, 2)
    assert _optimo(copia) != 8
    # Y el control: la copia SIN mutar sigue dando 8, así que lo que cambió el
    # resultado fue la mutación y no el hecho de copiar el archivo.
    intacta = tmp_path / 'n1_intacto.sok'
    shutil.copy(NIVELES / 'n1_micro.sok', intacta)
    assert _optimo(intacta) == 8


@pytest.mark.parametrize('celda,rompe', CELDAS_DE_PISO_N1,
                         ids=lambda v: str(v) if isinstance(v, tuple) else str(v))
def test_mutacion_de_cada_celda_de_piso_de_n1(tmp_path, celda, rompe):
    """El mapa completo: qué celdas de N1 son críticas y cuáles no.

    Cerrar cualquiera de las 7 celdas por las que pasa la solución la rompe.
    Cerrar los dos rincones de la fila 1, por los que la solución no pasa, deja
    el óptimo en 8 — y eso también es información: dice que el test anterior mide
    la criticidad de una celda concreta y no el simple hecho de haber tocado el
    archivo.
    """
    fila, columna = celda
    copia = _mutar_a_pared(NIVELES / 'n1_micro.sok',
                           tmp_path / 'n1_mutado.sok', fila, columna)
    if rompe:
        assert _optimo(copia) != 8
    else:
        assert _optimo(copia) == 8
