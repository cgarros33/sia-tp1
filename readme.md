# Trabajo Práctico Nº1 de Sistemas de Inteligencia Artificial

Sokoban resuelto con métodos de búsqueda clásicos, informados y no informados.

## Integrantes

- Celestino Garrós - Legajo 64375
- Leo Weitz - Legajo 64365
- Federico Ignacio Ruckauf - Legajo 64356
- Matías Romanato - Legajo 62072

---

## Instalación

Requiere **Python 3.11 o superior** (probado en 3.12).

```bash
python3 -m venv .venv
source .venv/bin/activate          # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Las dependencias son cinco y cada una tiene un motivo acotado: `numpy` y
`scipy` para el matching húngaro de las heurísticas h₃/h₄, `Pillow` para dibujar
los tableros y los GIF, `matplotlib` para las figuras de análisis y `pytest`
para la suite de regresión. El motor de búsqueda en sí (`src/busqueda/`,
`src/modelo/`) no usa nada fuera de la biblioteca estándar.

Si te olvidás de instalar, `main.py` intenta hacerlo solo la primera vez.

---

## Correr una búsqueda

El motor se configura **por archivo**, no por línea de comandos:

```bash
python main.py                      # usa config.json
python main.py mi_config.json       # usa otro archivo
```

Los flags existen para probar rápido mientras se trabaja y **pisan** al archivo:

```bash
python main.py --nivel niveles/n3_caminata.sok --metodo astar --heuristica h5 --deadlocks completo
```

### Qué imprime

```
Nivel:       niveles/n1_micro.sok  (1 cajas, 12 celdas)
Método:      bfs
Poda:        ninguno
----------------------------------------------------------------
Resultado:              ÉXITO
Costo de la solución:   8 movimientos (5 empujes)
Nodos expandidos:       38
Nodos generados:        94
Nodos en la frontera:   11 al terminar   (12 como máximo)
Estados visitados:      50
Memoria máxima:         62 nodos (frontera + visitados)
Tiempo de procesamiento: 0.000 s

Solución (8 movimientos):
  RRURDDDD
```

La solución se imprime como una cadena de `U`/`D`/`L`/`R` (arriba, abajo,
izquierda, derecha). Para ver el tablero paso a paso, mirá
[Reproductor](#reproductor-estado-por-estado).

Cuando no hay solución, la línea de resultado distingue **por qué**: el espacio
se agotó (el nivel es irresoluble), se acabó el tiempo, o se alcanzó el límite
de nodos. No es lo mismo y el informe lo reporta como cosas distintas.

Código de salida: `0` si encontró solución, `1` si no, `2` si la configuración
está mal escrita.

---

## El archivo de configuración

`config.json` acepta exactamente estas nueve claves. Una clave desconocida
**aborta la corrida** en vez de ignorarse: un `"heurstica"` mal tipeado daría
una corrida perfectamente exitosa que no es la que se pidió.

```json
{
  "nivel": "niveles/n4_matching.sok",
  "metodo": "astar",
  "heuristica": "h1",
  "deadlocks": "ninguno",
  "timeout_s": 300,
  "max_nodos": 3000000,
  "limite_profundidad": null,
  "w": 0.5,
  "mostrar_solucion": true
}
```

| Clave | Valores | Qué hace |
|---|---|---|
| `nivel` | ruta a un `.sok` | ver [Niveles](#niveles) |
| `metodo` | `bfs`, `dfs`, `iddfs`, `iddfs_puro`, `greedy`, `astar`, `hpa` | ver [Métodos](#métodos-de-búsqueda) |
| `heuristica` | `h0`…`h5`, `hna`, `hna4` | sólo la usan `greedy`, `astar` y `hpa` |
| `deadlocks` | `ninguno`, `estaticos`, `congelados`, `completo` | ver [Poda](#poda-de-deadlocks) |
| `timeout_s` | segundos | corte por tiempo |
| `max_nodos` | entero | corte determinístico por nodos expandidos |
| `limite_profundidad` | entero o `null` | sólo lo usa `dfs` |
| `w` | 0 a 1 | sólo lo usa `hpa` |
| `mostrar_solucion` | `true`/`false` | imprimir o no la secuencia de movimientos |

---

## Métodos de búsqueda

Los siete métodos comparten **un solo bucle de búsqueda** (`src/busqueda/motor.py`)
y se diferencian únicamente por la estructura de la frontera. Esa es la decisión
de arquitectura que hace justa la comparación: todos corren exactamente el mismo
código salvo esa clase.

| Nombre | Frontera | ¿Óptimo? |
|---|---|---|
| `bfs` | FIFO | sí, porque todo movimiento cuesta 1 |
| `dfs` | LIFO | no — encuentra *una* solución, no la mejor |
| `iddfs` | LIFO con límite creciente | sí |
| `iddfs_puro` | igual, pero sin tabla de visitados | sí, pero sólo termina en N1 |
| `greedy` | prioridad por `h` | no |
| `astar` | prioridad por `g + h` | sí, si `h` es admisible |
| `hpa` | prioridad por `(1−w)·g + w·h` | sí sólo si `w ≤ 0.5` |

`hpa` recorre el espectro completo con un solo número: `w=0` es costo uniforme,
`w=0.5` es A\* reescalado y `w=1` es Greedy.

`iddfs_puro` es el IDDFS de manual, sin tabla de transposiciones. No sirve para
resolver: existe para poder **medir** el intercambio entre memoria y trabajo
repetido, que es el resultado interesante del método.

---

## Heurísticas

Cada eslabón arregla un defecto medido del anterior. La demostración de
admisibilidad de cada una está escrita en el docstring de su módulo, en
`src/heuristicas/`.

| | Qué calcula | Admisible | Arregla |
|---|---|---|---|
| `h0` | 0 | sí | — (control: A\*(h₀) debe igualar a BFS) |
| `h1` | cajas fuera de meta | sí | — (línea de base) |
| `h2` | Σ Manhattan a la meta más cercana | sí | h₁ no distingue cerca de lejos |
| `h3` | matching óptimo con Manhattan | sí | h₂ asigna varias cajas a la misma meta |
| `h4` | matching con distancias reales de empuje | sí | h₃ atraviesa paredes |
| `h5` | h₄ + término del jugador | sí | las anteriores ignoran al jugador |
| `hna` | 2·h₄ | **no** | nada: es el experimento de control |
| `hna4` | 4·h₄ | **no** | nada: es el experimento de control |

Las dos últimas son **no admisibles a propósito**, para mostrar qué se rompe
cuando se pierde la garantía de optimalidad. Y no se rompe lo mismo en las dos:
`hna` devolvió el óptimo igual en los cinco niveles —que no prueba nada, porque
lo que se perdió es la *garantía*—, mientras que `hna4` sí da soluciones
subóptimas, 47 contra 45 en N2 y 82 contra 70 en N4, terminando 33 veces más
rápido.

---

## Poda de deadlocks

Un deadlock es un estado desde el cual el nivel ya es irresoluble. Podarlos no
rompe la optimalidad de A\*: los estados eliminados no admiten ninguna solución,
así que ningún camino óptimo pasa por ellos.

- `ninguno` — sin poda. Es la corrida de referencia.
- `estaticos` — celdas muertas, precalculadas una vez por nivel.
- `congelados` — bloques de 2×2 de cajas y paredes que ya no se pueden mover.
- `completo` — las dos anteriores.

Las dos reglas **no se dominan entre sí**: cada una detecta casos que la otra
no ve. Está medido en `docs/resumenes/FASE_5_RESUMEN.md`.

---

## Niveles

Los cinco niveles de `niveles/` están transcritos de colecciones publicadas y
**verificados contra los récords humanos de game-sokoban.com**:

| Archivo | Colección | Cajas | Movimientos | Empujes |
|---|---|---|---|---|
| `n1_micro.sok` | ABHT 02 · 01 | 1 | 8 | 5 |
| `n2_akk04.sok` | A.K.K. · 04 | 4 | 45 | 18 |
| `n3_caminata.sok` | Microban · 29 | 2 | 104 | 22 |
| `n4_matching.sok` | A.K.K. · 02 | 4 | 70 | 22 |
| `n5_limite.sok` | Sasquatch XII · 06 | 4 | 306 | 99 |

Si un método óptimo devuelve un costo distinto al de esta tabla, hay un bug.

Formato XSB: `#` pared, `@` jugador, `$` caja, `.` meta, `+` jugador sobre meta,
`*` caja sobre meta, espacio piso.

---

## La matriz completa de experimentos

Corre todos los niveles por todos los métodos y vuelca el CSV:

```bash
python -m runner.runner                                  # config por defecto, sale a resultados.csv
python -m runner.runner mi_matriz.json -o otro.csv
```

La matriz se define en `runner/config_runner.json` (hay un
`config_runner.example.json` comentado al lado). El `resultados.csv` del
repositorio son 645 corridas y tarda un rato largo: está commiteado justamente
para no tener que regenerarlo.

Criterio de repeticiones: BFS, IDDFS, Greedy y A\* son **determinísticos**, así
que los nodos y el costo se miden una sola vez y promediarlos no tendría
sentido. Lo que se repite es el **tiempo**. DFS es el único con variabilidad
real —depende del orden de sucesores— y se corre con todas las permutaciones de
direcciones.

---

## Reproductor estado por estado

Genera los GIF animados y las tiras de fotogramas de `presentacion/`:

```bash
python -m verificaciones.verificar_fase7
```

Sale doble: **GIF** para la presentación (corre solo, sin riesgo de demo en
vivo) y **tira de fotogramas clave** para el PDF, que no anima. También imprime
la tira de N1 en texto plano, para poder revisarla sin abrir ningún archivo.

Las soluciones que reproduce salen siempre de **BFS**, no de A\*: dos soluciones
igual de óptimas en movimientos pueden diferir en la cantidad de empujes, y los
empujes de BFS son los que están contrastados contra los récords publicados.

---

## Gráficos y análisis

```bash
python -m experimentos.barrido_w        # genera experimentos/barrido_w.csv
python -m experimentos.graficos         # genera presentacion/figuras/ (PNG + PDF)
```

`graficos.py` lee `resultados.csv` y `barrido_w.csv`; no vuelve a correr
ninguna búsqueda. Las cuatro figuras son: nodos expandidos por método y nivel en
escala logarítmica, dominancia empírica, el barrido de `w` de 0 a 1, y el muro
de los niveles grandes.

---

## Tests

```bash
pytest                          # la suite completa, ~3.5 minutos
pytest -m "not lento"           # saltea N4, N5 e IDDFS sobre N2/N3
pytest -m "not completo"        # saltea las corridas más pesadas
```

416 tests. Fijan los **números de oro**: si un cambio en `src/` rompe un costo
publicado o mueve una pared de un `.sok`, la suite se pone en rojo.

Los costos y empujes están validados contra los récords humanos (verdad externa,
no se negocian). Los nodos expandidos son una métrica de nuestra
implementación: se congelaron una vez medidos y sirven para detectar
regresiones, no porque haya un valor "correcto" externo.