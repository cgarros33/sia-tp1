"""h₄ — asignación óptima caja↔meta, con distancias de Manhattan."""

import numpy as np
from scipy.optimize import linear_sum_assignment

from .distancias import distancias_manhattan_por_meta


def h4(problema):
    """Fábrica: precalcula la matriz de costos por celda y devuelve `estado -> int`."""
    costos_por_celda = distancias_manhattan_por_meta(problema.tablero)

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
