# 02 — Plan de fases

Nueve fases. Cada una tiene un **criterio de aceptación verificable**: mientras
no se cumpla, la fase no está terminada y no se pasa a la siguiente.

La columna "dueño" es de las personas del grupo, no del agente. El dueño es
quien tiene que poder explicar esa parte en el oral, más allá de quién escribió
el código.

| Fase | Qué construye | Dueño | Criterio de aceptación |
|---|---|---|---|
| 1 | Modelo del problema | Matías | Los 5 niveles se parsean y el estado inicial se dibuja idéntico al archivo |
| 2 | Motor genérico + 5 métodos | Matías | BFS da el costo publicado en los 5 niveles |
| 3 | Tests de regresión | Celestino | `pytest` en verde; falla si se rompe una pared de un `.sok` |
| 4 | Escalera de heurísticas | Fede | A\*(h₃) expande menos que A\*(h₂) en N4, con el mismo costo |
| 5 | Deadlocks | Celestino | El costo no cambia al activar la poda, pero bajan los nodos |
| 6 | Runner + `config.json` | Leo | Un comando produce `resultados.csv` con toda la matriz |
| 7 | Reproductor estado por estado | Celestino | Existe el GIF de N1 con sus 8 movimientos |
| 8 | Gráficos y análisis | Leo | Las 4 figuras generadas desde el CSV |
| 9 | Presentación | los 4 | Ensayo cruzado superado |

---

## Fase 1 — Modelo del problema

Representar el mundo. Sin búsqueda todavía.

Archivos: `src/modelo/tablero.py`, `estado.py`, `parser_xsb.py`, `problema.py`.

La decisión central es la **separación entre lo estático y lo dinámico**: las
paredes y las metas no cambian nunca, así que no forman parte del estado.

Especificación completa: `docs/fases/FASE_1_MODELO.md`.

## Fase 2 — Motor genérico y los cinco métodos

Un solo bucle de búsqueda. Los métodos se diferencian **únicamente por la
estructura de la frontera**. Esta es la decisión de arquitectura que más se
defiende en el oral: concentrar la variación en un punto hace que la
comparación entre métodos sea justa por construcción, porque todos corren
exactamente el mismo código salvo esa clase.

Archivos: `src/busqueda/nodo.py`, `frontera.py`, `motor.py`, `algoritmos.py`.

Especificación completa: `docs/fases/FASE_2_MOTOR.md`.

## Fase 3 — Tests de regresión

La red de seguridad. Fija los números de oro para poder refactorizar dos
semanas sin miedo.

Distinción importante: el **costo y los empujes** están validados contra los
récords humanos publicados (verdad externa, no se negocian). Los **nodos
expandidos** son una métrica de nuestra implementación: no hay verdad externa,
se congelan una vez medidos y sirven para detectar regresiones.

Archivo: `tests/test_regresion.py`.

## Fase 4 — La escalera de heurísticas

**La fase que más pesa en la nota.** No son "tres heurísticas": es una cadena
donde cada eslabón arregla un defecto medido del anterior, y hay un nivel
concreto donde ese defecto se ve.

| | Heurística | Qué defecto arregla | Se ve en |
|---|---|---|---|
| h₀ | 0 | — (control: A\*(h₀) debe igualar a BFS) | todos |
| h₁ | cajas fuera de meta | — (línea de base) | — |
| h₂ | Σ Manhattan a la meta más cercana | h₁ no distingue cerca de lejos | N3 |
| h₃ | matching óptimo con Manhattan | h₂ asigna varias cajas a la misma meta | **N4** |
| h₄ | matching con distancias reales de empuje | h₃ atraviesa paredes | **N3** |
| h₅ | h₄ + término del jugador | las anteriores ignoran al jugador | N3, N5 |
| hₙₐ | 2·h₄ | ninguno, es a propósito | mostrar qué se rompe |

Cada una necesita su demostración de admisibilidad **escrita en dos renglones**,
porque eso es lo que se muestra en la presentación.

Hallazgo ya verificado que conviene aprovechar: al calcular las distancias
reales de empuje de h₄, las celdas que quedan inalcanzables desde toda meta son
exactamente las celdas muertas. **h₄ regala el detector de deadlocks estáticos
de la Fase 5.**

## Fase 5 — Deadlocks

Dos categorías: estáticos (celdas muertas, precalculadas una vez por nivel) y
dinámicos (bloques de 2×2 congelados).

Punto a defender: **podar deadlocks no rompe la optimalidad de A\***, porque los
estados eliminados no admiten ninguna solución y por lo tanto ningún camino
óptimo pasa por ellos.

## Fase 6 — Runner, configuración y CSV

Matriz de aproximadamente 5 niveles × 13 configuraciones ≈ 65 corridas, con
timeout y límite de nodos, volcada a CSV.

Precisión metodológica que hay que respetar: BFS, IDDFS, Greedy y A\* son
**determinísticos**. Los nodos expandidos no varían entre corridas, así que
promediarlos no tiene sentido y las barras de error darían cero. Entonces:

- Nodos y costo: **una corrida**, aclarando que es determinístico.
- Tiempo: **10 corridas**, media y desvío.
- DFS: es el único con variabilidad real, porque depende del orden de
  sucesores. **30 corridas con semilla**, media y desvío de costo y de nodos.

## Fase 7 — Reproductor estado por estado

La cátedra pidió explícitamente mostrar la secuencia, no el resultado.

Salida doble: **GIF animado** para la presentación (corre solo, sin riesgo de
demo en vivo) y **tira de fotogramas clave** para el PDF, que no anima.

## Fase 8 — Gráficos y análisis

Cuatro figuras mínimas:

1. Nodos expandidos por método y nivel, escala logarítmica.
2. Dominancia empírica: nodos expandidos contra `h(inicial)/óptimo`.
3. Barrido de `w` en `f = (1−w)·g + w·h`, de 0 a 1: recorre costo uniforme →
   A\* → Greedy en una sola curva.
4. El muro: espacio de estados contra nodos expandidos, incluyendo el nivel
   descartado de 5 cajas.

Sobre correlaciones, que fue una advertencia explícita de la cátedra: una
correlación sirve cuando **se mueve una variable y el resto queda fijo**. El
barrido de `w` es el ejemplo bueno. Comparar "cantidad de cajas contra tiempo"
mezclando niveles distintos es el ejemplo malo, porque está confundido con el
tamaño y la topología del tablero.

## Fase 9 — Presentación

28 minutos repartidos parejo, porque la nota es individual.

| Bloque | Quién | Min |
|---|---|---|
| Modelado, decisiones y los 5 niveles + demo de N1 | Matías | 6 |
| Métodos desinformados: dónde revienta cada uno | Celestino | 6 |
| La escalera de heurísticas y sus demostraciones | Fede | 8 |
| Análisis comparativo, barrido de w, el muro | Leo | 7 |
| Conclusiones, una por persona | los 4 | 2 |

Cierra con un **ensayo cruzado**: cada uno expone el bloque de otro. Donde
alguien se traba, ahí está el agujero real.
