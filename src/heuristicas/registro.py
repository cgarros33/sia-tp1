"""Las heurísticas disponibles, con h(estado) como única interfaz."""

from .h3_manhattan import h3
from .h4_matching_manhattan import h4
from .h5_matching_real import h5
from .h6_con_jugador import h6
from .hna_sobreestimada import hna, hna4


def h0(problema):
    """h ≡ 0. La heurística nula."""
    def calcular(estado):
        return 0
    return calcular


def h1(problema):
    """1 si queda alguna caja fuera de meta, 0 si no. La heurística trivial."""
    metas = problema.tablero.metas

    def calcular(estado):
        numero = len(estado.cajas - metas)
        if numero > 0:
            return 1
        else:
            return 0

    return calcular


def h2(problema):
    """Cantidad de cajas que NO están sobre una meta."""
    metas = problema.tablero.metas

    def calcular(estado):
        return len(estado.cajas - metas) #resta de sets de las coordenadas en donde estan

    return calcular


HEURISTICAS = {
    'h0': h0,
    'h1': h1,
    'h2': h2,
    'h3': h3,
    'h4': h4,
    'h5': h5,
    'h6': h6,
    'hna': hna,
    'hna4': hna4,
}


def construir(nombre, problema):
    """Devuelve la función h del nombre pedido, ya atada a este problema."""
    if nombre not in HEURISTICAS:
        raise ValueError(
            f'Heurística desconocida: {nombre!r}. Opciones: {sorted(HEURISTICAS)}'
        )
    return HEURISTICAS[nombre](problema)
