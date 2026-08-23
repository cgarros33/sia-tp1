"""h₄ — asignación óptima caja↔meta, con distancias reales de empuje."""

import numpy as np
from scipy.optimize import linear_sum_assignment

from .distancias import costos_de_empuje_por_celda


def h4(problema):
    """Fábrica: precalcula la matriz de empujes por celda y devuelve `estado -> int`."""
    costos_por_celda = costos_de_empuje_por_celda(problema.tablero)

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
