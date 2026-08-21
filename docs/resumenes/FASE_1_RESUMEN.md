# FASE 1 — Modelo del problema

**Estado:** terminada · **Fecha:** 2026-08-20

## En una frase

Los cinco niveles se leen del disco, se convierten en un modelo con lo estático
separado de lo dinámico, se vuelven a dibujar idénticos y generan sucesores
legales; todavía no hay ninguna búsqueda.

## Archivos creados

### `src/modelo/tablero.py`

**Qué hace:** guarda lo que no cambia nunca de un nivel —paredes, metas,
dimensiones— y precalcula la tabla `mover[p][d]` de a dónde se llega desde cada
celda en cada dirección. Además dibuja un estado en formato XSB.

**Por qué existe:** es la mitad estática del modelo, y la razón por la que la
Fase 2 va a ser viable. Hay un solo `Tablero` por nivel y todos los nodos lo
comparten por referencia. Si no existiera —si las paredes y las metas vivieran
adentro de cada estado— cada uno de los ~2.000.000 de estados que BFS expande en
N5 cargaría su propia copia de las paredes, y el hash del estado, que se
consulta una vez por nodo generado, tendría que recorrerlas siempre.

**La decisión importante:** **separar lo estático de lo dinámico.** Todo lo demás
del módulo son consecuencias de haberla tomado primero:

- *Posiciones linealizadas* (`p = fila * ancho + columna`, no tuplas). El motor
  pregunta millones de veces "¿hay una caja en `p`?" contra un `frozenset`:
  hashear un `int` es una operación primitiva, hashear una tupla implica
  combinar los hashes de sus dos componentes. Se paga en legibilidad, y se
  compensa con `coordenadas()` e `indice()`, que se usan sólo para
  entrada/salida.
- *Tabla de movimientos precalculada.* Validar una acción pasa a ser un acceso a
  una tupla en vez de recalcular límites y consultar el conjunto de paredes.
- *`DIRECCIONES` con orden fijo y explícito.* DFS depende del orden en que se
  generan los sucesores: fijarlo acá es lo que hace que el método sea
  reproducible entre corridas. Cambiar esa tupla cambia los números de DFS.

La alternativa descartada es la matriz de caracteres (`list[list[str]]`) que
mezcla paredes, metas y cajas: cómoda para imprimir, pésima para buscar. Es
mutable —y por lo tanto no hasheable—, copiarla cuesta O(alto × ancho) por
sucesor, y obliga a distinguir "caja sobre meta" de "caja" en cada consulta.

**Aclaración fijada en el código:** `transitables` es **toda celda del rectángulo
que no es pared**, sin filtro de alcanzabilidad. Es la definición que usa la
fórmula de estimación del espacio de estados de `docs/03_NUMEROS_DE_ORO.md`, y
la que da 12/32/35/31/41. **No** es lo mismo que "alcanzable por el jugador": en
`n2_akk04.sok`, con las cajas en su posición inicial, el jugador sólo alcanza 3
de esas 32 celdas.

### `src/modelo/estado.py`

**Qué hace:** representa una foto de la partida: posición del jugador más un
`frozenset` con las posiciones de las cajas, con el hash calculado una sola vez.

**Por qué existe:** es la mitad dinámica, y es la clave del diccionario de
visitados del motor. Todo lo que está acá adentro se copia millones de veces, así
que cada byte y cada operación de hash importan. Si el estado fuera más gordo o
más lento de hashear, N5 no entraría en memoria ni en tiempo.

**La decisión importante:** las cajas son un **`frozenset`**, por dos razones
distintas que conviene no mezclar en el oral. La primera es técnica: sólo los
objetos inmutables se pueden hashear —el hash se deriva del contenido, así que si
el contenido pudiera cambiar después de guardado el objeto quedaría archivado en
una posición de la tabla que ya no le corresponde y sería irrecuperable—, y sin
hash la consulta "¿ya visité esto?" pasaría de O(1) a O(n). La segunda es de
modelado: **las cajas son indistinguibles**, así que dos configuraciones que
difieren sólo en el orden en que las enumeramos son *el mismo estado del juego*.
Un conjunto captura esa simetría por construcción; con una lista habría que
normalizar el orden antes de cada comparación, y olvidarse de hacerlo
significaría expandir muchas veces el mismo estado sin darse cuenta.

Descartado: `numpy.ndarray`, que es mutable —por lo tanto no hasheable— y cuyo
operador de igualdad devuelve un arreglo de booleanos elemento a elemento en vez
de un `bool`, así que ni siquiera se puede usar en un `if`.

El hash se cachea en `__init__` porque CPython **no** cachea el de las tuplas: lo
recalcula en cada consulta. `__slots__` evita el `__dict__` por instancia, que
con millones de estados vivos es memoria que importa.

### `src/modelo/parser_xsb.py`

**Qué hace:** lee un nivel en formato XSB —el estándar de Sokoban y el que usa
game-sokoban.com— y devuelve `(Tablero, Estado inicial)`. Lanza `NivelInvalido`
si el nivel no es jugable.

**Por qué existe:** es la única frontera del proyecto donde un nivel todavía es
texto. Que esté aislado en un módulo es lo que permite el test de ida y vuelta:
dibujar y volver a parsear tiene que dar el mismo problema. Los comentarios `;`
de los archivos —que documentan de dónde salió cada nivel y cuál es el récord
publicado— se ignoran al leer pero se conservan en el archivo.

**La decisión importante:** **validar y fallar temprano.** Si no hay jugador, si
hay más de uno, si no hay cajas, si la cantidad de cajas no coincide con la de
metas o si aparece un carácter que no es del formato, se aborta con un mensaje
que dice exactamente qué pasa y en qué fila y columna. La alternativa
"tolerante" —tratar lo desconocido como piso— es la que convierte un typo en el
archivo en un número equivocado en la presentación.

Dos detalles del formato que están resueltos acá: las **filas cortas se rellenan
con pared**, porque muchos editores recortan los espacios finales y sin ese
relleno quedarían agujeros en el borde por donde el jugador se escaparía; y por
la misma razón los espacios finales se descartan al leer, así que el tablero es
el primer bloque de líneas no vacías del archivo.

### `src/modelo/problema.py`

**Qué hace:** arma los cinco componentes del problema bien definido —estado
inicial, acciones, modelo de transición, costo y condición de meta— y agrega
`reconstruir_estados()`, que reejecuta una secuencia de acciones desde el
inicial.

**Por qué existe:** es el contrato con el motor genérico de la Fase 2. El motor
no va a saber qué es una pared: sólo va a pedir sucesores y preguntar si un
estado es meta. Esa separación es lo que hace que los cinco métodos corran
exactamente el mismo modelo y que la comparación entre ellos sea justa por
construcción.

**La decisión importante:** **una acción es un movimiento del jugador, no un
empuje.** El enunciado pide optimizar cantidad de movimientos, así que todo
movimiento cuesta 1, empuje o no. Como el costo es uniforme, `g(n)` coincide con
la profundidad del nodo y BFS ya resulta óptimo, que es justamente lo que permite
usarlo como verdad de referencia contra los récords publicados.

La alternativa evaluada y descartada —hay que poder explicarla— es la
optimización clásica de Sokoban: normalizar al jugador a un representante de su
región alcanzable y buscar sobre **empujes**. Reduce muchísimo el espacio de
estados y es lo que usan los solvers serios. **La descartamos porque optimiza
otra métrica:** una solución con menos empujes puede necesitar más movimientos
del jugador entre empujes consecutivos, y el enunciado pide minimizar
movimientos. Se va a medir igual, para mostrar la diferencia, en la Fase 6.

Detalle de implementación que conviene conocer: `reconstruir_estados()` reaplica
las acciones **pasando por `sucesores()`** en vez de tener su propia copia de las
reglas. Es más lento, pero una solución tiene a lo sumo unos cientos de pasos y a
cambio queda garantizado que lo que dibuja el reproductor de la Fase 7 es
exactamente lo que recorrió la búsqueda. Con dos implementaciones de la
transición, un error en una de ellas sería invisible.

Eso sí, los pide **sin podar deadlocks** (`sucesores(estado,
podar_deadlocks=False)`). La poda es una optimización de la búsqueda, no una
regla del juego: reproducir un camino ya encontrado no tiene por qué pasar por
ella. Si el detector de la Fase 5 tuviera un bug y descartara un estado legal,
con la poda activada el reproductor cortaría el camino a la mitad con un error
de "acción no legal" que apunta al lugar equivocado; sin ella, el camino se
dibuja entero y el bug se ve donde está.

El parámetro `detector_deadlocks` es el gancho para la Fase 5. Firma:

```python
detector(cajas: frozenset[int], caja_movida: int) -> bool
```

Se consulta sólo después de un empuje —un movimiento que no empuja nada no puede
crear un deadlock, las cajas quedaron donde estaban— y con `None` no hace nada.

Recibe **la caja recién empujada** además del conjunto porque alcanza con
revisar esa: las demás ya se validaron cuando se movieron, y todo bloque de 2×2
congelado que aparezca ahora tiene que incluir a la recién empujada. En los
niveles de 4 cajas eso es un factor 4 de trabajo ahorrado por empuje, y cuesta
un parámetro. Además se consulta sobre el conjunto de cajas antes de construir
el `Estado`: si el empuje lleva a un deadlock, no se paga ni el objeto ni el
hash.

### `verificaciones/verificar_fase1.py`

**Qué hace:** corre las seis comprobaciones del criterio de aceptación sobre los
cinco niveles: imprime una línea por nivel más una línea para la solución de N1.
Devuelve código de salida 0 si todo pasa y 1 si algo falla.

**Por qué existe:** es la evidencia reproducible de que la fase está terminada.
Todo número que se muestre en la presentación tiene que ser reproducible, y esta
fase produce tres (cajas, metas, celdas transitables) que además se contrastan
contra la tabla de `docs/03_NUMEROS_DE_ORO.md`. Va en `verificaciones/` y no en
`tests/` porque `tests/` es de `pytest` y llega en la Fase 3; acá se busca una
salida legible para el grupo, no un reporte de test.

**La decisión importante:** que el script **compare contra la tabla del documento
03 en vez de imprimir lo que le dé**. Un verificador que sólo muestra números no
verifica nada: hay que decirle de antemano qué tiene que salir. Los valores
esperados están en una tupla al principio del archivo, copiados del documento, y
si alguno no coincide el script falla con código 1 en lugar de seguir.

La sexta comprobación es la más fuerte de la fase: ejecuta sobre N1 una solución
de 8 movimientos (`RRURDDDD`) y verifica que termine en meta con 5 empujes. Las
otras cinco comprueban que el modelo sea coherente **consigo mismo**; ésta lo
comprueba contra el récord humano publicado, que es la única verdad que no sale
de nuestro código, y lo hace sin que exista todavía ninguna búsqueda. Si el
parser pusiera una pared de más, o si empujar estuviera mal implementado, la
secuencia dejaría de llegar a meta.

### `src/__init__.py`, `src/modelo/__init__.py`, `verificaciones/__init__.py`

**Qué hacen:** marcan los tres directorios como paquetes de Python.
`src/modelo/__init__.py` además reexporta la interfaz pública del modelo, así que
`from src.modelo import Problema, leer_archivo` alcanza para todo.

**Por qué existen:** son lo que permite correr todo con `python -m` desde la raíz
sin tocar `sys.path`. Un `sys.path.append` en cada script es la clase de arreglo
que funciona en la máquina de quien lo escribió y falla en la de los otros tres.

## Archivos modificados

| Archivo | Qué cambió y por qué |
|---|---|
| — | Ninguno. La fase sólo agrega archivos nuevos; `niveles/` no se tocó. |

## Cuentas que se hacen acá

Ninguna. Esta fase no introduce cálculos: no hay heurísticas, ni pesos, ni
métricas derivadas, y por eso no correspondió ningún checkpoint del protocolo de
`docs/01_REGLAS_DE_TRABAJO.md`.

Lo único que parece una cuenta —`p = fila * ancho + columna` y su inversa
`divmod(p, ancho)`— es un cambio de índice, no una estimación: es una biyección
exacta entre la grilla y los enteros de `0` a `alto*ancho - 1`, y la verificación
de ida y vuelta la comprueba en los cinco niveles.

## Verificación

**Cómo se comprueba que está bien:**

```
python -m verificaciones.verificar_fase1
```

**Salida obtenida:**

```
Verificación de la Fase 1 — modelo del problema (5 niveles)

n1_micro.sok      1 cajas   1 metas   12 celdas   ida y vuelta OK   2 sucesores válidos
n2_akk04.sok      4 cajas   4 metas   32 celdas   ida y vuelta OK   2 sucesores válidos
n3_caminata.sok   2 cajas   2 metas   35 celdas   ida y vuelta OK   3 sucesores válidos
n4_matching.sok   4 cajas   4 metas   31 celdas   ida y vuelta OK   2 sucesores válidos
n5_limite.sok     4 cajas   4 metas   41 celdas   ida y vuelta OK   1 sucesor válido

n1_micro.sok      solución RRURDDDD: 9 estados, termina en meta, 5 empujes   OK

5/5 niveles OK.
```

Código de salida: `0`. Con un número esperado alterado a propósito, el script
imprime la falla y devuelve `1`.

**Sobre la última línea, para no decirlo mal en el oral:** `RRURDDDD` es **una
solución de 8 movimientos construida a mano**, no la solución publicada.
game-sokoban.com publica el tamaño del récord —8 movimientos y 5 empujes—, no el
camino; el camino lo dedujimos nosotros. Lo que vale es que su largo y su
cantidad de empujes coinciden con el récord publicado: eso contrasta el modelo
de transición contra una verdad externa **sin que exista todavía ninguna
búsqueda**.

## Números nuevos

| Nivel | Cajas | Metas | Celdas transitables | Sucesores del estado inicial |
|---|---|---|---|---|
| N1 `n1_micro.sok` | 1 | 1 | 12 | 2 |
| N2 `n2_akk04.sok` | 4 | 4 | 32 | 2 (uno de ellos es empuje) |
| N3 `n3_caminata.sok` | 2 | 2 | 35 | 3 |
| N4 `n4_matching.sok` | 4 | 4 | 31 | 2 |
| N5 `n5_limite.sok` | 4 | 4 | 41 | 1 |

Cajas, metas y celdas **no son números nuevos**: estaban en
`docs/03_NUMEROS_DE_ORO.md` y acá se reprodujeron.

La **cantidad de sucesores del estado inicial** sí es nueva y se congela como
referencia de regresión: es el factor de ramificación real en el primer nodo, y
si cambia sin que nadie haya tocado `niveles/`, es que se rompió el modelo de
transición. Lo medido es esto y nada más: **en nuestros cinco niveles el estado
inicial tiene entre 1 y 3 sucesores**, contra un máximo teórico de 4.

**Discrepancia con la especificación, para que quede registrada:** el ejemplo de
salida de `docs/fases/FASE_1_MODELO.md` muestra `4 sucesores válidos` para N1. El
número real es 2: el jugador arranca en la esquina superior izquierda, con pared
abajo y pared a la izquierda. El ejemplo de la especificación era ilustrativo —el
resto de sus líneas están con `...`—, así que se dejó el número medido y no se
tocó el nivel.

## Preguntas que esta fase habilita en el oral

- **¿Por qué las paredes no forman parte del estado?** Porque no cambian nunca.
  Si estuvieran adentro, cada uno de los ~2.000.000 de estados de N5 cargaría una
  copia y el hash —que se consulta una vez por nodo generado— tendría que
  recorrerlas siempre. Van en un único `Tablero` compartido por referencia.
- **¿Por qué `frozenset` y no una lista de cajas?** Por dos razones separadas:
  sólo lo inmutable se puede hashear, y sin hash el "¿ya lo visité?" pasa de O(1)
  a O(n); y las cajas son indistinguibles, así que el conjunto captura esa
  simetría por construcción en vez de obligar a normalizar el orden a mano.
- **¿Por qué el costo es 1 por movimiento y no por empuje?** Porque el enunciado
  pide minimizar movimientos. Como el costo queda uniforme, `g(n)` es la
  profundidad y BFS ya es óptimo, que es lo que nos permite compararlo contra los
  récords publicados.
- **¿No convenía buscar sobre empujes, que es mucho más chico?** Convendría si
  quisiéramos minimizar empujes. Optimiza otra métrica: menos empujes puede
  significar más caminata del jugador entre empuje y empuje. Lo medimos aparte en
  la Fase 6 para mostrar la diferencia.
- **¿Qué son las "celdas transitables" que reportan?** Toda celda que no es
  pared, sin filtro de alcanzabilidad, que es la definición de la fórmula de
  estimación del espacio de estados. No es lo mismo que alcanzable: en N2, con las
  cajas en su posición inicial, el jugador llega sólo a 3 de las 32.
- **¿Para qué sirve `dibujar()` si no hay interfaz gráfica?** Para el reproductor
  estado por estado de la Fase 7, que la cátedra pidió explícitamente, y para el
  test de ida y vuelta: si dibujar y reparsear no da el mismo problema, el
  reproductor mostraría tableros que no son los que recorrió la búsqueda.

## Qué quedó pendiente

- **Fase 2:** el motor genérico y los cinco métodos. Nada de este código
  construye nodos ni fronteras.
- **Fase 3:** los tests de `pytest` en `tests/`. `verificaciones/` no lo
  reemplaza: es una salida legible para el grupo, no una red de regresión.
- **Fase 5:** los deadlocks. El gancho `detector_deadlocks` existe con su firma
  definida —`detector(cajas, caja_movida) -> bool`—, se consulta sólo después de
  un empuje y, con `None`, no hace nada. No hay ninguna detección implementada.
- **Fase 7:** el reproductor. `dibujar()` y `reconstruir_estados()` son las dos
  piezas que va a consumir.

## Ideas para más adelante

- `sucesores()` ya devuelve `hubo_empuje`, así que contar los empujes de una
  solución es sumar ese booleano. Cuando la Fase 2 exista, conviene que el
  resultado de una corrida reporte movimientos **y** empujes: los dos están en la
  tabla de números de oro y que coincidan los dos es lo que da confianza en la
  transcripción de los niveles.
- Para la Fase 6, la variante "buscar sobre empujes con el jugador normalizado"
  se puede implementar como un `Problema` alternativo con la misma interfaz, sin
  tocar el motor. Sería la forma más limpia de mostrar la comparación entre las
  dos métricas.
