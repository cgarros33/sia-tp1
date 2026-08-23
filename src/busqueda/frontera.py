"""Las fronteras: lo único que distingue a un método de búsqueda de otro."""

import heapq
from collections import deque


class Frontera:
    """Interfaz común. El motor sólo conoce estos cuatro métodos."""

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
    """Cola: sale el más viejo. Es BFS."""

    def __init__(self):
        self._cola = deque()

    def agregar(self, nodo, h: float = 0.0) -> None:
        self._cola.append(nodo)

    def sacar(self):
        return self._cola.popleft()

    def __len__(self) -> int:
        return len(self._cola)


class FronteraLIFO(Frontera):
    """Pila: sale el más nuevo. Es DFS, y con límite creciente es IDDFS."""

    def __init__(self):
        self._pila = []

    def agregar(self, nodo, h: float = 0.0) -> None:
        self._pila.append(nodo)

    def sacar(self):
        return self._pila.pop()

    def __len__(self) -> int:
        return len(self._pila)


class FronteraPrioridad(Frontera):
    """Cola de prioridad: sale el de menor `peso_g · g(n) + peso_h · h(n)`."""

    usa_heuristica = True

    def __init__(self, peso_g: float = 1.0, peso_h: float = 1.0):
        self.peso_g = peso_g
        self.peso_h = peso_h
        self._monticulo = []
        self._contador = 0

    def agregar(self, nodo, h: float = 0.0) -> None:
        prioridad = self.peso_g * nodo.g + self.peso_h * h
        # Desempata primero menor h y después el orden de inserción. El contador
        # además evita que heapq compare Nodos, que no son comparables.
        heapq.heappush(self._monticulo, (prioridad, h, self._contador, nodo))
        self._contador += 1

    def sacar(self):
        return heapq.heappop(self._monticulo)[3]

    def __len__(self) -> int:
        return len(self._monticulo)
