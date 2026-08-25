# FASE 5 — Deadlocks

**Estado:** terminada · **Fecha:** 2026-08-23

## En una frase

La búsqueda descarta los estados que ya no admiten solución antes de crearlos:
el costo y hasta la secuencia de movimientos son idénticos con y sin poda en los
cinco niveles, y BFS pasa de 654.260 a 60.410 nodos en N4 y de 2.028.239 a
429.817 en N5.

## La idea que organiza la fase

**Los dos errores posibles de un detector no cuestan lo mismo.**

- Un **falso negativo** —no ver un deadlock que existe— cuesta nodos. Nada más.
- Un **falso positivo** —declarar muerto un estado que sí tenía solución— rompe
  la optimalidad, y en el peor caso hace que un nivel resoluble devuelva "sin
  solución".

De esa asimetría sale todo lo demás: ante la duda, no se poda. Una regla que
poda de menos es una regla floja; una que poda de más es un bug difícil de ver,
porque el programa termina igual y devuelve un número que parece razonable.

Y hay un ejemplo medido, no hipotético: quitándole a la regla de 2x2 una sola
cláusula, BFS declara **irresoluble** a `n4_matching`. Está en "Números nuevos".

| | Capa | Qué detecta | Qué necesita saber |
|---|---|---|---|
| 1 | `estaticos` | una caja en una celda desde la que no se llega a ninguna meta | sólo la geometría del nivel |
| 2 | `congelados` | un cuadrado de 2x2 lleno con alguna caja fuera de meta | dónde están **las otras** cajas |
| — | `completo` | las dos | |

## Archivos creados

### `src/deadlocks.py`

**Qué hace:** las dos reglas de detección y el registro de nombres que usa
`config.json`. Cada detector es una fábrica que recibe el `Tablero`, precalcula
lo que necesita y devuelve la función `(cajas, caja_movida) -> bool` que el motor
consulta después de cada empuje.

**Por qué existe:** hasta la Fase 4 la búsqueda exploraba estados irrecuperables
igual que cualquier otro. En N4 son la enorme mayoría: sacarlos baja los nodos de
BFS diez veces. El gancho para hacerlo estaba escrito desde la Fase 1 y no lo
usaba nadie; esta fase lo llena, sin tocar ni `src/modelo/` ni `src/busqueda/`.

**La decisión importante:** **son tres detectores y no uno**, porque **las dos
reglas no se dominan entre sí**. En `n2_akk04` la regla de 2x2 deja BFS en 9.839
nodos y la estática en 14.178; en `n4_matching` es al revés, 214.466 contra
73.813. Con una sola columna "con poda" no se podría responder cuál de las dos
hizo el trabajo, que es la pregunta que sigue naturalmente en el oral. Es el
mismo criterio con el que la Fase 4 armó una escalera de heurísticas en vez de
entregar la mejor sola.

Tres decisiones más chicas que conviene conocer:

- **`'ninguno'` devuelve `None`**, no una función que siempre dice que no.
  `sucesores()` pregunta `if detectar is not None` una vez por empuje: con `None`
  esa rama ni se toca y, sobre todo, **la corrida sin poda es exactamente la
  misma corrida de las Fases 2 a 4**, no una equivalente. Los números congelados
  no tienen forma de moverse.
- **La fábrica recibe el `Tablero` y no el `Problema`**, que es la única
  asimetría con las heurísticas. Porque un deadlock es geometría del nivel y no
  depende del estado inicial, y porque el `Problema` se construye *con* el
  detector adentro: pedirle el problema a la fábrica sería un huevo-y-gallina.
- **`completo` se compone llamando a las otras dos fábricas** en vez de repetir
  las cuentas, por el mismo motivo por el que h₅ reutiliza h₄: que el código diga
  literalmente "es una regla más la otra" es parte de lo que se defiende, y si
  una cambia, la otra cambia con ella.

### `verificaciones/verificar_fase5.py`

**Qué hace:** corre las cinco comprobaciones del criterio de aceptación sobre los
cinco niveles —60 corridas: 5 niveles × 3 métodos × 4 capas— e imprime una tabla
por nivel más las tablas resumen.

**Por qué existe:** los números de la presentación tienen que salir de un comando
que cualquiera del grupo pueda correr. Y hay uno que no se puede comprobar de
otra manera: que ninguna capa pode un estado del camino óptimo. Sin eso, "la poda
anda" sería "los cinco niveles siguen dando el mismo costo", que es cierto y no
alcanza, porque un detector podría estar podando estados con solución en ramas
que ningún nivel de la suite recorre.

**La decisión importante:** la comprobación 1 —el camino óptimo— **es una falla,
no una advertencia**. Es al revés que en la Fase 4, donde la dominancia en nodos
se reportaba sin hacer fallar la verificación. El motivo es la asimetría: en la
Fase 4 lo que se medía era cuánto ahorra una heurística, y un ahorro menor al
esperado es un resultado; acá lo que se mide es si el detector miente, y un
detector que miente no es un resultado, es un bug.

### `tests/test_deadlocks.py`

**Qué hace:** 17 funciones de test que, parametrizadas por nivel y por capa, dan
99 casos. Se dividen en tres grupos: que ninguna capa pode un estado con
solución, que la poda efectivamente ahorre nodos, y las dos reglas sobre dos
tableros diminutos construidos como texto dentro del test.

**Por qué existe:** la verificación se corre a mano y tarda minutos; la suite se
corre a cada rato. Y hay cosas que sólo se pueden testear con tableros armados a
propósito, porque los cinco niveles reales no tienen la forma necesaria: un
cuadrado de 2x2 con las cuatro cajas sobre metas, o dos cajas contra una pared
que son inofensivas por separado.

**La decisión importante:** los tableros de prueba se escriben **como texto XSB
dentro del archivo de tests**, nunca como archivos en `niveles/`, y las
configuraciones de cajas con las que se interroga al detector **no tienen por qué
ser alcanzables ni coincidir en cantidad con las del nivel**. Un detector es una
función de la geometría y de un conjunto de cajas, y se lo testea como tal. Meter
esos tableros en `niveles/` sería contaminar la suite de experimentos con
material de laboratorio.

## Archivos modificados

| Archivo | Qué cambió y por qué |
|---|---|
| `main.py` | Clave nueva `"deadlocks"` en `CLAVES` y `VALORES_POR_DEFECTO`, flag `--deadlocks`, y el `Problema` se construye con el detector. El principio está escrito en su propio docstring: si un número de la presentación no se puede reproducir con un archivo de configuración del repositorio, ese número no debería estar en la presentación. Esta fase produce una tabla de números y habría sido la primera en no poder cumplirlo. |
| `config.json` | `"deadlocks": "ninguno"`. El valor por defecto es sin poda a propósito: una configuración ya escrita tiene que seguir significando lo mismo que significaba. |
| `tests/conftest.py` | `cargar_problema()` y `correr()` aceptan qué capa usar, con `'ninguno'` por defecto para que ningún test de las Fases 2 a 4 cambie de significado; clave `deadlocks` en `ESPERADO` con los números congelados de esta fase; y `DETECTORES_A_VERIFICAR`, que es lo que mira el guardián del registro. |
| `docs/fases/FASE_5_DEADLOCKS.md` | Dos correcciones al texto original, para que la especificación no contradiga al código: la fábrica recibe el `Tablero` y no el `Problema` —el porqué está en la decisión de `src/deadlocks.py`, acá arriba— y la salida reporta rincones en vez de cuadrados vivos, porque contar cuadrados vivos da prácticamente el total de celdas transitables y no informa nada. Y el estado pasa a "terminada". |

Ningún archivo de `niveles/`, ningún número congelado de las Fases 2, 3 y 4, y
**ni una línea de `src/modelo/` ni de `src/busqueda/`**.

## Cuentas que se hacen acá

Antes de las dos reglas, el argumento del que dependen las dos.

### Por qué podar no rompe la optimalidad

- **Qué dice:** si un estado `s` no admite ninguna solución, sacarlo del grafo no
  cambia el costo óptimo.
- **Por qué es correcto:** si `s` no admite solución, ningún camino de la raíz a
  una meta pasa por `s`. Sacarlo no saca ninguna solución, así que el conjunto de
  soluciones queda idéntico, y el mínimo sobre un conjunto idéntico es el mismo
  número. Vale para BFS y para A\*.
- **Lo que hay que notar:** el argumento **no dice nada sobre el detector**. Toda
  la carga está en la hipótesis "`s` no admite ninguna solución". Por eso cada
  regla necesita su propia demostración de que marca únicamente estados sin
  solución, igual que cada heurística de la Fase 4 necesita la suya de
  admisibilidad. Lo que se defiende en el oral no es la poda: son las dos reglas.

### Regla 1 — celdas muertas (deadlock estático)

- **Qué calcula:** si la caja recién empujada quedó en una celda desde la que
  ninguna meta es alcanzable a empujones.
- **Fórmula:** `deadlock(cajas, caja_movida) ⟺ caja_movida ∈ celdas_muertas`,
  donde `celdas_muertas` son las celdas transitables que no aparecen en ninguna
  de las tablas de `distancias_de_empuje`. Es el mismo BFS de tirones que arma la
  matriz de costos de h₄, sin una línea de código nueva.
- **Por qué es correcta:** ese BFS construye el grafo de **todos** los empujes
  geométricamente posibles, ignorando las demás cajas y si el jugador puede
  llegar: es **más permisivo** que el juego real. Si en ese grafo permisivo no hay
  camino de la celda a ninguna meta, en el juego real tampoco lo hay. Una caja ahí
  no llega nunca a una meta, y sin todas las cajas en metas no hay solución.
- **Qué se descartó:** copiar el BFS de tirones dentro de `deadlocks.py` para no
  importar de `heuristicas/`. Serían dos implementaciones de la misma cuenta, y
  el día que una cambie la otra queda vieja en silencio. También se descartó
  mover `distancias.py` a `src/modelo/` para que el import se leyera mejor:
  obliga a tocar cuatro archivos estables de la Fase 4 a cambio de una línea más
  linda.

### Regla 2 — bloques de 2x2 congelados (deadlock dinámico)

- **Qué calcula:** si alguno de los cuatro cuadrados de 2x2 que contienen a la
  caja recién empujada quedó completamente ocupado por paredes y cajas, con al
  menos una de esas cajas fuera de meta.
- **Fórmula:** para cada celda `p` se precalcula la lista de cuadrados que la
  contienen, cada uno reducido a **las celdas de piso que falta ocupar** —las
  paredes ya están ocupadas y no hay nada que preguntarles—. Durante la búsqueda:
  `deadlock ⟺ ∃ cuadrado : requisitos(cuadrado) ⊆ cajas`.
- **Por qué es correcta:** tomemos una caja de un cuadrado de 2x2 lleno. Su
  vecina horizontal dentro del cuadrado está ocupada y su vecina vertical
  también. Para empujarla a la derecha hace falta que la celda de la derecha esté
  libre; para empujarla a la izquierda, que el jugador quepa a su derecha. Las dos
  cosas piden la misma celda, y esa celda está ocupada: **no se mueve en
  horizontal**. El mismo argumento en vertical, y por simetría vale para las
  cuatro celdas del cuadrado. Ninguna de esas cajas se mueve nunca más, así que si
  alguna no está sobre una meta, el nivel no se puede completar. Las paredes y el
  borde del rectángulo cuentan como ocupados porque son inmóviles y el jugador no
  puede pararse ahí.
- **La cláusula que no se puede olvidar:** "al menos una fuera de meta". Un
  cuadrado lleno con todas sus cajas sobre metas es el nivel resuelto: las cajas
  no se mueven más y no hace falta que se muevan. Sin esa cláusula el detector
  poda el estado meta de `n4_matching`, cuyas cuatro metas forman un bloque de
  2x2. Medido: se podan 4 de los 71 estados del camino óptimo y BFS termina con
  `motivo_fin = 'sin_solucion'`.
- **Por qué alcanza con revisar la caja recién empujada:** si después del empuje
  hay un cuadrado lleno que no la contiene, ese cuadrado ya estaba lleno antes
  —las otras cajas y las paredes no se movieron— y se detectó en el empuje
  anterior. La excepción es el estado inicial, que nunca pasa por un empuje y por
  lo tanto nunca se consulta; no ocurre en los cinco niveles y BFS lo prueba,
  porque encuentra el óptimo publicado en todos.
- **Qué se descartó:** (1) el **congelamiento recursivo**, la regla general que
  marca una caja como inmóvil si sus dos ejes están bloqueados por paredes o por
  cajas que a su vez estén congeladas. Poda bastante más y su demostración de que
  no tiene falsos positivos es recursiva y mucho más difícil de defender en un
  oral de 25 minutos. (2) Preguntar en cada empuje si todas las cajas del cuadrado
  están sobre metas: es decidible **al construir**, porque si todas las celdas de
  piso de un cuadrado son metas ese cuadrado nunca puede ser deadlock, y se
  descarta una vez por nivel en vez de una vez por empuje.

### Lo que NO se hizo, y es una decisión

No hay contador de cuántos estados podó cada capa. La diferencia en
`nodos_generados` entre dos corridas ya muestra el efecto, y un contador obligaría
a que el detector tuviera estado y a resetearlo entre corridas: exactamente lo que
hace que dos comparaciones dejen de ser independientes.

## Verificación

**Cómo se comprueba que está bien:**

```
python3 -m verificaciones.verificar_fase5
python3 -m pytest -q
python3 -m verificaciones.verificar_fase2
python3 -m verificaciones.verificar_fase4
```

**Salida obtenida** (`verificar_fase5`, el nivel del criterio y el cierre):

```
=== n4_matching.sok  (óptimo publicado: 70 mov / 22 empujes) ===
  celdas muertas: 12 de 31 transitables   ·   rincones: 6, de los cuales 0 no son celda muerta
  el camino óptimo (71 estados, 22 empujes) sobrevive a las tres capas   OK
  método   poda          costo  empujes   expandidos    generados     memoria  vs sin poda
  BFS      ninguno          70       22      654.260    1.728.078     671.278        1,00x
  BFS      estaticos        70       22       73.813      190.358      75.941        8,86x
  BFS      congelados       70       22      214.466      555.854     221.110        3,05x
  BFS      completo         70       22       60.410      155.205      62.306       10,83x
  A*(h4)   ninguno          70       22       54.754      144.304      63.669        1,00x
  A*(h4)   estaticos        70       22       54.754      141.282      57.625        1,00x
  A*(h4)   congelados       70       22       45.278      118.161      51.137        1,21x
  A*(h4)   completo         70       22       45.278      116.432      47.679        1,21x
  A*(h5)   ninguno          70       22       52.766      139.178      63.010        1,00x
  A*(h5)   estaticos        70       22       52.766      136.156      56.966        1,00x
  A*(h5)   congelados       70       22       43.628      113.919      50.579        1,21x
  A*(h5)   completo         70       22       43.628      112.190      47.121        1,21x

=== Cuál de las dos reglas poda más, por nivel (BFS) ===
  n1_micro      empatan en 35
  n2_akk04      congelados (9.839 contra 14.178)
  n3_caminata   estaticos (2.002 contra 2.944)
  n4_matching   estaticos (73.813 contra 214.466)
  n5_limite     congelados (508.669 contra 608.999)

5/5 niveles OK. Las 5 comprobaciones pasan.
```

`pytest -q` da **385 passed en 61,81 s**, contra 286 antes de la fase; la suite
rápida, `pytest -q -m "not lento"`, da **244 passed, 141 deselected en 1,40 s**.
`verificar_fase2` y `verificar_fase4` devuelven exactamente los mismos números que
antes: ni uno se movió.

## Números nuevos

### Nodos expandidos por capa, método y nivel

```
BFS
  poda              n1_micro      n2_akk04   n3_caminata   n4_matching     n5_limite
  ninguno                 38        44.124         6.360       654.260     2.028.239
  estaticos               35        14.178         2.002        73.813       608.999
  congelados              35         9.839         2.944       214.466       508.669
  completo                35         9.839         1.816        60.410       429.817

A*(h4)
  ninguno                 12         7.145         1.951        54.754       605.520
  estaticos               12         7.145         1.951        54.754       605.520
  congelados              12         5.228         1.765        45.278       427.520
  completo                12         5.228         1.765        45.278       427.520

A*(h5)
  ninguno                  8         6.100         1.888        52.766       604.472
  estaticos                8         6.100         1.888        52.766       604.472
  congelados               8         4.460         1.702        43.628       426.808
  completo                 8         4.460         1.702        43.628       426.808
```

Se congelan en `tests/conftest.py`, bajo la clave `deadlocks`, las cinco columnas
de BFS con poda `completo` y los nodos expandidos de las dos capas sueltas.
`'ninguno'` no se repite porque ya está en la clave `bfs` desde la Fase 3: un
número escrito dos veces es un número que alguien va a actualizar en un solo
lugar.

**Acumulado desde el principio del proyecto:** N4 pasa de 654.260 nodos con BFS a
43.628 con A\*(h₅) y poda completa, **15,0x**; N5 pasa de 2.028.239 a 426.808,
**4,75x**.

### El resultado que había que predecir antes de medirlo

La especificación de la fase dejó escrita esta predicción antes de correr nada:
que la poda estática ayudaría mucho a BFS y **poco a A\***, porque h₄ vale
`INALCANZABLE` (10⁶) en todo estado con una caja en celda muerta y ya los mandaba
al fondo de la frontera.

Salió más fuerte de lo previsto: la capa estática cambia **exactamente cero**
nodos expandidos de A\*(h₄) y A\*(h₅) **en los cinco niveles**. Lo único que
ahorra ahí son nodos generados y memoria, porque el estado no llega a construirse
(N5: 1.509.788 → 1.498.369 generados y 629.298 → 606.460 de memoria).

Lo que sí le dice algo nuevo a A\* es la regla de 2x2: 1,42x en N5 y 1,21x en N4.
Y tiene sentido, porque es la única de las dos que mira dónde están las **otras**
cajas, que es información que ninguna heurística de la escalera usa.

### Las dos reglas no se dominan, y los rincones sí

| nivel | rincones | celdas muertas | rincones que **no** son celda muerta |
|---|---|---|---|
| n1_micro | 3 | 5 | 0 |
| n2_akk04 | 9 | 13 | 0 |
| n3_caminata | 9 | 23 | 0 |
| n4_matching | 6 | 12 | 0 |
| n5_limite | 12 | 13 | 0 |

Un **rincón** es una celda que la regla de 2x2 declara deadlock con una sola caja,
sin mirar dónde están las demás. En los cinco niveles, **todos los rincones son
además celdas muertas**: la parte de la regla dinámica que funciona con una caja
sola está contenida en la estática. Es la medición que justifica llamarla
"dinámica" — todo lo que aporta de verdad depende de las otras cajas — y explica
por qué `completo` iguala a `congelados` en los nodos expandidos de A\*.

### El contraejemplo de la cláusula

Quitándole a la regla de 2x2 la condición "al menos una caja fuera de meta", sobre
`n4_matching`:

- se podan los estados **26, 59, 61 y 70** del camino óptimo, que tiene 71;
- BFS termina con `motivo_fin = 'sin_solucion'`.

Un falso positivo no devuelve un número peor: **declara irresoluble un nivel que
tiene solución**. Es el mejor material de la fase para la presentación.

## Preguntas que esta fase habilita en el oral

- **¿Cómo saben que la poda no les rompe la optimalidad?** Porque un estado sin
  solución no está en ningún camino a la meta, así que sacarlo deja el conjunto de
  soluciones idéntico. Lo que hay que demostrar no es eso, es que cada regla marca
  únicamente estados sin solución, y cada una tiene su argumento escrito.
- **¿Y cómo comprueban que ninguna regla se pasa?** Con el camino óptimo que ya
  encontró BFS: todos sus estados tienen solución por definición, así que si una
  capa marcara uno, sería un falso positivo seguro. Es el mismo truco con el que
  la Fase 3 verifica admisibilidad, y es una condición necesaria, no una
  demostración.
- **¿Por qué la regla de 2x2 pregunta si alguna caja está fuera de meta?** Porque
  un cuadrado lleno con todas las cajas sobre metas es el nivel terminado. Sin esa
  cláusula el detector poda el estado meta de N4, cuyas cuatro metas son un bloque
  de 2x2, y BFS declara el nivel irresoluble. Lo medimos.
- **¿Para qué podar, si h₄ ya manda esos estados al fondo de la frontera?** Para
  BFS es enorme: 10,8x en N4. Para A\* la capa estática no cambia ni un nodo
  expandido —eso está medido en los cinco niveles— y lo que sirve es la regla de
  2x2, que mira dónde están las otras cajas, que es algo que ninguna heurística de
  la escalera usa.
- **¿Por qué tienen tres detectores y no uno?** Porque las dos reglas no se
  dominan: en N2 gana la de 2x2 y en N4 gana la estática, por un factor 3. Con una
  sola columna "con poda" no podríamos decir cuál de las dos hizo el trabajo.
- **¿Por qué no implementaron el congelamiento recursivo, que poda más?** Porque
  su demostración de que no tiene falsos positivos es recursiva y bastante más
  difícil de defender, y en este proyecto una cuenta que no se puede explicar en
  el oral no sirve. Está anotado como alternativa evaluada.
- **¿Por qué el detector recibe la caja recién empujada y no sólo el conjunto?**
  Porque todo cuadrado que se llene ahora tiene que incluirla: los demás ya
  estaban llenos antes y se detectaron entonces. Con 4 cajas, eso es un factor 4
  de trabajo ahorrado por empuje y cuesta un parámetro.

## Qué quedó pendiente

- **La matriz completa de experimentos y el CSV — Fase 6.** Acá se midieron tres
  métodos; DFS, Greedy e IDDFS con poda quedan para allá. Vale la pena adelantar
  por qué: **en DFS la poda sí cambia el costo**, porque DFS no es óptimo y con
  menos ramas encuentra otra solución. No contradice el criterio de esta fase,
  que es una afirmación sobre los métodos óptimos.
- **La clave `"deadlocks"` del runner — Fase 6.** Ya existe en `config.json` y en
  `main.py`; el runner sólo tiene que recorrerla como una dimensión más de la
  matriz.
- **El nivel de 5 cajas descartado — Fase 8.** Con poda completa quizás entre en
  el límite de nodos. Si entrara, la figura del muro cambia de "no llegamos" a
  "llegamos gracias a la poda", que es una historia mejor.

## Ideas para más adelante

- El **congelamiento recursivo** como cuarta capa, medida contra `completo`. Si
  el ahorro fuera grande, valdría la pena pagar el costo de explicarlo; si fuera
  chico, el resultado en sí es una buena diapositiva: la regla más sofisticada no
  siempre compra lo que promete.
- Los **deadlocks de corral** (una región cerrada donde el jugador no puede entrar
  y hay una caja adentro sin meta). Es la familia que más poda en los solvers
  serios y la que peor escala en costo por nodo.
- La poda actual **no revisa el estado inicial**, porque el gancho se consulta
  sólo después de un empuje. Si alguna vez se agrega un nivel al repositorio,
  conviene pasarle el detector a mano una vez antes de buscar: es gratis y
  distingue "no hay solución" de "el nivel está mal transcripto".
