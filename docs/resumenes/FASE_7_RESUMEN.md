# FASE 7 — Reproductor estado por estado

**Estado:** terminada · **Fecha:** 2026-08-23

## En una frase

Existen tres GIF animados y tres tiras de fotogramas en `presentacion/`, cada
uno con un fotograma por estado de la solución óptima: la cátedra pidió ver la
secuencia y no el resultado, y ahora se ve sola, sin demo en vivo.

## La idea que organiza la fase

La cátedra fue explícita: hay que **mostrar la secuencia de estados que lleva a
la solución**. No alcanza con decir "lo resolvimos en 8 movimientos".

La consecuencia menos obvia es que la salida tiene que ser **doble**, porque los
dos soportes de la entrega son distintos:

| | Para qué | Por qué así |
|---|---|---|
| **GIF animado** | la presentación | Se inserta en la diapositiva y corre solo. Con 25 a 30 minutos y cuatro personas hablando, una demo interactiva que tarda veinte segundos en arrancar es tiempo regalado, y encima puede fallar |
| **Tira de fotogramas** | el PDF | El PDF que va al repositorio no anima. Necesita una versión estática, numerada, que se lea de un vistazo |

Y hay una tercera salida que no estaba en la especificación y que resultó la más
útil mientras se trabajaba: **la tira en texto XSB**, que imprime la
verificación. Es la forma más rápida de que alguien controle el reproductor sin
abrir un solo archivo.

## Archivos creados

### `src/viz/render.py`

**Qué hace:** dibuja un `Estado` sobre su `Tablero` y devuelve una imagen.
Paredes, piso, metas, cajas, cajas sobre meta y jugador, más una banda de texto
arriba con lo que se le pase.

**Por qué existe:** es la misma información que ya devolvía `Tablero.dibujar()`
desde la Fase 1, que es texto XSB, pero en píxeles. El texto sirve para depurar y
para los tests; esto sirve para la diapositiva. Que sean dos implementaciones
separadas no es duplicación desperdiciada: la verificación las imprime juntas, y
si las dos coinciden es porque coinciden en el estado y no en el código.

**La decisión importante:** **una caja sobre meta se distingue de una caja fuera
de meta por FORMA, no sólo por color.** Es el dato más importante del fotograma,
porque es lo que dice cuánto falta. Si la única diferencia fuera el color, en un
proyector con luz ambiente —o para alguien que no distingue dos colores entre
sí— la imagen dejaría de decir lo único que tiene que decir. Una caja sobre meta
lleva adentro el mismo rombo con el que se dibuja una meta vacía, así que se lee
"esta caja está sobre una de ésas". Por el mismo motivo la paleta no usa el par
rojo/verde en ningún lado.

Dos detalles del dibujo que tampoco son decorativos:

- **La cuadrícula tenue del piso** permite contar los casilleros que camina el
  jugador mirando el GIF, que es exactamente lo que hay que ver en
  `n3_caminata`.
- **El círculo del jugador es más chico que la celda**, para que cuando esté
  parado sobre una meta el rombo de abajo siga asomando.

### `src/viz/reproductor.py`

**Qué hace:** convierte `(problema, acciones)` en archivos. `generar_gif()`
escribe un fotograma por estado; `generar_tira()` escribe una grilla con los
estados elegidos. Las dos devuelven una `Reproduccion` con lo que la verificación
necesita medir.

**Por qué existe:** el `Resultado` del motor trae la lista de acciones, que es
una cadena de letras. Entre eso y algo que se pueda proyectar falta reconstruir
los estados, decidir cuáles se muestran, componerlos y escribir el archivo.

**La decisión importante:** **el reproductor no vuelve a aplicar las reglas del
juego.** Los estados salen de `problema.reconstruir_estados()`, que reaplica las
acciones pasando por `sucesores()`. Tener acá una segunda implementación de "qué
pasa cuando el jugador se mueve" sería la forma más fácil de dibujar un camino
que no es el que recorrió la búsqueda, y el error sería invisible: saldría un GIF
perfectamente prolijo de otra cosa.

De ahí sale también cómo se sabe si un paso fue empuje: **cambió el conjunto de
cajas respecto del estado anterior**. El motor lo sabe —`sucesores()` devuelve
`hubo_empuje`— pero no lo guarda en los estados, y pedírselo obligaría a pasarle
al reproductor el `Resultado` entero además del camino. Son dos caminos distintos
hacia el mismo número, y por eso la verificación los compara: si el reproductor
estuviera salteándose estados, los dos se separarían.

### `src/viz/__init__.py`

**Qué hace:** marca el paquete y reexporta `dibujar`, `generar_gif`,
`generar_tira` y `Reproduccion`.

**Por qué existe:** además de lo obvio, deja escrito en un lugar visible que éste
es **el único rincón de `src/` que no participa de la búsqueda**. Es
entrada/salida, es el único que usa una biblioteca fuera de `numpy` y `scipy`, y
nada de `src/modelo/` ni de `src/busqueda/` lo importa: el motor no sabe que
existe.

### `verificaciones/verificar_fase7.py`

**Qué hace:** genera todos los archivos de `presentacion/` y corre sobre ellos
las cinco comprobaciones del criterio de aceptación. Al final imprime la tira de
N1 en texto.

**Por qué existe:** los archivos que van a la presentación tienen que salir de un
comando que cualquiera del grupo pueda correr, igual que los números. Y hay una
comprobación que no se puede hacer de otra manera: que el GIF **se abra**. Un
archivo corrupto pesa y existe igual.

**La decisión importante:** **las soluciones salen de BFS y no de A\***. A\*(h₅)
con poda completa resolvería `n5_limite` en 426.808 nodos en vez de 2.028.239 y
la verificación tardaría bastante menos. Pero un nivel puede tener varias
soluciones óptimas distintas, con el mismo costo en movimientos y **distinta
cantidad de empujes**, y BFS es el método cuyo costo *y* empujes están
contrastados contra el récord publicado. Es lo que hace que la comprobación 4
valga contra `docs/03_NUMEROS_DE_ORO.md` y no sólo contra sí misma.

`generar_gif` y `generar_tira` reciben `(problema, acciones)`, así que no están
atadas a ningún método: la elección vive únicamente acá.

### `tests/test_reproductor.py`

**Qué hace:** 18 casos que cubren la cantidad de fotogramas, los empujes
marcados, el criterio de la tira y que el reproductor ignore la poda de
deadlocks. Todo lo que escriben va a `tmp_path`.

**Por qué existe:** **no estaba en la lista de archivos de la especificación**, y
se agregó porque la verificación tarda minutos —casi todos gastados en resolver
N5 con BFS— y se corre cuando se regeneran los entregables, o sea casi nunca.
Estos tests corren en menos de un segundo y cubren lo que se puede romper en
silencio.

**La decisión importante:** el GIF de cada nivel se genera **una sola vez por
módulo** y se comparte entre tests, con el mismo patrón y el mismo argumento que
la caché de corridas de `conftest.py`. Sin eso, tres tests dibujaban cada uno los
105 fotogramas de `n3_caminata` y la suite rápida pasaba de 1,4 a 5,2 segundos.
Con la caché quedó en 2,7 s, cómodamente abajo del presupuesto de 10 s que fijó
la Fase 3.

## Archivos modificados

| Archivo | Qué cambió y por qué |
|---|---|
| `docs/01_REGLAS_DE_TRABAJO.md` | La regla 5 autoriza `Pillow` **en `src/viz/` y sólo ahí**. Ver "Cuentas que se hacen acá". |
| `docs/fases/FASE_7_REPRODUCTOR_ESTADO_POR_ESTADO.md` | Estado a "terminada". |

Ningún archivo de `niveles/`, ningún número congelado, y nada de `src/modelo/`,
`src/busqueda/`, `src/heuristicas/` ni `src/deadlocks.py`.

## Cuentas que se hacen acá

Ninguna. Esta fase no introduce cálculos: no hay heurísticas, ni pesos, ni
métricas derivadas, y por eso no correspondió ningún checkpoint del protocolo de
`docs/01_REGLAS_DE_TRABAJO.md`. Lo único que se decide es **qué se muestra**, y
eso son dos criterios que sí hay que poder defender.

### El criterio de la tira

- **Qué elige:** el estado inicial, el estado **justo después de cada empuje**, y
  el final. Es el criterio `'empujes'`, que es el que corre por defecto.
  `'todos'` es la solución completa y se usa para las soluciones cortas.
- **Por qué:** en una imagen estática dos pasos de caminata consecutivos son casi
  el mismo dibujo, porque lo único que cambió de lugar es el jugador. De cada
  empuje interesa el estado de **después**, que es el que muestra dónde quedó la
  caja. El inicial y el final se agregan siempre aunque no sean empujes: una tira
  que no arranca en el tablero de partida ni termina en el resuelto no se
  entiende sola.
- **Consecuencia medible:** como en los cinco niveles el último movimiento es un
  empuje, la tira tiene exactamente `empujes + 1` fotogramas. Está escrito como
  test.
- **Qué se descartó:** tomar un fotograma cada N pasos. Es más simple y elige
  estados por una razón que no tiene nada que ver con la solución: puede saltearse
  tres empujes seguidos y gastar cuatro cuadros en un pasillo.

### La velocidad de cada GIF

- **Qué decide:** 400 ms por paso en N1, 300 en N2, 200 en N3.
- **Por qué:** 400 ms es cómodo para mirar 8 movimientos y son 42 segundos de GIF
  para los 104 de N3, que es más de lo que dura la diapositiva. N4 y N5 no llevan
  GIF: 306 movimientos no se muestran animados de ninguna manera.
- **El detalle que sí es una decisión:** el último fotograma dura cinco veces más
  que los demás. El GIF se repite en bucle, y sin esa pausa el tablero resuelto
  —que es justamente lo que hay que ver— aparece 400 ms y se va.

### La dependencia nueva, y por qué la regla 5 cambió

La especificación dejaba elegir entre `matplotlib` y `Pillow`. Se eligió
**Pillow directo**: un tablero de Sokoban son rectángulos, rombos y círculos, o
sea exactamente lo que hace `ImageDraw`, y dibujarlo directo da control exacto
del tamaño en píxeles, que es lo que mantiene los archivos chicos. Además
matplotlib **depende de Pillow**, así que elegirlo habría sido agregar una
dependencia grande para terminar usando ésta por dentro y escribir el GIF con
`PillowWriter` igual.

Eso chocaba con la regla 5, que sólo autoriza `numpy` y `scipy` en `src/`. Se
amplió la regla en vez de hacer la excepción en silencio: **`Pillow` queda
autorizada en `src/viz/` y sólo ahí**, con el argumento de que ese paquete es
entrada/salida y no participa de la búsqueda. La regla existe para que la
búsqueda sea nuestra, y dibujar un tablero no compite con eso.

## Verificación

**Cómo se comprueba que está bien:**

```
python3 -m verificaciones.verificar_fase7
python3 -m pytest -q
python3 -m verificaciones.verificar_fase2
```

**Salida obtenida:**

```
Verificación de la Fase 7 — el reproductor estado por estado
Las soluciones salen de BFS, con límite de 3.000.000 nodos, porque es el método
cuyos movimientos y empujes están contrastados contra los récords publicados.

=== n1_micro  (8 movimientos / 5 empujes) ===
  GIF      9 fotogramas · 5 empujes · 400 ms/paso ≈ 3 s · 19,1 KB   presentacion/animaciones/n1_micro.gif
  tira     9 fotogramas · criterio 'todos' · 13,4 KB   presentacion/tiras/n1_micro.png

=== n2_akk04  (45 movimientos / 18 empujes) ===
  GIF     46 fotogramas · 18 empujes · 300 ms/paso ≈ 14 s · 102,9 KB   presentacion/animaciones/n2_akk04.gif

=== n3_caminata  (104 movimientos / 22 empujes) ===
  GIF    105 fotogramas · 22 empujes · 200 ms/paso ≈ 21 s · 227,6 KB   presentacion/animaciones/n3_caminata.gif

=== n4_matching  (70 movimientos / 22 empujes) ===
  tira    23 fotogramas · criterio 'empujes' · 30,9 KB   presentacion/tiras/n4_matching.png

=== n5_limite  (306 movimientos / 99 empujes) ===
  tira   100 fotogramas · criterio 'empujes' · 104,7 KB   presentacion/tiras/n5_limite.png

=== La tira de N1 en texto, para revisarla sin abrir nada ===
El asterisco marca los pasos que son empuje.

paso 0/8     paso 1/8     paso 2/8 *   paso 3/8     paso 4/8
######       ######       ######       ######       ######
#    #       #    #       #    #       #  @ #       #   @#
#@ $ #       # @$ #       #  @$#       #   $#       #   $#
#### #       #### #       #### #       #### #       #### #
#### #       #### #       #### #       #### #       #### #
#### #       #### #       #### #       #### #       #### #
####.#       ####.#       ####.#       ####.#       ####.#
######       ######       ######       ######       ######

paso 5/8 *   paso 6/8 *   paso 7/8 *   paso 8/8 *
######       ######       ######       ######
#    #       #    #       #    #       #    #
#   @#       #    #       #    #       #    #
####$#       ####@#       #### #       #### #
#### #       ####$#       ####@#       #### #
#### #       #### #       ####$#       ####@#
####.#       ####.#       ####.#       ####*#
######       ######       ######       ######

5/5 niveles OK. Las 5 comprobaciones pasan.
```

Esa tira en texto es la solución `RRURDDDD`, la misma de 8 movimientos y 5
empujes con la que la Fase 1 verificó el modelo de transición antes de que
existiera ninguna búsqueda. En el último cuadro la caja aparece como `*`, que en
XSB es caja sobre meta.

`pytest -q` da **403 passed en 63,41 s**, contra 385 antes de la fase; la suite
rápida da **260 passed, 143 deselected en 2,74 s**. `verificar_fase2` sigue
dando 5/5 con los mismos números.

## Números nuevos

| Nivel | Archivo | Fotogramas | Empujes marcados | Tamaño |
|---|---|---|---|---|
| N1 | `animaciones/n1_micro.gif` | 9 | 5 | 19,1 KB |
| N2 | `animaciones/n2_akk04.gif` | 46 | 18 | 102,9 KB |
| N3 | `animaciones/n3_caminata.gif` | 105 | 22 | 227,6 KB |
| N1 | `tiras/n1_micro.png` | 9 | 5 | 13,4 KB |
| N4 | `tiras/n4_matching.png` | 23 | 22 | 30,9 KB |
| N5 | `tiras/n5_limite.png` | 100 | 99 | 104,7 KB |

**Los seis archivos juntos pesan menos de 500 KB.** Es el criterio 5 con
margen de sobra: el límite que aplica la verificación son 2 MB por archivo.

La cantidad de fotogramas no es una métrica nueva de nada: es `costo + 1` en los
GIF y `empujes + 1` en las tiras, y las dos igualdades están testeadas. Aparecen
acá porque son lo que hay que mirar si algún día un archivo sale distinto.

## Preguntas que esta fase habilita en el oral

- **¿Por qué un GIF y no una demo en vivo?** Porque corre solo dentro de la
  diapositiva. Con 25 a 30 minutos y cuatro personas hablando, veinte segundos
  esperando que arranque un programa son veinte segundos que no se recuperan, y
  además puede fallar.
- **¿Cómo saben que el GIF muestra la solución que encontró la búsqueda?** Porque
  el reproductor no reimplementa las reglas: los estados salen de
  `reconstruir_estados()`, que reaplica las acciones pasando por el mismo
  `sucesores()` que usó el motor. Y porque los empujes que marca el GIF —contados
  comparando conjuntos de cajas— coinciden con los que reportó el motor, que a su
  vez son el récord publicado.
- **¿Cómo eligen qué estados entran en la tira de N5, si son 307?** El inicial, el
  de después de cada empuje, y el final: 100 fotogramas. Los pasos de caminata no
  entran porque en una imagen estática no se distinguen del anterior, ya que lo
  único que se movió es el jugador.
- **¿Por qué las soluciones las resuelven con BFS si tienen A\* con poda, que es
  cinco veces más rápido?** Porque un nivel puede tener varias soluciones óptimas
  con el mismo costo y distinta cantidad de empujes, y BFS es el método cuyos dos
  números están contrastados contra el récord publicado.
- **¿Por qué la caja sobre meta tiene un rombo adentro si ya es de otro color?**
  Porque es el dato más importante de la imagen y no puede depender de que el
  proyector rinda bien o de que quien mira distinga esos dos colores.
- **¿Pillow no rompe la regla de dependencias?** La rompía, y por eso se cambió la
  regla en vez de hacer la excepción callados. `src/viz/` es entrada/salida, no
  participa de la búsqueda y nadie del motor lo importa; la regla existe para que
  la búsqueda sea nuestra.

## Qué quedó pendiente

- **Las figuras de análisis — Fase 8.** Acá se dibujan **tableros**; las barras,
  las curvas y el barrido de `w` son otra cosa y van con matplotlib en
  `experimentos/`, donde ya estaba autorizado.
- **El GIF de N4 y N5.** No existen a propósito: 70 y 306 movimientos no se
  muestran animados. Si alguna vez hiciera falta, `generar_gif` acepta
  `ms_por_paso`, así que es una línea.
- **Enganchar el reproductor a `main.py`**, para poder pedir el GIF de una corrida
  desde `config.json`. No se hizo porque es exactamente la clase de cosa que
  corresponde al runner de la **Fase 6**, que todavía no existe en esta rama.

## Ideas para más adelante

- **Un GIF que muestre la búsqueda y no la solución**: los nodos que A\* expande,
  en orden, pintando el tablero. Sería la forma más directa de mostrar la
  diferencia entre BFS y A\*(h₅) sin una sola tabla. No entra en esta fase porque
  no es "la secuencia que lleva a la solución", que es lo que pidió la cátedra.
- **Resaltar la caja que se acaba de empujar** en el fotograma siguiente. En N4,
  con cuatro cajas, cuesta un segundo encontrar cuál se movió.
- La tira de N5 tiene 100 fotogramas en una grilla de 10×10. Para el PDF quizás
  convenga partirla en dos páginas, o quedarse con los empujes de las últimas dos
  cajas, que es donde se ve el final. Se decide cuando exista el PDF.
