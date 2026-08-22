# FASE 3 — Tests de regresión

**Estado:** terminada · **Fecha:** 2026-08-22

## En una frase

`pytest` congela el comportamiento del proyecto en 206 tests: 133 corren en
menos de 2 segundos y los 206 en 74, y el grupo puede refactorizar sabiendo que
si algo se rompe, un comando lo dice.

## Archivos creados

### `pytest.ini`

**Qué hace:** registra el marcador `lento`, fija `testpaths = tests` y `-ra`.

**Por qué existe:** para que `pytest -q -m "not lento"` sea una operación
soportada y no un truco, y para que el marcador no tire un warning en cada
corrida. Los warnings que aparecen siempre son warnings que nadie lee.

**La decisión importante:** **no hay ningún plugin ni opción de timeout, y es a
propósito.** Todo corte de una corrida es por `max_nodos`. Un test que depende
del reloj falla en la máquina lenta de un integrante y pasa en la del otro, y
eso destruye la confianza en la suite entera: apenas alguien vea un test que
falla "a veces", va a dejar de correr todos.

### `tests/conftest.py`

**Qué hace:** contiene `ESPERADO`, la tabla con TODOS los números del proyecto,
y las funciones que cargan un nivel y corren un método.

**Por qué existe:** si los números vivieran repartidos por los cuatro archivos de
tests, revisar uno significaría buscarlo en cuatro lugares y arriesgarse a
actualizar tres. Acá se revisa una vez. Es también el archivo que la Fase 4 va a
tocar: agregar h₂ es agregar un nombre a `HEURISTICAS_A_VERIFICAR` y una fila a
`informatividad` en cada nivel.

**La decisión importante:** **las corridas se cachean por sesión.** `correr()`
guarda el `Resultado` de cada par (nivel, método) y se lo devuelve a todos los
tests que lo pidan. No es cosmético: BFS en N5 son 2.028.239 nodos y entre 8 y 47
segundos según la máquina, y hay cuatro archivos de tests que necesitan ese mismo
resultado —optimalidad, regresión, camino ejecutable y heurísticas—. Sin caché la
suite correría BFS de N5 media docena de veces, tardaría más de cinco minutos y
nadie la correría nunca. Es seguro porque `Resultado` no se muta y porque los
métodos son determinísticos, y eso último no se asume: se testea.

Se descartó la fixture parametrizada idiomática de pytest
(`@pytest.fixture(params=NIVELES, scope='session')`). Obliga a que cada test
reciba el nivel por la fixture, y entonces marcar `lento` sólo N4 y N5 deja de
ser posible, porque la marca se aplica al test y no a cada valor del parámetro.
Con `parametros_niveles()` la marca viaja pegada al nivel, que es donde
corresponde.

### `tests/test_modelo.py`

**Qué hace:** 52 tests sobre el parser y el modelo de transición: estructura del
nivel, ida y vuelta, sucesores, reglas del juego y rechazo de niveles inválidos.

**Por qué existe:** es la capa de abajo. Si algo de acá falla, todo lo que mide la
búsqueda mide otro juego, y los números de la presentación serían de otro
problema. Sin estos tests, un error en el parser aparecería recién como "el
óptimo de N3 dio 106" y se buscaría durante horas en el motor.

**La decisión importante:** los niveles inválidos se construyen **como texto en
el test**, nunca como archivos en `niveles/`. Esa carpeta está verificada contra
los récords publicados y no se toca; además, un nivel roto guardado ahí sería una
invitación a que alguien lo use por error.

El test que más paga es el de **ida y vuelta**: dibujar el estado inicial, volver
a parsear el dibujo y obtener el mismo problema. Cierra el círculo entre el lector
y el escritor, y no es un test de laboratorio: el reproductor estado por estado de
la Fase 7 usa exactamente `dibujar()`.

### `tests/test_optimalidad.py`

**Qué hace:** 48 tests de verdad externa: BFS, A\*(h1) e IDDFS devuelven el costo
y los empujes publicados en game-sokoban.com, y las soluciones son ejecutables.

**Por qué existe:** son los únicos números del proyecto que no dependen de
nosotros. Si uno falla, hay un bug y no hay otra explicación posible: o el motor
está mal, o la heurística no es admisible, o el nivel se rompió.

**La decisión importante:** el **test de control del motor**, `A*(h0) ≡ BFS`, no
compara "parecido" sino **costo, nodos expandidos exactos y memoria máxima**. Con
h = 0 los dos métodos extraen los nodos en el mismo orden, así que expanden el
mismo conjunto y en la misma secuencia; que además coincida `memoria_maxima`
prueba que coinciden instante a instante y no sólo al final. Es lo que separa un
bug del motor de un bug de una heurística **antes** de empezar a mirar código: si
este test falla, no hay que mirar las heurísticas.

### `tests/test_regresion.py`

**Qué hace:** 54 tests sobre el comportamiento congelado: las cinco columnas de
BFS, el determinismo de los métodos, las afirmaciones sobre DFS, Greedy e IDDFS,
y el test de mutación deliberada.

**Por qué existe:** es la red propiamente dicha. Los nodos expandidos no tienen
verdad externa, pero sí tienen un valor conocido: el que se midió al cerrar la
Fase 2. Congelarlo convierte cualquier cambio de comportamiento en un test rojo.

**La decisión importante:** **si un valor de acá cambia, NO se actualiza el número
esperado.** Un número que se mueve después de un refactor es la señal de que el
refactor cambió el comportamiento. Puede ser una mejora legítima o puede ser un
bug, y el test no distingue: esa parte la hace una persona. El test compara el
dict de las cinco columnas de una sola vez, en vez de cinco aserciones sueltas,
porque ver **cuáles** se movieron y cuáles no es la mitad del diagnóstico: si
cambian expandidos y generados pero no la frontera, el orden de sucesores es
sospechoso; si cambia sólo la memoria, lo que cambió es la política de repetidos.

### `tests/test_heuristicas.py`

**Qué hace:** 52 tests de admisibilidad, consistencia, `h(meta) = 0` e
informatividad de h0 y h1 sobre los cinco niveles, reusando
`verificaciones/admisibilidad.py`.

**Por qué existe:** **es la infraestructura de la Fase 4.** Agregar h₂…h₅ es
agregar un nombre a una lista y una fila de informatividad por nivel; no se
escribe ningún test nuevo. Sin esto, cada heurística de la Fase 4 llegaría con su
propia verificación escrita a mano y comparar seis heurísticas dejaría de ser
comparar seis funciones bajo el mismo criterio.

**La decisión importante:** hay un **guardián de sincronización**,
`test_todas_las_heuristicas_del_registro_estan_verificadas`. Si alguien agrega h₂
a `HEURISTICAS` y se olvida de declararla, el test falla con el nombre de la que
falta y obliga a tomar la decisión explícitamente: o va a
`HEURISTICAS_A_VERIFICAR`, o va a `HEURISTICAS_NO_ADMISIBLES` —hoy vacía, la Fase
4 va a poner ahí la hₙₐ = 2·h₄—. Es la diferencia entre "no es admisible a
propósito" y "nadie la verificó", que es la diferencia entre una decisión y un
olvido.

### `tests/__init__.py`

**Qué hace:** convierte `tests/` en un paquete.

**Por qué existe:** con `__init__.py`, pytest agrega la raíz del repositorio a
`sys.path`, y entonces `import src...`, `import main` e `import
verificaciones...` funcionan sin instalar nada ni tocar `PYTHONPATH`. Un paso
manual de configuración es un paso que alguien va a olvidar.

## Archivos modificados

| Archivo | Qué cambió y por qué |
|---|---|
| `src/busqueda/motor.py` | **Sólo comentarios.** Se documentó en el campo `memoria_maxima` de `Resultado` por qué no es la suma de las otras dos columnas. Cero cambios de comportamiento: los 206 tests y la verificación de la Fase 2 dan idéntico. |

## Cuentas que se hacen acá

Ninguna nueva. Esta fase no introduce cálculos: verifica los de las fases 1 y 2.
Lo que sí hizo fue **auditar** una cuenta existente, `memoria_maxima`, que estaba
implementada y documentada a medias.

- **Qué calcula:** el pico de consumo de memoria del método a lo largo de la
  corrida, contado en nodos.
- **Fórmula:** `max` sobre toda la corrida de `len(frontera) + len(visitados)`,
  muestreado una vez por expansión (`motor.py`, en el cierre del bucle).
- **Por qué es correcta:** la memoria que ocupa un método en un instante es la
  frontera más la estructura de repetidos; el consumo del método es el peor de
  esos instantes. Medir sólo la frontera diría que IDDFS ahorra 55 veces cuando
  en realidad mudó la memoria de la pila al diccionario.
- **Qué se descartó:** `frontera_maxima + estados_visitados`, que es la suma de
  los picos y **no** el pico de la suma. Ver la sección siguiente.

### Por qué `memoria máx` no es la suma de las otras dos columnas

Alguien va a sumar las columnas y no le va a dar. En N2:
`2.691 + 46.779 = 49.470`, y la tabla dice `49.434`.

Instrumentamos el bucle de BFS y registramos en qué momento ocurre cada pico:

| Nivel | Pico de FRONTERA | Pico de MEMORIA | Suma de picos | `memoria_maxima` |
|---|---|---|---|---|
| `n1_micro` | expansión 27: 12 + 39 = 51 | expansión 38: 12 + 50 | 62 | **62** |
| `n2_akk04` | expansión 40.180: 2.691 + 42.871 = 45.562 | expansión 44.124: **2.655** + 46.779 | 49.470 | **49.434** |
| `n3_caminata` | expansión 2.174: 220 + 2.394 = 2.614 | expansión 6.356: **133** + 6.489 | 6.711 | **6.622** |

**Es el pico de la suma, no la suma de los picos.** La frontera de BFS alcanza su
máximo en el medio de la corrida y para entonces la estructura de visitados
todavía va por la mitad; cuando la suma llega a su máximo, la frontera ya empezó a
vaciarse. En N2 la diferencia son 36 nodos y en N3 son 89.

Hay una asimetría más que conviene saber al leer la tabla: **la columna
"visitados" ni siquiera es un pico**, es el valor *final* de la estructura,
medido después del bucle. Con política `'cerrado'` esa estructura sólo crece, así
que final = máximo, pero se está sumando un pico de mitad de corrida con un valor
de cierre.

**Y N1 no da exacto porque "los dos picos coincidan" en algún sentido profundo:**
en un pasillo de 12 celdas la frontera llega a 12 en la expansión 27 y **se queda
en 12 hasta la última**, la 38, que es justo cuando visitados llega a su valor
final de 50. Es una coincidencia de tamaño, no una propiedad. Queda escrito como
test (`test_en_n1_la_suma_da_exacto_y_en_n2_no`) para que la explicación no sea
una afirmación sin respaldo.

## Verificación

**Comandos:**

```
pytest -q -m "not lento"     # la que se corre a cada rato
pytest -q                    # la completa, antes de commitear
```

**Salida obtenida:**

```
$ pytest -q -m "not lento"
........................................................................ [ 54%]
.............................................................            [100%]
133 passed, 73 deselected in 1.69s

real	0m2.030s
```

```
$ pytest -q
........................................................................ [ 69%]
..............................................................           [100%]
206 passed in 73.81s (0:01:13)
```

Y la verificación de la Fase 2 sigue dando lo mismo que antes de esta fase, como
corresponde a un cambio que sólo tocó comentarios.

## La demostración de que la red funciona

"Los tests pasan" no dice nada por sí solo. Hay que romper algo a propósito y ver
que la suite lo dice. Lo hicimos dos veces, y la primera dio un resultado que no
esperábamos.

### Intento 1 — invertir `DIRECCIONES`: **no cambió ningún número**

El plan era invertir `DIRECCIONES` en `src/modelo/tablero.py` y ver caer los
tests de DFS. La suite completa dio **196 passed**, sin una sola falla, y BFS, DFS,
Greedy y A\* devolvieron **exactamente los mismos números** que con el orden
original.

**Encontramos un bug latente.** `Tablero._construir_tabla_de_movimientos()` arma
cada fila de `mover` con `append` recorriendo `DIRECCIONES`, así que la fila queda
indexada por la **posición dentro de esa tupla** y no por la constante de
dirección. Hoy coinciden porque `DIRECCIONES` es `(0, 1, 2, 3)`. Si se la
reordena, la tabla queda permutada y `mover[p][ARRIBA]` devuelve la celda de otra
dirección:

```
orden invertido  DIRECCIONES = (3, 2, 1, 0)
  mover[13][3] (R) = 7   pero la celda que corresponde a R es 14
  mover[13][0] (U) = 14  pero la celda que corresponde a U es 7
```

Y lo insidioso: `sucesores()` recorre esa misma tupla permutada, así que **las
dos permutaciones se cancelan** y la búsqueda genera exactamente la misma
secuencia de estados. Lo que se rompe en silencio es el **código de acción**:

```
yield accion=0 (NOMBRE_DIR dice U) pero el jugador se movió DERECHA
yield accion=3 (NOMBRE_DIR dice R) pero el jugador se movió ARRIBA
```

Ese `d` es el que `NOMBRE_DIR` traduce a la letra U/D/L/R de la solución. O sea:
la cadena de movimientos que imprime `main.py` —y el GIF de la Fase 7— mostrarían
movimientos que no son los que hizo la búsqueda, **con todos los tests en verde**,
porque `reconstruir_estados()` usa la misma convención equivocada y el camino
"cierra".

Agregamos los dos tests que lo detectan
(`test_la_tabla_de_movimientos_esta_indexada_por_direccion` y
`test_la_accion_devuelta_es_el_movimiento_que_ocurrio`). Con ellos, invertir
`DIRECCIONES` sí falla:

```
FAILED tests/test_modelo.py::test_la_tabla_de_movimientos_esta_indexada_por_direccion[n1_micro]
FAILED tests/test_modelo.py::test_la_tabla_de_movimientos_esta_indexada_por_direccion[n2_akk04]
FAILED tests/test_modelo.py::test_la_tabla_de_movimientos_esta_indexada_por_direccion[n3_caminata]
FAILED tests/test_modelo.py::test_la_accion_devuelta_es_el_movimiento_que_ocurrio[n1_micro]
FAILED tests/test_modelo.py::test_la_accion_devuelta_es_el_movimiento_que_ocurrio[n2_akk04]
FAILED tests/test_modelo.py::test_la_accion_devuelta_es_el_movimiento_que_ocurrio[n3_caminata]
6 failed, 127 passed, 73 deselected in 1.44s
```

**El comentario de `tablero.py:26-29` que dice "Cambiar esta tupla cambia los
números de DFS" es falso hoy**, y la corrección de una línea está pendiente de
decisión: ver "Qué quedó pendiente".

### Intento 2 — invertir el orden de generación de sucesores

Para probar que la red también atrapa un cambio de **comportamiento**, cambiamos
`for d in DIRECCIONES` por `for d in reversed(DIRECCIONES)` en
`Problema.sucesores()`, que sí reordena de verdad la generación:

```
FAILED tests/test_regresion.py::test_columnas_congeladas_de_bfs[n1_micro]
FAILED tests/test_regresion.py::test_columnas_congeladas_de_bfs[n2_akk04]
FAILED tests/test_regresion.py::test_columnas_congeladas_de_bfs[n3_caminata]
FAILED tests/test_regresion.py::test_en_n1_la_suma_da_exacto_y_en_n2_no
4 failed, 129 passed, 73 deselected in 1.37s
```

Con el detalle de N1:

```
E       AssertionError: assert {'estados_vis...dos': 30, ...} == {'estados_vis...dos': 38, ...}
E         Differing items:
E         {'memoria_maxima': 53} != {'memoria_maxima': 62}
E         {'estados_visitados': 41} != {'estados_visitados': 50}
E         {'nodos_generados': 75} != {'nodos_generados': 94}
E         {'nodos_expandidos': 30} != {'nodos_expandidos': 38}
```

**Y esto es exactamente lo que se quería ver:** cayeron los cinco valores de
regresión interna, y **no cayó ni un solo test de verdad externa**. El costo sigue
siendo 8, 45, 104, 70 y 306, y los empujes 5, 18, 22, 22 y 99. Tiene que ser así:
el óptimo no depende del orden en que se exploran los sucesores. Si el costo de
BFS hubiera cambiado, eso sí habría sido un bug.

Los dos cambios fueron revertidos y la suite volvió a **206 passed**.

## Números nuevos

Ninguno de la búsqueda: esta fase congela los de la Fase 2, no mide otros. Lo que
sí es nuevo es la **trayectoria temporal de los picos de memoria** de la tabla de
más arriba, y estos dos, que quedan congelados en `conftest.py`:

| Métrica | Valor | Estatus |
|---|---|---|
| Tests totales | 206 | — |
| Tests de la suite rápida | 133 en 1,7 s | criterio de aceptación: < 10 s |
| Suite completa | 206 en 74 s | — |
| Ahorro de frontera de IDDFS contra BFS | 55× en N2, **4,2× en N3** | congelado como `> 2×` |
| Trabajo extra de IDDFS contra BFS | 29× en N2, **158× en N3** | congelado como `> 10×` |
| Memoria total de IDDFS / BFS | 0,87 en N2, 0,98 en N3 | congelado como 0,5–1,2 |

Los dos números en negrita se midieron en esta fase. El ahorro de frontera de
IDDFS **no es una constante del método**: en N3, con 2 cajas y una solución de 104
movimientos, el árbol es tan angosto que ni BFS acumula mucha frontera y el
ahorro cae de 55× a 4,2×. El primer intento de test usaba un factor 10 fijo y
falló en N3, que es la clase de cosa por la que esta fase existe.

## Preguntas que esta fase habilita en el oral

- **¿Por qué el costo y los nodos expandidos no tienen el mismo estatus en los
  tests?** El costo es **verdad externa**: es el récord publicado por jugadores
  humanos en game-sokoban.com y no depende de nuestro código. Si un método óptimo
  no lo reproduce, hay un bug, punto. Los nodos expandidos son **una métrica de
  nuestra implementación**: dependen del orden de sucesores, del desempate de la
  frontera y de la política de repetidos, y no hay ninguna referencia externa
  contra la cual compararlos. Se congelan una vez y sirven para detectar cambios
  de comportamiento, no para decir si el comportamiento es correcto.

- **¿Por qué no testean tiempos?** Porque no son reproducibles. En la Fase 2, BFS
  en N5 dio 13,4 s y 46,6 s en la misma máquina con **idénticos 2.028.239 nodos**:
  un factor 3 de variación con cero variación de trabajo. Un test sobre eso
  fallaría al azar, y un test que falla al azar hace que la gente deje de correr
  la suite. Por el mismo motivo no hay ningún timeout: todo corte es por
  `max_nodos`, que es determinístico.

- **¿Por qué la afirmación sobre la memoria de IDDFS está corregida?** Los libros
  dicen que IDDFS usa mucha menos memoria que BFS, y en nuestra implementación es
  **falso**: 0,87× en N2 y 0,98× en N3, o sea ninguna ventaja apreciable. El
  motivo es que nuestro IDDFS mantiene estructura de visitados, porque sin ella,
  en Sokoban, las transposiciones lo hacen inviable; al guardarlos, la memoria se
  muda de la pila al diccionario y el ahorro desaparece. Lo que sí es cierto es
  que su **frontera** es mucho más chica (55× en N2) y que expande muchos más
  nodos (29× en N2). Testear la frase del libro habría sido testear el libro en
  vez de nuestro código, y habría fallado.

- **¿Por qué `memoria máx` no es la suma de `frontera máx` y `visitados`?**
  Porque es el **pico de la suma** y no la suma de los picos: los dos máximos no
  ocurren en el mismo instante. En N2 la frontera llega a 2.691 en la expansión
  40.180 y para entonces visitados va por 42.871; cuando la suma llega a su
  máximo, en la última expansión, la frontera ya bajó a 2.655. En N1 la suma da
  exacto por tamaño, no por una propiedad: en un pasillo de 12 celdas la frontera
  no llega a decrecer antes del final.

- **¿Cómo saben que los tests sirven de algo?** Rompimos el código a propósito
  dos veces. La segunda vez —invertir el orden de generación de sucesores— cayeron
  las cinco columnas congeladas de BFS en los tres niveles rápidos y **ningún**
  test de verdad externa, que es exactamente lo que corresponde. La primera vez
  —invertir `DIRECCIONES`— no cayó nada, y eso nos hizo encontrar un bug latente
  en la tabla de movimientos que habría hecho que la solución impresa mostrara
  letras equivocadas con la suite en verde.

- **¿Por qué el test de mutación cierra una celda en vez de abrir una pared?**
  Porque abrir no puede cambiar el óptimo. Abrir una celda nunca elimina un camino
  que ya existía, así que el óptimo sólo puede quedarse igual o bajar, y en N1
  ninguna apertura individual crea un atajo: probamos las 33 mutaciones
  pared→piso y ninguna mueve el 8. Cerrar sí lo rompe, en 7 de las 9 celdas de
  piso. Las otras 2 son los rincones de la fila 1, por los que la solución no
  pasa, y también están testeadas: que cerrarlas **no** cambie nada es lo que
  prueba que el test mide la criticidad de una celda concreta y no el simple hecho
  de haber tocado el archivo.

## Qué quedó pendiente

**La corrección del bug de `_construir_tabla_de_movimientos()`, a decidir por el
grupo.** El arreglo es indexar la fila por la constante de dirección en vez de por
la posición en `DIRECCIONES`:

```python
vecinos = [-1, -1, -1, -1]
for d in DIRECCIONES:
    ...
    vecinos[d] = -1 if destino in self.paredes else destino
```

Con `DIRECCIONES = (0, 1, 2, 3)` produce **exactamente la misma tabla**, así que
no mueve ni un número de oro. No se aplicó porque toca código de la Fase 1 y la
regla es una fase por vez. Los dos tests que lo detectan ya están en la suite: si
se aplica el arreglo, invertir `DIRECCIONES` pasa a cambiar los números de DFS, que
es lo que el comentario de `tablero.py` afirma hoy y no es cierto.

- **Heurísticas h₂ a h₅ y la no admisible** → Fase 4. La infraestructura está:
  `HEURISTICAS_A_VERIFICAR` y `HEURISTICAS_NO_ADMISIBLES` en `conftest.py`.
- **Deadlocks** → Fase 5. Cuando se activen, el test que hay que agregar es que el
  costo no cambie y los nodos bajen.
- **Runner y CSV** → Fase 6.

## Ideas para más adelante

- **IDDFS en N4 y N5 no se corre en ningún test.** Ahí agota los 3.000.000 de
  nodos, y eso ES un resultado del TP: se reporta en la Fase 6, no se testea acá.
  Vale la pena que el runner de la Fase 6 lo deje explícito en el CSV como
  `motivo_fin = max_nodos` y no como una celda vacía.
- El test de mutación se podría extender a los cinco niveles cerrando una celda
  del camino óptimo de cada uno. Con N1 alcanza para el criterio de aceptación, y
  en N4 y N5 costaría un BFS completo por celda.
- Cuando llegue la Fase 5, conviene un test de que la poda de deadlocks **no**
  cambia el conjunto de soluciones óptimas, y no sólo su costo.
