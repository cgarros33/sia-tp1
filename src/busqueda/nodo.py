"""El nodo del árbol de búsqueda.

QUÉ REPRESENTA
    Un `Nodo` es un estado MÁS SU HISTORIA: qué nodo lo generó, con qué acción,
    cuánto costó llegar y a qué profundidad está. La distinción con `Estado` es
    la que más se pregunta en el oral:

        estado = una configuración del mundo. No sabe cómo se llegó ahí.
        nodo   = un estado y el camino por el que llegamos a él.

    Un mismo estado puede aparecer en varios nodos con distinto `g`, si hay
    varios caminos que llevan a él. Por eso el conjunto de visitados del motor
    se indexa POR ESTADO y no por nodo: si se indexara por nodo, un estado ya
    visto entraría de nuevo cada vez que se lo alcanza por otro camino y la
    búsqueda no terminaría nunca en un grafo con ciclos, que es exactamente lo
    que es Sokoban (todo movimiento del jugador es reversible mientras no
    empuje una caja).

LA DECISIÓN DE DISEÑO
    Cada nodo guarda una referencia a su PADRE, no la lista de acciones que lo
    llevaron hasta ahí. El camino se reconstruye una sola vez, al final,
    subiendo por los padres.

    Guardar el camino completo en cada nodo multiplicaría la memoria por la
    profundidad: en N5, con ~2.000.000 de nodos y soluciones de 306
    movimientos, serían cientos de millones de enteros almacenados para usar
    uno solo de esos caminos. Con el padre, cada nodo agrega una referencia.

QUÉ SE DESCARTÓ
    Hacer que `Nodo` sea comparable (`__lt__`) para poder meterlo directo en un
    `heapq`. Se descartó porque la relación de orden entre nodos no es una
    propiedad del nodo: depende del método de búsqueda. Un mismo nodo va antes
    o después según se esté corriendo A* o Greedy. El orden es responsabilidad
    de la frontera, y por eso vive en `frontera.py`.
"""


class Nodo:
    """Un estado con su historia.

    `g` y `profundidad` valen siempre lo mismo en este TP, porque el costo es
    uniforme (1 por movimiento). Se guardan igual por separado porque son
    conceptos distintos —costo acumulado contra cantidad de aristas— y porque
    el día que el costo deje de ser uniforme el motor no habría que tocarlo.
    Tener los dos hace explícito que BFS es óptimo acá por una razón puntual:
    minimizar profundidad y minimizar costo son lo mismo cuando cada arista
    cuesta 1.
    """

    __slots__ = ('estado', 'padre', 'accion', 'g', 'profundidad', 'hubo_empuje')

    def __init__(self, estado, padre=None, accion=None,
                 g: int = 0, profundidad: int = 0, hubo_empuje: bool = False):
        self.estado = estado
        self.padre = padre
        self.accion = accion
        self.g = g
        self.profundidad = profundidad
        self.hubo_empuje = hubo_empuje

    def camino_acciones(self) -> list[int]:
        """Devuelve las acciones desde la raíz hasta este nodo, en orden."""
        acciones = []
        nodo = self
        while nodo.padre is not None:
            acciones.append(nodo.accion)
            nodo = nodo.padre
        acciones.reverse()  # se subió del nodo a la raíz: hay que darlo vuelta
        return acciones

    def cantidad_empujes(self) -> int:
        """Cuenta los empujes del camino desde la raíz hasta este nodo.

        Existe para poder contrastar contra los números de oro. Que coincidan
        movimientos Y empujes es lo que da confianza en que el modelo y la
        transcripción de los niveles están bien: con una sola pared mal puesta,
        el óptimo daría distinto en al menos una de las dos cifras.
        """
        empujes = 0
        nodo = self
        while nodo.padre is not None:
            if nodo.hubo_empuje:
                empujes += 1
            nodo = nodo.padre
        return empujes

    def __repr__(self) -> str:
        return f'<Nodo g={self.g} prof={self.profundidad} {self.estado!r}>'
