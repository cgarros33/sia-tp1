"""Lo dinámico del nivel: dónde está el jugador y dónde están las cajas.

QUÉ REPRESENTA
    Un `Estado` es una foto completa de la partida en un instante. Todo lo que
    no está acá (paredes, metas, dimensiones) es constante y vive en `Tablero`.

LA DECISIÓN DE DISEÑO
    Las cajas son un `frozenset[int]`, no una lista ni una tupla ordenada.

    Razón 1 - inmutabilidad, y por lo tanto hasheabilidad. El motor pregunta
    "¿ya visité este estado?" una vez por cada nodo generado, millones de veces.
    Con un conjunto basado en hash esa consulta es O(1); recorriendo una lista
    sería O(n). Python sólo hashea objetos inmutables, precisamente porque el
    hash se deriva del contenido: si el contenido pudiera cambiar después de
    guardado, el objeto quedaría archivado en una posición de la tabla que ya no
    le corresponde y sería irrecuperable.

    Razón 2 - las cajas son indistinguibles. Dos configuraciones que difieren
    sólo en el orden en que enumeramos las cajas son EL MISMO estado del juego.
    Un conjunto captura esa simetría por construcción. Con una lista habría que
    normalizar el orden antes de cada comparación, y olvidarse de hacerlo
    significaría expandir muchas veces el mismo estado sin darse cuenta.

QUÉ SE DESCARTÓ
    `numpy.ndarray`: es mutable, por lo tanto no hasheable, y su operador de
    igualdad devuelve un arreglo de booleanos elemento a elemento en vez de un
    `bool`, así que ni siquiera se puede usar en un `if`.
"""


class Estado:
    """Jugador y cajas, con el hash calculado una sola vez.

    CPython NO cachea el hash de las tuplas: lo recalcula en cada consulta. El
    `frozenset` sí cachea el suyo, pero combinarlo con la posición del jugador
    en cada lookup sigue costando. Por eso se calcula una vez en `__init__` y se
    guarda. `__slots__` evita el `__dict__` por instancia, que con millones de
    estados vivos es memoria que importa.
    """

    __slots__ = ('jugador', 'cajas', '_hash')

    def __init__(self, jugador: int, cajas: frozenset[int]):
        self.jugador = jugador
        self.cajas = cajas
        self._hash = hash((jugador, cajas))

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, otro) -> bool:
        # El hash se compara primero porque es un entero ya calculado: descarta
        # de una la enorme mayoría de las colisiones sin tocar el frozenset.
        if self is otro:
            return True
        if not isinstance(otro, Estado):
            return NotImplemented
        return (self._hash == otro._hash
                and self.jugador == otro.jugador
                and self.cajas == otro.cajas)

    def __repr__(self) -> str:
        return f'Estado(jugador={self.jugador}, cajas={sorted(self.cajas)})'
