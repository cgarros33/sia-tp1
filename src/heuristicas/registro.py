"""Las heurísticas disponibles, con h(estado) como única interfaz.

QUÉ REPRESENTA
    Una heurística estima cuánto falta desde un estado hasta la meta. El motor
    no sabe nada de Sokoban: sólo llama a una función `estado -> número`.

LA DECISIÓN DE DISEÑO — cada heurística es una FÁBRICA
    `h0(problema)` no es la heurística: DEVUELVE la heurística. La función que
    devuelve ya tiene adentro todo lo que necesita del nivel.

    Parece un rodeo y es lo que hace posible la Fase 4. h₃ y h₄ van a necesitar
    tablas precalculadas por nivel —distancias reales de empuje desde cada
    celda hasta cada meta—, y esas tablas se calculan UNA vez al construir la
    heurística, no una vez por cada uno de los millones de estados evaluados.
    Sin fábricas, o se recalcularía todo en cada llamada, o habría que
    ensuciar el motor pasándole tablas que no le importan.

QUÉ SE DESCARTÓ
    Que la heurística fuera un método del `Problema`. Se descartó porque
    obligaría a tener un `Problema` distinto por heurística, y entonces
    comparar dos heurísticas dejaría de ser comparar dos funciones sobre el
    mismo problema. Acá el problema es uno solo y la heurística se enchufa.
"""


def h0(problema):
    """h ≡ 0. La heurística nula.

    ADMISIBLE Y CONSISTENTE trivialmente: 0 nunca sobreestima nada, y la
    desigualdad triangular h(n) <= c(n,n') + h(n') se cumple porque los costos
    son positivos.

    No existe para resolver niveles: existe como INSTRUMENTO DE MEDICIÓN. Con
    h = 0, A* degenera en búsqueda de costo uniforme, y con costo unitario eso
    es exactamente BFS. Entonces A*(h0) tiene que expandir la misma cantidad de
    nodos que BFS, y si no lo hace el bug está en el motor —orden de la
    frontera, control de repetidos o momento del test de meta— y no en ninguna
    heurística. Es el primer test que hay que correr cuando algo no cierra.
    """
    def calcular(estado):
        return 0
    return calcular


def h1(problema):
    """Cantidad de cajas que NO están sobre una meta.

    ADMISIBLE: cada caja fuera de meta necesita al menos un empuje para llegar
    a una, y cada empuje es un movimiento del jugador. Como son cajas
    distintas, esos movimientos son distintos entre sí, así que
    h1(n) <= empujes que faltan <= movimientos que faltan = h*(n).

    CONSISTENTE: un movimiento cambia la cuenta a lo sumo en 1 —sólo se puede
    empujar una caja por vez—, así que h1(n) - h1(n') <= 1 = c(n, n').

    Es la línea de base de la escalera de la Fase 4: la heurística más pobre
    que igual informa algo. Su defecto es que no distingue una caja pegada a la
    meta de una caja en la otra punta del tablero, y ese defecto es exactamente
    lo que arregla h₂ sumando distancias de Manhattan.

    No existe para resolver rápido: existe para que Greedy sea ejecutable y
    para tener contra qué comparar cuando llegue h₂.
    """
    # Se captura el conjunto de metas una sola vez, al construir: es lo que
    # hace la fábrica. La resta de conjuntos está implementada en C y con 4
    # cajas resulta más barata que un bucle en Python.
    metas = problema.tablero.metas

    def calcular(estado):
        return len(estado.cajas - metas)

    return calcular


#: Nombre -> fábrica. `config.json` y el runner de la Fase 6 usan estos nombres.
#: La escalera h₂...h₅ de la Fase 4 se agrega acá sin tocar nada más.
HEURISTICAS = {
    'h0': h0,
    'h1': h1,
}


def construir(nombre, problema):
    """Devuelve la función h del nombre pedido, ya atada a este problema."""
    if nombre not in HEURISTICAS:
        raise ValueError(
            f'Heurística desconocida: {nombre!r}. Opciones: {sorted(HEURISTICAS)}'
        )
    return HEURISTICAS[nombre](problema)
