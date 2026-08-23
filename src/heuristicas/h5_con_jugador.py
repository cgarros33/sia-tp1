"""h₅ — h₄ más el recorrido del jugador hasta el primer empuje.

    h₅(s) = h₄(s) + máx(0, mín distancia(jugador, caja) - 1)
                          cajas

    y h₅(s) = 0 si s ya es meta.

EL DEFECTO QUE ARREGLA
    Las cuatro heurísticas anteriores tratan al jugador como si no existiera:
    todas estiman EMPUJES. Pero el costo que pide el enunciado son MOVIMIENTOS, y
    en `n3_caminata` 82 de los 104 movimientos de la solución óptima son el
    jugador caminando entre empuje y empuje — el 79 %. Ninguna heurística de la
    escalera ve ese 79 %.

    Ése es el punto ciego que explica por qué A* rinde bastante menos en Sokoban
    que en el 8-puzzle: allá cada movimiento hace progreso medible, acá la enorme
    mayoría de los movimientos no toca ninguna caja y por lo tanto no cambia
    ninguna de las heurísticas anteriores.

POR QUÉ ES ADMISIBLE — el argumento más delicado de la fase, en tres piezas
    1. LA DISYUNCIÓN. Si el estado no es meta, falta al menos un empuje. Ese
       primer empuje es de alguna caja, y para empujarla el jugador tiene que
       estar parado en una celda adyacente a ella: llegar hasta ahí cuesta al
       menos distancia(jugador, caja) - 1 movimientos. Esos movimientos ocurren
       ANTES del primer empuje, así que ninguno de ellos ES un empuje. Como h₄
       acota por debajo la cantidad de EMPUJES que faltan, los dos conjuntos de
       movimientos son disjuntos y las dos cotas se pueden sumar:
           h₄ + caminata ≤ empujes + no-empujes = movimientos que faltan = h*(s).

    2. EL MÍNIMO SOBRE TODAS LAS CAJAS, INCLUIDAS LAS QUE YA ESTÁN EN META. No
       sabemos cuál va a ser la primera caja empujada, así que hay que tomar el
       mínimo sobre todas las candidatas. Restringirlo a las cajas fuera de meta
       parece más informativo y ES UN ERROR: puede convenir mover primero una
       caja que ya está colocada —porque estorba, o para despejar el paso— y
       entonces la cota se pasaría de largo.

    3. LA DISTANCIA SE CALCULA IGNORANDO LAS CAJAS. Son obstáculos que sólo
       pueden ALARGAR el recorrido del jugador, nunca acortarlo, así que
       ignorarlas mantiene el número como cota inferior. Igual que en h₄.

EL CASO BORDE QUE NO SE PUEDE OLVIDAR
    En un estado meta h₄ vale 0 pero el término del jugador puede ser positivo, y
    una heurística admisible tiene que valer 0 donde el costo restante es 0. El
    propio argumento lo resuelve: "si el estado no es meta, falta al menos un
    empuje" no dice absolutamente nada cuando el estado SÍ es meta. Por eso hay
    un return explícito, y no es una defensa contra un caso raro: sin él h₅ no
    sería admisible.

POR QUÉ DOMINA A h₄
    El término que se suma nunca es negativo, por el máx(0, ...): h₄ ≤ h₅ siempre.

SOBRE LA CONSISTENCIA — acá no se promete, se mide
    h₂, h₃ y h₄ son consistentes por un argumento simple: un movimiento cambia a
    lo sumo una entrada de la matriz de costos y a lo sumo en 1. Para h₅ ese
    argumento NO vale: el jugador se mueve en TODOS los movimientos, así que el
    término puede cambiar en cada paso y no es obvio que el total no baje más
    de 1.

    Medido con la herramienta de la Fase 3: consistente en los cinco niveles,
    sobre los estados del camino óptimo y sus sucesores directos. Eso no es lo
    mismo que "consistente en todo el espacio" —la verificación es una condición
    necesaria, no una demostración—, y por eso se reporta con la aclaración. Si
    apareciera un contraejemplo no sería un fracaso: A* sigue siendo óptimo con
    la política `mejor_g` que el motor ya usa, sólo que reabriría nodos. El motor
    está escrito para no asumir consistencia justamente por esto.

QUÉ SE DESCARTÓ
    1. El mínimo sólo sobre las cajas fuera de meta. Más informativo y NO
       admisible, por el motivo 2 de arriba.
    2. Sumar el recorrido COMPLETO del jugador para toda la solución, por ejemplo
       la suma de las caminatas entre empujes consecutivos. Sería mucho más
       informativo y no hay forma de acotarlo por debajo sin conocer el orden de
       los empujes: se pasaría, y con eso se pierde la optimalidad de A*.
    3. máx(h₄, término) en vez de h₄ + término. Sería lo correcto si los dos
       contaran los MISMOS movimientos. Cuentan movimientos disjuntos, así que
       sumar es válido y estrictamente mejor.

LO QUE ESTE ESLABÓN NO ARREGLA — y conviene decirlo antes de que lo pregunten
    El término aporta poco: en N5 baja de 605.520 a 604.472 nodos, un 0,2 %. El
    motivo es que mira sólo el PRÓXIMO empuje y, para ser una cota segura, tiene
    que ser el mínimo sobre todas las cajas: en un tablero chico el jugador casi
    siempre tiene alguna caja cerca, así que el mínimo es 0 o 1 la mayor parte
    del tiempo. El punto ciego del jugador queda mayormente abierto.
"""

from .distancias import INALCANZABLE, distancias_libres
from .h4_matching_real import h4


def h5(problema):
    """Fábrica: h₄ más el término del jugador, con las dos tablas precalculadas.

    Reutiliza la fábrica de h₄ en vez de repetir el matching. Que el código diga
    literalmente "h₅ es h₄ más un término" es parte de lo que se defiende: la
    escalera es una cadena, no cinco heurísticas sueltas, y si h₄ cambiara, h₅
    tiene que cambiar con ella.
    """
    empujes_que_faltan = h4(problema)
    caminata = distancias_libres(problema.tablero)
    es_meta = problema.es_meta

    def calcular(estado):
        # Ver "EL CASO BORDE" en el docstring del módulo: sin esto h₅ no es
        # admisible, porque en la meta el costo restante es 0 y el término del
        # jugador no tiene por qué serlo.
        if es_meta(estado):
            return 0

        desde_el_jugador = caminata[estado.jugador]
        # `.get` con INALCANZABLE y no un acceso directo: si el piso del nivel
        # tuviera dos regiones separadas y las cajas quedaran del otro lado, el
        # estado no tiene solución y corresponde un valor enorme, no un KeyError.
        mas_cerca = min(desde_el_jugador.get(caja, INALCANZABLE)
                        for caja in estado.cajas)
        return empujes_que_faltan(estado) + max(0, mas_cerca - 1)

    return calcular
