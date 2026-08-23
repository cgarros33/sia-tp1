"""Lo estático del nivel: paredes, metas y dimensiones."""

ARRIBA, ABAJO, IZQUIERDA, DERECHA = 0, 1, 2, 3

DIRECCIONES = (ARRIBA, ABAJO, IZQUIERDA, DERECHA)

NOMBRE_DIR = {ARRIBA: 'U', ABAJO: 'D', IZQUIERDA: 'L', DERECHA: 'R'}

DESPLAZAMIENTO = ((-1, 0), (1, 0), (0, -1), (0, 1))


class Tablero:
    """La parte inmutable de un nivel."""

    __slots__ = ('alto', 'ancho', 'paredes', 'metas', 'transitables', 'mover', 'nombre')

    def __init__(self, alto: int, ancho: int,
                 paredes: frozenset[int], metas: frozenset[int],
                 nombre: str = ''):
        self.alto = alto
        self.ancho = ancho
        self.paredes = frozenset(paredes)
        self.metas = frozenset(metas)
        self.nombre = nombre

        # Transitable = toda celda que no es pared, sin filtro de alcanzabilidad.
        # Es la definición que usa la fórmula de espacio de estados de docs/03.
        self.transitables = frozenset(
            p for p in range(alto * ancho) if p not in self.paredes
        )

        self.mover = self._construir_tabla_de_movimientos()

    def _construir_tabla_de_movimientos(self) -> tuple[tuple[int, ...], ...]:
        """Precalcula `mover[p][d]`: a qué celda se llega desde `p` yendo en `d`."""
        tabla = []
        for p in range(self.alto * self.ancho):
            fila, col = divmod(p, self.ancho)
            vecinos = []
            for d in DIRECCIONES:
                df, dc = DESPLAZAMIENTO[d]
                nueva_fila, nueva_col = fila + df, col + dc
                if 0 <= nueva_fila < self.alto and 0 <= nueva_col < self.ancho:
                    destino = nueva_fila * self.ancho + nueva_col
                    vecinos.append(-1 if destino in self.paredes else destino)
                else:
                    vecinos.append(-1)
            tabla.append(tuple(vecinos))
        return tuple(tabla)

    def coordenadas(self, p: int) -> tuple[int, int]:
        """Posición lineal -> (fila, columna). Sólo para entrada/salida."""
        return divmod(p, self.ancho)

    def indice(self, fila: int, col: int) -> int:
        """(fila, columna) -> posición lineal. Sólo para entrada/salida."""
        return fila * self.ancho + col

    def dibujar(self, estado) -> str:
        """Devuelve el tablero con `estado` encima, en formato XSB."""
        filas = []
        for fila in range(self.alto):
            caracteres = []
            for col in range(self.ancho):
                p = fila * self.ancho + col
                if p in self.paredes:
                    caracteres.append('#')
                elif p in estado.cajas:
                    caracteres.append('*' if p in self.metas else '$')
                elif p == estado.jugador:
                    caracteres.append('+' if p in self.metas else '@')
                elif p in self.metas:
                    caracteres.append('.')
                else:
                    caracteres.append(' ')
            filas.append(''.join(caracteres))
        return '\n'.join(filas)

    def __repr__(self) -> str:
        return (f'<Tablero {self.nombre or "sin nombre"} '
                f'{self.alto}x{self.ancho}, {len(self.transitables)} transitables, '
                f'{len(self.metas)} metas>')
