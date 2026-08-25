# FASE 6 — Runner, configuración y CSV

**Estado:** terminada · **Fecha:** 2026-08-23

## En una frase

Un script ejecutable (`python -m runner`) automatiza la matriz completa de experimentos (niveles × métodos × heurísticas × capas de poda × repeticiones) y vuelca los resultados crudos a un archivo CSV reproducible (`resultados.csv`) con escritura incremental y soporte para variabilidad en DFS.

## Archivos creados

### `runner/__init__.py`

**Qué hace:** Declara el paquete `runner`.

**Por qué existe:** Permite invocar la herramienta mediante `python -m runner` desde la raíz del proyecto sin modificar el `PYTHONPATH`.

**La decisión importante:** Mantener la lógica de ejecución automatizada aislada en su propia carpeta `runner/` para no contaminar `src/` (reservado al solver) ni `experimentos/` (reservado para análisis/graficado de la Fase 8).

### `runner/config_runner.json`

**Qué hace:** Especifica la matriz predeterminada de 645 corridas.

**Por qué existe:** Define la configuración completa de experimentos exigida por el TP: BFS con todas las capas de poda, DFS con las 24 permutaciones del orden de sucesores, e IDDFS, Greedy y A* con todas las heurísticas sobre la poda `completo`.

**La decisión importante:** Permitir múltiples entradas por método para habilitar configuraciones arbitrariamente granulares (ej. distintas heurísticas para distintos niveles), y desacoplar los límites de nodos (`max_nodos`) y tiempo (`timeout_s`) leyéndolos desde `config.json`.

### `runner/config_runner.example.json`

**Qué hace:** Versión de ejemplo documentada del archivo de configuración.

**Por qué existe:** Incluye la sección `"_comentarios"` con la explicación detallada de cada campo global y de matriz, para que cualquier integrante del grupo pueda armar configuraciones personalizadas sin consultar la especificación.

**La decisión importante:** Mantener las claves de comentarios con un prefijo `_` para que el validador del runner las ignore automáticamente.

### `runner/runner.py`

**Qué hace:** Carga la configuración, valida la matriz, genera la lista de tuplas de ejecución, ejecuta cada búsqueda y escribe inmediatamente cada fila resultante al CSV.

**Por qué existe:** Es la herramienta de automatización central de la Fase 6 que elimina la ejecución manual de experimentos.

**La decisión importante:** **Escritura incremental estado a estado.** Cada fila se escribe y se fuerza la descarga a disco (`flush()`) inmediatamente después de concluir una corrida. Si el script se interrumpe tras cientos de corridas, los resultados obtenidos no se pierden.

### `verificaciones/verificar_fase6.py`

**Qué hace:** Ejecuta las 5 comprobaciones del criterio de aceptación sobre el runner y el CSV generado.

**Por qué existe:** Proporciona un mecanismo auditable para comprobar que el runner funciona correctamente, produce columnas con los tipos requeridos, valida que los métodos óptimos mantengan los costos publicados y asegura que DFS reporte la variabilidad de sus 24 permutaciones.

**La decisión importante:** Usar directorios y archivos CSV temporales para las comprobaciones del runner, evitando sobrescribir o alterar archivos de datos del usuario o del proyecto.

### `tests/test_runner.py`

**Qué hace:** Implementa los tests de regresión para el runner divididos en tres marcas de rendimiento (`light`, `medium`, `completo`).

**Por qué existe:** Garantiza que los cambios futuros en el código no rompan la funcionalidad del runner ni la validez del CSV generado.

**La decisión importante:** Agrupar las pruebas con los marcadores de pytest `lento` y `completo` para permitir ejecuciones ultra rápidas durante el desarrollo diario (`pytest -q -m "not lento"`).

---

## Archivos modificados

| Archivo | Qué cambió y por qué |
|---|---|
| `src/modelo/problema.py` | Se agregaron el atributo `orden_direcciones` a `__slots__`, `__init__` y el bucle en `sucesores()`. Permite a DFS alterar el orden de generación de sucesores para evaluar sus 24 permutaciones sin romper la compatibilidad con el resto del proyecto. |
| `pytest.ini` | Se registró el marcador `completo` para clasificar ejecuciones masivas o pesadas del runner y la suite de tests. |
| `docs/resumenes/README.md` | Se actualizó el estado de la Fase 6 a "escrito". |

---

## Cuentas que se hacen acá

Ninguna. Esta fase no introduce cálculos ni agregaciones estadísticas. El runner genera únicamente **datos crudos (raw data)** en el CSV. Las métricas agregadas (promedios, desviaciones estándar, intervalos de confianza) y las visualizaciones se realizan en la Fase 8.

---

## Verificación

**Cómo se comprueba que está bien:**

```bash
python3 -m verificaciones.verificar_fase6
```

**Salida obtenida:**

```
Verificación de la Fase 6 — Runner, configuración y CSV

1. Comprobando generación de CSV válido (config reducida)...
28/28 corridas completadas en 0s. Salida: /tmp/tmpyprpru4g/salida_test.csv (28 filas).
   CSV válido: 17 columnas, formato y filas OK.

2. Comprobando exactitud de costos y comportamientos esperados...
74/74 corridas completadas en 31s. Salida: /tmp/tmpqd1333l5/salida_verif.csv (74 filas).
   Métodos óptimos: 24/24 corridas validadas contra números of oro.
   DFS en n1_micro: 24 permutaciones distintas generadas  OK
   DFS en n2_akk04: 24 permutaciones distintas, 18 costos distintos  OK
   IDDFS en n4_matching: motivo_fin='max_nodos'  OK
   IDDFS en n5_limite: motivo_fin='max_nodos'  OK

3. Ejecutando la suite de regresión pytest...
   pytest (-m 'not lento'): suite en verde  OK

==========================================
VERIFICACIÓN COMPLETA — TODOS LOS CHECKS EN VERDE
```

Además, la suite de pytest completa dio 398 pasados en verde:

```bash
python3 -m pytest -q
# Output: 398 passed in 198.31s (0:03:18)
```

---

## Números nuevos

La matriz por defecto genera **645 filas** en `resultados.csv` desglosadas de la siguiente manera:

| Bloque / Método | Configuración | Corridas totales |
|---|---|---|
| **BFS** | 5 niveles × 4 podas × 5 repeticiones | 100 |
| **DFS** | 5 niveles × 1 poda (`completo`) × 24 permutaciones | 120 |
| **IDDFS** | 5 niveles × 1 poda (`completo`) × 5 repeticiones | 25 |
| **Greedy** | 5 niveles × 8 heurísticas × 1 poda (`completo`) × 5 repeticiones | 200 |
| **A\*** | 5 niveles × 8 heurísticas × 1 poda (`completo`) × 5 repeticiones | 200 |
| **Total** | | **645** |

---

## Preguntas que esta fase habilita en el oral

- **¿Por qué el runner no calcula promedios ni desviaciones estándar directamente?**  
  Porque el principio de separabilidad y auditabilidad exige preservar los datos crudos (raw data) de cada corrida individual. De este modo, si se necesita re-evaluar o aplicar otros filtros estadísticos, no es necesario volver a ejecutar horas de búsquedas.

- **¿Por qué DFS requiere 24 corridas con permutaciones de direcciones y los otros métodos no?**  
  DFS es no óptimo y profundamente sensible al orden de expansión de sucesores. Evaluar las `4! = 24` permutaciones posibles de las 4 direcciones de movimiento revela la variabilidad real en el costo de la solución encontrada. Los métodos informados y BFS son determinísticos dada una frontera con desempate fijo.

- **¿Cómo se garantiza que una interrupción en medio de una matriz de 600+ ejecuciones no pierda datos?**  
  Mediante escritura incremental con `flush()` explícito tras cada corrida individual en el CSV.

- **¿Qué sucede si una configuración del runner asigna heurísticas a BFS?**  
  El runner emite una advertencia (*warning*) por stderr indicando la inconsistencia de configuración y procede ejecutando BFS sin evaluar heurísticas, evitando fallos catastróficos.

---

## Qué quedó pendiente

- **Visualización y tablas resumen (Fase 8):** Procesar `resultados.csv` para generar las 4 figuras obligatorias y el análisis de dominancia/rendimiento.
