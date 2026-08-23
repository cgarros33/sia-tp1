"""h₂ — suma de distancias de Manhattan de cada caja a su meta más cercana.

    h₂(s) = Σ      mín      manhattan(caja, meta)
          cajas    metas

EL DEFECTO QUE ARREGLA
    h₁ cuenta cajas fuera de meta y nada más. Con 4 cajas sólo puede valer 0, 1,
    2, 3 o 4: cinco valores distintos para repartir entre los 654.260 estados que
    A* recorre en N4. No distingue una caja pegada a su meta de una caja en la
    otra punta del tablero, así que casi todos los nodos de la frontera empatan
    en f y el desempate lo termina haciendo g: A*(h₁) es BFS con un sombrero. En
    N5 le ahorra 796 nodos sobre 2.028.239, o sea el 0,04 %.

    h₂ le da al valor un rango de verdad —23 en el estado inicial de N5, contra
    4— y con eso, capacidad real de ordenar la frontera.

POR QUÉ ES ADMISIBLE — la demostración que va a la presentación
    h₂ es el costo óptimo de un problema RELAJADO: uno sin paredes, donde las
    cajas se atraviesan entre sí y el jugador se teletransporta. Toda solución
    del Sokoban real también resuelve el relajado, así que el óptimo del relajado
    es cota inferior del óptimo real.

    Dicho como cuenta: mover una caja un casillero cambia su distancia de
    Manhattan a cualquier meta fija en a lo sumo 1, así que llevarla de `c` hasta
    su meta más cercana cuesta al menos mín_m manhattan(c, m) EMPUJES. Las cajas
    son distintas, así que esos empujes son distintos entre sí, y todo empuje es
    un movimiento del jugador. Entonces
        h₂ ≤ empujes que faltan ≤ movimientos que faltan = h*(s).

Y ADEMÁS ES CONSISTENTE, que es lo que hace que A* no tenga que reabrir nodos:
    un movimiento mueve a lo sumo una caja y a lo sumo un casillero, así que h₂
    baja como mucho 1 por movimiento, que es exactamente el costo del arco.

SU PROPIO DEFECTO — la transición a h₃
    El mínimo se toma caja por caja, en forma independiente. Si dos cajas tienen
    la misma meta como más cercana, las dos suman esa distancia, cuando en la
    realidad una de las dos va a tener que ir a otra meta, más lejos. h₂
    SUBESTIMA DE MÁS. Se ve en `n4_matching`, donde las cuatro metas están
    juntas en un bloque de 2x2: ahí h₂(s₀) = 16 y el matching óptimo da 20.

QUÉ SE DESCARTÓ
    Asignar de antemano cada caja a una meta fija (la caja i a la meta i) y sumar
    esas distancias. Es más informativa y NO es admisible: si la solución óptima
    usa otra asignación, la cuenta sobreestima. El mínimo sobre todas las metas
    es la versión segura; el problema que introduce es exactamente el que arregla
    h₃ resolviendo el matching.

    También se descartó la distancia euclídea: en una grilla de 4 vecinos es una
    cota inferior más floja que Manhattan (en la diagonal da √2 donde el camino
    real cuesta 2) y encima devuelve flotantes. Estrictamente peor, sin ventaja.
"""

from .distancias import distancias_manhattan


def h2(problema):
    """Fábrica: precalcula la tabla del nivel y devuelve la función `estado -> int`.

    La tabla se calcula UNA vez acá y no dentro de `calcular`. No es cosmética:
    en N5 la heurística se evalúa unos dos millones de veces, y recorrer las
    cuatro metas en cada llamada sería recalcular en cada nodo un número que está
    fijo desde que se leyó el archivo. Para esto existe el diseño de fábricas.
    """
    minimo_a_una_meta = distancias_manhattan(problema.tablero)

    def calcular(estado):
        return sum(minimo_a_una_meta[caja] for caja in estado.cajas)

    return calcular
