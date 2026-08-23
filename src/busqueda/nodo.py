"""El nodo del árbol de búsqueda."""


class Nodo:
    """Un estado con su historia."""

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
        acciones.reverse()
        return acciones

    def cantidad_empujes(self) -> int:
        """Cuenta los empujes del camino desde la raíz hasta este nodo."""
        empujes = 0
        nodo = self
        while nodo.padre is not None:
            if nodo.hubo_empuje:
                empujes += 1
            nodo = nodo.padre
        return empujes

    def __repr__(self) -> str:
        return f'<Nodo g={self.g} prof={self.profundidad} {self.estado!r}>'
