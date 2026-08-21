# FASE 2 — Motor genérico y los cinco métodos

**Estado:** terminada · **Fecha:** 2026-08-20

## En una frase

Los cinco métodos resuelven los cinco niveles con un único bucle de búsqueda,
BFS reproduce exactamente los diez números de oro y A\*(h0) expande exactamente
la misma cantidad de nodos que BFS en los cinco niveles.

## Archivos creados

### `src/busqueda/nodo.py`

**Qué hace:** representa un nodo del árbol de búsqueda: un estado más su
historia (padre, acción, `g`, profundidad, si el movimiento fue empuje).

**Por qué existe:** porque un estado no alcanza. La búsqueda necesita saber
**cómo** se llegó a cada configuración para poder devolver el camino, y el
mundo no necesita saberlo. Separarlos es lo que permite que el conjunto de
visitados se indexe por estado —hay uno solo por configuración— mientras el
árbol tiene tantos nodos como caminos explorados.

**La decisión importante:** cada nodo guarda una **referencia a su padre**, no
la lista de acciones que lo llevaron hasta ahí; el camino se reconstruye una
sola vez, al final, subiendo por los padres. Guardar el camino completo en cada
nodo multiplicaría la memoria por la profundidad: en N5, con 2.028.239 nodos
expandidos y soluciones de 306 movimientos, serían cientos de millones de
enteros guardados para usar uno solo de esos caminos.

Se descartó hacer `Nodo` comparable con `__lt__` para poder meterlo directo en
un `heapq`: el orden entre dos nodos no es una propiedad del nodo, depende del
método —un mismo par de nodos se ordena distinto en A\* que en Greedy—, así que
el orden vive en la frontera.

### `src/busqueda/frontera.py`

**Qué hace:** tres estructuras con la misma interfaz —FIFO, LIFO y cola de
prioridad con pesos— que deciden qué nodo sale a expandirse.

**Por qué existe:** es donde está encerrada **toda** la diferencia entre los
cinco métodos. Si este archivo no existiera, la diferencia estaría desparramada
en cinco bucles distintos y cualquier comparación entre métodos quedaría
contaminada por diferencias de implementación.

**La decisión importante:** `FronteraPrioridad(peso_g, peso_h)` es **una sola
clase parametrizada** en vez de tres. Con `(1, 0)` es costo uniforme, con
`(1, 1)` es A\*, con `(0, 1)` es Greedy y con `(1−w, w)` es el Heuristic Path
Algorithm. Eso es lo que va a permitir el barrido de `w` de la Fase 8 —recorrer
el espectro completo de costo uniforme a Greedy— sin escribir una línea de
código nueva.

El **criterio de desempate** tiene dos niveles y hay que poder explicar los dos.
Ante igual prioridad se prefiere **menor `h`**: entre dos nodos que prometen el
mismo costo total, conviene abrir el que ya avanzó más hacia la meta. Ante igual
prioridad y `h`, desempata un **contador de inserción** monótono, y esto **no es
algorítmico sino de reproducibilidad**: sin él `heapq` intentaría comparar
objetos `Nodo` entre sí —que no son comparables: `TypeError`— y, peor, el orden
de exploración podría variar entre corridas, con lo cual los nodos expandidos
dejarían de ser reproducibles. Y los nodos expandidos son la métrica central de
todo el TP.

### `src/busqueda/motor.py`

**Qué hace:** el bucle de búsqueda. Uno solo, para los cinco métodos. Además
define `Resultado`, el `dataclass` con todo lo que pide el enunciado más lo que
necesita el análisis.

**Por qué existe:** es **la decisión de arquitectura de toda la fase**. Los
cinco métodos corren exactamente el mismo código de expansión, el mismo control
de estados repetidos y el mismo contador de nodos. Consecuencia: la comparación
entre métodos es **justa por construcción**. Si BFS expande más nodos que A\*,
es por la política de la frontera y no porque uno esté mejor implementado.
Segunda consecuencia: agregar un método es escribir una subclase de frontera,
no tocar el motor.

**Las tres decisiones importantes:**

1. **El test de meta se hace al EXTRAER, no al generar.** Es obligatorio para la
   optimalidad de A\*: un nodo meta generado temprano puede no ser el más
   barato, porque puede haber en la frontera otro camino a la meta con menor `f`
   todavía sin extraer. Con BFS y costo uniforme daría lo mismo, pero se
   mantiene **un único criterio para los cinco métodos**: si no, la comparación
   de nodos expandidos entre ellos no sería homogénea.

2. **Los repetidos se detectan al GENERAR, no al expandir.** Un estado ya
   conocido ni siquiera entra a la frontera. Achica la frontera —que es
   memoria— y no cambia qué se expande, porque igual habría sido descartado al
   salir.

3. **Hay dos políticas de repetidos, no una.** Es la parte más delicada:
   - `'cerrado'`: un estado visto no se reinserta nunca. Vale cuando la primera
     vez que llegamos a un estado ya fue por el camino más barato, que es el
     caso de BFS con costo uniforme. Lo usa también Greedy: no garantiza
     optimalidad de todas formas, así que reabrir sólo agregaría trabajo.
   - `'mejor_g'`: se guarda el mejor `g` conocido y se reabre si se llega por un
     camino más barato. Lo necesitan **dos métodos por razones distintas**. A\*,
     porque si `h` es admisible pero **no consistente** un estado puede
     expandirse antes de haber encontrado su camino óptimo, y sin reapertura se
     perdería la optimalidad; nuestras heurísticas son consistentes, pero el
     motor no puede asumirlo. IDDFS, porque un estado cerrado a profundidad 20
     puede ser alcanzable a profundidad 12 por otra rama, y cerrarlo
     definitivamente haría **perder soluciones que sí entran en el límite**.

   Con `'mejor_g'` y cola de prioridad hay que descartar las **entradas
   obsoletas**: al extraer un nodo cuyo `g` es peor que el mejor conocido para
   ese estado, se saltea sin expandir (`heapq` no permite borrar del medio).

**Sobre las métricas de memoria: son tres y hay que no confundirlas.**
`frontera_final` es cuántos nodos quedaron sin expandir al terminar.
`frontera_maxima` es el pico de la frontera. Y `memoria_maxima` es el pico de
**frontera + estructura de visitados**, que es **la memoria real del método**.

La distinción no es un detalle: es el error que casi se cuela en esta fase. La
primera versión comparaba frontera contra frontera y concluía que IDDFS usa 55
veces menos memoria que BFS en N2. Es falso. IDDFS tiene una frontera de 49
nodos, sí, pero mantiene un diccionario de visitados que llega a 43.159
entradas, contra 2.691 + 46.779 de BFS: la memoria total es **0,87 veces** la de
BFS, no 55 veces menos. En N3 es 0,98. Ver la sección de números nuevos.

**Sobre `motivo_fin`:** distinguir `'sin_solucion'` de `'timeout'` y de
`'max_nodos'` es obligatorio. Son resultados cualitativamente distintos y
confundirlos en la presentación sería un error grave: "IDDFS no resuelve N4" es
falso, lo correcto es "IDDFS no resuelve N4 dentro de los 3.000.000 de nodos".

Tres campos que no estaban en la especificación y se agregaron con motivo:
`memoria_maxima`, explicado arriba; `podados_por_limite` —si es 0 y no hubo
solución, el espacio quedó agotado y no hay solución; si es mayor que 0, sólo
sabemos que no la hay dentro del límite, y es lo que le permite a IDDFS decidir
si vale otra iteración— e `iteraciones`, que la propia especificación pide para
IDDFS.

### `src/busqueda/algoritmos.py`

**Qué hace:** los cinco métodos, cada uno como una elección de frontera más una
política, y `resolver()`, que despacha por nombre.

**Por qué existe:** es la demostración de que la arquitectura funciona. `bfs`,
`dfs`, `greedy` y `a_estrella` son **una línea de código cada uno**: toda la
lógica vive en el motor. Si alguno hubiera necesitado su propio bucle, la
comparación entre métodos habría dejado de ser justa.

**La decisión importante:** IDDFS es el único que no es una sola llamada, porque
tiene que **acumular métricas entre iteraciones**. Los nodos expandidos se
**suman** —ese trabajo se hizo de verdad— pero `frontera_maxima` y
`memoria_maxima` son el **máximo, no la suma**, porque las pasadas no coexisten
en memoria: cada iteración arranca con las estructuras vacías.

Acá vive también `iddfs_puro()`, que es el mismo IDDFS con la política
`'camino'`: **sin estructura de visitados**, evitando solamente repetir estados
que ya están en el camino actual. Es el IDDFS de los libros, el que
efectivamente tiene memoria lineal en la profundidad. Existe para poder **medir**
el intercambio, no para usarlo: termina en N1 y en ningún otro nivel de la
suite.

### `src/heuristicas/registro.py`

**Qué hace:** h0 (constante 0) y h1 (cajas fuera de meta), más el registro
nombre → fábrica que usan `config.json` y `main.py`.

**Por qué existe:** son dos **instrumentos**, no dos intentos de resolver
rápido. h0 existe para el test de control del motor; h1, para que Greedy sea
ejecutable y para tener una línea de base contra la cual medir la escalera de la
Fase 4.

**La decisión importante:** cada heurística es una **fábrica**: `h1(problema)`
no es la heurística, **devuelve** la heurística, ya con lo que necesita del
nivel adentro. Parece un rodeo y es lo que hace posible la Fase 4: h₃ y h₄ van
a precalcular tablas de distancias reales de empuje, y esas tablas se calculan
una vez al construir, no una vez por cada uno de los millones de estados
evaluados. Se descartó que la heurística fuera un método del `Problema`: eso
obligaría a un `Problema` distinto por heurística, y entonces comparar dos
heurísticas dejaría de ser comparar dos funciones sobre el mismo problema.

### `verificaciones/admisibilidad.py`

**Qué hace:** `verificar_admisibilidad`, `verificar_consistencia`,
`verificar_heuristica` (las dos juntas) e `informatividad`. Funciones genéricas,
sin nada específico de h0 ni de h1.

**Por qué existe:** la Fase 4 tiene seis heurísticas y cada una necesita su
demostración de admisibilidad. La demostración se escribe a mano —son dos
renglones y van a la presentación— pero una demostración que nadie contrastó
contra el código es la demostración de la heurística que **creímos** escribir.
Esto contrasta la que escribimos de verdad. Está en `verificaciones/` y no en
`src/` porque no es parte del solver: es herramienta de verificación, y la Fase
4 la va a importar tal cual.

**La decisión importante:** verificar sobre **un camino óptimo completo** y no
sólo sobre el estado inicial. Ver la sección de cuentas: es lo que convierte una
comprobación en un estado en una comprobación en 307 estados, gratis.

### `verificaciones/verificar_fase2.py`

**Qué hace:** corre las seis configuraciones sobre los cinco niveles —más el
IDDFS puro en N1—, imprime una tabla por nivel, verifica las cinco
comprobaciones del criterio de aceptación más admisibilidad y consistencia, y
devuelve código de salida 1 si algo falla.

**Por qué existe:** es la evidencia reproducible de la fase y la fuente de la
tabla de nodos expandidos por BFS que la Fase 3 va a congelar.

**La segunda decisión importante:** **todos los métodos se cortan por límite de
nodos, nunca por reloj**, y el límite sale de `config.json`, así que es el mismo
para todos y es un dato versionado. Con timeout, dos corridas de IDDFS en N4
daban 3.453.866 y 1.798.624 nodos expandidos: la métrica central del TP dejaba
de ser reproducible por algo tan ajeno al algoritmo como qué más estaba
corriendo la máquina. Con límite de nodos dan 3.000.000 las dos.

**La decisión importante:** que los valores esperados —los diez números de oro—
estén escritos en el archivo y no se lean de la corrida. Es la misma decisión
que en la Fase 1: un verificador que imprime lo que le da no verifica nada.

### `main.py` y `config.json`

**Qué hacen:** resuelven un nivel con un método según un archivo de
configuración, e imprimen todo lo que pide el enunciado: éxito o fracaso, costo,
nodos expandidos, nodos en la frontera, la solución completa y el tiempo.

**Por qué existen:** el enunciado pide configuración **por archivo**, no
hardcodeada.

**La decisión importante:** los flags de línea de comandos existen y **pisan** al
archivo, pero son para probar rápido mientras se trabaja. Los experimentos que
van a la presentación se corren siempre desde un archivo, porque un archivo se
commitea y un comando tipeado a mano no. Si un número de la presentación no se
puede reproducir con un archivo de configuración del repositorio, ese número no
debería estar en la presentación. Además, una clave desconocida en el JSON
**aborta**: un `"heuristica": "h2"` mal tipeado daría una corrida perfectamente
exitosa que no es la que se pidió.

### `src/busqueda/__init__.py`, `src/heuristicas/__init__.py`

**Qué hacen:** marcan los paquetes y reexportan la interfaz pública, para que
`from src.busqueda import bfs, a_estrella` alcance.

**Por qué existen:** por lo mismo que en la Fase 1 — que todo corra con
`python -m` desde la raíz sin tocar `sys.path`.

## Archivos modificados

| Archivo | Qué cambió y por qué |
|---|---|
| — | Ninguno. Nada de la Fase 1 hizo falta tocar: el modelo quedó bien. |

## Cuentas que se hacen acá

### h1 — cantidad de cajas fuera de meta

- **Qué calcula:** cuenta cuántas cajas del estado no están sobre una celda
  meta. Un entero entre 0 y la cantidad de cajas. No mira distancias, ni al
  jugador, ni qué caja va a qué meta.
- **Fórmula:** `h1(s) = |cajas(s) \ metas|`.
- **Por qué es admisible:** cada caja fuera de meta necesita al menos un empuje
  para llegar a una, y cada empuje es un movimiento del jugador; como son cajas
  distintas, esos movimientos son distintos entre sí. Entonces
  `h1(n) ≤ empujes que faltan ≤ movimientos que faltan = h*(n)`.
- **Por qué es consistente:** un movimiento cambia la cuenta a lo sumo en 1
  —sólo se puede empujar una caja por vez—, así que `h1(n) − h1(n') ≤ 1 = c(n,n')`.
- **Qué se descartó:** contar metas vacías en lugar de cajas fuera de meta (da
  exactamente el mismo número, porque hay tantas cajas como metas; se eligió la
  versión con cajas porque es la que se generaliza a h₂, una distancia por
  caja); y multiplicarla por 2 "porque cada caja necesita al jugador al lado",
  que **no es admisible** y es justamente la hₙₐ deliberada de la Fase 4.

### La comprobación de admisibilidad sobre un camino óptimo

- **Qué calcula:** dado un camino óptimo `s0, s1, ..., sL`, verifica
  `h(si) ≤ L − i` para todo `i`.
- **Por qué es correcta:** si el camino completo es óptimo, el tramo de `si` a
  la meta también lo es, y por lo tanto el costo real restante desde `si` es
  **exactamente** `L − i`. (Si existiera un camino más corto de `si` a la meta,
  pegándolo al tramo `s0..si` daría una solución de menos de `L` movimientos, y
  `L` era el óptimo.) Entonces `h(si) ≤ L − i` es exactamente la definición de
  admisibilidad, evaluada en esos estados.
- **Por qué así:** verificar admisibilidad en general exigiría conocer el costo
  óptimo desde **cada** estado, o sea resolver el nivel una vez por estado.
  Sobre el camino óptimo el costo restante se conoce gratis. Son 307 estados
  verificados en N5 por el precio de una búsqueda que ya habíamos hecho.
- **Qué NO es:** una demostración. Es una condición **necesaria**: si falla, la
  heurística no es admisible, seguro; si pasa, sólo sabemos que no falla en los
  estados del camino óptimo. La demostración sigue siendo el argumento escrito.
  Esto es la red que atrapa el error de implementación —un signo cambiado, un
  factor de más— que el argumento no puede atrapar, porque el argumento habla de
  la heurística ideal y el código puede decir otra cosa.
- **La consistencia**, con costo unitario, se reduce a que `h` no baje más de 1
  en un movimiento: `h(si) − h(t) ≤ 1` para todo sucesor `t`.

### `informatividad` = h(s0) / óptimo

- **Qué calcula:** qué fracción del costo real captura la heurística en el
  estado inicial. 0 es h0, que no informa nada; 1 sería la heurística perfecta.
- **Por qué así:** es el eje horizontal del gráfico de dominancia empírica de la
  Fase 8, y lo que ordena la escalera de la Fase 4.
- **Qué se descartó:** el margen mínimo `min((L−i) − h(si))` sobre todo el
  camino, que es la medida intuitiva y **es inútil**: en la meta toda heurística
  admisible vale 0 y el costo restante es 0, así que ese mínimo da 0 siempre y
  no distingue una heurística de otra. Se probó, dio 0 en las diez
  combinaciones, y se reemplazó.

## Verificación

**Cómo se comprueba que está bien:**

```
python -m verificaciones.verificar_fase2
```

**Salida obtenida** (código de salida `0`; tarda unos tres minutos):

```
Verificación de la Fase 2 — motor genérico y los cinco métodos
Límite de nodos por corrida: 3.000.000 (config.json), el mismo para todos los métodos.
La columna memoria es frontera + visitados: la memoria real del método.

=== n1_micro.sok  (óptimo publicado: 8 mov / 5 empujes) ===
método       costo  empujes  expandidos  front.máx    memoria    tiempo  resultado
BFS              8        5          38         12         62    0.00 s  OK
A*(h0)           8        5          38         12         62    0.00 s  OK  ≡ BFS
A*(h1)           8        5          27         12         51    0.00 s  OK  28.9 % menos nodos que BFS
Greedy(h1)       8        5          27         12         51    0.00 s  OK  óptimo por casualidad, sin garantía
DFS              8        5          18          7         30    0.00 s  óptimo por topología del nivel (esperado, ver ESPERADO)
IDDFS            8        5          79          7         32    0.00 s  OK  frontera 1.7x menor, 2.1x más nodos, pero memoria TOTAL 0.52x la de BFS
  IDDFS, últimas iteraciones (límite: nodos expandidos) — 6: 15, 7: 20, 8: 15
IDDFS puro       8        5         137          8          8    0.00 s  OK  memoria 7.8x menor que BFS de verdad, pagando 3.6x más nodos
  admisibilidad y consistencia sobre el camino óptimo (9 estados):
    h0   admisible OK     consistente OK     h(s0)/óptimo = 0.000
    h1   admisible OK     consistente OK     h(s0)/óptimo = 0.125

=== n2_akk04.sok  (óptimo publicado: 45 mov / 18 empujes) ===
método       costo  empujes  expandidos  front.máx    memoria    tiempo  resultado
BFS             45       18      44.124      2.691     49.434    0.26 s  OK
A*(h0)          45       18      44.124      2.691     49.434    0.32 s  OK  ≡ BFS
A*(h1)          45       18      35.315      2.512     40.171    0.27 s  OK  20.0 % menos nodos que BFS
Greedy(h1)      45       18       3.397        264      3.879    0.02 s  OK  óptimo por casualidad, sin garantía
DFS            137       40      55.150        176     55.322    0.30 s  subóptimo (esperado), 3.0x el óptimo
IDDFS           45       18   1.261.013         49     43.180    8.03 s  OK  frontera 55x menor, 29x más nodos, pero memoria TOTAL 0.87x la de BFS
  IDDFS, últimas iteraciones (límite: nodos expandidos) — 43: 108.977, 44: 118.543, 45: 87.311
  admisibilidad y consistencia sobre el camino óptimo (46 estados):
    h0   admisible OK     consistente OK     h(s0)/óptimo = 0.000
    h1   admisible OK     consistente OK     h(s0)/óptimo = 0.089

=== n3_caminata.sok  (óptimo publicado: 104 mov / 22 empujes) ===
método       costo  empujes  expandidos  front.máx    memoria    tiempo  resultado
BFS            104       22       6.360        220      6.622    0.03 s  OK
A*(h0)         104       22       6.360        220      6.622    0.13 s  OK  ≡ BFS
A*(h1)         104       22       6.048        221      6.364    0.04 s  OK  4.9 % menos nodos que BFS
Greedy(h1)     116       22       4.685        213      4.835    0.03 s  subóptimo (esperado), 1.4x menos nodos que BFS
DFS            200       42       5.106        110      5.279    0.03 s  subóptimo (esperado), 1.9x el óptimo
IDDFS          104       22   1.005.854         53      6.466    5.99 s  OK  frontera 4.2x menor, 158x más nodos, pero memoria TOTAL 0.98x la de BFS
  IDDFS, últimas iteraciones (límite: nodos expandidos) — 102: 46.591, 103: 48.132, 104: 45.155
  admisibilidad y consistencia sobre el camino óptimo (105 estados):
    h0   admisible OK     consistente OK     h(s0)/óptimo = 0.000
    h1   admisible OK     consistente OK     h(s0)/óptimo = 0.019

=== n4_matching.sok  (óptimo publicado: 70 mov / 22 empujes) ===
método       costo  empujes  expandidos  front.máx    memoria    tiempo  resultado
BFS             70       22     654.260     21.345    671.278    5.23 s  OK
A*(h0)          70       22     654.260     21.345    671.278    8.07 s  OK  ≡ BFS
A*(h1)          70       22     621.068     21.829    640.478    7.97 s  OK  5.1 % menos nodos que BFS
Greedy(h1)      84       24      10.654      2.369     15.146    0.08 s  subóptimo (esperado), 61x menos nodos que BFS
DFS            366       50     539.404      1.964    539.793    3.17 s  subóptimo (esperado), 5.2x el óptimo
IDDFS            —        —   3.000.000         38    204.620   18.67 s  max_nodos (esperado en N4 y N5), 40 iteraciones
  IDDFS, últimas iteraciones (límite: nodos expandidos) — 37: 421.945, 38: 499.592, 39: 251.842
  admisibilidad y consistencia sobre el camino óptimo (71 estados):
    h0   admisible OK     consistente OK     h(s0)/óptimo = 0.000
    h1   admisible OK     consistente OK     h(s0)/óptimo = 0.057

=== n5_limite.sok  (óptimo publicado: 306 mov / 99 empujes) ===
método       costo  empujes  expandidos  front.máx    memoria    tiempo  resultado
BFS            306       99   2.028.239     20.365  2.028.699   12.54 s  OK
A*(h0)         306       99   2.028.239     20.365  2.028.699   19.30 s  OK  ≡ BFS
A*(h1)         306       99   2.027.443     20.742  2.028.117   20.14 s  OK  0.0 % menos nodos que BFS
Greedy(h1)     380      103   2.007.670     30.221  2.008.960   31.58 s  subóptimo (esperado), 1.0x menos nodos que BFS
DFS          6.992    1.289   1.935.958      3.824  1.942.647   18.95 s  subóptimo (esperado), 23x el óptimo
IDDFS            —        —   3.000.000         42     77.779   15.93 s  max_nodos (esperado en N4 y N5), 76 iteraciones
  IDDFS, últimas iteraciones (límite: nodos expandidos) — 73: 231.584, 74: 250.207, 75: 103.414
  admisibilidad y consistencia sobre el camino óptimo (307 estados):
    h0   admisible OK     consistente OK     h(s0)/óptimo = 0.000
    h1   admisible OK     consistente OK     h(s0)/óptimo = 0.013

=== Nodos expandidos por BFS — VALORES A CONGELAR EN LA FASE 3 ===
nivel             costo  empujes   expandidos    generados  front.máx   visitados     memoria
n1_micro.sok          8        5           38           94         12          50          62
n2_akk04.sok         45       18       44.124      112.849      2.691      46.779      49.434
n3_caminata.sok     104       22        6.360       15.594        220       6.491       6.622
n4_matching.sok      70       22      654.260    1.728.078     21.345     662.769     671.278
n5_limite.sok       306       99    2.028.239    5.010.835     20.365   2.028.469   2.028.699
Son métricas de NUESTRA implementación, no verdad externa: dependen del
orden de sucesores, del desempate de la frontera y de la política de
repetidos. Se congelan en la Fase 3 y si cambian hay que entender por qué.

5/5 niveles OK.
```

La Fase 1 se volvió a correr antes de empezar y sigue en verde:
`python -m verificaciones.verificar_fase1` devuelve 0.

## Números nuevos

### Los que se congelan en la Fase 3

| Nivel | Costo | Empujes | Expandidos | Generados | Front. máx | Visitados | Memoria |
|---|---|---|---|---|---|---|---|
| N1 | 8 | 5 | 38 | 94 | 12 | 50 | 62 |
| N2 | 45 | 18 | 44.124 | 112.849 | 2.691 | 46.779 | 49.434 |
| N3 | 104 | 22 | 6.360 | 15.594 | 220 | 6.491 | 6.622 |
| N4 | 70 | 22 | 654.260 | 1.728.078 | 21.345 | 662.769 | 671.278 |
| N5 | 306 | 99 | 2.028.239 | 5.010.835 | 20.365 | 2.028.469 | 2.028.699 |

**Memoria** es el pico de frontera + visitados, que es lo que hay que comparar
entre métodos. La frontera sola no alcanza: ver más abajo.

Costo y empujes son **verdad externa** y coinciden exactamente con los récords
publicados. Las otras columnas son métricas de nuestra implementación:
**no hay verdad externa contra la cual compararlas**, dependen del orden de
sucesores, del desempate de la frontera y de la política de repetidos. Se
congelan y, si cambian, hay que entender por qué antes de actualizar el valor
esperado.

Los valores de referencia de `docs/03_NUMEROS_DE_ORO.md` —41.440 en N2, 6.207 en
N3, 644.933 en N4, 2.027.982 en N5— fueron medidos con una implementación
equivalente pero no idéntica. Los nuestros quedan entre 0,01 % (N5) y 6,5 % (N2) por encima,
que es exactamente lo que el documento anticipa cuando dice que son orden de
magnitud esperado y no valor exacto a alcanzar.

### Cuánto informa h1

| Nivel | h1(inicial) | Óptimo | h(s0)/óptimo | Nodos que ahorra A\*(h1) sobre BFS |
|---|---|---|---|---|
| N1 | 1 | 8 | 0,125 | 28,9 % |
| N2 | 4 | 45 | 0,089 | 20,0 % |
| N3 | 2 | 104 | 0,019 | 4,9 % |
| N4 | 4 | 70 | 0,057 | 5,1 % |
| N5 | 4 | 306 | 0,013 | 0,0 % |

**Este es el número que justifica la Fase 4 entera.** h1 captura el 1,3 % del
costo real en N5 y ahorra 796 nodos sobre 2.028.239: A\*(h1) es BFS con un
sombrero. La correlación entre las dos últimas columnas es la que hay que
mostrar: cuanto más informa la heurística, menos nodos se expanden.

### Los métodos no óptimos

| Nivel | Óptimo | DFS | Greedy(h1) | Nodos DFS | Nodos Greedy |
|---|---|---|---|---|---|
| N1 | 8 | 8 | 8 | 18 | 27 |
| N2 | 45 | 137 | 45 | 55.150 | 3.397 |
| N3 | 104 | 200 | 116 | 5.106 | 4.685 |
| N4 | 70 | 366 | 84 | 539.404 | 10.654 |
| N5 | 306 | **6.992** | 380 | 1.935.958 | 2.007.670 |

**La afirmación precisa es "DFS no da ninguna garantía", no "DFS siempre es
peor".** En N1 devuelve el óptimo, y no por suerte: es un pasillo de 12 celdas
donde la topología deja un solo camino. Corriendo DFS con los 24 órdenes
posibles de `DIRECCIONES`, N1 da 8 en los 24. En N2 el rango de esos mismos 24
órdenes es 113–181 contra un óptimo de 45, y en N3 es 164–448 contra 104: ahí
no hay orden de sucesores que salve a DFS. En N5 devuelve una solución de 6.992
movimientos, 23 veces el óptimo, con 1.289 empujes contra 99.

Greedy tiene el mismo tipo de comportamiento: es óptimo por casualidad en N1 y
N2, subóptimo en N3, N4 y N5. Su valor está en otro lado — en N4 encuentra una
solución 20 % peor expandiendo **61 veces menos nodos** que BFS.

### La memoria de IDDFS: el resultado más interesante de la fase

**En Sokoban, IDDFS no compra lo que promete.** Esta sección arranca corrigiendo
un error que casi entra al resumen.

| Nivel | Front. máx BFS | Front. máx IDDFS | Memoria BFS | Memoria IDDFS | Memoria IDDFS / BFS | Nodos IDDFS / BFS |
|---|---|---|---|---|---|---|
| N1 | 12 | 7 | 62 | 32 | 0,52× | 2,1× |
| N2 | 2.691 | 49 | 49.434 | 43.180 | **0,87×** | 29× |
| N3 | 220 | 53 | 6.622 | 6.466 | **0,98×** | 158× |
| N4 | 21.345 | — | 671.278 | — | — | corta en 3.000.000 |
| N5 | 20.365 | — | 2.028.699 | — | — | corta en 3.000.000 |

Mirando **sólo la frontera**, IDDFS parece ahorrar 55 veces la memoria en N2.
Mirando la **memoria real** —frontera más estructura de visitados— ahorra un
13 %, y en N3 un 2 %. La frontera se achicó, pero la memoria se mudó al
diccionario de visitados: 43.159 entradas contra las 46.779 de BFS.

**La explicación, que es lo que hay que decir en el oral:** el IDDFS de manual
tiene memoria lineal en la profundidad porque **no guarda visitados**. En
Sokoban eso es impracticable, por dos razones que se suman: las soluciones son
profundas (306 movimientos en N5) y el espacio está lleno de **transposiciones**
—el jugador puede dar vueltas sin empujar nada, así que al mismo estado se llega
por muchísimos caminos distintos—. Sin tabla de transposiciones, cada estado se
vuelve a expandir una vez por cada camino que lleva a él. Entonces le agregamos
detección de repetidos, y **al hacerlo perdimos exactamente la ventaja que
justificaba usar el método**. Queda pagando el trabajo repetido —158 veces más
nodos que BFS en N3— sin cobrar el ahorro de memoria.

Para cuantificar el otro lado del intercambio corrimos la versión **pura**, sin
visitados, en N1, que es el único nivel de la suite donde termina:

| Método en N1 | Nodos expandidos | Memoria máxima |
|---|---|---|
| BFS | 38 | 62 |
| IDDFS con visitados | 79 | 32 |
| **IDDFS puro** (sin visitados) | **137** | **8** |

Ahí sí se ve el compromiso del libro: 7,8 veces menos memoria que BFS, pagando
3,6 veces más nodos. **En los otros cuatro niveles no termina**, y eso también
es el resultado: en un nivel de 12 celdas el intercambio es favorable, y en
cuanto el espacio crece deja de serlo.

La conclusión para la presentación es una sola frase: *en Sokoban, IDDFS es
óptimo como BFS, expande entre 2 y 158 veces más nodos, y no ahorra memoria*.

## Preguntas que esta fase habilita en el oral

- **¿Por qué A\*(h0) tiene que dar igual que BFS?** Con `h = 0`, `f = g`, así que
  A\* degenera en búsqueda de costo uniforme; y con costo unitario, costo
  uniforme es BFS. Si difieren, el bug está en el motor —orden de la frontera,
  control de repetidos o momento del test de meta— y no en ninguna heurística.
  Es el primer test que corremos cuando algo no cierra.
- **¿Por qué chequean la meta al sacar y no al generar?** Porque un nodo meta
  generado temprano puede no ser el más barato: puede haber en la frontera otro
  camino a la meta con menor `f` sin extraer. Con BFS daría lo mismo, pero
  mantenemos un criterio único para los cinco métodos, si no la comparación de
  nodos expandidos no sería homogénea.
- **¿Por qué A\* necesita reabrir estados si sus heurísticas son consistentes?**
  Porque el motor no puede asumir que lo sean. Con una heurística admisible pero
  no consistente, un estado puede expandirse antes de haber encontrado su camino
  óptimo y se perdería la optimalidad. En la Fase 4 tenemos una heurística no
  admisible a propósito, así que la política tiene que aguantar ese caso.
- **¿Por qué IDDFS usa `mejor_g` si no es A\*?** Por un motivo distinto: un
  estado cerrado a profundidad 20 puede ser alcanzable a profundidad 12 por otra
  rama. Cerrarlo definitivamente haría perder soluciones que sí entran en el
  límite. Es un error clásico y sin `mejor_g` IDDFS dejaría de ser óptimo.
- **¿Por qué reportan tres números de memoria?** Porque miden cosas distintas y
  confundirlas lleva a una conclusión falsa. Lo que quedó en la frontera al
  terminar no dice nada del consumo; el pico de la frontera dice sólo la mitad;
  la memoria del método es frontera **más** estructura de visitados. En N2, la
  frontera de IDDFS es 55 veces más chica que la de BFS, y su memoria total es
  0,87 veces la de BFS. La primera cifra sola diría que IDDFS ahorra muchísima
  memoria, y es mentira.
- **Entonces, ¿para qué sirve IDDFS en este TP?** Como resultado negativo, y
  está bien que así sea. Es óptimo como BFS y expande entre 2 y 158 veces más
  nodos sin ahorrar memoria, porque le tuvimos que agregar detección de
  repetidos: sin ella, las transposiciones de Sokoban lo hacen impracticable.
  Lo medimos: la versión pura usa 7,8 veces menos memoria que BFS en N1, y no
  termina en ninguno de los otros cuatro niveles.
- **El contador de inserción de la cola de prioridad, ¿es parte del
  algoritmo?** No. Es reproducibilidad. Sin él `heapq` intentaría comparar nodos
  entre sí —`TypeError`— y el orden de exploración podría cambiar entre
  corridas, con lo cual los nodos expandidos dejarían de ser reproducibles.
- **¿DFS siempre es peor que BFS?** No: DFS **no da ninguna garantía**, que no
  es lo mismo. En N1 da el óptimo porque el nivel es un pasillo, y lo verificamos
  con los 24 órdenes posibles de sucesores. En N5 da 6.992 movimientos contra
  306. Lo que sí es cierto siempre es que su costo nunca puede ser menor al
  óptimo: si lo fuera, habría un bug.
- **Greedy dio el óptimo en dos niveles, ¿entonces es óptimo?** No, fue
  casualidad. Greedy prioriza sólo por `h` e ignora lo que ya costó llegar: nada
  le impide meterse por un camino largo. En N4 y N5 devuelve 84 y 380 contra 70
  y 306. Lo que sí compra es velocidad: en N4, 61 veces menos nodos.
- **¿Por qué A\*(h1) apenas mejora a BFS?** Porque h1 casi no informa: en N5 vale
  4 cuando faltan 306 movimientos, o sea el 1,3 % del costo real. Una heurística
  admisible pero floja hace que `f ≈ g` y A\* se comporta como costo uniforme.
  Eso es exactamente lo que arregla la escalera de la Fase 4.
- **¿Cómo saben que h1 es admisible, más allá de la demostración?** La
  verificamos sobre los caminos óptimos completos de los cinco niveles: en un
  camino óptimo el costo real restante desde el estado `i` es exactamente
  `L − i`, así que comprobamos `h(si) ≤ L − i` en los 307 estados de N5, no sólo
  en el inicial. Es condición necesaria, no demostración: la demostración es el
  argumento de los dos renglones.
- **¿Por qué un solo bucle para los cinco métodos?** Para que la comparación sea
  justa por construcción. Los cinco comparten el código de expansión, el control
  de repetidos y los contadores; la única diferencia es qué nodo sale de la
  frontera. Con cinco bucles separados, cualquier diferencia medida entre dos
  métodos podría ser una diferencia de implementación.

## Qué quedó pendiente

- **Fase 3:** los tests de `pytest` y el congelamiento de la tabla de BFS.
- **Fase 4:** la escalera h₂ a h₅ y la hₙₐ no admisible. `registro.py` está
  preparado para recibirlas y `verificaciones/admisibilidad.py` para
  verificarlas.
- **Fase 5:** deadlocks. El gancho sigue sin usarse; el motor no lo toca.
- **Fase 6:** el runner de la matriz completa y el CSV. `resolver()` y el
  registro de métodos son la puerta de entrada que va a usar.
- **Fase 7:** el reproductor estado por estado. `main.py` imprime la secuencia
  de movimientos, no los tableros.
- **Fase 8:** el barrido de `w`. `hpa()` ya existe y funciona; falta el
  experimento.

## Ideas para más adelante

- El barrido de `w` de la Fase 8 se puede correr hoy mismo: `hpa` está
  implementado y probado por construcción, sólo falta el experimento y el
  gráfico.
- **Regla metodológica para las Fases 6 y 8: se compara por NODOS EXPANDIDOS,
  no por tiempo.** Los nodos expandidos son determinísticos: dos corridas del
  mismo experimento dan exactamente el mismo número. El tiempo no: BFS en N5 dio
  13,4 s en una corrida y 46,6 s en otra **con los mismos 2.028.239 nodos**,
  simplemente porque la máquina estaba ocupada. Los tiempos sólo valen dentro de
  una misma sesión en una misma máquina, y **nunca entre las máquinas de los
  cuatro**: si cada uno mide en su computadora, esos números no se pueden poner
  en la misma tabla. Cuando el tiempo se reporte igual —el enunciado lo pide—
  va con 10 repeticiones, media y desvío, y aclarando en qué máquina se midió.
- Por lo mismo, **todo corte es por límite de nodos y nunca por reloj**. Con
  timeout, dos corridas de IDDFS en N4 daban 3.453.866 y 1.798.624 nodos
  expandidos; con límite de nodos dan 3.000.000 las dos, con las mismas 40
  iteraciones. El límite vive en `config.json` y es el mismo para todos los
  métodos, así que ni siquiera depende de qué script lo corra.
- `podados_por_limite` habilita un DFS con límite que reporte honestamente "no
  hay solución dentro del límite" en vez de "no hay solución". Puede ser útil
  para el análisis de la Fase 8.
