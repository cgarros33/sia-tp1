# FASE 5 — Deadlocks

**Dueño:** Celestino · **Estado:** terminada

Podar los estados que ya no admiten solución. Al terminar, la búsqueda descarta
esos estados antes de crearlos, el costo de las soluciones no cambia en ningún
nivel, y está medido cuánto ahorra cada una de las dos reglas de detección.

---

## La asimetría que organiza toda la fase

Un detector de deadlocks se puede equivocar de dos maneras, y **no cuestan lo
mismo**:

- **Falso negativo** — no ve un deadlock que existe. Cuesta nodos. Nada más.
- **Falso positivo** — declara muerto un estado que sí tenía solución. **Rompe la
  optimalidad**, y en el peor caso hace que un nivel resoluble devuelva "sin
  solución".

Todas las decisiones de esta fase salen de ahí: **ante la duda, no podar**. Una
regla que poda de menos es una regla floja; una regla que poda de más es un bug
difícil de ver, porque el programa termina igual y devuelve un número que parece
razonable.

## Por qué podar no rompe la optimalidad

Si un estado `s` no admite ninguna solución, entonces ningún camino de la raíz a
una meta pasa por `s`. Sacarlo del grafo no saca ninguna solución: el conjunto de
soluciones queda idéntico, y el mínimo sobre un conjunto idéntico es el mismo
número. BFS sigue devolviendo el óptimo y A\* también.

Fijate que la demostración **no dice nada sobre el detector**: toda la carga está
en la hipótesis "`s` no admite ninguna solución". Lo que hay que defender en el
oral no es la poda, es que **cada regla marca únicamente estados sin solución**.
Por eso cada regla lleva su propio argumento escrito, igual que cada heurística
de la Fase 4 lleva su demostración de admisibilidad.

### La contracara empírica, que sale gratis

Igual que en la Fase 3 con la admisibilidad: el camino óptimo que ya encontró BFS
da una comprobación regalada. **Todos los estados de un camino óptimo tienen
solución**, por definición. Entonces:

> Si alguna capa de poda marca un estado del camino óptimo, esa capa tiene un
> falso positivo, seguro.

Es una condición necesaria, no una demostración —igual que la verificación de
admisibilidad—, y cuesta una búsqueda que igual había que hacer. Es la
comprobación 1 del criterio de aceptación.

---

## Archivos a crear

```
src/deadlocks.py
verificaciones/verificar_fase5.py
tests/test_deadlocks.py
```

Y modificar `main.py`, `config.json` y `tests/conftest.py`.

**`src/modelo/` y `src/busqueda/` no se tocan.** El gancho está desde la Fase 1 y
el motor ni se entera de que existe la poda: `sucesores()` ya consulta al
detector después de cada empuje y `reconstruir_estados()` ya lo saltea. Si en el
medio de la implementación parece que hay que tocarlos, entonces algo del gancho
estaba mal pensado: **decilo antes de tocar** (regla 9).

---

## El diseño: tres detectores, no uno

Un detector es una **fábrica**, igual que una heurística: recibe el nivel y
devuelve una función. La firma de la función es la que fijó la Fase 1:

```python
detector(cajas: frozenset[int], caja_movida: int) -> bool
```

`True` significa "esta configuración de cajas ya no admite solución".

La fábrica recibe el **`Tablero`** y no el `Problema`, que es la única diferencia
con las heurísticas. Por dos motivos: un deadlock es geometría del nivel y no
depende del estado inicial, y sobre todo porque el `Problema` se construye **con**
el detector adentro, así que pedirle el problema a la fábrica sería un
huevo-y-gallina.

```python
DETECTORES = {
    'ninguno':    ...,   # devuelve None, no una función
    'estaticos':  ...,   # regla 1: celdas muertas
    'congelados': ...,   # regla 2: bloques de 2x2
    'completo':   ...,   # las dos
}
```

**Tres y no uno, por el mismo motivo por el que la Fase 4 tiene cinco heurísticas
y no una:** para poder decir cuánto aporta cada regla. Una tabla con una sola
columna "con poda" no permite responder "¿y cuál de las dos reglas hizo el
trabajo?", que es exactamente el tipo de pregunta que se hace en el oral.

### Decisión: `'ninguno'` devuelve `None`, no una función que siempre dice que no

Parece un detalle y no lo es. `Problema.sucesores()` pregunta
`if detectar is not None` una vez por empuje; con `None` esa rama ni se toca, y
sobre todo **la corrida sin poda es exactamente la misma corrida de las Fases 2 a
4**, no una versión equivalente. Los números congelados en `tests/conftest.py` no
se pueden mover, y con `None` no hay ninguna forma de que se muevan.

---

## Regla 1 — celdas muertas (deadlock estático)

> Un empuje que deja la caja en una celda desde la que **ninguna meta es
> alcanzable a empujones** es un deadlock.

Ya está calculado: `distancias.celdas_muertas(tablero)`, subproducto del BFS de
tirones de h₄. El detector es una consulta a un `frozenset`.

**Por qué no tiene falsos positivos.** El BFS de tirones construye el grafo de
*todos* los empujes geométricamente posibles, ignorando las otras cajas y si el
jugador puede llegar: eso lo hace **más permisivo** que el juego real. Si en ese
grafo permisivo no hay camino de la celda a ninguna meta, en el juego real
tampoco lo hay. Una caja ahí no llega nunca a una meta, y sin todas las cajas en
metas no hay solución.

**Se precalcula una vez por nivel** porque no depende del estado: es geometría
del tablero, igual que la tabla de h₄, y sale del mismo cálculo. Que la
heurística y la poda salgan de la misma cuenta es un hecho del código, no una
frase de la presentación.

### Decisión: importar `celdas_muertas` en vez de recalcularla

`src/deadlocks.py` va a importar de `src/heuristicas/distancias.py`, que a
primera vista se lee raro: la poda no usa ninguna heurística. Es correcto igual,
porque `distancias.py` no es una heurística sino **la geometría del nivel**, y
está escrito como módulo sin estado justamente para esto.

Se descarta copiar el BFS de tirones a `deadlocks.py`: serían dos
implementaciones de la misma cuenta, y el día que una cambie la otra queda vieja
en silencio. También se descarta mover `distancias.py` a `src/modelo/`: es más
prolijo y obliga a tocar cuatro archivos estables de la Fase 4 para ganar
únicamente una línea de import más linda.

---

## Regla 2 — bloques de 2x2 congelados (deadlock dinámico)

> Un empuje que deja la caja en `p` es un deadlock si alguno de los cuatro
> cuadrados de 2x2 que contienen a `p` queda **completamente ocupado** por
> paredes y cajas, y **al menos una de las cajas de ese cuadrado no está sobre
> una meta**.

**Por qué no tiene falsos positivos.** Tomemos una caja de un cuadrado de 2x2
lleno. Su vecina horizontal dentro del cuadrado está ocupada y su vecina vertical
también. Para empujarla a la derecha hace falta que la celda de la derecha esté
libre; para empujarla a la izquierda, que el jugador quepa a su derecha. Las dos
cosas piden la misma celda, y esa celda está ocupada: **la caja no se puede mover
en horizontal**. El mismo argumento en vertical. Y vale para las cuatro celdas
del cuadrado por simetría, así que ninguna de esas cajas se vuelve a mover nunca.
Si alguna no está sobre una meta, no se puede completar el nivel.

Las paredes cuentan como ocupadas por el mismo motivo que las cajas: son
inmóviles y el jugador no puede pararse ahí. Lo de afuera del rectángulo también,
porque una caja nunca puede salir del tablero.

### La cláusula que no se puede olvidar: "al menos una fuera de meta"

Sin ella, el detector **podaría la solución de `n4_matching`**. No es una
hipótesis: las cuatro metas de N4 forman un bloque de 2x2, así que el estado meta
de ese nivel *es* un cuadrado de 2x2 lleno de cajas. Con la regla mal escrita, N4
devolvería "sin solución".

Es el ejemplo con el que se explica la asimetría de arriba en la presentación, y
es también el motivo por el que la comprobación 1 del criterio de aceptación
—"ninguna capa poda un estado del camino óptimo"— tiene que correr sobre los
cinco niveles y no sobre uno de muestra.

### Decisión: los cuadrados que nunca pueden ser deadlock se descartan al construir

Si **todas** las celdas de piso de un cuadrado son metas, entonces cuando ese
cuadrado se llene todas sus cajas van a estar sobre metas, así que jamás va a ser
un deadlock. Eso se sabe sin mirar el estado: se decide una vez por nivel al
construir la fábrica, en vez de preguntarlo en cada empuje.

La tabla precalculada es, para cada celda `p`, la lista de los cuadrados que la
contienen y que sí podrían ser deadlock, cada uno reducido a **las celdas de piso
que faltan ocupar** (las paredes ya están, no hay nada que preguntar). Chequear un
empuje es entonces: ¿alguna de esas listas está toda contenida en el conjunto de
cajas? Con listas de a lo sumo tres elementos y cuatro cuadrados por celda.

### Decisión: alcanza con revisar la caja recién empujada

Es la razón por la que la firma del gancho recibe `caja_movida`, escrita desde la
Fase 1. Si después del empuje hay un cuadrado lleno que **no** contiene a la caja
movida, entonces ese cuadrado ya estaba lleno antes del empuje —las otras cajas y
las paredes no se movieron—, así que se habría detectado en el empuje anterior.

**El estado inicial es la excepción**, porque nunca pasa por un empuje y por lo
tanto nunca se consulta. Si un nivel arrancara ya muerto, el detector no lo diría.
No pasa en los cinco de la suite y BFS lo prueba: encuentra el óptimo publicado
en todos.

---

## La combinación

`'completo'` consulta primero la celda muerta —una pertenencia a un `frozenset`—
y sólo si pasa mira los cuadrados. El orden es por costo, no por importancia.

Las dos reglas **no están ordenadas por dominancia**: hay deadlocks estáticos que
la regla de 2x2 no ve (una caja sola en un pasillo contra la pared equivocada) y
deadlocks de 2x2 que la regla estática no ve (dos cajas pegadas contra una pared,
cada una en una celda perfectamente viva). Por eso la tabla de resultados es un
retículo y no una cadena: `ninguno ≥ estaticos ≥ completo` y
`ninguno ≥ congelados ≥ completo`, pero `estaticos` y `congelados` no son
comparables entre sí.

---

## `config.json` — la clave nueva

```json
{
  "nivel": "niveles/n4_matching.sok",
  "metodo": "astar",
  "heuristica": "h5",
  "deadlocks": "completo",
  ...
}
```

Se agrega `"deadlocks"` a `CLAVES` y a `VALORES_POR_DEFECTO` de `main.py`, con un
flag `--deadlocks` que la pisa, exactamente como `"heuristica"`. El valor por
defecto es `"ninguno"`: la configuración que ya está commiteada tiene que seguir
significando lo mismo que significaba.

**Por qué en esta fase y no en la Fase 6.** Está escrito en el docstring de
`main.py`: si un número de la presentación no se puede reproducir con un archivo
de configuración del repositorio, ese número no debería estar en la presentación.
Esta fase produce una tabla de números y sería la primera en no poder cumplirlo.

`imprimir_resultado()` suma una línea con qué poda se usó, por el mismo motivo por
el que ya imprime cuál heurística.

---

## Recordatorio: esta fase lleva dos checkpoints

`docs/01_REGLAS_DE_TRABAJO.md`, regla 3, nombra `src/deadlocks.py` explícitamente.
Son dos checkpoints, uno por regla, y **no se agrupan**: escribí uno, esperá el
OK, implementá, verificá, y recién ahí pasá al siguiente.

Con una adaptación del formato: donde el checkpoint dice **POR QUÉ ES ADMISIBLE**,
acá va **POR QUÉ NO TIENE FALSOS POSITIVOS**. Es la misma pregunta —¿por qué esto
no rompe la optimalidad?— hecha sobre una poda en vez de sobre una heurística, y
la respuesta es igual de importante: es lo que se dice en la diapositiva.

El de la regla 1 va a ser corto, porque la cuenta ya está hecha y verificada desde
la Fase 4. El de la regla 2 es el que importa.

---

## Qué se espera medir, y una predicción que hay que confirmar o desmentir

La poda estática y h₄ **se solapan a propósito**: h₄ vale `INALCANZABLE` (10⁶) en
cualquier estado con una caja en celda muerta, así que A\*(h₄) ya los manda al
fondo de la frontera y casi nunca los expande — los genera igual.

De ahí sale una predicción concreta, y conviene escribirla antes de medir:

1. En **BFS**, que no mira ninguna heurística, la poda estática debería bajar
   fuerte **expandidos y generados**.
2. En **A\*(h₄) y A\*(h₅)**, la poda estática debería bajar mucho los **generados**
   y la **memoria**, y bastante menos los **expandidos**, porque la heurística ya
   estaba haciendo casi todo ese trabajo.
3. La poda de **congelados** sí le dice a A\* algo que no sabía: dos cajas pegadas
   contra una pared es un estado muerto al que h₄ le asigna un valor finito y
   chico. Debería aportar en los tres métodos.

**Si algún número contradice la predicción, gana el número.** Se reporta y se
explica, no se esconde y no se ajusta la predicción después de verla — es la
misma regla con la que la Fase 4 reportó que 2·h₄ expande *más* nodos que h₄ en
N5.

---

## Criterio de aceptación

`verificaciones/verificar_fase5.py`, sobre los cinco niveles, con corte por
`max_nodos` de `config.json` y **nunca por reloj**:

**1. Ninguna capa poda un estado del camino óptimo.** Se recorre el camino que
devuelve BFS y, en cada empuje, se le pregunta a las tres capas exactamente lo
que les preguntaría la búsqueda: la caja movida sale de la diferencia entre los
conjuntos de cajas de dos estados consecutivos. Un solo positivo acá es una falla
de la fase, no una advertencia.

**2. El costo no cambia.** BFS, A\*(h₄) y A\*(h₅), con las cuatro configuraciones
de poda, devuelven el costo publicado en los cinco niveles. Son 60 corridas.

**3. Los nodos bajan, y en ningún caso suben.** Por método y nivel:
`ninguno ≥ estaticos ≥ completo` y `ninguno ≥ congelados ≥ completo`, en nodos
expandidos y en generados. Que no puedan subir tiene argumento: podar sólo saca
sucesores, y sacar elementos no reordena a los que quedan —el contador de
inserción de la frontera es monótono—, así que lo que se expande con poda es un
subconjunto de lo que se expandía sin ella. Si un nivel lo contradice, es un
resultado que hay que entender antes de seguir.

**4. Los números de las Fases 2, 3 y 4 no se movieron.** `pytest -q` en verde sin
tocar un solo valor congelado. Es la comprobación de que `'ninguno'` es de verdad
la corrida de antes y no una equivalente.

**5. Los casos construidos a mano.** En `tests/test_deadlocks.py`, como texto XSB
dentro del test y **nunca** como archivos en `niveles/`:

- caja en un rincón → las dos reglas dicen deadlock;
- dos cajas pegadas contra una pared, ambas en celdas vivas → sólo `congelados`;
- caja en un pasillo contra la pared, sin meta en esa fila → sólo `estaticos`;
- cuadrado de 2x2 con las cuatro cajas sobre metas → **no** es deadlock;
- el mismo cuadrado con una sola caja fuera de meta → sí lo es.

Salida esperada, por nivel:

```
=== n4_matching.sok  (óptimo publicado: 70 mov / 22 empujes) ===
  celdas muertas: 12 de 31 transitables   ·   rincones: 6, de los cuales 0 no son celda muerta
  el camino óptimo (71 estados, 22 empujes) sobrevive a las tres capas   OK
  método    poda          costo  expandidos    generados    memoria  vs sin poda
  BFS       ninguno          70     654.260    1.728.078    671.278       1,00x
  BFS       estaticos        70     xxx.xxx    x.xxx.xxx    xxx.xxx       x,xxx
  BFS       congelados       70     xxx.xxx    x.xxx.xxx    xxx.xxx       x,xxx
  BFS       completo         70     xxx.xxx    x.xxx.xxx    xxx.xxx       x,xxx
  A*(h4)    ninguno          70      54.754      xxx.xxx    xxx.xxx       1,00x
  A*(h4)    completo         70      xx.xxx      xxx.xxx    xxx.xxx       x,xxx
  A*(h5)    ninguno          70      52.766      xxx.xxx    xxx.xxx       1,00x
  A*(h5)    completo         70      xx.xxx      xxx.xxx    xxx.xxx       x,xxx
```

y al final las dos tablas resumen: cuánto ahorra cada capa por método y nivel, y
cuál de las dos reglas poda más en cada uno.

Un **rincón** es una celda para la que la regla de 2x2 tiene un cuadrado sin
requisitos, o sea que la declara deadlock con una sola caja. Se reporta al lado
de las celdas muertas porque la comparación entre los dos números es la medida de
cuánto se solapan las dos reglas cuando hay una sola caja en juego. Contar
cuántos cuadrados quedan vivos, en cambio, no informa nada: da prácticamente el
total de celdas transitables en los cinco niveles.

**Tarda más que la verificación de la Fase 4**: son 60 corridas y cuatro de ellas
rondan los dos millones de nodos. Que vaya imprimiendo nivel por nivel.

### Números nuevos a congelar en `tests/conftest.py`

- Celdas muertas por nivel: 5 · 13 · 23 · 12 · 13 (ya medidas en la Fase 4).
- Las cinco columnas de BFS con poda `completo`, en los cinco niveles.

Van a `ESPERADO` bajo una clave nueva, con la misma advertencia de siempre: si
uno cambia, no se actualiza el valor esperado hasta entender por qué.

`cargar_problema()` y `correr()` de `conftest` pasan a aceptar qué poda usar, con
`'ninguno'` por defecto para que ni un test existente cambie de significado. Y va
un guardián como el de las heurísticas: **todo detector del registro tiene que
estar en la lista de los que se verifican**, para que agregar una regla nueva sin
verificarla falle en vez de pasar desapercibido.

---

## Cosas que NO van en esta fase

- **El congelamiento recursivo** (la regla general de *freeze deadlocks*, que marca
  una caja como inmóvil si sus dos ejes están bloqueados por paredes, cajas
  congeladas u otras cajas que a su vez estén congeladas). Poda bastante más y el
  argumento de por qué no tiene falsos positivos es recursivo y mucho más difícil
  de defender en un oral. Mencionalo en el resumen como alternativa evaluada, con
  ese motivo.
- **Deadlocks de corral y tablas de patrones precomputadas.** Es lo que usan los
  solvers serios y no entra en el alcance del TP.
- **DFS, Greedy e IDDFS con poda → Fase 6.** Vale la pena aclarar por qué quedan
  afuera: en DFS la poda **sí cambia el costo**, porque DFS no es óptimo y con
  menos ramas encuentra otra solución. Eso no contradice el criterio de la fase
  —"el costo no cambia"— porque ese criterio es una afirmación sobre los métodos
  óptimos. Es un buen resultado y es material de la Fase 6.
- **La matriz completa de experimentos y el CSV → Fase 6.**

---

## Al terminar

1. Corré `python3 -m verificaciones.verificar_fase5` y mostrá la salida completa.
2. Corré `python3 -m pytest -q` y `python3 -m pytest -q -m "not lento"`, y mostrá
   que ningún número congelado de las Fases 2, 3 y 4 se movió.
3. Escribí `docs/resumenes/FASE_5_RESUMEN.md` siguiendo la plantilla. La sección
   "Cuentas que se hacen acá" tiene que tener **los dos argumentos de por qué cada
   regla no tiene falsos positivos**, completos: son lo que se dice en la
   diapositiva. Y actualizá el índice de `docs/resumenes/README.md`.
4. Listá los archivos creados y modificados y **esperá**. No commitees.
