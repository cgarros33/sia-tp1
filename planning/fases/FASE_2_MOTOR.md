# FASE 2 — Motor genérico y los cinco métodos

**Dueño:** Matías · **Estado:** pendiente

La fase más importante del proyecto desde el punto de vista de la arquitectura.
Al terminar, los cinco métodos de búsqueda resuelven los cinco niveles y BFS
reproduce los costos publicados.

---

## Archivos a crear

```
src/busqueda/__init__.py
src/busqueda/nodo.py
src/busqueda/frontera.py
src/busqueda/motor.py
src/busqueda/algoritmos.py
src/heuristicas/__init__.py
src/heuristicas/registro.py        (sólo h0 y h1; la escalera es la Fase 4)
main.py
config.json
verificaciones/verificar_fase2.py
```

---

## La decisión de arquitectura de toda la fase

> **Hay UN SOLO bucle de búsqueda. Los cinco métodos se diferencian
> únicamente por la estructura de datos de la frontera.**

No cinco archivos con cinco bucles parecidos. Un `motor.py` que implementa el
algoritmo genérico de la Clase 3, y una jerarquía de fronteras que decide en qué
orden salen los nodos.

Dos consecuencias, y las dos hay que poder defenderlas:

1. **La comparación entre métodos es justa por construcción.** Todos corren
   exactamente el mismo código de expansión, el mismo control de estados
   repetidos y la misma recolección de métricas. Si BFS expande más nodos que
   A\*, es por la política de la frontera y no porque uno esté mejor
   implementado que el otro. Con cinco bucles separados, cualquier diferencia
   sería sospechosa.

2. **Agregar un método es escribir una subclase, no tocar el motor.** El
   Heuristic Path Algorithm de la Fase 8 sale gratis de esto.

---

## `nodo.py`

### `Nodo` no es `Estado` — la distinción que más se pregunta

- Un **estado** es una configuración del mundo: dónde está el jugador y dónde
  están las cajas. No sabe cómo se llegó ahí.
- Un **nodo** es un estado **más su historia**: qué nodo lo generó, con qué
  acción, cuánto costó llegar y a qué profundidad está.

Un mismo estado puede aparecer en varios nodos con distinto `g`, si hay varios
caminos que llevan a él. **Por eso el conjunto de visitados se indexa por estado
y no por nodo.**

### Decisión: guardar el padre, no el camino

`padre` es una referencia al nodo anterior. El camino se reconstruye una sola
vez, al final, subiendo por los padres. Guardar la lista de acciones completa en
cada nodo multiplicaría la memoria por la profundidad: en N5, con soluciones de
306 movimientos y ~2 millones de nodos, sería inviable.

### Interfaz

```python
class Nodo:
    __slots__ = ('estado','padre','accion','g','profundidad','hubo_empuje')
    def camino_acciones(self) -> list[int]     # sube por los padres
    def cantidad_empujes(self) -> int          # cuenta hubo_empuje en el camino
```

`cantidad_empujes()` existe para poder contrastar contra los números de oro:
que coincidan **movimientos y empujes** es lo que da confianza en que el modelo
y la transcripción están bien.

---

## `frontera.py`

Una interfaz con tres implementaciones:

| Clase | Método | Estructura | Sale |
|---|---|---|---|
| `FronteraFIFO` | BFS | `collections.deque` | el más viejo |
| `FronteraLIFO` | DFS, IDDFS | lista como pila | el más nuevo |
| `FronteraPrioridad` | Greedy, A\*, HPA | `heapq` | el de menor prioridad |

### `FronteraPrioridad` con pesos

```python
FronteraPrioridad(peso_g, peso_h)   →   prioridad = peso_g · g(n) + peso_h · h(n)
```

| Configuración | `peso_g` | `peso_h` | Qué es |
|---|---|---|---|
| Costo uniforme | 1 | 0 | equivalente a BFS con costo unitario |
| A\* | 1 | 1 | `f = g + h` |
| Greedy | 0 | 1 | `f = h` |
| HPA con `w` | `1-w` | `w` | el barrido de la Fase 8 |

Parametrizar así, en vez de tener tres clases, es lo que permite recorrer el
espectro completo con un solo parámetro en la Fase 8 sin escribir código nuevo.

### Decisión: el criterio de desempate

Ante igual prioridad, preferir **menor `h`**. Intuición: entre dos nodos que
prometen el mismo costo total, conviene abrir el que ya avanzó más hacia la
meta, porque está más cerca de cerrar la solución.

Ante igual prioridad y `h`, desempatar por un **contador de inserción**
monótono. Esto **no es algorítmico sino de reproducibilidad**: sin él, `heapq`
intentaría comparar los objetos `Nodo` entre sí (que no son comparables, sería
un `TypeError`) y, peor, el orden de exploración podría variar entre corridas.
Con el contador, dos corridas del mismo experimento recorren el árbol en el
mismo orden y producen exactamente los mismos números.

---

## `motor.py`

### El bucle

Los seis pasos del algoritmo genérico:

1. Inicializar la frontera con el nodo raíz.
2. Si la frontera está vacía → fracaso.
3. Extraer un nodo según la política de la frontera.
4. Si su estado es meta → devolver la solución.
5. Expandirlo: generar sus sucesores.
6. Insertar en la frontera los que corresponda. Volver a 2.

### Decisión: el chequeo de meta se hace al EXTRAER, no al generar

Es obligatorio para la optimalidad de A\*: un nodo meta generado temprano puede
no ser el más barato, porque puede haber en la frontera otro camino a la meta
con menor `f` todavía sin extraer. Con BFS y costo uniforme daría lo mismo, pero
**mantenemos un único criterio para los cinco métodos**, porque si no la
comparación de nodos expandidos entre ellos no sería homogénea.

### Decisión: dos políticas de estados repetidos

Esta es la parte más delicada de la fase.

**`'cerrado'`** — un estado visitado no se vuelve a insertar nunca.
Válido cuando la **primera** vez que llegamos a un estado ya fue por el camino
más barato. Es el caso de BFS con costo uniforme. También lo usa Greedy: no
garantiza optimalidad de todas formas, así que reabrir nodos sólo agregaría
trabajo.

**`'mejor_g'`** — se guarda el mejor `g` conocido de cada estado y se reabre si
se llega por un camino más barato.

Lo necesitan dos métodos, por razones distintas:

- **A\***, porque si la heurística es admisible pero **no consistente**, un
  estado puede expandirse antes de haber encontrado su camino óptimo. Sin
  reapertura se perdería la optimalidad. Nuestras heurísticas de la Fase 4 van a
  ser consistentes, pero el motor no puede asumirlo.
- **IDDFS**, por un motivo completamente distinto: un estado cerrado a
  profundidad 20 podría ser alcanzable a profundidad 12 por otra rama, y
  cerrarlo definitivamente haría **perder soluciones que sí entran en el
  límite**. Es un error clásico y la cátedra lo marcó explícitamente en la
  Clase 3.

Cuando se usa `'mejor_g'` con cola de prioridad, hay que descartar las
**entradas obsoletas**: al extraer un nodo cuyo `g` es peor que el mejor
conocido para ese estado, se saltea sin expandir.

### Decisión: dos métricas de frontera, no una

El enunciado pide "cantidad de nodos frontera". Reportamos dos, porque
significan cosas distintas:

- **`frontera_final`**: cuántos quedaron sin expandir al terminar.
- **`frontera_maxima`**: el pico a lo largo de la corrida. **Es el número que
  describe el consumo de memoria del método**, y el que va a hacer visible por
  qué IDDFS existe.

### `Resultado`

Un `dataclass` con todo lo que pide el enunciado más lo que necesita el análisis:

```python
exito, costo, nodos_expandidos, frontera_final, acciones, tiempo_s   # el enunciado
frontera_maxima, nodos_generados, estados_visitados, empujes,
profundidad, motivo_fin, metodo, heuristica, nivel                   # el análisis
```

`motivo_fin` ∈ `{'meta', 'sin_solucion', 'timeout', 'max_nodos'}`. **Distinguir
"no hay solución" de "me quedé sin tiempo" es obligatorio**: son resultados
cualitativamente distintos y confundirlos en la presentación sería un error
grave.

### Límites

`max_nodos` y `timeout_s` se chequean en cada iteración del bucle.
`limite_profundidad` poda los nodos que llegan al límite sin expandirlos (lo usa
DFS con límite e IDDFS).

---

## `algoritmos.py`

Cada método es una elección de frontera más una política. Fijate lo cortos que
quedan: toda la lógica vive en el motor.

| Función | Frontera | Política | ¿Óptimo? |
|---|---|---|---|
| `bfs` | FIFO | cerrado | **Sí**, porque el costo es uniforme |
| `dfs` | LIFO | cerrado | No |
| `iddfs` | LIFO + límite creciente | mejor_g | **Sí** |
| `greedy` | prioridad (0, 1) | cerrado | No |
| `a_estrella` | prioridad (1, 1) | mejor_g | **Sí** si `h` es admisible |
| `hpa` | prioridad (1−w, w) | según `w` | Sí sólo si `w ≤ 0.5` |

### Detalles de `dfs`

Sin límite de profundidad por defecto. **Termina igual**, porque el espacio de
estados es finito y llevamos el conjunto de visitados. El costo que devuelve va
a ser malísimo, y eso es exactamente lo que queremos mostrar.

### Detalles de `iddfs`

Las métricas se **acumulan** entre iteraciones: los nodos expandidos son la suma
de todas las pasadas. Pero `frontera_maxima` es el **máximo, no la suma**,
porque las pasadas no coexisten en memoria — y ese es justamente el punto del
método.

Guardar además la lista `(límite, nodos_expandidos_en_esa_iteración)`: es el
dato que muestra el crecimiento geométrico entre iteraciones y explica por qué
el trabajo repetido es tolerable.

**Se espera que IDDFS haga timeout en N4 y N5.** No es un fallo de la
implementación: es un resultado del TP y va reportado como tal.

---

## `src/heuristicas/registro.py` — sólo dos, por ahora

La escalera completa es la Fase 4. Acá hacen falta dos, como instrumentos:

- **`h0`**: constante 0. Admisible y consistente trivialmente. Sirve para el
  **test de control del motor**: A\*(h0) tiene que expandir exactamente la misma
  cantidad de nodos que BFS.
- **`h1`**: cantidad de cajas que no están sobre una meta. Hace falta para que
  Greedy sea ejecutable y se pueda mostrar que no es óptimo.

Cada heurística es una **fábrica**: recibe el problema y devuelve una función
`estado -> número`. Ese diseño permite precalcular tablas una sola vez por nivel,
que es lo que van a necesitar h₃ y h₄ en la Fase 4.

> **`h1` dispara el protocolo de checkpoint** de `docs/01_REGLAS_DE_TRABAJO.md`,
> porque es un archivo que calcula. Va a ser un checkpoint corto —la
> demostración de admisibilidad es una línea— y sirve de ensayo para los de la
> Fase 4, que son los importantes. Hacelo igual.

---

## `main.py` y `config.json`

El enunciado pide configuración por archivo, no hardcodeada.

```json
{
  "nivel": "niveles/n4_matching.sok",
  "metodo": "astar",
  "heuristica": "h1",
  "timeout_s": 300,
  "max_nodos": 5000000,
  "limite_profundidad": null,
  "w": 0.5,
  "mostrar_solucion": true
}
```

`main.py` acepta un archivo de configuración alternativo como argumento y flags
que lo pisan (`--nivel`, `--metodo`, ...). Los flags son para probar rápido; los
experimentos que van a la presentación se corren siempre desde un archivo, para
que sean reproducibles.

La salida por pantalla tiene que incluir **todo lo que pide el enunciado**:
éxito o fracaso, costo, nodos expandidos, nodos frontera, la solución y el
tiempo.

---

## Criterio de aceptación

`verificaciones/verificar_fase2.py` corre y verifica, sobre los cinco niveles:

**1. BFS reproduce los números de oro.** Costo y empujes exactos contra
`docs/03_NUMEROS_DE_ORO.md`. Si alguno falla, código de salida 1.

**2. El test de control: A\*(h0) ≡ BFS.** Mismo costo **y misma cantidad exacta
de nodos expandidos**, en los cinco niveles. Es la invariante que separa bugs
del motor de bugs de heurísticas.

**3. Las soluciones son ejecutables.** Pasar las acciones por
`reconstruir_estados()` y verificar que el último estado es meta y que la
cantidad de estados es `costo + 1`.

**4. Los métodos no óptimos se comportan como se espera.** DFS devuelve una
solución con costo estrictamente mayor al óptimo. Greedy expande menos nodos que
BFS y su costo es mayor o igual.

**5. IDDFS usa mucha menos memoria máxima que BFS** en los niveles donde
termina, y expande más nodos.

Salida esperada, con una tabla por nivel:

```
=== n4_matching.sok  (óptimo publicado: 70 mov / 22 empujes) ===
método       costo  empujes  expandidos  front.máx   tiempo   resultado
BFS             70       22     xxx.xxx     xx.xxx    x.xx s  OK
A*(h0)          70       22     xxx.xxx     xx.xxx    x.xx s  OK  ≡ BFS
A*(h1)          70       22     xxx.xxx     xx.xxx    x.xx s  OK
Greedy(h1)      xx       xx      xx.xxx      x.xxx    x.xx s  subóptimo (esperado)
DFS            xxx      xxx     xxx.xxx     xx.xxx    x.xx s  subóptimo (esperado)
IDDFS            —        —   x.xxx.xxx         xx    x.xx s  timeout (esperado)
```

Al final, la tabla de nodos expandidos por BFS en los cinco niveles, **marcada
como valores a congelar en la Fase 3**.

---

## Cosas que NO van en esta fase

- Heurísticas más allá de h0 y h1 → Fase 4.
- Deadlocks. El gancho existe desde la Fase 1 y sigue sin usarse → Fase 5.
- El runner de la matriz de experimentos y el CSV → Fase 6.
- El reproductor y los GIF → Fase 7.

---

## Al terminar

1. Corré la verificación y mostrá la salida completa.
2. Escribí `docs/resumenes/FASE_2_RESUMEN.md` siguiendo la plantilla. Prestá
   atención especial a la sección "Preguntas que esta fase habilita en el oral":
   esta fase es la que más preguntas genera.
3. Listá los archivos creados y **esperá**. No commitees.
