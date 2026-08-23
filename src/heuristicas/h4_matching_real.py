"""h₄ — asignación óptima caja↔meta, con distancias reales de empuje.

Es h₃ con otra matriz de costos. La única diferencia entre las dos es de dónde
sale el número que va en cada casillero, y toda la ganancia viene de ahí.

EL DEFECTO QUE ARREGLA
    Manhattan atraviesa paredes. h₃ cree que una caja separada de su meta por un
    muro está a la distancia de la línea recta, cuando el rodeo real puede ser
    varias veces más largo. Y hay algo peor que una subestimación floja: hay
    celdas de las que una caja NO PUEDE SALIR, y para Manhattan son celdas
    comunes a unos pocos pasos de la meta.

    Se ve en `n3_caminata`, donde las metas están detrás de paredes: A*(h₃)
    expande 5.348 nodos y A*(h₄), 1.951. Y se ve más fuerte todavía en
    `n5_limite`, donde h₃(s₀) = 27 y h₄(s₀) = 63 sobre un óptimo de 306.

CAMINAR NO ES EMPUJAR — la decisión que se defiende
    La matriz de h₄ NO es la distancia de camino entre celdas: es la distancia de
    EMPUJE, que además exige que el jugador quepa detrás de la caja. La cuenta
    está en `distancias.distancias_de_empuje`, con el porqué completo.

    La diferencia entre las dos lecturas es una sola condición en el BFS, y se
    midió antes de elegir:

        nivel          A*(h₃)   A*(distancia de camino)   A*(distancia de empuje)
        n1_micro           12                        12                       12
        n2_akk04       20.694                    18.794                    7.145
        n3_caminata     5.348                     5.348                    1.951
        n4_matching   473.191                   462.427                   54.754
        n5_limite   2.019.787                 2.019.787                  605.520

    Con distancia de camino, en los cinco niveles todas las celdas de piso están
    conectadas entre sí: la tabla las alcanza a todas, el conjunto de celdas
    muertas queda VACÍO y en n3 y n5 h₄ es idéntica a h₃. O sea que el defecto
    que h₄ dice arreglar no se vería en ningún nivel de la suite.

POR QUÉ ES ADMISIBLE — la demostración que va a la presentación
    Cuando una caja se empuja de q a p, el tablero real exige que p esté libre y
    que el jugador esté en la celda de atrás, que también tiene que estar libre.
    Entonces toda secuencia real de empujes de una caja es un camino en ese mismo
    grafo, y su largo es ≥ la distancia mínima que devuelve el BFS. El BFS ignora
    a las otras cajas y si el jugador puede llegar hasta ahí: son restricciones
    que sólo pueden ALARGAR el recorrido real, nunca acortarlo.

    Con eso cada entrada de la matriz es cota inferior de los empujes de esa caja
    a esa meta; el mínimo sobre todas las biyecciones es cota inferior de los
    empujes totales (mismo argumento que h₃); y todo empuje es un movimiento:
        h₄ ≤ empujes que faltan ≤ movimientos que faltan = h*(s).

POR QUÉ DOMINA A h₃, en un renglón
    Un camino de empujes es un camino de celdas adyacentes, así que su largo es
    siempre ≥ la distancia de Manhattan entre las dos puntas. Entrada por entrada
    la matriz de h₄ es ≥ la de h₃, y si toda entrada crece, el óptimo de la
    asignación también: h₃ ≤ h₄ en todo estado.

EL ESTADO SIN SOLUCIÓN
    Si alguna caja quedó en una celda desde la que no se alcanza ninguna meta, no
    hay asignación válida. Esas entradas valen `INALCANZABLE` (ver la constante en
    `distancias.py`), así que h₄ devuelve un valor enorme y A* manda ese estado al
    fondo de la frontera. Sobreestimar un estado sin solución no rompe la
    admisibilidad, porque ahí h* = infinito.

    En los cinco niveles de la suite ninguna caja arranca en una celda muerta
    —está verificado—, así que esto no afecta ninguno de los números de la fase.
    Pero pasa todo el tiempo DURANTE la búsqueda, y es la razón por la que h₄
    ahorra tantos nodos: no poda esos estados, pero los deja para el final.

SU PROPIO DEFECTO — la transición a h₅
    h₄ sigue sin ver al jugador. Cuenta empujes y nada más, y en `n3_caminata`
    82 de los 104 movimientos de la solución óptima son el jugador caminando.
"""

import numpy as np
from scipy.optimize import linear_sum_assignment

from .distancias import costos_de_empuje_por_celda


def h4(problema):
    """Fábrica: precalcula la matriz de empujes por celda y devuelve `estado -> int`."""
    costos_por_celda = costos_de_empuje_por_celda(problema.tablero)

    # Mismo motivo que en h₃: el valor depende sólo del conjunto de cajas, y la
    # enorme mayoría de los sucesores son movimientos del jugador que no mueven
    # ninguna. No cambia ni un nodo expandido, sólo el tiempo.
    memoria = {}

    def calcular(estado):
        valor = memoria.get(estado.cajas)
        if valor is None:
            matriz = np.array([costos_por_celda[caja] for caja in estado.cajas])
            filas, columnas = linear_sum_assignment(matriz)
            valor = int(matriz[filas, columnas].sum())
            memoria[estado.cajas] = valor
        return valor

    return calcular
