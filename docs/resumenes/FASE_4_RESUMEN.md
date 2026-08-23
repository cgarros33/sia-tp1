# FASE 4 — La escalera de heurísticas

**Estado:** terminada · **Fecha:** 2026-08-23

## En una frase

Existen seis heurísticas admisibles y dos no admisibles a propósito, cada una
con su demostración escrita, y está medido cuánto aporta cada eslabón sobre el
anterior: A\*(h₅) resuelve N4 con 52.766 nodos donde BFS necesita 654.260, y en
N5 baja de 2.028.239 a 604.472.

## La idea que organiza la fase

No son cinco heurísticas sueltas. Es **una cadena donde cada eslabón arregla un
defecto medido del anterior**, y para cada defecto hay un nivel concreto donde
se ve. Ése es el hilo de la presentación.

| | Heurística | Qué defecto arregla | Dónde se ve |
|---|---|---|---|
| h₀ | 0 | — (control: A\*(h₀) tiene que ser BFS) | los cinco |
| h₁ | cajas fuera de meta | — (línea de base) | — |
| h₂ | Σ Manhattan a la meta más cercana | h₁ sólo toma 5 valores distintos | los cinco |
| h₃ | matching óptimo con Manhattan | h₂ manda varias cajas a la misma meta | **N4** |
| h₄ | matching con distancias de empuje | h₃ atraviesa paredes | **N3, N5** |
| h₅ | h₄ + término del jugador | las anteriores ignoran al jugador | N3 |
| hₙₐ | 2·h₄ | ninguno, es a propósito | qué se rompe |
| hₙₐ₄ | 4·h₄ | ninguno, es a propósito | qué se rompe |

El argumento que abre la fase ya venía medido de la Fase 2: en N5, A\*(h₁) le
ahorra a BFS **796 nodos sobre 2.028.239, el 0,04 %**. No hay que convencer a
nadie de que hacía falta algo mejor.

## Archivos creados

### `src/heuristicas/distancias.py`

**Qué hace:** calcula, una vez por nivel, las tablas de distancias que las
heurísticas necesitan: Manhattan a cada meta, empujes a cada meta, recorrido del
jugador entre todos los pares de celdas, y el conjunto de celdas muertas.

**Por qué existe:** las paredes y las metas no cambian nunca, así que la
distancia de una celda a una meta tampoco. Calcularla dentro de la heurística
sería recalcular millones de veces un número fijo desde que se leyó el archivo.
Y sobre todo, las tablas **se comparten**: h₄, h₅, hₙₐ y hₙₐ₄ usan exactamente la
misma matriz de distancias de empuje, y la Fase 5 va a usar el conjunto de
celdas muertas que sale de esa misma cuenta.

**La decisión importante:** el módulo no guarda estado global y las tablas no
son atributos del `Tablero`. `Tablero` es el nivel; no es lo que las heurísticas
piensan del nivel. Colgarlas ahí rompería la separación de la Fase 1 y obligaría
a pagar el cálculo aunque el nivel se resuelva con BFS, que no usa heurísticas.
Construir todas las tablas de un nivel cuesta un puñado de BFS sobre 12 a 41
celdas: es instantáneo, así que no hace falta ninguna caché entre heurísticas.

### `src/heuristicas/h2_manhattan.py`

**Qué hace:** para cada caja, la distancia de Manhattan a la meta más cercana, y
las suma.

**Por qué existe:** h₁ cuenta cajas fuera de meta y nada más. Con 4 cajas sólo
puede valer 0, 1, 2, 3 o 4: cinco valores para repartir entre 654.260 estados en
N4. Casi todos los nodos de la frontera empatan en f y el desempate lo termina
haciendo g, o sea que A\*(h₁) es BFS con un sombrero. h₂ le da al valor un rango
de verdad —23 en el inicial de N5, contra 4— y con eso, capacidad de ordenar.

**La decisión importante:** el mínimo se toma sobre **todas** las metas, no
contra una meta asignada de antemano. Asignar de antemano es más informativo y
no es admisible: si la solución óptima usa otra asignación, la cuenta
sobreestima. El problema que introduce el mínimo —que dos cajas reclamen la
misma meta— es exactamente lo que arregla h₃.

### `src/heuristicas/h3_matching_manhattan.py`

**Qué hace:** resuelve el problema de asignación de costo mínimo entre cajas y
metas sobre la misma matriz de distancias de Manhattan, con
`scipy.optimize.linear_sum_assignment` (algoritmo húngaro, O(n³)).

**Por qué existe:** h₂ toma el mínimo caja por caja, independientemente. Si dos
cajas tienen la misma meta como más cercana, las dos suman esa distancia, cuando
en la realidad una va a tener que ir a otra meta más lejos. h₂ subestima de más,
y cuanto más agrupadas están las metas, peor. `n4_matching` está elegido para
eso: las cuatro metas forman un bloque de 2x2, y ahí h₂(s₀) = 16 contra
h₃(s₀) = 20, un 25 % más de información sacada de las mismas 16 distancias.

**La decisión importante:** el valor se memoriza por **configuración de cajas**,
no por estado. h₃ no depende de dónde está el jugador, y la enorme mayoría de los
sucesores son movimientos del jugador que no mueven ninguna caja. La memoria está
acotada por C(celdas, cajas) —31.465 en N4— y es una optimización de tiempo que
**no cambia ni un nodo expandido**.

### `src/heuristicas/h4_matching_real.py`

**Qué hace:** el mismo matching de h₃, pero la matriz de costos son distancias
reales de **empuje** sobre el tablero, con sus paredes.

**Por qué existe:** Manhattan atraviesa paredes. Y hay algo peor que una
subestimación floja: hay celdas de las que una caja no puede salir, y para
Manhattan son celdas comunes a unos pasos de la meta. Es el eslabón que más
aporta de toda la escalera: en N4 baja de 473.191 a 54.754 nodos y en N5 de
2.019.787 a 605.520.

**La decisión importante — y la que más se va a preguntar:** la tabla NO es la
distancia de camino entre celdas. Es la de empuje, que además exige que el
jugador quepa detrás de la caja. Se calcula con un BFS **hacia atrás** desde cada
meta: si la caja está en `p`, pudo haber llegado empujada desde `q`, y para eso
el jugador tenía que estar en la celda siguiente a `q` en la misma dirección; se
retrocede sólo si las dos están libres. Caminar y empujar no son lo mismo, y una
caja en un rincón lo muestra: se llega caminando y no se sale empujando.

### `src/heuristicas/h5_con_jugador.py`

**Qué hace:** h₄ más los pasos que el jugador tiene que caminar antes de poder
empujar cualquier caja.

**Por qué existe:** las cuatro anteriores estiman **empujes**, pero el enunciado
pide minimizar **movimientos**. En `n3_caminata`, 82 de los 104 movimientos de la
solución óptima son el jugador caminando entre empuje y empuje: el 79 % del
costo es invisible para toda la escalera. Es el punto ciego que explica por qué
A\* rinde menos en Sokoban que en el 8-puzzle.

**La decisión importante:** el mínimo se toma sobre **todas** las cajas,
incluidas las que ya están sobre una meta. Restringirlo a las cajas fuera de meta
parece más informativo y es un error: puede convenir mover primero una caja ya
colocada, porque estorba. Y hay un `return 0` explícito en la meta: sin él, h₅
valdría más que 0 donde el costo restante es 0 y dejaría de ser admisible.

### `src/heuristicas/hna_sobreestimada.py`

**Qué hace:** `hna = 2·h₄` y `hna4 = 4·h₄`. Ninguna es admisible, y ése es el
punto.

**Por qué existe:** para mostrar que la admisibilidad no es un tecnicismo sino la
garantía de optimalidad. Es la única entrada de la fase que no lleva
demostración: lleva contraejemplo.

**La decisión importante:** multiplicar, y no romper la admisibilidad de otra
manera, porque **aísla la variable**. hₙₐ tiene exactamente la misma información
que h₄, el mismo orden relativo entre estados y la misma forma; lo único que
cambia es la escala, así que todo lo que se observe es atribuible a haber perdido
la admisibilidad y a nada más. Es la advertencia de la cátedra sobre
correlaciones aplicada al diseño del experimento.

Son dos y no una porque **2·h₄ no alcanza**: A\* devuelve el óptimo en los cinco
niveles. Ver "Los tres resultados" más abajo.

### `verificaciones/verificar_fase4.py`

**Qué hace:** corre las cinco comprobaciones del criterio de aceptación sobre los
cinco niveles e imprime la tabla por nivel más las dos tablas resumen.

**Por qué existe:** los números de la presentación tienen que salir de un comando
que cualquiera del grupo pueda correr. Si un número no se puede reproducir con un
comando del repositorio, ese número no debería estar en la presentación.

**La decisión importante:** la dominancia en nodos se **reporta como advertencia**
y no hace fallar la verificación, salvo el criterio explícito de la fase. Dominar
en valor garantiza expandir a lo sumo los mismos nodos sólo bajo ciertas
condiciones, así que un nivel donde no se cumpla no es necesariamente un bug.
Esconderlo sería peor que no medirlo. (En la práctica se cumple en los cinco.)

## Archivos modificados

| Archivo | Qué cambió y por qué |
|---|---|
| `src/heuristicas/registro.py` | Suma `h2 h3 h4 h5 hna hna4` al diccionario `HEURISTICAS`. h₀ y h₁ siguen escritas ahí porque son de dos líneas; de h₂ en adelante cada una tiene su archivo, porque cada una necesita su demostración escrita y esa demostración es el docstring del módulo. |
| `src/heuristicas/__init__.py` | Reexporta las fábricas nuevas y `celdas_muertas`. |
| `tests/conftest.py` | `HEURISTICAS_A_VERIFICAR` pasa a `h0..h5` y `HEURISTICAS_NO_ADMISIBLES` a `('hna', 'hna4')`; una fila por heurística en la clave `informatividad` de los cinco niveles, escrita como fracción exacta para que el numerador sea auditable. **No se escribió ningún test nuevo**: la infraestructura de la Fase 3 estaba preparada para esto. |
| `tests/test_heuristicas.py` | Un solo cambio: `test_h0_no_informa_y_h1_si` se parametriza sobre `('h0', 'h1')` en vez de sobre `HEURISTICAS_A_VERIFICAR`. Asserta `h(s₀) == cantidad de cajas`, que es cierto sólo para h₁. |
| `docs/fases/FASE_4_HEURISTICAS.md` | Nota al pie con las dos desviaciones respecto del texto original y sus números. |

Ningún archivo de `niveles/` y ningún número congelado de las Fases 2 y 3.

## Cuentas que se hacen acá

### h₂ — suma de Manhattan a la meta más cercana

- **Qué calcula:** para cada caja, la cantidad de pasos que costaría llegar a su
  meta más cercana si el tablero fuera un plano vacío. Las suma.
- **Fórmula:** `h₂(s) = Σ_cajas mín_metas manhattan(caja, meta)`
- **Por qué es admisible:** es el costo óptimo de un problema relajado —sin
  paredes, con las cajas atravesándose entre sí y el jugador teletransportándose—
  y toda solución del problema real también resuelve el relajado. En forma de
  cuenta: mover una caja un casillero cambia su Manhattan a cualquier meta fija
  en a lo sumo 1, así que llevarla hasta su meta más cercana cuesta al menos
  ese número de **empujes**; las cajas son distintas, así que esos empujes son
  distintos entre sí; y todo empuje es un movimiento. Entonces
  `h₂ ≤ empujes que faltan ≤ movimientos que faltan = h*`.
- **Consistente:** un movimiento mueve a lo sumo una caja y a lo sumo un
  casillero, así que h₂ baja como mucho 1 por movimiento, que es el costo del arco.
- **Qué se descartó:** asignar cada caja a una meta fija (más informativo y no
  admisible) y la distancia euclídea (cota más floja que Manhattan en una grilla
  de 4 vecinos, y con flotantes).

### h₃ — asignación óptima con Manhattan

- **Qué calcula:** el emparejamiento caja↔meta más barato, una meta por caja.
- **Fórmula:** `h₃(s) = mín_{σ biyección} Σ manhattan(caja, σ(caja))`
- **Por qué es admisible:** es el mínimo sobre **todas** las biyecciones. En la
  solución óptima real cada caja termina en una meta y cada meta recibe una caja:
  esa correspondencia es una biyección, o sea una de las que se minimizaron, así
  que su costo es ≥ h₃. Y ese costo acota por debajo los empujes que faltan, por
  el mismo argumento que h₂.
- **Por qué domina a h₂:** h₂ es la misma minimización pero permitiendo que
  varias cajas compartan meta, o sea sobre un conjunto **más grande** de
  asignaciones. El mínimo sobre un conjunto más grande es menor o igual.
- **Consistente:** un movimiento cambia a lo sumo una entrada de la matriz y a lo
  sumo en 1, así que el óptimo de la asignación se mueve a lo sumo en 1.
- **Qué se descartó:** la asignación golosa (tres líneas, no da el mínimo, puede
  **sobreestimar** y por lo tanto no es admisible) y probar las 4! = 24
  permutaciones a mano (mismo número, pero lo que se defiende es "es el problema
  de asignación y se resuelve en O(n³)", no "son 24 permutaciones y con 8 cajas
  ya no termina").

### h₄ — asignación óptima con distancias de empuje

- **Qué calcula:** lo mismo que h₃, con una matriz de costos donde cada entrada
  es la cantidad mínima de empujes para llevar esa caja a esa meta en este
  tablero.
- **Fórmula:** `h₄(s) = mín_{σ biyección} Σ empujes(caja, σ(caja))`, donde
  `empujes` sale de un BFS hacia atrás desde cada meta sobre el grafo de
  "tirones": de `p` se retrocede a `q` sólo si `q` está libre **y** la celda
  siguiente a `q` en la misma dirección también, porque ahí es donde tiene que
  estar parado el jugador.
- **Por qué es admisible:** cuando una caja se empuja de `q` a `p`, el tablero
  real exige que `p` esté libre y que el jugador esté en la celda de atrás, que
  también tiene que estar libre. Entonces **toda secuencia real de empujes de una
  caja es un camino en ese mismo grafo**, y su largo es ≥ la distancia mínima que
  devuelve el BFS. El BFS ignora a las otras cajas y si el jugador puede llegar
  hasta ahí: son restricciones que sólo pueden **alargar** el recorrido real,
  nunca acortarlo. Con eso cada entrada de la matriz es cota inferior, el mínimo
  sobre las biyecciones acota los empujes totales, y todo empuje es un movimiento.
- **Por qué domina a h₃:** un camino de empujes es un camino de celdas adyacentes,
  así que su largo es siempre ≥ la Manhattan entre las puntas. Entrada por entrada
  la matriz de h₄ es ≥ la de h₃, y si toda entrada crece, el óptimo también.
- **Qué se descartó:** el BFS de adyacencia (distancia de **camino**), que es lo
  que decía la especificación. Ver la nota al pie de `FASE_4_HEURISTICAS.md`:
  daría cero celdas muertas en los cinco niveles y h₄ idéntica a h₃ en N3 y N5.
  También se descartó la distancia de empuje **exacta**, que además exigiría que
  el jugador pueda llegar esquivando las otras cajas: es más informativa y deja de
  ser una tabla estática, habría que recalcularla en cada evaluación.

### h₅ — h₄ más el recorrido del jugador

- **Qué calcula:** h₄ más los pasos que el jugador necesita para ponerse al lado
  de alguna caja.
- **Fórmula:** `h₅(s) = h₄(s) + máx(0, mín_cajas distancia(jugador, caja) − 1)`,
  y `h₅(s) = 0` si `s` ya es meta.
- **Por qué es admisible**, en tres piezas que hacen falta las tres:
  1. **La disyunción.** Si el estado no es meta, falta al menos un empuje. Ese
     primer empuje es de alguna caja, y para empujarla el jugador tiene que estar
     en una celda adyacente: llegar cuesta al menos `distancia − 1` movimientos,
     que ocurren **antes** del primer empuje y por lo tanto **no son empujes**.
     Como h₄ acota por debajo los empujes que faltan, los dos conjuntos son
     disjuntos y las cotas se suman.
  2. **El mínimo sobre todas las cajas**, incluidas las que ya están en meta: no
     sabemos cuál va a ser la primera empujada, y puede convenir mover primero una
     ya colocada.
  3. **La distancia ignora las cajas**, que son obstáculos que sólo pueden alargar
     el recorrido del jugador.
- **El caso borde:** en la meta h₄ vale 0 pero el término del jugador puede ser
  positivo, y una heurística admisible tiene que valer 0 donde el costo restante
  es 0. El propio argumento lo resuelve —"si el estado no es meta" no dice nada
  cuando el estado sí es meta—, y el `return 0` explícito lo implementa.
- **Consistencia:** el argumento de h₂/h₃/h₄ **no vale acá**, porque el jugador se
  mueve en todos los movimientos y el término puede cambiar en cada paso. Medido
  con la herramienta de la Fase 3: **consistente en los cinco niveles**, sobre los
  estados del camino óptimo y sus sucesores directos. Eso es una condición
  necesaria, no una demostración de consistencia en todo el espacio.
- **Qué se descartó:** el mínimo sólo sobre las cajas fuera de meta (no
  admisible), sumar el recorrido completo del jugador para toda la solución (no
  hay forma de acotarlo por debajo sin conocer el orden de los empujes) y
  `máx(h₄, término)` en vez de la suma (sumar es válido **porque los movimientos
  son disjuntos**, y es estrictamente mejor).

### hₙₐ y hₙₐ₄ — las no admisibles

- **Qué calculan:** `2·h₄` y `4·h₄`.
- **Por qué NO son admisibles:** h₄ ya es una cota ajustada de los empujes que
  faltan. Multiplicarla rompe `h ≤ h*` apenas h₄ pasa la mitad del costo
  restante, y eso ocurre siempre cerca del final: con una caja a un empuje de su
  meta, `h₄ = 1` y `2·h₄ = 2` cuando falta 1 movimiento. Violan admisibilidad en
  los cinco niveles.
- **Qué se descartó:** dejar sólo una de las dos. Ver abajo.

### Sobre combinar heurísticas

En la teoría, `máx(h_a, h_b)` de dos admisibles es admisible y domina a las dos.
**Acá no aporta**, porque nuestras heurísticas forman una cadena de dominancia:
h₅ ≥ h₄ ≥ h₃ ≥ h₂, así que el máximo es siempre h₅. Que una técnica conocida no
aplique, y saber por qué, es mejor respuesta que no haberla considerado.

## Verificación

**Cómo se comprueba que está bien:**

```
python3 -m verificaciones.verificar_fase4
python3 -m pytest -q
python3 -m verificaciones.verificar_fase2
```

**Salida obtenida** (`verificar_fase4`, las dos tablas resumen y el cierre):

```
=== Comprobación 5 — informatividad h(s0)/óptimo ===

heurística       n1_micro      n2_akk04   n3_caminata   n4_matching     n5_limite
h0                  0,000         0,000         0,000         0,000         0,000
h1                  0,125         0,089         0,019         0,057         0,013
h2                  0,625         0,244         0,115         0,229         0,075
h3                  0,625         0,311         0,115         0,286         0,088
h4                  0,625         0,400         0,115         0,314         0,206
h5                  0,750         0,400         0,125         0,343         0,229
hna                 1,250         0,800         0,231         0,629         0,412
hna4                2,500         1,600         0,462         1,257         0,824

=== Nodos expandidos por A*, por heurística y nivel ===
heurística       n1_micro      n2_akk04   n3_caminata   n4_matching     n5_limite
h0                     38        44.124         6.360       654.260     2.028.239
h1                     27        35.315         6.048       621.068     2.027.443
h2                     12        24.872         5.589       507.229     2.022.934
h3                     12        20.694         5.348       473.191     2.019.787
h4                     12         7.145         1.951        54.754       605.520
h5                      8         6.100         1.888        52.766       604.472
hna                    11         1.783         1.899        32.584       637.656
hna4                   11         1.563         1.845         1.661     1.820.141

hna: viola admisibilidad en 5 de 5 niveles — es lo que se espera.
hna4: viola admisibilidad en 5 de 5 niveles — es lo que se espera.
hna4: devuelve solución SUBÓPTIMA en 2 niveles — n2_akk04: 47 contra 45; n4_matching: 82 contra 70
hna: NO es admisible y aun así devolvió el óptimo en 5 de 5 niveles.

5/5 niveles OK. Las 5 comprobaciones pasan.
```

Y el criterio de aceptación explícito de la fase, en `n4_matching`:

```
CRITERIO DE LA FASE:  A*(h3)=473.191 < A*(h2)=507.229 con el mismo costo 70  OK
```

## Números nuevos

**Todas las heurísticas admisibles devuelven el costo publicado en los cinco
niveles.** Admisibilidad y consistencia: OK para h₀…h₅ en los cinco.

Cuánto ahorra cada eslabón sobre BFS (nodos expandidos):

| nivel | BFS | h₁ | h₂ | h₃ | h₄ | h₅ | h₅ vs BFS |
|---|---|---|---|---|---|---|---|
| n1_micro | 38 | 27 | 12 | 12 | 12 | 8 | 4,8x |
| n2_akk04 | 44.124 | 35.315 | 24.872 | 20.694 | 7.145 | 6.100 | 7,2x |
| n3_caminata | 6.360 | 6.048 | 5.589 | 5.348 | 1.951 | 1.888 | 3,4x |
| n4_matching | 654.260 | 621.068 | 507.229 | 473.191 | 54.754 | 52.766 | 12,4x |
| n5_limite | 2.028.239 | 2.027.443 | 2.022.934 | 2.019.787 | 605.520 | 604.472 | 3,4x |

La dominancia en nodos **se cumple en los cinco niveles**, sin excepciones que
reportar. Los valores de informatividad quedan congelados en `tests/conftest.py`
como fracciones exactas y son ahora referencia de regresión.

**El eslabón que más aporta es h₄**, con diferencia: en N4 pasa de 473.191 a
54.754 nodos (8,6x) y en N5 de 2.019.787 a 605.520 (3,3x). h₂ y h₃ juntas
apenas mueven la aguja en los niveles grandes.

### Los tres resultados de las no admisibles

| | N2 (ópt. 45) | N4 (ópt. 70) | N5 (ópt. 306) |
|---|---|---|---|
| h₄ | 45 / 7.145 | 70 / 54.754 | 306 / 605.520 |
| 2·h₄ | 45 / 1.783 | 70 / 32.584 | 306 / **637.656** |
| 4·h₄ | **47** / 1.563 | **82** / 1.661 | 306 / **1.820.141** |

1. **Perder la admisibilidad pierde la garantía, no necesariamente la
   respuesta.** 2·h₄ devolvió el óptimo en los cinco niveles. Nadie podía saberlo
   de antemano: si el resultado hubiera dependido de eso, habríamos entregado un
   número sin saber si era correcto.
2. **Cuando la pierde, la pierde caro.** 4·h₄ en N4 termina 33 veces más rápido y
   devuelve 82 movimientos donde el óptimo es 70: 17 % peor.
3. **Sobreestimar tampoco garantiza ir más rápido.** En N5, 2·h₄ expande **más**
   nodos que h₄ (637.656 contra 605.520) y 4·h₄ expande el triple (1.820.141), y
   las tres devuelven 306. Una h inflada empuja a A\* a comprometerse temprano con
   una rama equivocada, y desandarla cuesta más de lo que ahorró.

### Celdas muertas — el subproducto para la Fase 5

| nivel | celdas transitables | celdas muertas |
|---|---|---|
| n1_micro | 12 | 5 |
| n2_akk04 | 32 | 13 |
| n3_caminata | 35 | 23 |
| n4_matching | 31 | 12 |
| n5_limite | 41 | 13 |

Salen gratis del BFS de tirones de h₄: son las celdas transitables que no
aparecen en ninguna tabla, o sea desde las que ninguna meta es alcanzable a
empujones. **Nadie las usa todavía.** Está verificado que ninguna caja de los
cinco estados iniciales cae en una: si cayera, el nivel sería irresoluble y BFS
no habría encontrado el óptimo, así que es también un control cruzado del
detector contra la Fase 2.

## Preguntas que esta fase habilita en el oral

- **¿Por qué h₄ no usa simplemente la distancia de camino entre celdas?** Porque
  caminar y empujar no son lo mismo: para empujar, el jugador tiene que caber
  detrás de la caja. Con distancia de camino, en los cinco niveles todas las
  celdas quedan conectadas, no habría ninguna celda muerta y h₄ daría idéntica a
  h₃ en N3 y N5.
- **¿Cómo saben que h₅ es admisible si suma dos cosas?** Porque cuentan
  movimientos **disjuntos**: h₄ acota los empujes, y el término del jugador cuenta
  pasos que ocurren antes del primer empuje y por lo tanto no son empujes. Si
  contaran lo mismo habría que tomar el máximo, no la suma.
- **¿Por qué el mínimo de h₅ incluye las cajas que ya están en su meta?** Porque
  no sabemos cuál va a ser la primera caja empujada y puede convenir mover primero
  una ya colocada, por ejemplo si estorba el paso. Restringirlo a las cajas fuera
  de meta daría un número mayor que podría pasarse del costo real.
- **¿Por qué 2·h₄ devolvió el óptimo si no es admisible?** Porque h₄ subestima
  mucho —entre el 21 % y el 63 % del costo real—, así que duplicarla la deja igual
  por debajo de h\* casi en todas partes. Que haya salido bien es suerte, no
  garantía: es exactamente lo que la admisibilidad compra.
- **¿Por qué A\*(h₅) apenas mejora a A\*(h₄)?** Porque el término del jugador mira
  sólo el próximo empuje y, para ser una cota segura, tiene que ser el mínimo
  sobre todas las cajas: en un tablero chico el jugador casi siempre tiene alguna
  cerca, así que el término vale 0 o 1 la mayor parte del tiempo. El punto ciego
  del jugador queda mayormente abierto.
- **¿Por qué no combinan las heurísticas con máx()?** Porque forman una cadena de
  dominancia: h₅ ≥ h₄ ≥ h₃ ≥ h₂, así que el máximo es siempre h₅.

## Qué quedó pendiente

- **La poda de deadlocks — Fase 5.** `distancias.celdas_muertas()` está escrita y
  verificada, y **nadie la usa**. El gancho del `Problema` para el detector ya
  existe desde la Fase 1.
- **El barrido de w — Fase 8.** hₙₐ y hₙₐ₄ son dos puntos de ese barrido vistos
  como heurísticas: `f = g + 2·h` es lo mismo que ponderar h frente a g.
- **La matriz completa de experimentos y el CSV — Fase 6.**
- **La figura de dominancia empírica — Fase 8**, que usa como eje horizontal la
  tabla de informatividad de acá.

## Ideas para más adelante

- La memoria por configuración de cajas de h₃/h₄ podría compartirse entre las
  heurísticas de un mismo nivel: hoy hₙₐ, hₙₐ₄ y h₅ construyen cada una su propia
  h₄ con su propia memoria. No se hizo porque cada corrida usa una sola
  heurística y compartir estado entre fábricas complicaría el argumento de que
  las comparaciones son independientes.
- Una heurística de **empujes con jugador**, que exija además que el jugador
  pueda llegar de verdad a la celda de empuje esquivando las otras cajas. Sería
  bastante más informativa y ya no se podría precalcular: habría que medir si el
  costo por evaluación se paga con los nodos ahorrados.
