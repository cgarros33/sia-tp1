"""Lo dinámico del nivel: dónde está el jugador y dónde están las cajas."""


class Estado:
    """Jugador y cajas, con el hash calculado una sola vez."""

    __slots__ = ('jugador', 'cajas', '_hash')

    def __init__(self, jugador: int, cajas: frozenset[int]):
        self.jugador = jugador
        self.cajas = cajas
        self._hash = hash((jugador, cajas))

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, otro) -> bool:
        if self is otro:
            return True
        if not isinstance(otro, Estado):
            return NotImplemented
        return (self._hash == otro._hash
                and self.jugador == otro.jugador
                and self.cajas == otro.cajas)

    def __repr__(self) -> str:
        return f'Estado(jugador={self.jugador}, cajas={sorted(self.cajas)})'
