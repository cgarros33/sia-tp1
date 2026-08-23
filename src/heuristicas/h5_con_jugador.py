"""h₅ — h₄ más el recorrido del jugador hasta el primer empuje."""

from .distancias import INALCANZABLE, distancias_libres
from .h4_matching_real import h4


def h5(problema):
    """Fábrica: h₄ más el término del jugador, con las dos tablas precalculadas."""
    empujes_que_faltan = h4(problema)
    caminata = distancias_libres(problema.tablero)
    es_meta = problema.es_meta

    def calcular(estado):
        if es_meta(estado):
            return 0

        desde_el_jugador = caminata[estado.jugador]
        mas_cerca = min(desde_el_jugador.get(caja, INALCANZABLE)
                        for caja in estado.cajas)
        return empujes_que_faltan(estado) + max(0, mas_cerca - 1)

    return calcular
