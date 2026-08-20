# FASE 1 — Modelo del problema

**Dueño:** Matías · **Estado:** pendiente

Representar el mundo de Sokoban. Todavía no hay búsqueda: sólo tablero, estado,
lector de niveles y la formulación del problema.

---

## Archivos a crear

```
src/__init__.py
src/modelo/__init__.py
src/modelo/tablero.py
src/modelo/estado.py
src/modelo/parser_xsb.py
src/modelo/problema.py
```

---

## `tablero.py` — lo estático

Contiene **toda la información que no cambia durante la búsqueda**: paredes,
metas, dimensiones.

### Decisión 1: separar lo estático de lo dinámico

Las paredes y las metas no cambian nunca. Por lo tanto **no forman parte del
estado**: viven en un único objeto `Tablero` que todos los nodos comparten por
referencia.

Si estuvieran dentro de cada estado, cada uno de los ~2.000.000 de estados de N5
cargaría una copia de las paredes, y el hash del estado tendría que recorrerlas
en cada consulta de "¿ya visité esto?", que es la operación más frecuente del
motor.

### Decisión 2: linealizar las posiciones

Una posición es un entero `p = fila * ancho + columna`, no una tupla
`(fila, columna)`.

Motivo: el motor consulta constantemente si hay una caja en una posición,
contra un `frozenset`. Hashear un `int` es una operación primitiva; hashear una
tupla implica combinar los hashes de sus dos componentes. Sobre millones de
consultas, se nota.

Contra: el código queda menos legible. Se compensa con los métodos
`coordenadas(p)` e `indice(fila, col)`, que se usan sólo para entrada/salida.

### Decisión 3: precalcular la tabla de movimientos

`tablero.mover[p][d]` devuelve la celda a la que se llega desde `p` en dirección
`d`, o `-1` si es pared o está fuera del tablero.

Así verificar si una acción es válida es un acceso a una lista, en vez de
recalcular límites y consultar el conjunto de paredes millones de veces.

### Interfaz

```python
ARRIBA, ABAJO, IZQUIERDA, DERECHA = 0, 1, 2, 3
DIRECCIONES = (ARRIBA, ABAJO, IZQUIERDA, DERECHA)   # orden FIJO, ver abajo
NOMBRE_DIR  = {ARRIBA:'U', ABAJO:'D', IZQUIERDA:'L', DERECHA:'R'}

class Tablero:
    __slots__ = ('alto','ancho','paredes','metas','transitables','mover','nombre')
    def coordenadas(self, p) -> (fila, col)
    def indice(self, fila, col) -> int
    def dibujar(self, estado) -> str      # devuelve el tablero en formato XSB
```

**El orden de `DIRECCIONES` tiene que ser fijo y explícito.** DFS depende del
orden en que se generan los sucesores: fijarlo es lo que hace que el método sea
reproducible entre corridas.

`dibujar()` no es un lujo: la Fase 7 lo usa para el reproductor, y la Fase 3
para el test de ida y vuelta.

---

## `estado.py` — lo dinámico

```
estado = (posición del jugador, conjunto de posiciones de las cajas)
```

### Por qué `frozenset` y no lista ni tupla ordenada

**Razón 1 — inmutabilidad, y por lo tanto hasheabilidad.** El motor pregunta
"¿ya visité este estado?" una vez por cada nodo generado, millones de veces. Con
un conjunto basado en hash esa consulta es O(1); recorriendo una lista sería
O(n). Python sólo hashea objetos inmutables, precisamente porque el hash se
deriva del contenido: si el contenido pudiera cambiar después de guardado, el
objeto quedaría archivado en una posición de la tabla que ya no le corresponde y
sería irrecuperable.

**Razón 2 — las cajas son indistinguibles.** Dos configuraciones que difieren
sólo en el orden en que enumeramos las cajas son **el mismo estado del juego**.
Un conjunto captura esa simetría por construcción. Con una lista habría que
normalizar el orden antes de cada comparación, y olvidarse de hacerlo
significaría expandir el mismo estado muchas veces sin darse cuenta.

**Descartado: `numpy.ndarray`.** Es mutable, por lo tanto no hasheable. Además
su operador de igualdad devuelve un arreglo de booleanos elemento a elemento, no
un `bool`, así que ni siquiera se puede usar en un `if`.

### Por qué una clase con `__slots__` y hash cacheado

CPython **no cachea** el hash de las tuplas: lo recalcula en cada consulta. El
`frozenset` sí cachea el suyo, pero combinarlo con la posición del jugador en
cada lookup sigue costando. Se calcula una vez en el `__init__` y se guarda.
`__slots__` evita el `__dict__` por instancia, que con millones de estados es
memoria que importa.

### Interfaz

```python
class Estado:
    __slots__ = ('jugador','cajas','_hash')
    def __init__(self, jugador: int, cajas: frozenset[int])
    def __hash__(self)     # devuelve self._hash, precalculado
    def __eq__(self, otro) # compara hash primero, después contenido
```

---

## `parser_xsb.py` — lector de niveles

Formato XSB, el estándar de Sokoban y el que usa game-sokoban.com:

```
#  pared          .  meta              (espacio) piso
$  caja           *  caja sobre meta
@  jugador        +  jugador sobre meta
```

Las líneas que empiezan con `;` son comentarios y se ignoran. Nuestros niveles
las usan para documentar de dónde salieron y cuál es el récord publicado: **no
las borres**.

### Detalles que importan

- **Rellenar las filas cortas con pared.** Muchos editores recortan los espacios
  finales; sin este relleno quedarían agujeros en el borde del tablero y el
  jugador podría "escaparse".
- **Validar y fallar temprano.** Si no hay jugador, si no hay cajas, o si la
  cantidad de cajas no coincide con la de metas, lanzar `NivelInvalido` con un
  mensaje claro. Es mucho más barato que depurar después una búsqueda que se
  comporta raro.

### Interfaz

```python
class NivelInvalido(Exception): ...
def leer_texto(texto: str, nombre='') -> (Tablero, Estado)
def leer_archivo(ruta) -> (Tablero, Estado)
```

---

## `problema.py` — la formulación

Los cinco componentes del problema bien definido, tal como se vieron en clase:

| Componente | Dónde está |
|---|---|
| Estado inicial | `problema.inicial` |
| Conjunto de acciones | las 4 direcciones (movimiento del **jugador**) |
| Modelo de transición | `problema.sucesores()` |
| Función de costo | 1 por movimiento (uniforme) |
| Condición de meta | `problema.es_meta()` |

### Sobre la función de costo

El enunciado pide optimizar **cantidad de movimientos**, así que todo movimiento
del jugador cuesta 1, empuje o no. Como el costo es uniforme, `g(n)` coincide
con la profundidad del nodo y **BFS ya resulta óptimo**.

### Alternativa evaluada y descartada — hay que poder explicarla

Existe una optimización clásica de Sokoban que normaliza al jugador a un
representante de su región alcanzable y busca sobre **empujes** en vez de
movimientos. Reduce muchísimo el espacio de estados.

**La descartamos porque optimiza otra métrica.** Una solución con menos empujes
puede requerir más movimientos del jugador entre empujes consecutivos, y el
enunciado pide minimizar movimientos.

La medimos igual, para poder mostrar la diferencia. Eso va en la Fase 6, no acá.

### Interfaz

```python
class Problema:
    def __init__(self, tablero, inicial, detector_deadlocks=None)
    def es_meta(self, estado) -> bool
    def sucesores(self, estado)          # genera (accion, estado, hubo_empuje)
    def reconstruir_estados(self, acciones) -> list[Estado]
```

`detector_deadlocks` es un gancho para la Fase 5. En esta fase se recibe y se
ignora si es `None`; no implementes nada de deadlocks todavía.

`reconstruir_estados()` devuelve la secuencia **completa** de estados de una
solución. Es lo que va a consumir el reproductor de la Fase 7, y también lo que
permite verificar que una solución es realmente ejecutable.

---

## Criterio de aceptación

Un script de verificación que, para los cinco niveles:

1. Los parsea sin errores.
2. Reporta cantidad de cajas, metas y celdas transitables, y coincide con la
   tabla de `docs/03_NUMEROS_DE_ORO.md`.
3. Verifica que cajas y metas sean la misma cantidad.
4. Dibuja el estado inicial con `tablero.dibujar()`, lo vuelve a parsear, y
   obtiene el mismo problema (ida y vuelta).
5. Desde el estado inicial genera los sucesores y verifica que ninguno atraviese
   una pared ni superponga dos cajas.

Salida esperada:

```
n1_micro.sok      1 cajas   1 metas   12 celdas   ida y vuelta OK   4 sucesores válidos
n2_akk04.sok      4 cajas   4 metas   32 celdas   ida y vuelta OK   ...
n3_caminata.sok   2 cajas   2 metas   35 celdas   ida y vuelta OK   ...
n4_matching.sok   4 cajas   4 metas   31 celdas   ida y vuelta OK   ...
n5_limite.sok     4 cajas   4 metas   41 celdas   ida y vuelta OK   ...
```

---

## Al terminar

1. Corré la verificación y mostrá la salida.
2. Escribí `docs/resumenes/FASE_1_RESUMEN.md` siguiendo la plantilla.
3. Listá los archivos creados y **esperá**. No commitees.
