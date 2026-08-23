# FASE 4 — La escalera de heurísticas

**Dueño:** Fede · **Estado:** terminada

La fase que más pesa en la nota. Al terminar, existen cinco heurísticas nuevas,
cada una con su demostración de admisibilidad escrita, y está medido cuánto
aporta cada eslabón sobre el anterior.

---

## La idea que organiza toda la fase

No son "cinco heurísticas". Es **una cadena donde cada eslabón arregla un
defecto medido del anterior**, y para cada defecto hay un nivel concreto donde
se ve.

Eso no es una decisión estética: la cátedra pidió explícitamente que la
presentación siga un hilo del tipo *"como esto nos pareció que no estaba tan
bueno, entonces probamos con esto otro"*. Si en vez de eso mostramos una tabla
con cinco heurísticas sueltas, perdemos justamente lo que dijeron que valoran.

**El argumento que abre la fase ya está medido.** En la Fase 2, con h₁:

| Nivel | `h(s₀)/óptimo` | Nodos que ahorra A\*(h₁) sobre BFS |
|---|---|---|
| n1_micro | 0,125 | 28,9 % |
| n2_akk04 | 0,089 | 20,0 % |
| n3_caminata | 0,019 | 4,9 % |
| n4_matching | 0,057 | 5,1 % |
| n5_limite | 0,013 | **796 nodos sobre 2.028.239 (0,04 %)** |

En N5, A\*(h₁) es BFS con un sombrero. No hay que convencer a nadie de que hace
falta algo mejor: el número lo dice.

---

## Archivos a crear

```
src/heuristicas/h2_manhattan.py
src/heuristicas/h3_matching_manhattan.py
src/heuristicas/h4_matching_real.py
src/heuristicas/h5_con_jugador.py
src/heuristicas/hna_sobreestimada.py
src/heuristicas/distancias.py          (tablas compartidas por h4 y h5)
verificaciones/verificar_fase4.py
```

Y ampliar `src/heuristicas/registro.py` con las entradas nuevas.

Toda heurística sigue siendo una **fábrica**: recibe el problema y devuelve una
función `estado -> número`. Ese diseño existe para esto: h₃, h₄ y h₅ precalculan
tablas una sola vez por nivel en lugar de recalcularlas en cada evaluación.

---

## Recordatorio: cada heurística dispara un checkpoint

`docs/01_REGLAS_DE_TRABAJO.md`, regla 3. Son cinco checkpoints, uno por
heurística, y **no son un trámite**: el texto de cada uno —qué calcula, por qué
así, por qué es admisible, qué se descartó— es literalmente lo que hay que
poder decir en el oral.

Escribí uno, esperá el OK, implementá, verificá, y recién ahí pasá al siguiente.
No los agrupes.

---

## h₂ — Suma de distancias Manhattan a la meta más cercana

```
h₂(s) = Σ  mín  manhattan(caja, meta)
       cajas metas
```

**Defecto que arregla.** h₁ cuenta cajas fuera de lugar pero no distingue una
caja pegada a su meta de una caja en la otra punta del tablero. Con 4 cajas,
h₁ sólo puede valer 0, 1, 2, 3 o 4: cinco valores distintos para millones de
estados.

**Por qué es admisible.** Resuelve una versión relajada del problema donde no
hay paredes, las cajas se atraviesan entre sí y el jugador se teletransporta.
Toda solución del problema real también lo es del relajado, así que el óptimo
del relajado es cota inferior del real. Además cada empuje mueve una caja un
casillero, y todo empuje es un movimiento.

**Su propio defecto, para la transición a h₃.** Si dos cajas tienen la misma
meta como más cercana, las dos suman esa distancia, pero en la realidad una de
las dos va a tener que ir a otra meta, más lejos. **Subestima de más.** Se ve
en `n4_matching`, donde las cuatro metas están juntas en un bloque de 2×2.

---

## h₃ — Asignación óptima caja↔meta con distancias Manhattan

Resolver el problema de asignación de costo mínimo entre cajas y metas, con
`scipy.optimize.linear_sum_assignment` (autorizado en las reglas exactamente
para esto).

```
h₃(s) = mín      Σ manhattan(caja, σ(caja))
      σ biyección
```

**Por qué es admisible.** Es el mínimo sobre **todas** las asignaciones
posibles. La asignación que efectivamente ocurre en la solución óptima es una de
ellas, así que su costo es ≥ h₃.

**Por qué domina a h₂.** h₂ es el mismo cálculo pero permitiendo que varias
cajas compartan meta, o sea, minimizando sobre un conjunto más grande de
asignaciones. El mínimo sobre un conjunto más grande es menor o igual.

**Su propio defecto.** Las distancias Manhattan atraviesan paredes. Se ve en
`n3_caminata`, donde las metas están detrás de paredes y el rodeo real es mucho
más largo que la línea recta.

---

## h₄ — Asignación óptima con distancias reales

Igual que h₃, pero la matriz de costos usa **distancias reales sobre el tablero**
en vez de Manhattan.

**Cómo se calculan.** Un BFS desde cada meta sobre las celdas transitables,
**ignorando las cajas y al jugador**. Da una tabla `distancia[meta][celda]` por
nivel, calculada una sola vez.

**Por qué es admisible.** Una caja que va de `c` a la meta `m` necesita al menos
`distancia[m][c]` empujes: el BFS ya considera las paredes y sólo ignora
obstáculos que pueden agregar recorrido, nunca quitarlo. Distintas cajas
necesitan empujes distintos, y todo empuje es un movimiento.

**Por qué domina a h₃.** La distancia real es siempre ≥ la Manhattan, porque las
paredes sólo pueden alargar el camino. Como cada entrada de la matriz de costos
es mayor o igual, el óptimo de la asignación también lo es.

### El regalo: el detector de deadlocks estáticos

Si una celda **no aparece en ninguna de las tablas**, significa que desde ella no
se puede alcanzar ninguna meta. Una caja ahí vuelve el nivel irresoluble.

Ese conjunto de **celdas muertas** es exactamente lo que necesita la Fase 5, y
sale como subproducto de calcular h₄. Dejalo expuesto en `distancias.py` con una
función que lo devuelva; **no implementes la poda todavía**, eso es la Fase 5.

Es un hallazgo lindo para la presentación: la heurística y la poda salen del
mismo cálculo.

### Cuidado con la asignación imposible

Si alguna caja está en una celda muerta, no hay asignación válida.
`linear_sum_assignment` necesita una matriz finita, así que hay que decidir qué
poner en esas entradas. Documentá qué elegiste y por qué, y qué devuelve la
heurística en ese caso.

---

## h₅ — h₄ más el recorrido del jugador

Las cuatro anteriores tratan al jugador como si no existiera. Pero en `n3_caminata`,
**82 de los 104 movimientos de la solución óptima son el jugador caminando**
(79 %), y ninguna heurística los ve.

```
h₅(s) = h₄(s) + máx(0, mín distancia_jugador(caja) − 1)
                       cajas
```

**Por qué es admisible.** Si el estado no es meta, falta al menos un empuje. El
primer empuje es de alguna caja, y para empujarla el jugador tiene que estar en
una celda adyacente: eso son al menos `distancia(jugador, caja) − 1` movimientos
que **no son empujes**, y por lo tanto son disjuntos de los que cuenta h₄. Como
no sabemos cuál va a ser la primera caja empujada, tomamos el mínimo sobre
**todas** las cajas, incluidas las que ya están sobre una meta.

> **Ojo con esto último.** Tomar el mínimo sólo sobre las cajas fuera de meta
> sería un error: puede convenir mover primero una caja que ya está en una meta.
> El mínimo sobre todas es una cota inferior segura.

La distancia del jugador se calcula también ignorando las cajas: son obstáculos
que sólo pueden alargar el recorrido.

**Sobre la consistencia.** h₂, h₃ y h₄ deberían ser consistentes. h₅ **no es
obvio que lo sea**: el término del jugador puede saltar más de una unidad entre
estados vecinos. Verificalo con la herramienta de la Fase 3 y **reportá el
resultado tal cual salga**. Si no es consistente, no es un fracaso: A\* sigue
siendo óptimo con la política `mejor_g` que ya tiene el motor, sólo que puede
reabrir nodos. Eso es exactamente por qué el motor no asume consistencia.

---

## hₙₐ — La no admisible, a propósito

```
hₙₐ(s) = 2 · h₄(s)
```

**No es admisible**, y está para mostrar qué se rompe. Es la única heurística de
la fase que no necesita demostración: necesita un **contraejemplo**.

Buscá un nivel donde A\*(hₙₐ) devuelva un costo mayor al óptimo, y mostrá los
dos números juntos: cuánto más rápido terminó y cuánto peor es la solución.

Es el material para la conclusión de que **la admisibilidad no es un tecnicismo:
es la garantía de optimalidad**.

---

## Sobre combinar heurísticas

En la teoría se ve que `máx(h_a, h_b)` de dos admisibles es admisible y domina a
las dos. **Acá no aporta**, porque nuestras heurísticas forman una cadena de
dominancia: h₅ ≥ h₄ ≥ h₃ ≥ h₂, así que el máximo es siempre h₅.

Mencionalo en el resumen igual, con esa justificación. Que una técnica conocida
no aplique, y saber por qué, es una respuesta mejor que no haberla considerado.

---

## Criterio de aceptación

`verificaciones/verificar_fase4.py` verifica, sobre los cinco niveles:

**1. Admisibilidad y consistencia de las seis heurísticas** (h₀ a h₅), con las
herramientas de la Fase 3, sobre el camino óptimo. hₙₐ debe **fallar**
admisibilidad en al menos un nivel: si pasa, no estamos demostrando nada.

**2. La cadena de dominancia se cumple en valor:**
`h₁(s₀) ≤ h₂(s₀) ≤ h₃(s₀) ≤ h₄(s₀) ≤ h₅(s₀)` en los cinco niveles.

**3. La cadena de dominancia se cumple en nodos expandidos**, que es lo que de
verdad importa: A\*(h₂) ≥ A\*(h₃) ≥ A\*(h₄) ≥ A\*(h₅) en nodos, **con el mismo
costo en todos**. El criterio de la fase es que A\*(h₃) expanda menos que A\*(h₂)
en `n4_matching`.

> Si en algún nivel la dominancia en nodos no se cumple, **no es
> necesariamente un bug**: dominar en valor garantiza expandir a lo sumo los
> mismos nodos sólo bajo ciertas condiciones. Reportalo y explicá el caso, no lo
> escondas.

**4. Todos los A\* con heurística admisible devuelven el costo publicado**, y
A\*(hₙₐ) devuelve uno mayor en al menos un nivel.

**5. Tabla de informatividad** `h(s₀)/óptimo` para las seis, en los cinco
niveles. Es el eje X de la figura 2 de la Fase 8.

Salida esperada, por nivel:

```
=== n4_matching.sok  (óptimo 70 / 22 empujes) ===
heurística   h(s0)  h(s0)/óptimo  admisible  consistente  costo  expandidos  vs BFS
h0               0         0,000     OK          OK          70     654.260    1,00x
h1               4         0,057     OK          OK          70     621.068    1,05x
h2              xx         x,xxx     OK          OK          70     xxx.xxx    x,xxx
h3              xx         x,xxx     OK          OK          70     xxx.xxx    x,xxx
h4              xx         x,xxx     OK          OK          70     xxx.xxx    x,xxx
h5              xx         x,xxx     OK          ??          70     xxx.xxx    x,xxx
hna             xx         x,xxx     FALLA       —           xx     xxx.xxx    x,xxx   subóptimo
```

---

## Cosas que NO van en esta fase

- La poda de deadlocks. `distancias.py` expone las celdas muertas, pero nadie
  las usa todavía → Fase 5.
- El barrido del parámetro `w` → Fase 8.
- Correr la matriz completa de experimentos → Fase 6.

---

## Al terminar

1. Corré la verificación y mostrá la salida completa.
2. Escribí `docs/resumenes/FASE_4_RESUMEN.md`. La sección "Cuentas que se hacen
   acá" tiene que tener **las cinco demostraciones de admisibilidad completas**:
   es el guion del bloque más importante de la presentación.
3. Listá los archivos creados y **esperá**. No commitees.

---

## Nota al pie — dos cosas que la implementación hizo distinto

Escrita al cerrar la fase, para que este documento no contradiga al código.
El detalle completo está en `docs/resumenes/FASE_4_RESUMEN.md`.

### 1. La tabla de h₄ es un BFS de TIRONES, no de rejilla

Arriba dice "un BFS desde cada meta sobre las celdas transitables". Leído como
adyacencia de celdas —caminar— eso da distancia de **camino**, y se midió antes
de elegir:

| nivel | A\*(h₃) | A\*(h₄ camino) | A\*(h₄ empuje) | celdas muertas camino / empuje |
|---|---|---|---|---|
| n1_micro | 12 | 12 | 12 | 0 / 5 |
| n2_akk04 | 20.694 | 18.794 | **7.145** | 0 / 13 |
| n3_caminata | 5.348 | 5.348 | **1.951** | 0 / 23 |
| n4_matching | 473.191 | 462.427 | **54.754** | 0 / 12 |
| n5_limite | 2.019.787 | 2.019.787 | **605.520** | 0 / 13 |

Con distancia de camino los cinco niveles quedan completamente conectados, así
que **el conjunto de celdas muertas es vacío** y la sección "El regalo" de este
documento no se cumpliría; además en N3 y N5 h₄ daría idéntica a h₃, o sea que
el defecto que h₄ dice arreglar no se vería en ningún nivel de la suite.

La distancia de **empuje** exige que la celda de atrás también esté libre,
porque ahí es donde tiene que caber el jugador. Es una sola condición más en el
BFS y arregla los tres problemas de una.

### 2. hₙₐ = 2·h₄ no alcanza para el criterio 4: se agregó hₙₐ₄ = 4·h₄

A\*(2·h₄) devuelve el **óptimo en los cinco niveles**, así que la fase se
quedaría sin el contraejemplo de solución subóptima. El motivo es que h₄
subestima tanto (0,21 a 0,63 del óptimo) que duplicarla la deja igual por
debajo del costo real. Sí falla admisibilidad, así que el criterio 1 se cumple.

Se quedan las dos, y juntas dicen más que cualquiera sola:

| | N2 (ópt. 45) | N4 (ópt. 70) | N5 (ópt. 306) |
|---|---|---|---|
| h₄ | 45 / 7.145 nodos | 70 / 54.754 | 306 / 605.520 |
| 2·h₄ | 45 / 1.783 | 70 / 32.584 | 306 / **637.656** |
| 4·h₄ | **47** / 1.563 | **82** / 1.661 | 306 / **1.820.141** |

Tres conclusiones en vez de una: perder la admisibilidad pierde la garantía y
no necesariamente la respuesta; cuando la pierde la pierde caro (+17 % en N4);
y sobreestimar tampoco garantiza ir más rápido (en N5 las dos expanden **más**
nodos que h₄).
