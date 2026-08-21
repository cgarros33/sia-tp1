"""Las fronteras: lo ÚNICO que distingue a un método de búsqueda de otro.

QUÉ REPRESENTA
    La frontera es el conjunto de nodos generados y todavía no expandidos. Qué
    nodo sale de ahí es toda la diferencia entre BFS, DFS, Greedy y A*.

LA DECISIÓN DE ARQUITECTURA DE LA FASE
    Hay un solo bucle de búsqueda (`motor.py`) y los métodos se diferencian
    únicamente por la estructura de datos de esta interfaz. No cinco archivos
    con cinco bucles parecidos.

    Dos consecuencias, y las dos se defienden en el oral:

    1. La comparación entre métodos es JUSTA POR CONSTRUCCIÓN. Todos corren
       exactamente el mismo código de expansión, el mismo control de estados
       repetidos y la misma recolección de métricas. Si BFS expande más nodos
       que A*, es por la política de la frontera y no porque uno esté mejor
       implementado que el otro. Con cinco bucles separados, cualquier
       diferencia entre métodos sería sospechosa.
    2. Agregar un método es escribir una subclase, no tocar el motor. El
       Heuristic Path Algorithm del barrido de `w` de la Fase 8 sale gratis de
       `FronteraPrioridad`.

QUÉ SE DESCARTÓ
    Tres clases distintas para costo uniforme, A* y Greedy. Se descartó porque
    los tres son el mismo algoritmo con distintos pesos sobre `g` y `h`: una
    sola clase parametrizada permite recorrer el espectro completo —de costo
    uniforme a Greedy, pasando por A*— moviendo un único número, que es
    justamente el experimento del barrido de `w`.
"""

import heapq
from collections import deque


class Frontera:
    """Interfaz común. El motor sólo conoce estos cuatro métodos.

    `agregar()` recibe el valor de `h` ya calculado en vez de calcularlo acá.
    El motor es el que sabe cuál es la heurística y el único que debe contar
    cuántas veces se la evalúa; las fronteras desinformadas simplemente lo
    ignoran.
    """

    #: Si es False, el motor ni siquiera llama a la heurística. Evita pagar h
    #: en BFS, DFS e IDDFS, donde el valor se descartaría.
    usa_heuristica = False

    def agregar(self, nodo, h: float = 0.0) -> None:
        raise NotImplementedError

    def sacar(self):
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def vacia(self) -> bool:
        return len(self) == 0


class FronteraFIFO(Frontera):
    """Cola: sale el más viejo. Es BFS.

    `deque` y no una lista porque sacar del principio de una lista es O(n)
    —hay que correr todos los elementos— mientras que en un `deque` es O(1).
    Con 2.000.000 de nodos en N5 esa diferencia es la que hace que el nivel
    corra en segundos y no en horas.
    """

    def __init__(self):
        self._cola = deque()

    def agregar(self, nodo, h: float = 0.0) -> None:
        self._cola.append(nodo)

    def sacar(self):
        return self._cola.popleft()

    def __len__(self) -> int:
        return len(self._cola)


class FronteraLIFO(Frontera):
    """Pila: sale el más nuevo. Es DFS, y con límite creciente es IDDFS.

    Una lista alcanza: `append` y `pop` sobre el final son O(1).

    Consecuencia importante para el oral: como los sucesores se insertan en el
    orden fijo de `DIRECCIONES` y salen en orden inverso, DFS explora primero
    la ÚLTIMA dirección generada. El orden es arbitrario pero fijo, y fijarlo
    es lo que hace que DFS sea reproducible entre corridas.
    """

    def __init__(self):
        self._pila = []

    def agregar(self, nodo, h: float = 0.0) -> None:
        self._pila.append(nodo)

    def sacar(self):
        return self._pila.pop()

    def __len__(self) -> int:
        return len(self._pila)


class FronteraPrioridad(Frontera):
    """Cola de prioridad: sale el de menor `peso_g · g(n) + peso_h · h(n)`.

    Los pesos cubren todo el espectro con una sola clase:

        peso_g=1, peso_h=0   costo uniforme (con costo unitario, ≡ BFS)
        peso_g=1, peso_h=1   A*, f = g + h
        peso_g=0, peso_h=1   Greedy, f = h
        peso_g=1-w, peso_h=w Heuristic Path Algorithm, el barrido de la Fase 8
    """

    usa_heuristica = True

    def __init__(self, peso_g: float = 1.0, peso_h: float = 1.0):
        self.peso_g = peso_g
        self.peso_h = peso_h
        self._monticulo = []
        # Contador de inserción monótono. NO es una decisión algorítmica sino de
        # reproducibilidad, y hay que poder explicar las dos razones:
        #   1. Sin él, ante prioridad y h iguales, heapq compararía los objetos
        #      Nodo entre sí, que no son comparables: TypeError.
        #   2. Peor todavía si lo fueran: el orden de exploración podría variar
        #      entre corridas y los nodos expandidos dejarían de ser
        #      reproducibles, que es la métrica central de todo el TP.
        self._contador = 0

    def agregar(self, nodo, h: float = 0.0) -> None:
        prioridad = self.peso_g * nodo.g + self.peso_h * h
        # Ante igual prioridad se prefiere MENOR h: entre dos nodos que prometen
        # el mismo costo total, conviene abrir el que ya avanzó más hacia la
        # meta, porque está más cerca de cerrar la solución. Recién ante igual
        # prioridad y h desempata el contador, o sea el orden de generación.
        heapq.heappush(self._monticulo, (prioridad, h, self._contador, nodo))
        self._contador += 1

    def sacar(self):
        return heapq.heappop(self._monticulo)[3]

    def __len__(self) -> int:
        return len(self._monticulo)
