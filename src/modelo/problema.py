"""La formulación del problema: los cinco componentes vistos en clase.

    Estado inicial        problema.inicial
    Acciones              las 4 direcciones (movimiento del JUGADOR)
    Modelo de transición  problema.sucesores()
    Costo                 1 por movimiento, uniforme
    Condición de meta     problema.es_meta()

LA DECISIÓN DE DISEÑO — qué es una acción
    Una acción es un movimiento del jugador, no un empuje de caja. El enunciado
    pide optimizar CANTIDAD DE MOVIMIENTOS, así que todo movimiento cuesta 1,
    empuje o no. Como el costo es uniforme, g(n) coincide con la profundidad del
    nodo y BFS ya resulta óptimo, que es lo que permite usarlo como verdad de
    referencia contra los récords publicados.

QUÉ SE DESCARTÓ — hay que poder explicarlo en el oral
    Existe una optimización clásica de Sokoban: normalizar al jugador a un
    representante de su región alcanzable y buscar sobre EMPUJES en vez de
    movimientos. Reduce muchísimo el espacio de estados —en N5 el jugador tiene
    41 celdas posibles que colapsan a unas pocas regiones—, y es lo que usan los
    solvers serios.

    La descartamos porque optimiza otra métrica: una solución con menos empujes
    puede necesitar más movimientos del jugador entre empujes consecutivos, y el
    enunciado pide minimizar movimientos. La medimos igual para poder mostrar la
    diferencia, pero eso es Fase 6, no acá.
"""

from .estado import Estado
from .tablero import DIRECCIONES


class Problema:
    """Un nivel concreto, listo para que el motor de la Fase 2 lo recorra.

    No guarda estado de la búsqueda: `sucesores()` es una función pura del
    estado que recibe. Esa pureza es lo que permite que los cinco métodos
    compartan el mismo modelo y que la comparación entre ellos sea justa.
    """

    __slots__ = ('tablero', 'inicial', 'detector_deadlocks', 'orden_direcciones')

    def __init__(self, tablero, inicial: Estado, detector_deadlocks=None, orden_direcciones=None):
        self.tablero = tablero
        self.inicial = inicial
        # Gancho para la Fase 5. Firma:
        #     detector(cajas: frozenset[int], caja_movida: int) -> bool
        # True si esa configuración de cajas ya no admite solución.
        #
        # Recibe la caja recién empujada y no sólo el conjunto porque alcanza
        # con revisar esa: las demás ya se validaron cuando se movieron, y todo
        # bloque de 2x2 congelado que aparezca ahora tiene que incluir a la
        # recién empujada. En los niveles de 4 cajas eso es un factor 4 de
        # trabajo ahorrado por cada empuje, y cuesta un parámetro.
        #
        # Se consulta sólo después de un empuje: un movimiento del jugador que
        # no empuja nada no puede crear un deadlock, las cajas quedaron donde
        # estaban.
        self.detector_deadlocks = detector_deadlocks
        # El orden en que sucesores() genera las acciones. DIRECCIONES por defecto.
        # DFS depende de este orden: cambiarlo cambia qué solución encuentra. Con
        # las 24 permutaciones posibles se mide la variabilidad real de DFS.
        self.orden_direcciones = orden_direcciones if orden_direcciones is not None else DIRECCIONES

    def es_meta(self, estado: Estado) -> bool:
        """True si todas las cajas están sobre metas.

        Alcanza con la igualdad de conjuntos porque el parser ya garantizó que
        hay tantas cajas como metas: si los tamaños coinciden, "todas las cajas
        están en metas" y "todas las metas tienen caja" son la misma condición.
        """
        return estado.cajas == self.tablero.metas

    def sucesores(self, estado: Estado, podar_deadlocks: bool = True):
        """Genera (accion, estado_siguiente, hubo_empuje) para cada acción legal.

        Es el punto más caliente del proyecto: se ejecuta una vez por nodo
        expandido, o sea ~2.000.000 de veces en N5. Por eso las tres tablas que
        más se consultan se copian a variables locales antes del bucle (en
        CPython un local es más barato que un atributo) y no se delega en
        funciones auxiliares.

        `podar_deadlocks=False` devuelve todos los sucesores legales sin
        consultar el detector de la Fase 5. Lo usa `reconstruir_estados()`: ver
        la explicación ahí.
        """
        mover = self.tablero.mover
        cajas = estado.cajas
        detectar = self.detector_deadlocks if podar_deadlocks else None
        movimientos_del_jugador = mover[estado.jugador]

        for d in self.orden_direcciones:
            destino = movimientos_del_jugador[d]
            if destino == -1:
                continue  # pared o borde del tablero

            if destino in cajas:
                atras = mover[destino][d]
                # Una caja se empuja sólo si detrás hay piso libre: ni pared, ni
                # borde, ni otra caja. El jugador nunca tira, sólo empuja.
                if atras == -1 or atras in cajas:
                    continue
                nuevas_cajas = (cajas - {destino}) | {atras}
                # El detector se consulta sobre el conjunto de cajas, antes de
                # construir el Estado: si el empuje lleva a un deadlock, ni
                # siquiera se paga el objeto ni el hash.
                if detectar is not None and detectar(nuevas_cajas, atras):
                    continue
                yield d, Estado(destino, nuevas_cajas), True
            else:
                # Sin empuje las cajas no cambian, así que se comparte el mismo
                # frozenset en vez de copiarlo: son la enorme mayoría de los
                # sucesores y el objeto es inmutable, no hay riesgo de aliasing.
                yield d, Estado(destino, cajas), False

    def reconstruir_estados(self, acciones) -> list[Estado]:
        """Aplica una secuencia de acciones desde el inicial y devuelve TODOS los estados.

        Devuelve la lista completa, empezando por el inicial: es lo que consume
        el reproductor de la Fase 7, porque la cátedra pidió explícitamente
        mostrar la solución estado por estado y no sólo el resultado final.

        Reaplica las acciones pasando por `sucesores()` en lugar de tener su
        propia copia de las reglas del juego. Es más lento, pero una solución
        tiene a lo sumo unos cientos de pasos y a cambio queda garantizado que
        lo que se dibuja es exactamente lo que recorrió la búsqueda: si hubiera
        dos implementaciones de la transición, un error en una de ellas se
        volvería invisible.

        Pide los sucesores SIN podar deadlocks a propósito. La poda es una
        optimización de la búsqueda, no una regla del juego: reproducir un
        camino ya encontrado no tiene por qué pasar por ella. Si el detector de
        la Fase 5 tuviera un bug y descartara un estado legal, con la poda
        activada el reproductor cortaría el camino a la mitad con un error de
        "acción no legal", que apunta al lugar equivocado; sin ella, el camino
        se dibuja entero y el bug del detector se ve donde está, comparando
        nodos expandidos.
        """
        estados = [self.inicial]
        actual = self.inicial
        for paso, accion in enumerate(acciones):
            siguiente = None
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
