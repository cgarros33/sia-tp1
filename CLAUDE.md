# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

TP1 de Sistemas de Inteligencia Artificial (ITBA): Sokoban resuelto con métodos
de búsqueda clásicos. Python 3.11+, sin frameworks de IA.

## Idioma

**Todo en español**: código, nombres de variables y funciones, docstrings,
documentos y respuestas al usuario. Es el idioma en el que el grupo rinde el
oral.

## Reglas que no se negocian

Están completas en `REGLAS.md` y `docs/01_REGLAS_DE_TRABAJO.md`. Las que más se
rompen sin querer:

1. **Nunca `git commit` ni `git push`** (ni `merge`, `rebase`, `reset`,
   `checkout <rama>`, `stash`, `gh pr create`). Leer sí: `status`, `diff`,
   `log`, `show`. Al terminar, listá los archivos tocados y **esperá**.
2. **Nunca te agregues como coautor** ni firmes nada (`Co-Authored-By`,
   `Generated with Claude Code`) en commits, código o documentación.
3. **Pará y explicá antes de escribir cualquier archivo que calcule algo**
   (heurísticas, pesos, fórmulas, métricas, agregaciones). Protocolo de
   checkpoint en `docs/01_REGLAS_DE_TRABAJO.md`, regla 3.
4. **Al cerrar una fase**, escribí `docs/resumenes/FASE_N_RESUMEN.md` según
   `docs/resumenes/_PLANTILLA.md`.
5. **No toques `niveles/*.sok`**: están verificados contra los récords de
   game-sokoban.com. Si uno parece mal, avisá.
6. **No agregues dependencias** fuera de las cinco de `requirements.txt`
   (`numpy`, `scipy`, `Pillow`, `matplotlib`, `pytest`) sin preguntar.
7. **El código va sin comentarios** y con docstrings de una línea. Se comenta
   sólo una cuenta que no se lee del código o una regla que si alguien la borra
   rompe algo. El porqué va a `docs/resumenes/`, nunca al `.py`.
8. **Una fase por vez**, y sólo la que el usuario indique.

## Comandos

```bash
python main.py                       # resuelve usando config.json
python main.py mi_config.json        # otro archivo de configuración
python main.py --nivel niveles/n3_caminata.sok --metodo astar --heuristica h6 --deadlocks completo

pytest                               # suite completa (~3.5 min, 416 tests)
pytest -m "not lento"                # saltea N4, N5 e IDDFS sobre N2/N3
pytest -m "not completo"             # saltea las corridas más pesadas
pytest tests/test_optimalidad.py::test_control_del_motor_astar_h0_es_bfs   # un test solo

python -m runner.runner                        # matriz completa -> resultados.csv
python -m runner.runner mi_matriz.json -o otro.csv

python -m experimentos.barrido_w     # -> experimentos/barrido_w.csv
python -m experimentos.graficos      # lee los dos CSV -> presentacion/figuras/

python -m verificaciones.verificar_fase1   # ... hasta verificar_fase8
```

`main.py` se configura **por archivo** (`config.json`, nueve claves exactas: una
clave desconocida aborta la corrida); los flags pisan al archivo y existen para
probar rápido. Código de salida: `0` con solución, `1` sin solución, `2`
configuración inválida.

Los `verificaciones/verificar_faseN.py` son los chequeos narrados de cada fase
(imprimen y devuelven código de salida); `tests/` es la suite de regresión.
`verificar_fase7` es además lo que regenera los GIF y las tiras de
`presentacion/`.

## Arquitectura

**Un solo bucle de búsqueda para todos los métodos.** `src/busqueda/motor.py`
implementa `buscar()`; los siete métodos (`bfs`, `dfs`, `iddfs`, `iddfs_puro`,
`greedy`, `astar`, `hpa`) se diferencian sólo por la **frontera** que le pasan y
la **política de repetidos**. Esa es la decisión que hace justa la comparación:
tocar `motor.py` cambia a los siete a la vez.

- `frontera.py`: `FronteraFIFO` (BFS), `FronteraLIFO` (DFS/IDDFS),
  `FronteraPrioridad(peso_g, peso_h)` — A\* es `(1,1)`, Greedy `(0,1)`, HPA
  `(1−w, w)`. Sólo `FronteraPrioridad` tiene `usa_heuristica = True`.
- Políticas de repetidos: `CERRADO` (conjunto de visitados), `MEJOR_G`
  (diccionario estado→mejor g, necesario para que A\* sea óptimo) y `CAMINO`
  (chequeo contra los ancestros, sin memoria: es `iddfs_puro`).
- `algoritmos.py`: las funciones por método más `resolver()`, que despacha por
  nombre y es la puerta de entrada de `main.py` y del runner. `iddfs` envuelve
  llamadas sucesivas a `buscar()` con límite creciente y **acumula** las
  métricas de todas las iteraciones.
- `Resultado` (en `motor.py`) es el dataclass con todas las métricas.
  `memoria_maxima` es el pico de (frontera + visitados), no la suma de los picos.
  `motivo_fin` distingue `meta` / `sin_solucion` / `timeout` / `max_nodos`: un
  fracaso por corte **no** dice que el nivel sea irresoluble.

**Modelo** (`src/modelo/`), separado en estático y dinámico:

- `Tablero`: paredes, metas, dimensiones. Precalcula `mover[p][d]` → celda
  destino o `-1` si es pared o borde. Las posiciones son **enteros lineales**
  (`fila * ancho + col`); `coordenadas()`/`indice()` sólo para entrada/salida.
- `Estado`: `jugador: int` + `cajas: frozenset[int]`, con el hash cacheado.
  Inmutable y hasheable: es la clave de todas las estructuras de visitados.
- `Problema.sucesores()` genera `(accion, estado_siguiente, hubo_empuje)` en el
  orden de `orden_direcciones` (fijo por defecto; el runner lo permuta para
  medir la variabilidad de DFS). **La poda de deadlocks se aplica acá**, al
  generar el sucesor, no al expandirlo.
- `parser_xsb.py`: formato XSB (`#` pared, `@` jugador, `$` caja, `.` meta,
  `+` jugador sobre meta, `*` caja sobre meta).

**Heurísticas y deadlocks son fábricas.** `construir(nombre, problema)` en
`src/heuristicas/registro.py` devuelve una función `h(estado) -> int` que ya
tiene precalculadas sus tablas del nivel (`distancias.py`: BFS de empuje,
Manhattan, celdas muertas). Igual `src/deadlocks.py`: `construir(nombre,
tablero)` devuelve `detectar(cajas, caja_movida) -> bool`, o `None` para
`ninguno`. Para agregar una heurística: módulo nuevo + entrada en el diccionario
`HEURISTICAS`; para un detector, entrada en `DETECTORES`. La demostración de
admisibilidad de cada heurística vive en el docstring de su módulo, y
`verificaciones/admisibilidad.py` la comprueba empíricamente sobre un camino
óptimo.

`hna`/`hna4` (2·h₅ y 4·h₅) son **no admisibles a propósito**: son el
experimento de control sobre qué se pierde al romper la garantía. No las
"arregles".

**Runner y análisis.** `runner/runner.py` recorre la matriz de
`runner/config_runner.json` y vuelca `resultados.csv` (17 columnas, una fila por
corrida). `experimentos/graficos.py` **sólo lee** los CSV, nunca vuelve a
correr una búsqueda. `resultados.csv` y las figuras están commiteados a
propósito: son la evidencia y no se regeneran para cada cambio.

## Los números de oro

`docs/03_NUMEROS_DE_ORO.md` es la tabla que nunca se rompe, y
`tests/conftest.py` (`ESPERADO`) es el **único** lugar donde viven los valores
esperados de la suite. Dos niveles de exigencia distintos:

- **Verdad externa, no se negocia**: costo y empujes de los cinco niveles
  (N1 8/5, N2 45/18, N3 104/22, N4 70/22, N5 306/99), contrastados contra los
  récords humanos. Si un método óptimo devuelve otro costo, hay un bug.
- **Regresión interna**: nodos expandidos, generados, frontera y memoria. No hay
  un valor "correcto" externo; se congelaron una vez medidos para detectar
  regresiones. Si un cambio los mueve, hay que **entender por qué** antes de
  actualizarlos.

Test de control del motor: A\*(h₀) tiene que expandir lo mismo que BFS.

No hay timeouts en la suite y es a propósito: todo corte es por `max_nodos`,
que es determinístico y da lo mismo en la máquina de cada integrante.

## Mapa de documentos

- `docs/00_CONTEXTO.md` — qué pide la cátedra y cómo se evalúa
- `docs/01_REGLAS_DE_TRABAJO.md` — reglas normativas del agente (con el porqué)
- `docs/02_PLAN_DE_FASES.md` — el mapa de las ocho fases
- `docs/03_NUMEROS_DE_ORO.md` — la tabla de verificación
- `docs/fases/FASE_N_*.md` — especificación detallada de cada fase
- `docs/resumenes/FASE_N_RESUMEN.md` — qué se hizo, por qué y qué se descartó
- `readme.md` — el manual de uso para los cuatro integrantes
