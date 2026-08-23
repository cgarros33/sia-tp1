"""h₂ — suma de distancias de Manhattan de cada caja a su meta más cercana."""

from .distancias import distancias_manhattan


def h2(problema):
    """Fábrica: precalcula la tabla del nivel y devuelve la función `estado -> int`."""
    minimo_a_una_meta = distancias_manhattan(problema.tablero)

    def calcular(estado):
        return sum(minimo_a_una_meta[caja] for caja in estado.cajas)

    return calcular
