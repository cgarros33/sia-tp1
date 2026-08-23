"""La poda de los estados que ya no admiten solución."""

from .heuristicas.distancias import celdas_muertas

ESQUINAS_DEL_CUADRADO = ((-1, -1), (-1, 0), (0, -1), (0, 0))


def sin_poda(tablero):
    """Ningún detector. Devuelve `None`, no una función que siempre dice que no."""
    return None


def deadlocks_estaticos(tablero):
    """Una caja en una celda desde la que ninguna meta es alcanzable a empujones."""
    muertas = celdas_muertas(tablero)

    def detectar(cajas, caja_movida):
        return caja_movida in muertas

    return detectar


def cuadrados_por_celda(tablero) -> dict[int, tuple[tuple[int, ...], ...]]:
    """Para cada celda de piso, qué haría falta para congelar un 2x2 que la contenga."""
    metas = tablero.metas
    paredes = tablero.paredes
    cuadrados = {}

    for celda in tablero.transitables:
        fila, columna = tablero.coordenadas(celda)
        candidatos = []
        for desplazamiento_fila, desplazamiento_columna in ESQUINAS_DEL_CUADRADO:
            piso = []
            for f in (fila + desplazamiento_fila, fila + desplazamiento_fila + 1):
                for c in (columna + desplazamiento_columna,
                          columna + desplazamiento_columna + 1):
                    if 0 <= f < tablero.alto and 0 <= c < tablero.ancho:
                        p = tablero.indice(f, c)
                        if p not in paredes:
                            piso.append(p)
            if all(p in metas for p in piso):
                continue
            candidatos.append(tuple(p for p in piso if p != celda))
        cuadrados[celda] = tuple(candidatos)

    return cuadrados


def deadlocks_congelados(tablero):
    """Un cuadrado de 2x2 lleno de paredes y cajas, con alguna caja fuera de meta.

    La cláusula "fuera de meta" no es opcional: las cuatro metas de n4_matching
    forman un 2x2, así que sin ella se podaría el estado meta de ese nivel.
    """
    cuadrados = cuadrados_por_celda(tablero)

    def detectar(cajas, caja_movida):
        return any(all(celda in cajas for celda in requisitos)
                   for requisitos in cuadrados[caja_movida])

    return detectar


def deadlocks_completo(tablero):
    """Las dos reglas. Primero la estática, que es una pertenencia a un conjunto."""
    estatico = deadlocks_estaticos(tablero)
    congelado = deadlocks_congelados(tablero)

    def detectar(cajas, caja_movida):
        return estatico(cajas, caja_movida) or congelado(cajas, caja_movida)

    return detectar


DETECTORES = {
    'ninguno': sin_poda,
    'estaticos': deadlocks_estaticos,
    'congelados': deadlocks_congelados,
    'completo': deadlocks_completo,
}


def construir(nombre, tablero):
    """Devuelve el detector del nombre pedido, ya atado a este tablero."""
    if nombre not in DETECTORES:
        raise ValueError(
            f'Detector de deadlocks desconocido: {nombre!r}. '
            f'Opciones: {sorted(DETECTORES)}'
        )
    return DETECTORES[nombre](tablero)
