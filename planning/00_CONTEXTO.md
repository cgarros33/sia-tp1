# 00 — Contexto del trabajo práctico

## Quiénes somos

Grupo de 4 de Sistemas de Inteligencia Artificial, ITBA:
Celestino Garrós (64375), Leo Weitz (64365), Federico Ruckauf (64356),
Matías Romanato (62072).

## Qué pide el enunciado

El TP tiene dos partes.

**Ejercicio 1 — 8-puzzle.** Conceptual, sin implementación. Pide estructura de
estado, al menos dos heurísticas admisibles no triviales, y qué métodos de
búsqueda se usarían y por qué. **Ya está resuelto y documentado aparte.** No es
parte del trabajo de este repositorio.

**Ejercicio 2 — Sokoban.** Es lo que implementa este repositorio. Requiere:

- Métodos: BFS, DFS, Greedy y A\*. IDDFS es opcional (lo hacemos igual).
- Al menos dos heurísticas admisibles distintas, comparables entre sí.
  Las no admisibles son opcionales (hacemos una, a propósito, para mostrar qué
  se rompe).
- Salida por corrida: éxito o fracaso, costo de la solución, cantidad de nodos
  expandidos, cantidad de nodos en la frontera, la solución completa desde el
  estado inicial hasta el final, y tiempo de procesamiento.
- Configuración por **archivo**, no hardcodeada.

## Cómo se evalúa — esto define todas las decisiones del proyecto

Aclaraciones que dieron los profesores en clase, y que pesan más que cualquier
otra consideración técnica:

- **No hay informe.** El entregable es una presentación oral de 25–30 minutos.
  El PDF de las diapositivas va en una carpeta del repositorio, pero los
  profesores **no lo leen**: evalúan lo que decimos.
- **La nota es individual, no grupal.** Hay que repartir la exposición para que
  los cuatro hablemos aproximadamente lo mismo, y cada uno tiene que poder
  responder sobre cualquier parte.
- **Lo más importante es justificar todo lo que se dice.** Textual: "si está
  justificado, por lo general está bien".
- **No hay que explicar teoría.** Nada de diapositivas sobre cómo funciona una
  cola FIFO. Se asume sabido. Se va directo a los resultados.
- **No mostrar código en la presentación.** Sí mostrar que las heurísticas son
  admisibles, y qué pasa con cada método y cada heurística.
- **Valoran la creatividad**, en particular explorar heurísticas distintas e
  interesantes, y comparar métodos entre sí para enriquecer el análisis.
- **Hay que mostrar la solución estado por estado**, no el resultado final.
- **Cuidado con las correlaciones.** Si se analiza cómo se relacionan dos
  variables, las variables tienen que tener sentido.
- **La narrativa importa.** Textual: seguir el hilo tipo "como esto nos pareció
  que no estaba tan bueno, entonces probamos con esto otro".

## Consecuencias prácticas para este repositorio

De lo anterior se desprende cómo hay que construir el proyecto:

1. **Cada decisión de diseño se documenta con su justificación.** No alcanza con
   que el código funcione: el grupo tiene que poder explicar por qué está hecho
   así y qué alternativa se descartó. Por eso existe la carpeta
   `docs/resumenes/`.

2. **Los experimentos se diseñan como una narrativa, no como una tabla.** Cada
   heurística nueva existe porque arregla un defecto **medido** de la anterior,
   y hay un nivel específico donde ese defecto se ve. Ver
   `docs/02_PLAN_DE_FASES.md`, Fase 4.

3. **Todo número que se muestre tiene que ser reproducible.** De ahí los tests
   de regresión y los números de oro (`docs/03_NUMEROS_DE_ORO.md`).

4. **El código lo escribe un agente, pero el grupo lo tiene que entender.** Por
   eso el protocolo de checkpoints: antes de escribir cualquier archivo que
   haga cuentas, el agente para y explica.

## Los cinco niveles

Salen de game-sokoban.com. **Ya están transcriptos y verificados**: el óptimo
que encuentra nuestro solver coincide exactamente con el récord humano
publicado en el sitio, en movimientos y en empujes. Cada uno está en el
repositorio con un comentario que dice de dónde salió y qué rol cumple.

| | Archivo | lid | Colección | Cajas | Celdas | Nodos BFS | Rol en la presentación |
|---|---|---|---|---|---|---|---|
| N1 | `n1_micro.sok` | 37953 | ABHT 02 · 01 | 1 | 12 | ~30 | Control de sanidad y demo estado por estado |
| N2 | `n2_akk04.sok` | 29619 | A.K.K. · 04 | 4 | 32 | ~4 × 10⁴ | El primero "real", barato para iterar |
| N3 | `n3_caminata.sok` | 953 | Microban · 29 | 2 | 35 | ~6 × 10³ | El punto ciego de la heurística |
| N4 | `n4_matching.sok` | 29617 | A.K.K. · 02 | 4 | 31 | ~6 × 10⁵ | Metas agrupadas: justifica el matching óptimo |
| N5 | `n5_limite.sok` | 8602 | Sasquatch XII · 06 | 4 | 41 | ~2 × 10⁶ | El límite del método |

**El orden N1 a N5 sigue la narrativa de la presentación, no el esfuerzo de
búsqueda.** N3 es más barato que N2 a pesar de ir después: tiene sólo 2 cajas,
pero introduce un concepto más avanzado (el punto ciego de la heurística) que
conviene contar recién después de haber mostrado un nivel de 4 cajas. En
conjunto la suite cubre cinco órdenes de magnitud de esfuerzo, de decenas de
nodos a millones.

El `lid` es el identificador del nivel en game-sokoban.com y está en la primera
línea de cada archivo. Sirve para verificar de un vistazo que no haya niveles
duplicados ni confundidos: **dos archivos con el mismo `lid` son el mismo
nivel**.

## Un nivel descartado que igual sirve

Probamos ABHT 02 · 03 (5 cajas, 89 celdas transitables, óptimo publicado de 155
movimientos). A\* con matching y poda de deadlocks expandió **3.000.000 de nodos
y su frontera iba por f = 76** cuando el óptimo es 155. El espacio de estados es
de 3,7 × 10⁹, contra 9,8 × 10⁵ de N4.

Ese experimento fallido es material de presentación: muestra dónde está el muro
y por qué. Si en algún momento se guarda en el repositorio, va en
`niveles/fuera_de_alcance/` y **no** entra en la batería de experimentos.
