"""Las tablas de distancias que las heurísticas precalculan una vez por nivel."""

from collections import deque

from ..modelo.tablero import DIRECCIONES

# Costo de una asignación imposible. Finito porque linear_sum_assignment no
# acepta infinitos, y lo bastante grande para que nunca sea el mínimo.
INALCANZABLE = 10 ** 6


def metas_ordenadas(tablero) -> tuple[int, ...]:
    """Las metas en un orden fijo, para que sirvan de columnas de una matriz."""
    return tuple(sorted(tablero.metas))


def distancias_manhattan_por_meta(tablero) -> dict[int, tuple[int, ...]]:
    """Para cada celda transitable, la distancia de Manhattan a CADA meta."""
    ancho = tablero.ancho
    metas = [divmod(meta, ancho) for meta in metas_ordenadas(tablero)]
    tabla = {}
    for celda in tablero.transitables:
        fila, columna = divmod(celda, ancho)
        tabla[celda] = tuple(
            abs(fila - fila_meta) + abs(columna - columna_meta)
            for fila_meta, columna_meta in metas
        )
    return tabla


def distancias_manhattan(tablero) -> dict[int, int]:
    """Para cada celda transitable, la mínima distancia de Manhattan a una meta."""
    return {
        celda: min(distancias)
        for celda, distancias in distancias_manhattan_por_meta(tablero).items()
    }


def distancias_de_empuje(tablero) -> tuple[dict[int, int], ...]:
    """Cuántos EMPUJES cuesta como mínimo llevar una caja de cada celda a cada meta."""
    mover = tablero.mover
    tablas = []
    for meta in metas_ordenadas(tablero):
        distancia = {meta: 0}
        pendientes = deque([meta])
        while pendientes:
            p = pendientes.popleft()
            for d in DIRECCIONES:
                q = mover[p][d]
                if q == -1:
                    continue
                # Empujar exige que la celda de atrás esté libre: ahí va el jugador.
                if mover[q][d] == -1:
                    continue
                if q not in distancia:
                    distancia[q] = distancia[p] + 1
                    pendientes.append(q)
        tablas.append(distancia)
    return tuple(tablas)


def celdas_muertas(tablero) -> frozenset[int]:
    """Las celdas desde las que NINGUNA meta es alcanzable a empujones."""
    tablas = distancias_de_empuje(tablero)
    return frozenset(
        celda for celda in tablero.transitables
        if not any(celda in tabla for tabla in tablas)
    )


def costos_de_empuje_por_celda(tablero) -> dict[int, tuple[int, ...]]:
    """Para cada celda transitable, los empujes hasta CADA meta. La matriz de h₄."""
    tablas = distancias_de_empuje(tablero)
    return {
        celda: tuple(tabla.get(celda, INALCANZABLE) for tabla in tablas)
        for celda in tablero.transitables
    }


def distancias_libres(tablero) -> dict[int, dict[int, int]]:
    """Distancia de camino entre TODOS los pares de celdas transitables."""
    mover = tablero.mover
    tablas = {}
    for origen in tablero.transitables:
        distancia = {origen: 0}
        pendientes = deque([origen])
        while pendientes:
            p = pendientes.popleft()
            for d in DIRECCIONES:
                vecino = mover[p][d]
                if vecino != -1 and vecino not in distancia:
                    distancia[vecino] = distancia[p] + 1
                    pendientes.append(vecino)
        tablas[origen] = distancia
    return tablas
