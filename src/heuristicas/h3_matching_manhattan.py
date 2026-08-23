"""h₃ — asignación óptima caja↔meta, con distancias de Manhattan.

    h₃(s) =    mín        Σ manhattan(caja, σ(caja))
            σ biyección

EL DEFECTO QUE ARREGLA
    h₂ toma el mínimo caja por caja, en forma independiente. Si dos cajas tienen
    la misma meta como más cercana, LAS DOS suman esa distancia, cuando en la
    realidad una de las dos va a tener que ir a otra meta, más lejos. h₂
    subestima de más, y cuanto más agrupadas estén las metas, peor.

    Ese es el diseño de `n4_matching`: las cuatro metas están juntas en un bloque
    de 2x2. Ahí h₂(s₀) = 16 y h₃(s₀) = 20, un 25 % más de información sacada de
    exactamente las mismas 16 distancias.

QUÉ PROBLEMA SE RESUELVE Y CON QUÉ
    El problema de asignación de costo mínimo: dada la matriz de 4x4 con las
    distancias de cada caja a cada meta, encontrar la biyección caja → meta más
    barata. Lo resuelve `scipy.optimize.linear_sum_assignment` con el algoritmo
    húngaro, en O(n³). Es el único uso de scipy que autorizan las reglas del
    proyecto, y está autorizado exactamente para esto.

POR QUÉ ES ADMISIBLE — la demostración que va a la presentación
    h₃ es el mínimo sobre TODAS las biyecciones caja-meta posibles. En la
    solución óptima real cada caja termina en una meta y cada meta recibe una
    caja: esa correspondencia es una biyección, o sea UNA de las que se
    minimizaron, así que su costo es ≥ h₃. Y ese costo es a su vez cota inferior
    de los empujes que faltan —cada empuje mueve una caja un casillero y
    Manhattan ignora las paredes—, y todo empuje es un movimiento. Entonces
    h₃ ≤ empujes que faltan ≤ movimientos que faltan = h*(s).

POR QUÉ DOMINA A h₂, en un renglón
    h₂ es la misma minimización pero permitiendo que varias cajas compartan meta:
    minimiza sobre TODAS las funciones caja → meta, no sólo sobre las biyectivas.
    El mínimo sobre un conjunto más grande es menor o igual, así que h₂ ≤ h₃ en
    todo estado, siempre.

CONSISTENCIA
    Un movimiento mueve a lo sumo una caja y a lo sumo un casillero, así que
    cambia a lo sumo en 1 cualquier entrada de la matriz de costos, y por lo
    tanto el óptimo de la asignación se mueve a lo sumo en 1. h₃ baja como mucho
    1 por movimiento, que es exactamente el costo del arco.

SU PROPIO DEFECTO — la transición a h₄
    Manhattan atraviesa paredes. En `n3_caminata` las metas están detrás de
    paredes y el rodeo real es mucho más largo que la línea recta, así que h₃
    sigue subestimando muchísimo: h₃(s₀) = 12 contra un óptimo de 104. Eso es lo
    que arregla h₄ cambiando la matriz de costos por distancias reales de empuje.

QUÉ SE DESCARTÓ
    1. Asignación golosa: ordenar los pares por distancia y tomar el más barato
       disponible. Son tres líneas y NO da el mínimo, así que puede devolver más
       que el óptimo de la asignación y SOBREESTIMAR. Una heurística que deja de
       ser admisible por descuido es el peor error posible en esta fase: A*
       seguiría corriendo y devolvería soluciones subóptimas sin avisar.
    2. Probar las 4! = 24 permutaciones a mano. Da el mismo número y con 4 cajas
       hasta sería más rápido. Se descartó porque lo que se defiende en el oral
       es "esto es el problema de asignación y se resuelve en O(n³)", no "esto
       son 24 permutaciones y con 8 cajas ya no termina".
"""

import numpy as np
from scipy.optimize import linear_sum_assignment

from .distancias import distancias_manhattan_por_meta


def h3(problema):
    """Fábrica: precalcula la matriz de costos por celda y devuelve `estado -> int`."""
    costos_por_celda = distancias_manhattan_por_meta(problema.tablero)

    # h₃ depende SÓLO del conjunto de cajas: dónde está el jugador no cambia el
    # emparejamiento. Y la enorme mayoría de los sucesores son movimientos del
    # jugador que no mueven ninguna caja, así que sin esta memoria se resolvería
    # el mismo problema de asignación una y otra vez. Está acotada por la
    # cantidad de configuraciones de cajas del nivel —C(31,4) = 31.465 en N4—, y
    # es una optimización de TIEMPO que no cambia ni un nodo expandido: los
    # números de la tabla salen iguales con y sin ella.
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
