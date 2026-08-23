"""La formulación del problema: los cinco componentes vistos en clase."""

from .estado import Estado
from .tablero import DIRECCIONES


class Problema:
    """Un nivel concreto, listo para que el motor de la Fase 2 lo recorra."""

    __slots__ = ('tablero', 'inicial', 'detector_deadlocks', 'orden_direcciones')

    def __init__(self, tablero, inicial: Estado, detector_deadlocks=None, orden_direcciones=None):
        self.tablero = tablero
        self.inicial = inicial
        self.detector_deadlocks = detector_deadlocks
        self.orden_direcciones = orden_direcciones if orden_direcciones is not None else DIRECCIONES

    def es_meta(self, estado: Estado) -> bool:
        """True si todas las cajas están sobre metas."""
        return estado.cajas == self.tablero.metas

    def sucesores(self, estado: Estado, podar_deadlocks: bool = True):
        """Genera (accion, estado_siguiente, hubo_empuje) para cada acción legal."""
        mover = self.tablero.mover
        cajas = estado.cajas
        detectar = self.detector_deadlocks if podar_deadlocks else None
        movimientos_del_jugador = mover[estado.jugador]

        for d in self.orden_direcciones:
            destino = movimientos_del_jugador[d]
            if destino == -1:
                continue

            if destino in cajas:
                atras = mover[destino][d]
                if atras == -1 or atras in cajas:
                    continue
                nuevas_cajas = (cajas - {destino}) | {atras}
                if detectar is not None and detectar(nuevas_cajas, atras):
                    continue
                yield d, Estado(destino, nuevas_cajas), True
            else:
                yield d, Estado(destino, cajas), False

    def reconstruir_estados(self, acciones) -> list[Estado]:
        """Reejecuta una secuencia de acciones y devuelve todos los estados."""
        estados = [self.inicial]
        actual = self.inicial
        for paso, accion in enumerate(acciones):
            siguiente = None
            # Sin poda: reproducir un camino ya encontrado no pasa por el detector.
            for candidata, resultado, _ in self.sucesores(actual, podar_deadlocks=False):
                if candidata == accion:
                    siguiente = resultado
                    break
            if siguiente is None:
                raise ValueError(
                    f'La acción {accion} del paso {paso} no es legal en el estado '
                    f'{actual}. La secuencia no es ejecutable.'
                )
            estados.append(siguiente)
            actual = siguiente
        return estados

    def __repr__(self) -> str:
        return f'<Problema {self.tablero!r}, inicial={self.inicial!r}>'
