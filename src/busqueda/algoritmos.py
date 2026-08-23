"""Los cinco métodos. Cada uno es una elección de frontera más una política."""

import time

from .frontera import FronteraFIFO, FronteraLIFO, FronteraPrioridad
from .motor import CAMINO, CERRADO, MEJOR_G, Resultado, buscar


def bfs(problema, max_nodos=None, timeout_s=None, nivel='') -> Resultado:
    """Primero en anchura. Óptimo acá porque todo movimiento cuesta 1."""
    return buscar(problema, FronteraFIFO(), politica=CERRADO,
                  max_nodos=max_nodos, timeout_s=timeout_s,
                  metodo='BFS', nivel=nivel)


def dfs(problema, limite_profundidad=None, max_nodos=None, timeout_s=None,
        nivel='') -> Resultado:
    """Primero en profundidad. Sin límite por defecto."""
    return buscar(problema, FronteraLIFO(), politica=CERRADO,
                  limite_profundidad=limite_profundidad,
                  max_nodos=max_nodos, timeout_s=timeout_s,
                  metodo='DFS', nivel=nivel)


def greedy(problema, heuristica, nombre_heuristica='', max_nodos=None,
           timeout_s=None, nivel='') -> Resultado:
    """Ávido: prioriza sólo por h, ignora lo que ya costó llegar."""
    return buscar(problema, FronteraPrioridad(peso_g=0, peso_h=1),
                  politica=CERRADO, heuristica=heuristica,
                  max_nodos=max_nodos, timeout_s=timeout_s,
                  metodo='Greedy', nombre_heuristica=nombre_heuristica, nivel=nivel)


def a_estrella(problema, heuristica, nombre_heuristica='', max_nodos=None,
               timeout_s=None, nivel='') -> Resultado:
    """A*: f = g + h. Óptimo si h es admisible."""
    return buscar(problema, FronteraPrioridad(peso_g=1, peso_h=1),
                  politica=MEJOR_G, heuristica=heuristica,
                  max_nodos=max_nodos, timeout_s=timeout_s,
                  metodo='A*', nombre_heuristica=nombre_heuristica, nivel=nivel)


def hpa(problema, heuristica, w=0.5, nombre_heuristica='', max_nodos=None,
        timeout_s=None, nivel='') -> Resultado:
    """Heuristic Path Algorithm: f = (1-w)·g + w·h."""
    return buscar(problema, FronteraPrioridad(peso_g=1 - w, peso_h=w),
                  politica=CERRADO if w >= 1 else MEJOR_G,
                  heuristica=heuristica,
                  max_nodos=max_nodos, timeout_s=timeout_s,
                  metodo=f'HPA(w={w})', nombre_heuristica=nombre_heuristica, nivel=nivel)


def iddfs(problema, limite_inicial=0, max_nodos=None, timeout_s=None,
          nivel='', politica=MEJOR_G, metodo='IDDFS') -> Resultado:
    """Profundización iterativa: DFS con límite creciente."""
    comienzo = time.perf_counter()
    expandidos = generados = 0
    frontera_maxima = 0
    memoria_maxima = 0
    estados_visitados = 0
    iteraciones = []
    limite = limite_inicial

    while True:
        restante_s = None
        if timeout_s is not None:
            restante_s = timeout_s - (time.perf_counter() - comienzo)
            if restante_s <= 0:
                return _fracaso_iddfs('timeout', expandidos, generados,
                                      frontera_maxima, memoria_maxima,
                                      estados_visitados, iteraciones,
                                      comienzo, nivel, metodo)
        restante_nodos = None
        if max_nodos is not None:
            restante_nodos = max_nodos - expandidos
            if restante_nodos <= 0:
                return _fracaso_iddfs('max_nodos', expandidos, generados,
                                      frontera_maxima, memoria_maxima,
                                      estados_visitados, iteraciones,
                                      comienzo, nivel, metodo)

        parcial = buscar(problema, FronteraLIFO(), politica=politica,
                         limite_profundidad=limite,
                         max_nodos=restante_nodos, timeout_s=restante_s,
                         metodo=metodo, nivel=nivel)

        expandidos += parcial.nodos_expandidos
        generados += parcial.nodos_generados
        frontera_maxima = max(frontera_maxima, parcial.frontera_maxima)
        memoria_maxima = max(memoria_maxima, parcial.memoria_maxima)
        estados_visitados = max(estados_visitados, parcial.estados_visitados)
        iteraciones.append((limite, parcial.nodos_expandidos))

        if parcial.exito:
            parcial.nodos_expandidos = expandidos
            parcial.nodos_generados = generados
            parcial.frontera_maxima = frontera_maxima
            parcial.memoria_maxima = memoria_maxima
            parcial.estados_visitados = estados_visitados
            parcial.tiempo_s = time.perf_counter() - comienzo
            parcial.iteraciones = iteraciones
            return parcial

        if parcial.motivo_fin in ('timeout', 'max_nodos'):
            return _fracaso_iddfs(parcial.motivo_fin, expandidos, generados,
                                  frontera_maxima, memoria_maxima,
                                  estados_visitados, iteraciones,
                                  comienzo, nivel, metodo,
                                  frontera_final=parcial.frontera_final)

        if parcial.podados_por_limite == 0:
            return _fracaso_iddfs('sin_solucion', expandidos, generados,
                                  frontera_maxima, memoria_maxima,
                                  estados_visitados, iteraciones,
                                  comienzo, nivel, metodo)

        limite += 1


def _fracaso_iddfs(motivo, expandidos, generados, frontera_maxima,
                   memoria_maxima, estados_visitados, iteraciones, comienzo,
                   nivel, metodo='IDDFS', frontera_final=0) -> Resultado:
    """Arma el Resultado acumulado de un IDDFS que no encontró solución."""
    return Resultado(
        exito=False, costo=None, nodos_expandidos=expandidos,
        frontera_final=frontera_final, acciones=[],
        tiempo_s=time.perf_counter() - comienzo,
        frontera_maxima=frontera_maxima, memoria_maxima=memoria_maxima,
        nodos_generados=generados,
        estados_visitados=estados_visitados, empujes=None, profundidad=None,
        motivo_fin=motivo, metodo=metodo, heuristica='', nivel=nivel,
        iteraciones=iteraciones,
    )


def iddfs_puro(problema, limite_inicial=0, max_nodos=None, timeout_s=None,
               nivel='') -> Resultado:
    """El IDDFS de manual: sin estructura de visitados."""
    return iddfs(problema, limite_inicial=limite_inicial, max_nodos=max_nodos,
                 timeout_s=timeout_s, nivel=nivel, politica=CAMINO,
                 metodo='IDDFS puro')


METODOS = ('bfs', 'dfs', 'iddfs', 'iddfs_puro', 'greedy', 'astar', 'hpa')

METODOS_INFORMADOS = ('greedy', 'astar', 'hpa')


def resolver(problema, metodo, heuristica=None, nombre_heuristica='', w=0.5,
             limite_profundidad=None, limite_inicial=0, max_nodos=None,
             timeout_s=None, nivel='') -> Resultado:
    """Despacha por nombre. Es la puerta de entrada de `main.py`."""
    if metodo not in METODOS:
        raise ValueError(f'Método desconocido: {metodo!r}. Opciones: {METODOS}')
    if metodo in METODOS_INFORMADOS and heuristica is None:
        raise ValueError(f'El método {metodo!r} necesita una heurística.')

    if metodo == 'bfs':
        return bfs(problema, max_nodos=max_nodos, timeout_s=timeout_s, nivel=nivel)
    if metodo == 'dfs':
        return dfs(problema, limite_profundidad=limite_profundidad,
                   max_nodos=max_nodos, timeout_s=timeout_s, nivel=nivel)
    if metodo == 'iddfs':
        return iddfs(problema, limite_inicial=limite_inicial,
                     max_nodos=max_nodos, timeout_s=timeout_s, nivel=nivel)
    if metodo == 'iddfs_puro':
        return iddfs_puro(problema, limite_inicial=limite_inicial,
                          max_nodos=max_nodos, timeout_s=timeout_s, nivel=nivel)
    if metodo == 'greedy':
        return greedy(problema, heuristica, nombre_heuristica=nombre_heuristica,
                      max_nodos=max_nodos, timeout_s=timeout_s, nivel=nivel)
    if metodo == 'astar':
        return a_estrella(problema, heuristica, nombre_heuristica=nombre_heuristica,
                          max_nodos=max_nodos, timeout_s=timeout_s, nivel=nivel)
    return hpa(problema, heuristica, w=w, nombre_heuristica=nombre_heuristica,
               max_nodos=max_nodos, timeout_s=timeout_s, nivel=nivel)
