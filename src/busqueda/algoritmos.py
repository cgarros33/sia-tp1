"""Los cinco métodos. Cada uno es una elección de frontera más una política.

Fijate lo cortos que quedan: toda la lógica vive en `motor.py`. Eso NO es una
casualidad de estilo, es el punto de la arquitectura de la fase — si alguno de
estos métodos necesitara su propio bucle, la comparación entre ellos dejaría de
ser justa.

| función      | frontera              | política  | ¿óptimo?                  |
|--------------|-----------------------|-----------|---------------------------|
| bfs          | FIFO                  | cerrado   | sí, porque el costo es 1  |
| dfs          | LIFO                  | cerrado   | no                        |
| iddfs        | LIFO + límite         | mejor_g   | sí                        |
| iddfs_puro   | LIFO + límite         | camino    | sí, pero sólo termina N1  |
| greedy       | prioridad (0, 1)      | cerrado   | no                        |
| a_estrella   | prioridad (1, 1)      | mejor_g   | sí si h es admisible      |
| hpa          | prioridad (1-w, w)    | según w   | sí sólo si w <= 0.5       |
"""

import time

from .frontera import FronteraFIFO, FronteraLIFO, FronteraPrioridad
from .motor import CAMINO, CERRADO, MEJOR_G, Resultado, buscar


def bfs(problema, max_nodos=None, timeout_s=None, nivel='') -> Resultado:
    """Primero en anchura. Óptimo acá porque todo movimiento cuesta 1.

    Es la vara del proyecto: sus costos se contrastan contra los récords
    publicados en game-sokoban.com, y sus nodos expandidos se congelan como
    referencia de regresión en la Fase 3.
    """
    return buscar(problema, FronteraFIFO(), politica=CERRADO,
                  max_nodos=max_nodos, timeout_s=timeout_s,
                  metodo='BFS', nivel=nivel)


def dfs(problema, limite_profundidad=None, max_nodos=None, timeout_s=None,
        nivel='') -> Resultado:
    """Primero en profundidad. Sin límite por defecto.

    Termina igual sin límite, porque el espacio de estados es finito y llevamos
    el conjunto de visitados. El costo que devuelve va a ser malísimo, y eso es
    exactamente lo que queremos mostrar: encuentra UNA solución, no la mejor.
    """
    return buscar(problema, FronteraLIFO(), politica=CERRADO,
                  limite_profundidad=limite_profundidad,
                  max_nodos=max_nodos, timeout_s=timeout_s,
                  metodo='DFS', nivel=nivel)


def greedy(problema, heuristica, nombre_heuristica='', max_nodos=None,
           timeout_s=None, nivel='') -> Resultado:
    """Ávido: prioriza sólo por h, ignora lo que ya costó llegar.

    Política 'cerrado' y no 'mejor_g' a propósito: no garantiza optimalidad de
    ninguna manera, así que reabrir estados por un g mejor sólo agregaría
    trabajo sin comprar nada.
    """
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
    """Heuristic Path Algorithm: f = (1-w)·g + w·h.

    Recorre el espectro completo con un solo número: w=0 es costo uniforme,
    w=0.5 es A* reescalado y w=1 es Greedy. Es el barrido de la Fase 8.

    La política acompaña al extremo: con w=1 el término g desaparece y el
    método es Greedy, así que se usa 'cerrado' por el mismo motivo que allá.
    Para cualquier otro w hay componente de costo y corresponde 'mejor_g'.
    """
    return buscar(problema, FronteraPrioridad(peso_g=1 - w, peso_h=w),
                  politica=CERRADO if w >= 1 else MEJOR_G,
                  heuristica=heuristica,
                  max_nodos=max_nodos, timeout_s=timeout_s,
                  metodo=f'HPA(w={w})', nombre_heuristica=nombre_heuristica, nivel=nivel)


def iddfs(problema, limite_inicial=0, max_nodos=None, timeout_s=None,
          nivel='', politica=MEJOR_G, metodo='IDDFS') -> Resultado:
    """Profundización iterativa: DFS con límite creciente.

    Es óptimo con costo uniforme por la misma razón que BFS: la primera solución
    que aparece está a la mínima profundidad posible.

    OJO CON LA MEMORIA, que es el resultado interesante de la fase. El IDDFS de
    manual tiene memoria lineal en la profundidad porque NO guarda visitados.
    Éste sí los guarda —política 'mejor_g'— porque sin eso, en Sokoban, las
    transposiciones lo hacen inviable. Y al guardarlos, la ventaja de memoria se
    evapora: la frontera queda diminuta pero el diccionario crece hasta el orden
    del de BFS. Comparar frontera contra frontera diría que ahorra 55 veces;
    comparar memoria total dice que ahorra un 13 %. Por eso `Resultado` reporta
    `memoria_maxima`. La versión sin visitados es `iddfs_puro`.

    Las métricas se ACUMULAN entre iteraciones: los nodos expandidos son la suma
    de todas las pasadas, porque ese trabajo se hizo de verdad. Pero
    `frontera_maxima` y `memoria_maxima` son el MÁXIMO y no la suma, porque las
    pasadas no coexisten en memoria.

    Se espera que agote el límite de nodos en N4 y N5. No es un fallo de la
    implementación: es un resultado del TP y va reportado como tal.
    """
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

        # Cada iteración arranca con estructuras vacías: es lo que hace que la
        # memoria de IDDFS sea la de una sola pasada y no la de todas juntas.
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

        # Ningún nodo tocó el límite: el espacio quedó agotado y subir el límite
        # volvería a recorrer exactamente lo mismo. No hay solución, punto.
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
    """El IDDFS de manual: sin estructura de visitados.

    Sólo evita repetir estados que ya están en el camino actual. Ésa es la
    versión que tiene memoria lineal en la profundidad, y la que justifica la
    frase "IDDFS usa mucha menos memoria" de los libros.

    En Sokoban no sirve, y ese es el punto: sin tabla de transposiciones, cada
    estado alcanzable por k caminos distintos se expande k veces, y como el
    jugador puede pasear sin empujar nada, k es enorme. Termina en N1 y no
    termina en ningún otro nivel de la suite. Existe para poder MEDIR el
    intercambio entre memoria y trabajo repetido, no para usarlo.
    """
    return iddfs(problema, limite_inicial=limite_inicial, max_nodos=max_nodos,
                 timeout_s=timeout_s, nivel=nivel, politica=CAMINO,
                 metodo='IDDFS puro')


#: Nombres que acepta `config.json`. El runner de la Fase 6 va a usar este mismo
#: registro, así que agregar un método es agregar una línea acá.
METODOS = ('bfs', 'dfs', 'iddfs', 'iddfs_puro', 'greedy', 'astar', 'hpa')

#: Qué métodos necesitan una heurística para poder correr.
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
