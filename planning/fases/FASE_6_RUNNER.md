# FASE 6 — Runner, configuración y CSV

**Dueño:** Cele · **Estado:** pendiente

Correr la matriz completa de experimentos — todos los niveles por todos los
métodos, con sus heurísticas, capas de poda y repeticiones — y volcar los
resultados crudos a un CSV reproducible. Al terminar, un solo comando produce
`resultados.csv` con toda la matriz, y cada fila es verificable contra los
números de oro.

---

## Archivos a crear

```
runner/__init__.py
runner/runner.py
runner/config_runner.json
runner/config_runner.example.json
verificaciones/verificar_fase6.py
tests/test_runner.py
```

Y modificar `src/modelo/problema.py`, `tests/conftest.py` y `pytest.ini`.

---

## `config_runner.json` — la matriz de experimentos

Un JSON que describe **qué corridas hacer**. Cada entrada de `"matriz"` define
un bloque de corridas: un método, con qué heurísticas, sobre qué niveles, con
qué capas de poda. Se permiten **varias entradas para el mismo método** con
distintas combinaciones, lo que da la granularidad para cosas como "A\* usa h₀,
h₂, h₄ en N2 y N4, y h₁, h₃, h₅ en N1, N3 y N5".

### Estructura

```json
{
  "runs": 5,
  "separador_decimal": ".",
  "encoding": "utf-8",
  "intervalo_progreso_s": 15,
  "matriz": [
    {
      "metodo": "bfs",
      "niveles": ["n1_micro", "n2_akk04", "n3_caminata", "n4_matching", "n5_limite"],
      "deadlocks": ["ninguno", "estaticos", "congelados", "completo"]
    },
    {
      "metodo": "dfs",
      "niveles": ["n1_micro", "n2_akk04", "n3_caminata", "n4_matching", "n5_limite"],
      "deadlocks": ["completo"],
      "todas_las_direcciones": true
    },
    {
      "metodo": "iddfs",
      "niveles": ["n1_micro", "n2_akk04", "n3_caminata", "n4_matching", "n5_limite"],
      "deadlocks": ["completo"]
    },
    {
      "metodo": "greedy",
      "heuristicas": ["h0", "h1", "h2", "h3", "h4", "h5", "hna", "hna4"],
      "niveles": ["n1_micro", "n2_akk04", "n3_caminata", "n4_matching", "n5_limite"],
      "deadlocks": ["completo"]
    },
    {
      "metodo": "astar",
      "heuristicas": ["h0", "h1", "h2", "h3", "h4", "h5", "hna", "hna4"],
      "niveles": ["n1_micro", "n2_akk04", "n3_caminata", "n4_matching", "n5_limite"],
      "deadlocks": ["completo"]
    }
  ]
}
```

### Campos globales

| Campo | Tipo | Default | Qué hace |
|---|---|---|---|
| `runs` | int | 5 | Repeticiones por tupla (nivel, método, heurística, poda). Para medir tiempo con media y desvío. Se ignora en entradas con `todas_las_direcciones`. |
| `separador_decimal` | string | `"."` | `"."` o `","`. Sólo afecta al CSV. |
| `encoding` | string | `"utf-8"` | Encoding del CSV de salida. |
| `intervalo_progreso_s` | int | 15 | Cada cuántos segundos se imprime una línea de progreso por pantalla. |

`max_nodos` y `timeout_s` se leen del `config.json` del proyecto (el mismo que
usan `main.py` y los tests), no se duplican acá. Es el mismo límite para toda
la matriz, porque un número que depende de qué script lo corra no es un
número reproducible.

### Campos por entrada de `"matriz"`

| Campo | Obligatorio | Default | Qué hace |
|---|---|---|---|
| `metodo` | sí | — | Uno de `METODOS` de `algoritmos.py`: `bfs`, `dfs`, `iddfs`, `iddfs_puro`, `greedy`, `astar`, `hpa`. |
| `niveles` | sí | — | Lista de nombres de nivel (sin `.sok`). |
| `heuristicas` | no | `[]` | Lista de nombres de heurística. Para métodos no informados se **ignora con un warning**, no se aborta. Para métodos informados es obligatoria si no es `[]`. |
| `deadlocks` | no | `["completo"]` | Lista de capas de poda. Cada combinación (nivel, heurística, poda) se ejecuta. |
| `runs` | no | el global | Pisa el valor global para esta entrada. |
| `todas_las_direcciones` | no | `false` | Sólo para DFS. Genera las 24 permutaciones de `DIRECCIONES` y corre cada una una vez, ignorando `runs`. |

### Validación

- Clave desconocida en el JSON → **aborta**, igual que `main.py`.
- `metodo` no existe en `METODOS` → aborta.
- `heuristicas` con un nombre no registrado → aborta.
- `niveles` con un archivo que no existe → aborta.
- `deadlocks` con un nombre no registrado → aborta.
- `heuristicas` no vacía en un método no informado → **warning** por stderr,
  corre el método sin heurística.
- `todas_las_direcciones` en un método que no es DFS → warning, se ignora.
- Tuplas duplicadas entre entradas distintas → **warning**, se corren igual.
  Es responsabilidad del usuario; el runner no filtra.

---

## `config_runner.example.json` — la versión documentada

Una copia del `config_runner.json` con los mismos valores por defecto, pero con
un campo `"_comentarios"` que explica cada campo. No lo lee el runner; existe
para que alguien del grupo pueda armar una config a medida sin abrir la
especificación.

---

## `runner/runner.py` — el script

### Invocación

```bash
python -m runner                           # usa runner/config_runner.json
python -m runner otra_config.json          # usa otro archivo
python -m runner -o mis_resultados.csv     # cambia el archivo de salida
python -m runner otra.json -o salida.csv   # las dos cosas
```

Salida por defecto: `resultados.csv` en el directorio actual.

### Qué hace

1. Lee `config_runner.json` y `config.json` (para `max_nodos` y `timeout_s`).
2. Enumera todas las tuplas `(nivel, método, heurística, poda, corrida)` que
   implica la matriz, contándolas.
3. Para cada tupla:
   - Carga el nivel, construye el `Problema` con la poda y el orden de
     direcciones que corresponda.
   - Construye la heurística si el método es informado.
   - Llama a la función del método (de `src/busqueda/algoritmos.py`).
   - Escribe la fila al CSV **inmediatamente**, no al final. Si el proceso se
     corta, las corridas ya hechas no se pierden.
4. Cada `intervalo_progreso_s` segundos imprime por stderr una línea de
   progreso:

   ```
   [  42/645]  ejecutando: n3_caminata · A*(h4) · completo · corrida 3    (2m 15s)
   ```

5. Al terminar imprime un resumen: total de corridas, tiempo total, filas
   escritas.

### DFS con `todas_las_direcciones`

Genera las `4! = 24` permutaciones de `(ARRIBA, ABAJO, IZQUIERDA, DERECHA)`
con `itertools.permutations`. Para cada una:

- Construye un `Problema` con `orden_direcciones=permutación` (ver la
  modificación a `problema.py` abajo).
- Corre DFS **una sola vez** con esa permutación.
- Escribe una fila con la columna `orden_sucesores` indicando el orden usado
  (por ejemplo `UDLR`, `DLRU`).

El campo `runs` se ignora para estas entradas: son 24 corridas por nivel, una
por permutación.

---

## Modificación a `src/modelo/problema.py`

Para que DFS pueda correr con distintos órdenes de sucesores.

### El cambio

Agregar `orden_direcciones` a `Problema.__init__`, con default `DIRECCIONES`:

```python
__slots__ = ('tablero', 'inicial', 'detector_deadlocks', 'orden_direcciones')

def __init__(self, tablero, inicial, detector_deadlocks=None, orden_direcciones=None):
    ...
    # El orden en que sucesores() genera las acciones. DIRECCIONES por defecto.
    # DFS depende de este orden: cambiarlo cambia qué solución encuentra. Con
    # las 24 permutaciones posibles se mide la variabilidad real de DFS.
    self.orden_direcciones = orden_direcciones if orden_direcciones is not None else DIRECCIONES
```

Y en `sucesores()`:

```python
for d in self.orden_direcciones:    # era: for d in DIRECCIONES
```

Son 3 líneas. Con `orden_direcciones=None` (el default) el comportamiento es
**idéntico** al actual: los 385 tests existentes pasan sin cambios, los números
de oro no se mueven, y todo el código que construye un `Problema` sin ese
parámetro sigue funcionando igual.

**Por qué acá y no en el runner.** El orden de sucesores es una propiedad del
problema, no del motor. Si viviera en el runner, el motor recibiría un problema
que genera los sucesores en un orden y el runner le pediría otro: los dos
estarían mintiendo.

**Lo que NO se toca.** `reconstruir_estados()` sigue usando
`self.orden_direcciones` porque llama a `self.sucesores()`, que ya usa el
campo. Y `src/busqueda/` no se toca en absoluto.

---

## El CSV de salida

### Columnas

| # | Columna | Tipo | Ejemplo | Notas |
|---|---|---|---|---|
| 1 | `nivel` | str | `n3_caminata` | Nombre del nivel, sin `.sok`. |
| 2 | `metodo` | str | `A*` | Nombre legible del método (el de `Resultado.metodo`). |
| 3 | `heuristica` | str | `h5` | Nombre de la heurística, o `—` si no aplica. |
| 4 | `deadlocks` | str | `completo` | Capa de poda usada. |
| 5 | `corrida` | int | `3` | Número de corrida, 1-indexado. |
| 6 | `orden_sucesores` | str | `UDLR` | Orden de direcciones usado. `—` si no es DFS con variabilidad. |
| 7 | `exito` | bool | `True` | Si encontró solución. |
| 8 | `motivo_fin` | str | `meta` | `meta`, `sin_solucion`, `timeout`, `max_nodos`. |
| 9 | `costo` | int/vacío | `70` | Costo de la solución. Vacío si `exito=False`. |
| 10 | `empujes` | int/vacío | `22` | Empujes de la solución. Vacío si `exito=False`. |
| 11 | `nodos_expandidos` | int | `52766` | |
| 12 | `nodos_generados` | int | `139178` | |
| 13 | `frontera_maxima` | int | `3841` | |
| 14 | `frontera_final` | int | `1203` | |
| 15 | `estados_visitados` | int | `53199` | |
| 16 | `memoria_maxima` | int | `56040` | frontera + visitados |
| 17 | `tiempo_s` | float | `0.483` | Tiempo de la corrida individual. |

El separador de columnas es `,`. El separador decimal es el del config.

Las filas se escriben **una por una**, en el orden en que se ejecutan. Las
repeticiones de la misma tupla quedan como filas separadas: la agregación
(media, desvío) es trabajo de la Fase 8, no de esta.

### Filas esperadas con la config por defecto

| Bloque | Corridas |
|---|---|
| BFS: 5 niveles × 4 podas × 5 runs | 100 |
| DFS: 5 niveles × 1 poda × 24 permutaciones | 120 |
| IDDFS: 5 niveles × 1 poda × 5 runs | 25 |
| Greedy: 5 niveles × 8 heurísticas × 1 poda × 5 runs | 200 |
| A\*: 5 niveles × 8 heurísticas × 1 poda × 5 runs | 200 |
| **Total** | **645** |

---

## Progreso por pantalla

Cada `intervalo_progreso_s` segundos (configurable, default 15), el runner
imprime por **stderr** una línea con el formato:

```
[  42/645]  ejecutando: n3_caminata · A*(h4) · completo · corrida 3    (2m 15s)
```

`n/m` es la cantidad de corridas completadas sobre el total. El tiempo es el
transcurrido desde el inicio. Va por stderr para que stdout quede limpio si
alguien redirige la salida.

Al terminar:

```
645/645 corridas completadas en 18m 32s. Salida: resultados.csv (645 filas).
```

---

## Recordatorio: esta fase lleva un checkpoint

`docs/01_REGLAS_DE_TRABAJO.md`, regla 3, nombra las "agregaciones estadísticas
del runner" entre los archivos que llevan checkpoint. El runner en sí no agrega
—escribe filas crudas—, pero la verificación calcula resúmenes (cuántas
corridas por grupo, media y desvío de tiempo), así que el checkpoint aplica al
script de verificación si introduce algún cálculo no trivial.

---

## Criterio de aceptación

`verificaciones/verificar_fase6.py`, que produce la salida legible para el
grupo:

**1. El runner produce un CSV válido.** Se corre con una config reducida (sólo
N1, una corrida por método) y se verifica que el CSV existe, tiene las 17
columnas, que los tipos son los correctos y que no hay filas incompletas.

**2. Todos los métodos óptimos dan el costo publicado.** En todas las filas
donde `exito=True` y el método es óptimo (BFS, IDDFS, A\* con heurística
admisible), el costo coincide con el número de oro. Lo mismo para los empujes.
Greedy, DFS y A\* con hna/hna4 quedan exentos porque no son óptimos.

**3. DFS con las 24 permutaciones produce 24 filas por nivel.** Cada una con
un `orden_sucesores` distinto. El costo puede variar entre permutaciones y eso
es un resultado, no un error.

**4. IDDFS en N4 y N5 termina con `motivo_fin = 'max_nodos'`.** Es un resultado
esperado del TP, no un fallo del runner. El CSV lo registra con `exito=False`.

**5. Los números de las Fases 1 a 5 no se movieron.** `pytest -q` sigue dando
los mismos 385 passed. El cambio a `problema.py` no mueve nada porque el
default de `orden_direcciones` es `DIRECCIONES`.

Salida esperada (la real, medida):

```
Verificación de la Fase 6 — runner y CSV

1. CSV válido con config reducida (N1, 1 run por método)
   5 métodos × 1 nivel = XX filas escritas, 17 columnas, tipos OK

2. Costos de métodos óptimos
   BFS: 5/5 niveles coinciden con el número de oro
   IDDFS: 3/3 niveles resueltos coinciden (N4 y N5: max_nodos, esperado)
   A*(admisibles): XX/XX coinciden

3. DFS con 24 permutaciones
   n1_micro: 24 filas, 24 órdenes distintos, costo constante = 8  (1 valor)
   n2_akk04: 24 filas, rango de costo [X..Y]  (K valores distintos)
   ...

4. IDDFS en N4: max_nodos OK, IDDFS en N5: max_nodos OK

5. pytest -q: 385+ passed, 0 failed

Verificación completa.
```

---

## Tests — `tests/test_runner.py`

Tres niveles de cobertura, organizados con los marcadores `lento` y `completo`.

### Suite light — `pytest -q -m "not lento"`

Es la que se corre a cada rato. Usa sólo N1 a N3 y un subconjunto chico de
configuraciones.

- **`test_csv_valido`**: corre el runner sobre N1 con una config mínima
  (BFS + A\*(h1), 1 run, poda `completo`), verifica que el CSV tiene las 17
  columnas, los tipos correctos y las filas esperadas.
- **`test_costos_optimos_light`** (parametrizado por N1, N2, N3): corre BFS
  y A\*(h5) con `completo`, verifica que el costo es el publicado.
- **`test_dfs_24_ordenes_light`** (N1): corre DFS con
  `todas_las_direcciones`, verifica 24 filas, 24 órdenes distintos, todos
  con `exito=True`.

### Suite medium — `pytest -q -m "not completo"`

Agrega N4 y N5, pero **sin BFS** (que es el método más pesado con diferencia).

- **`test_costos_optimos_medium`** (N4, N5, marcados `lento`): corre
  A\*(h5) con `completo`, verifica costo publicado.
- **`test_iddfs_max_nodos`** (N4, N5, marcados `lento`): corre IDDFS,
  verifica `motivo_fin = 'max_nodos'` y `exito=False`.
- **`test_dfs_24_ordenes_medium`** (N4, N5, marcados `lento`): verifica
  24 filas y que hay variabilidad en el costo.

### Suite completa — `pytest -q`

Agrega las corridas pesadas de BFS.

- **`test_costos_bfs_completo`** (N4, N5, marcados `lento` + `completo`):
  BFS sobre N4 y N5 sin poda, verifica costo publicado.

### Modificaciones a archivos existentes

| Archivo | Cambio |
|---|---|
| `pytest.ini` | Registrar el marcador `completo`. |
| `tests/conftest.py` | Ninguno. Los tests del runner usan su propia config reducida y su propio CSV temporal, no pisan la caché de corridas existente. |

---

## Cosas que NO van en esta fase

- **El barrido de `w` (HPA) → Fase 8.** `hpa()` existe y funciona; el
  experimento con el barrido de pesos es la Fase 8.
- **Agregaciones estadísticas (media, desvío, tablas resumen) → Fase 8.** El
  runner escribe filas crudas. Quien lee el CSV y produce las figuras es la
  Fase 8.
- **Gráficos → Fase 8.**
- **`iddfs_puro` no está en la config por defecto.** Sólo termina en N1. Se
  puede agregar en la config si se quiere, pero no entra en la matriz estándar.

---

## Al terminar

1. Corré `python -m runner` con la config por defecto y mostrá el resumen de
   progreso y el conteo de filas del CSV.
2. Corré `python3 -m verificaciones.verificar_fase6` y mostrá la salida.
3. Corré `python3 -m pytest -q -m "not lento"` y mostrá que los tests pasan.
4. Corré `python3 -m pytest -q` y mostrá que los 385+ tests siguen en verde.
5. Escribí `docs/resumenes/FASE_6_RESUMEN.md` siguiendo la plantilla.
6. Listá los archivos creados y modificados y **esperá**. No commitees.
