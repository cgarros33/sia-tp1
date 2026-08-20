"""Lo estático del nivel: paredes, metas y dimensiones.

QUÉ REPRESENTA
    Un `Tablero` es todo lo que NO cambia durante la búsqueda. Hay un único
    objeto por nivel y todos los nodos lo comparten por referencia.

LA DECISIÓN DE DISEÑO
    Separar lo estático de lo dinámico. Si las paredes y las metas vivieran
    adentro del estado, cada uno de los ~2.000.000 de estados que expande BFS
    en N5 cargaría su propia copia, y el hash del estado —que se consulta una
    vez por cada nodo generado— tendría que recorrerlas siempre. Todo lo demás
    de este módulo (posiciones linealizadas, tabla de movimientos
    precalculada) son consecuencias de haber tomado esa decisión primero.

QUÉ SE DESCARTÓ
    Representar el nivel como una matriz de caracteres (`list[list[str]]`) que
    mezcle paredes, metas, cajas y jugador. Es cómoda para imprimir y pésima
    para buscar: es mutable —y por lo tanto no hasheable—, copiarla cuesta
    O(alto x ancho) por sucesor, y obliga a distinguir "caja sobre meta" de
    "caja" en cada consulta. Acá los caracteres aparecen sólo en `dibujar()`,
    que es entrada/salida y se llama unas pocas veces por corrida.
"""

ARRIBA, ABAJO, IZQUIERDA, DERECHA = 0, 1, 2, 3

# El orden es fijo y explícito a propósito: DFS depende del orden en que se
# generan los sucesores, así que fijarlo acá es lo que hace que el método sea
# reproducible entre corridas. Cambiar esta tupla cambia los números de DFS.
DIRECCIONES = (ARRIBA, ABAJO, IZQUIERDA, DERECHA)

# Letras del estándar de Sokoban (Up/Down/Left/Right). Se usan para imprimir la
# solución; game-sokoban.com publica los récords con esta misma notación, así
# que sirven para comparar contra la fuente externa sin traducir nada.
NOMBRE_DIR = {ARRIBA: 'U', ABAJO: 'D', IZQUIERDA: 'L', DERECHA: 'R'}

# (delta_fila, delta_columna) indexado por dirección. La fila crece hacia abajo
# porque así se lee el archivo XSB: la fila 0 es la primera línea del texto.
DESPLAZAMIENTO = ((-1, 0), (1, 0), (0, -1), (0, 1))


class Tablero:
    """La parte inmutable de un nivel.

    Las posiciones son enteros: `p = fila * ancho + columna`. No son tuplas
    `(fila, columna)` porque el motor pregunta millones de veces "¿hay una caja
    en p?" contra un `frozenset`: hashear un `int` es una operación primitiva,
    mientras que hashear una tupla implica combinar los hashes de sus dos
    componentes. El costo es que el código queda menos legible; se compensa con
    `coordenadas()` e `indice()`, que se usan sólo para entrada/salida.
    """

    __slots__ = ('alto', 'ancho', 'paredes', 'metas', 'transitables', 'mover', 'nombre')

    def __init__(self, alto: int, ancho: int,
                 paredes: frozenset[int], metas: frozenset[int],
                 nombre: str = ''):
        self.alto = alto
        self.ancho = ancho
        self.paredes = frozenset(paredes)
        self.metas = frozenset(metas)
        self.nombre = nombre

        # "Transitable" = toda celda del rectángulo que no es pared. Sin filtro
        # de alcanzabilidad: es la definición que usa la fórmula de estimación
        # del espacio de estados de docs/03_NUMEROS_DE_ORO.md, y la que da
        # 12/32/35/31/41 en los cinco niveles. NO es lo mismo que "alcanzable
        # por el jugador": en n2_akk04.sok, con las cajas en su posición
        # inicial, el jugador sólo alcanza 3 de esas 32 celdas.
        self.transitables = frozenset(
            p for p in range(alto * ancho) if p not in self.paredes
        )

        self.mover = self._construir_tabla_de_movimientos()

    def _construir_tabla_de_movimientos(self) -> tuple[tuple[int, ...], ...]:
        """Precalcula `mover[p][d]`: a qué celda se llega desde `p` yendo en `d`.

        Devuelve -1 si ahí hay pared o si se cae fuera del tablero. Así, durante
        la búsqueda, validar una acción es un acceso a una tupla en vez de
        recalcular límites y consultar el conjunto de paredes millones de veces.
        Se calcula para TODA celda, incluidas las paredes, para que el índice
        coincida con la posición y no haga falta traducir.
        """
        tabla = []
        for p in range(self.alto * self.ancho):
            fila, col = divmod(p, self.ancho)
            vecinos = []
            for d in DIRECCIONES:
                df, dc = DESPLAZAMIENTO[d]
                nueva_fila, nueva_col = fila + df, col + dc
                # Las dos coordenadas se controlan por separado: con posiciones
                # linealizadas, moverse a la izquierda desde la columna 0 daría
                # p-1, que es una celda existente pero de la fila anterior.
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
        """Devuelve el tablero con `estado` encima, en formato XSB.

        No es un lujo: la Fase 7 lo usa para el reproductor estado por estado
        que pidió la cátedra, y la Fase 3 para el test de ida y vuelta (dibujar
        y volver a parsear tiene que dar el mismo problema). Que la salida sea
        XSB válido —y no un formato propio— es lo que hace posible ese test.
        """
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
