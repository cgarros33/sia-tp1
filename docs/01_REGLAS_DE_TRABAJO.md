# 01 — Reglas de trabajo del agente

Este documento es normativo. Ante cualquier duda entre "hacer algo útil" y
"cumplir una de estas reglas", gana la regla.

---

## 1. Git: leer sí, escribir nunca

**Prohibido sin excepción:**

```
git commit        git push         git merge
git rebase        git reset        git checkout <rama>
git stash         git tag          gh pr create
```

**Permitido siempre:** `git status`, `git diff`, `git log`, `git show`.

Cuando termines un bloque de trabajo, cerrá con un resumen así:

```
Listo. Archivos creados:
  src/modelo/tablero.py
  src/modelo/estado.py
Archivos modificados:
  main.py
Verificación: los 5 niveles siguen dando el costo esperado.

No commiteé nada. Revisalo y commiteá vos cuando quieras.
```

**Por qué esta regla existe.** El repositorio es la evidencia de que el trabajo
lo hicieron cuatro personas. Los profesores pueden mirar el historial. Un
historial con commits automáticos, o con muchos commits seguidos del mismo
autor a las 3 de la mañana, cuenta una historia que no queremos contar. Además,
commitear antes de que alguien lea el cambio rompe la regla del proyecto de que
nada entra sin que un humano lo entienda.

## 2. Autoría: el trabajo es del grupo

**Nunca** agregues, ni sugieras agregar, ninguna de estas líneas:

```
Co-Authored-By: Claude <noreply@anthropic.com>
🤖 Generated with Claude Code
Co-authored-by: Claude Code
```

Tampoco en comentarios de código, docstrings, encabezados de archivo, README,
CHANGELOG ni mensajes de commit sugeridos.

Si el usuario te pide que redactes un mensaje de commit, redactalo limpio, sin
firma de ningún tipo, y aclarale que lo ejecute él.

**Por qué.** La nota es individual y se defiende oralmente. La autoría del
trabajo académico es de las cuatro personas que lo van a rendir.

## 3. Checkpoint: parar antes de cualquier archivo que calcule

Antes de escribir un archivo que **decida, pondere, puntúe, estime, agregue o
compare numéricamente**, tenés que parar y explicar. Concretamente aplica a:

- Heurísticas (`src/heuristicas/*`)
- Detección de deadlocks (`src/deadlocks.py`)
- Fórmulas de prioridad de la frontera y sus pesos
- Métricas derivadas (factor de ramificación efectivo, ratios de dominancia)
- Agregaciones estadísticas del runner (medias, desvíos, cuántas corridas)
- Cualquier gráfico que relacione dos variables

**Formato del checkpoint:**

```
CHECKPOINT — voy a escribir src/heuristicas/h3_matching.py

QUÉ CALCULA
  <en dos o tres oraciones, sin código>

POR QUÉ ASÍ
  <qué problema del enfoque anterior resuelve>

POR QUÉ ES ADMISIBLE
  <la demostración, en dos renglones, que va a ir en la presentación>

QUÉ SE DESCARTÓ
  <la alternativa evaluada y el motivo>

CÓMO SE VERIFICA
  <el test o la comparación que prueba que está bien>

¿Avanzo?
```

Después esperá respuesta. No escribas el archivo hasta que te digan que sí.

**Por qué.** Los profesores preguntan sobre cualquier parte, a cualquiera de los
cuatro. Un archivo que hace cuentas que el grupo no puede explicar es peor que
no tenerlo: es una pregunta que no se va a poder responder en el oral.

## 4. Resúmenes: uno por fase, en `docs/resumenes/`

Al terminar cada fase, escribí `docs/resumenes/FASE_N_RESUMEN.md` siguiendo
`docs/resumenes/_PLANTILLA.md`. Tiene que estar escrito para alguien que **no
vio el código**: los otros tres integrantes lo van a leer para entender qué
existe y por qué.

Regla dura: **todo archivo nuevo aparece en el resumen de su fase**, con una
línea sobre qué hace y un párrafo sobre por qué existe. Si un archivo no
justifica un párrafo, probablemente no debería existir.

## 5. Dependencias

Autorizadas en `src/`: sólo la biblioteca estándar de Python, más `numpy` y
`scipy` (esta última exclusivamente para `linear_sum_assignment`, el matching
húngaro de la Fase 4).

Autorizada en `src/viz/` y **sólo ahí**: `Pillow`, exclusivamente para escribir
imágenes y GIF (el reproductor de la Fase 7). Ese paquete es entrada/salida y no
participa de la búsqueda: nada de `src/modelo/` ni de `src/busqueda/` lo importa.
La regla existe para que la búsqueda sea nuestra, y dibujar un tablero no compite
con eso.

Autorizadas en `experimentos/` y `tests/`: además `matplotlib`, `pandas` y
`pytest`.

**Prohibidas:** cualquier biblioteca que implemente búsqueda, heurísticas o
resolución de Sokoban. El TP consiste en implementar eso. Usar una biblioteca
que lo resuelva es entregar el trabajo de otro.

Si creés que hace falta algo más, preguntá antes de instalarlo.

## 6. Alcance: una fase por vez

No adelantes trabajo de fases posteriores aunque sea tentador. Si mientras
hacés la Fase 2 se te ocurre algo de la Fase 5, anotalo en el resumen de la
fase bajo "Ideas para más adelante" y seguí.

**Por qué.** Cada fase tiene un criterio de aceptación verificable. Si se
mezclan, cuando algo falla no se sabe qué lo rompió.

## 7. Verificación: los números de oro mandan

Después de cualquier cambio en `src/`, corré la verificación de
`docs/03_NUMEROS_DE_ORO.md`. Si un número cambió:

1. **No** actualices el valor esperado.
2. Avisá qué cambió y cuál pensás que es la causa.
3. Esperá indicación.

Un número que cambia después de un refactor es la señal de que el refactor
cambió el comportamiento. Puede estar bien o mal, pero hay que entender cuál de
las dos antes de seguir.

## 8. El código va sin comentarios

El código se explica solo. Los nombres son largos y en castellano justamente
para eso, y quien lo lee ya sabe leer Python. **Las explicaciones viven en
`docs/resumenes/`**: qué se construyó, por qué existe cada archivo, qué decisión
hay detrás y qué alternativa se descartó. Ahí es donde el grupo las va a buscar,
y ahí es donde tienen espacio para estar bien escritas.

Un comentario se justifica sólo en dos casos:

- **Una cuenta que no se lee del código.** Por qué una constante vale lo que
  vale, por qué una condición está en un bucle, qué se eligió cuando había dos
  opciones numéricas posibles.
- **Una regla que, si alguien la borra, rompe algo.** Ejemplo real: la cláusula
  "alguna caja fuera de meta" del detector de cuadrados de 2x2. Sin ella se
  poda el estado meta de `n4_matching` y el nivel devuelve "sin solución".

Todo lo demás sobra.

```python
# MAL - describe lo que ya se ve
# recorremos las cuatro direcciones
for d in DIRECCIONES:

# MAL - es una explicación de diseño: eso va al resumen de la fase
# El orden de DIRECCIONES es fijo a propósito porque DFS depende del orden en
# que se generan los sucesores, así que fijarlo es lo que lo hace reproducible.
for d in DIRECCIONES:

# BIEN - una condición que el código no explica por sí solo
# Empujar exige que la celda de atrás esté libre: ahí va el jugador.
if mover[q][d] == -1:
```

**Docstrings: uno de una línea** por módulo, clase y función, diciendo qué es.
Nada de secciones "QUÉ REPRESENTA", "LA DECISIÓN DE DISEÑO" o "QUÉ SE DESCARTÓ"
dentro de un archivo `.py`.

Única excepción: cuando una spec de `docs/fases/` pide explícitamente que algo
quede escrito en un docstring. Son cuatro casos, todos señalados en el resumen
de la fase que los pidió.

La documentación no desapareció, se
mudó a `docs/resumenes/`, que es su lugar. El código se limpió en la misma
pasada en que se cambió la regla.

## 9. Cuando algo no cierra

Si una especificación de `docs/fases/` te parece equivocada, incompleta o
contradictoria: **decilo antes de implementarla**. Preferimos discutir una
decisión diez minutos que descubrir en el oral que estaba mal fundada.
