# FASE 3 — Tests de regresión

**Dueño:** Celestino · **Estado:** pendiente

La red de seguridad del proyecto. Al terminar, el grupo puede refactorizar
durante dos semanas sabiendo que si algo se rompe, `pytest` lo dice.

---

## Por qué existe esta fase

Faltan seis fases y todas tocan `src/`. La Fase 4 mete seis heurísticas, la
Fase 5 conecta la poda de deadlocks al modelo de transición, la Fase 6 corre 65
experimentos. Cualquiera de esas puede cambiar silenciosamente un número que
después va a ir a una diapositiva.

Sin tests, la única forma de detectarlo sería correr la verificación de la Fase
2 a mano y comparar de memoria contra una salida vieja. Con tests, es un
comando.

---

## Archivos a crear

```
tests/__init__.py
tests/conftest.py
tests/test_modelo.py
tests/test_optimalidad.py
tests/test_regresion.py
tests/test_heuristicas.py
pytest.ini                 (o pyproject.toml con [tool.pytest.ini_options])
```

---

## Los dos niveles de exigencia

Esta distinción organiza toda la fase y hay que poder explicarla:

**Verdad externa — no se negocia.** Costo y empujes salen de los récords
publicados por jugadores en game-sokoban.com. No dependen de nuestra
implementación. Si un método óptimo devuelve otro número, hay un bug, punto.

**Regresión interna — se congela.** Nodos expandidos, generados, frontera y
memoria son métricas de *nuestra* implementación: dependen del orden de
sucesores, del desempate de la frontera y de la política de repetidos. No hay
verdad externa contra la cual compararlos. Se congelan una vez y a partir de ahí
sirven para detectar cambios de comportamiento.

> **Si un valor de regresión cambia, NO se actualiza el número esperado.**
> Se entiende primero por qué cambió. Puede ser una mejora legítima o puede ser
> un bug, y el test no distingue: esa parte la hace una persona.

---

## Valores a congelar

Medidos al cerrar la Fase 2, con corte por límite de nodos (determinístico) y
sin ningún timeout.

### Verdad externa

| Nivel | Cajas | Metas | Celdas | Costo | Empujes |
|---|---|---|---|---|---|
| `n1_micro` | 1 | 1 | 12 | **8** | **5** |
| `n2_akk04` | 4 | 4 | 32 | **45** | **18** |
| `n3_caminata` | 2 | 2 | 35 | **104** | **22** |
| `n4_matching` | 4 | 4 | 31 | **70** | **22** |
| `n5_limite` | 4 | 4 | 41 | **306** | **99** |

### Regresión interna — BFS

| Nivel | Expandidos | Generados | Frontera máx | Visitados | Memoria máx |
|---|---|---|---|---|---|
| `n1_micro` | 38 | 94 | 12 | 50 | 62 |
| `n2_akk04` | 44.124 | 112.849 | 2.691 | 46.779 | 49.434 |
| `n3_caminata` | 6.360 | 15.594 | 220 | 6.491 | 6.622 |
| `n4_matching` | 654.260 | 1.728.078 | 21.345 | 662.769 | 671.278 |
| `n5_limite` | 2.028.239 | 5.010.835 | 20.365 | 2.028.469 | 2.028.699 |

### Sucesores del estado inicial

| Nivel | Sucesores | De ellos, empujes |
|---|---|---|
| `n1_micro` | 2 | 0 |
| `n2_akk04` | 2 | 1 |
| `n3_caminata` | 3 | 0 |
| `n4_matching` | 2 | 0 |
| `n5_limite` | 1 | 0 |

---

## Antes de escribir los tests: confirmar y documentar `memoria_maxima`

La columna "memoria máx" **no es la suma de las otras dos**:

```
n2_akk04:   2.691 + 46.779 = 49.470,  pero la tabla dice 49.434
n1_micro:      12 +     50 =     62,  y la tabla dice        62
```

La explicación esperada es que se mide el **pico de la suma**, no la suma de los
picos: la frontera de BFS alcanza su máximo en el medio de la corrida y el
conjunto de visitados al final, así que los dos picos no coinciden en el tiempo.
Por eso en N1, que es diminuto, sí coinciden y la suma da exacto.

**Verificar que sea eso**, y si lo es, dejarlo escrito en el docstring de
`Resultado` y en el resumen de esta fase. Alguien va a sumar las dos columnas y
va a preguntar por qué no da.

Si resultara ser otra cosa, avisar antes de congelar nada.

---

## Qué tiene que testear cada archivo

### `conftest.py`

Fixtures compartidas: cargar un nivel por nombre, y las tablas de valores
esperados en un solo lugar. Que los números vivan en un único diccionario y no
repartidos por los tests: cuando haya que revisar uno, se revisa una vez.

Definir también el marcador `lento` para los tests que tardan más de un par de
segundos, y registrarlo en la configuración de pytest para que no tire warning.

### `test_modelo.py` — lo de la Fase 1, ahora automatizado

- Cajas, metas y celdas transitables coinciden con la tabla.
- Cajas y metas son la misma cantidad.
- Ida y vuelta: dibujar el estado inicial, volver a parsearlo, obtener el mismo
  problema.
- Cantidad de sucesores del estado inicial y cuántos son empuje.
- Ningún sucesor atraviesa una pared ni superpone dos cajas.
- El parser rechaza niveles inválidos: sin jugador, sin cajas, cajas ≠ metas.
  Construirlos como texto en el test, **no** como archivos en `niveles/`.

### `test_optimalidad.py` — verdad externa

- BFS devuelve el costo y los empujes publicados en los cinco niveles.
- **Test de control del motor:** A\*(h0) coincide con BFS en costo, en nodos
  expandidos **exactos** y en memoria máxima. Es la invariante que separa un bug
  del motor de un bug de una heurística: si falla, no hay que mirar las
  heurísticas.
- La solución es ejecutable: pasar las acciones por `reconstruir_estados()`,
  verificar que el último estado es meta y que hay `costo + 1` estados.
- IDDFS devuelve el óptimo en los niveles donde termina (N1, N2, N3).

### `test_regresion.py` — comportamiento congelado

- Las cinco columnas de BFS, exactas, en los cinco niveles.
- **Determinismo:** dos corridas seguidas del mismo método sobre el mismo nivel
  dan idénticos nodos expandidos. Este test existe por una razón concreta: con
  corte por reloj, IDDFS daba 3.453.866 y 1.798.624 en dos corridas. El corte
  por límite de nodos lo arregló, y este test evita que alguien reintroduzca un
  timeout sin darse cuenta.
- **Métodos no óptimos, con la afirmación precisa:**
  - DFS: costo ≥ óptimo **siempre**. Si diera menor, sería un bug grave.
  - DFS: costo **estrictamente** mayor en N2, N3 y N4. N1 es excepción
    documentada: es un pasillo sin ramificación real y DFS da el óptimo con
    los 24 órdenes posibles de sucesores.
  - Greedy: expande menos nodos que BFS y su costo es ≥ al óptimo. Que en N1 y
    N2 dé el óptimo no contradice nada: Greedy no da garantía, no da lo
    contrario de la garantía.
- **IDDFS, con la afirmación corregida:** *no* testear que use mucha menos
  memoria que BFS, porque es falso en nuestra implementación (0,87× en N2,
  0,98× en N3). Testear lo que sí es cierto: su frontera es mucho más chica que
  la de BFS, pero su memoria total es comparable, porque mantiene estructura de
  visitados. Y que expande muchos más nodos.

### `test_heuristicas.py` — admisibilidad y consistencia

Reusar los helpers de `verificaciones/admisibilidad.py`:

- Para h0 y h1, sobre los cinco niveles: admisible y consistente a lo largo del
  camino óptimo. El argumento de por qué el camino óptimo alcanza para verificar
  admisibilidad —el costo restante desde `sᵢ` es exactamente `L − i`— va escrito
  en el docstring del módulo de tests.
- `h(estado meta) == 0` para las dos.
- La informatividad `h(s₀)/óptimo` no baja de los valores medidos. Es la métrica
  que la Fase 4 va a usar para mostrar la dominancia entre heurísticas:
  `h0` da 0,000 en los cinco; `h1` da 0,125 · 0,089 · 0,019 · 0,057 · 0,013.

**Este archivo es la infraestructura de la Fase 4.** Dejalo preparado para que
agregar una heurística sea agregar una entrada a una lista parametrizada, no
escribir tests nuevos.

---

## Reglas para los tests

**Sin timeouts. Nunca.** Todo corte es por `max_nodos`, que es determinístico.
Un test que depende del reloj falla en la máquina lenta de un integrante y pasa
en la del otro, y eso destruye la confianza en la suite entera.

**Sin aserciones sobre tiempos.** Los tiempos varían un factor 3 en la misma
máquina con los mismos nodos (medido en la Fase 2: BFS en N5 dio 13,4 s y
46,6 s con idénticos 2.028.239 nodos). No se testean.

**Marcar los lentos.** Todo lo que toque N4 o N5 lleva `@pytest.mark.lento`.
Tiene que poder correrse la suite rápida en menos de 10 segundos:

```
pytest -q -m "not lento"     # la que se corre a cada rato
pytest -q                    # la completa, antes de commitear
```

---

## Criterio de aceptación

**1. `pytest -q` en verde**, con la cuenta de tests que pasan.

**2. `pytest -q -m "not lento"` termina en menos de 10 segundos.**

**3. El test de mutación deliberada.** Un test que copia `n1_micro.sok` a un
directorio temporal, le cambia **una** pared por piso, y verifica que el óptimo
deja de ser 8. Es la comprobación de que la suite realmente detecta un nivel
alterado y no está pasando por casualidad.

Usar `tmp_path` de pytest. **Nunca** tocar `niveles/`.

**4. Una demostración de que la suite atrapa una regresión real.** Introducir a
mano un cambio de comportamiento en el motor —por ejemplo invertir el orden de
`DIRECCIONES`—, correr la suite, mostrar qué tests fallan, y revertirlo. Pegar
esa salida en el resumen.

Esto no es un test: es la evidencia de que la red funciona. Sin esto, "los tests
pasan" no dice nada.

---

## Cosas que NO van en esta fase

- Heurísticas nuevas → Fase 4. Acá sólo se testean h0 y h1.
- Deadlocks → Fase 5.
- El runner de experimentos → Fase 6.

---

## Al terminar

1. Mostrá la salida de `pytest -q` y de `pytest -q -m "not lento"` con sus
   tiempos.
2. Mostrá la salida del criterio 4: qué tests fallan al invertir `DIRECCIONES`.
3. Escribí `docs/resumenes/FASE_3_RESUMEN.md`. En "Preguntas que esta fase
   habilita en el oral" incluí por lo menos: por qué costo y nodos expandidos
   tienen distinto estatus, por qué no se testean tiempos, y por qué la
   afirmación sobre la memoria de IDDFS se corrigió.
4. Listá los archivos creados y **esperá**. No commitees.
