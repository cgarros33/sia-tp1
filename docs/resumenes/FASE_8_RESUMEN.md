# FASE 8 — Gráficos, análisis y material de presentación

**Estado:** terminada · **Fecha:** 2026-08-23

## En una frase

Existen las cuatro figuras que se van a proyectar, salen de un comando sobre los
CSV ya medidos, y el único experimento nuevo —el barrido de w— está corrido,
versionado y contrastado contra la matriz de la Fase 6 en los dos puntos donde
tiene que coincidir exactamente.

## La idea que organiza la fase

La cátedra advirtió que si se analiza cómo se relacionan dos variables, **las
variables tienen que tener sentido**, y una correlación sirve cuando se mueve una
variable y todo lo demás queda fijo.

Eso no es una recomendación de estilo: decidió el diseño de las cuatro figuras.
Cada función de `graficos.py` lleva escrito en su docstring qué va en cada eje y
**qué se mantiene fijo**, y donde algo no se puede mantener fijo —comparar
niveles distintos— la figura usa paneles separados en vez de un eje compartido,
para no sugerir una comparación que no es válida.

| | Figura | Eje X | Eje Y | Qué queda fijo |
|---|---|---|---|---|
| 1 | Métodos | nivel (categórico) | nodos expandidos (log) | h₅ y poda completa en los cinco métodos |
| 2 | Dominancia | informatividad h(s₀)/óptimo | nodos de A\* (log) y relativos a A\*(h₀) | método, poda y nivel dentro de cada serie |
| 3 | Barrido de w | w, de 0 a 1 | costo y nodos (log) | nivel, h₅, poda, límite de nodos, motor |
| 4 | El muro | espacio de estados (log) | nodos de BFS sin poda (log) | el método: BFS en los seis puntos |

## Archivos creados

### `experimentos/barrido_w.py`

**Qué hace:** corre el motor con `f = (1−w)·g + w·h` para 21 valores de w sobre
tres niveles, y escribe `experimentos/barrido_w.csv` con una fila por corrida.

**Por qué existe:** es el único experimento nuevo de la fase y el más fuerte del
TP. Todo lo demás compara métodos o heurísticas que difieren en muchas cosas a la
vez; acá se mueve **exactamente un parámetro**, sobre el mismo nivel, con la
misma heurística, la misma poda y el mismo motor. Es el experimento controlado de
manual, y es la respuesta directa a la advertencia de la cátedra.

**La decisión importante:** **una sola corrida por (nivel, w)**, y no es pereza.
Los dos ejes que grafica la figura 3 son determinísticos, y eso no se asume: está
medido sobre las 645 filas de `resultados.csv`, donde ninguna de las 225
configuraciones varía sus nodos entre sus cinco corridas. Promediar daría el
mismo número y las barras de error darían cero. El tiempo sí varía, se guarda
igual, y no se grafica.

### `experimentos/graficos.py`

**Qué hace:** genera las cuatro figuras desde los CSV y las escribe en
`presentacion/figuras/`, en PNG de proyección (200 dpi) y en PDF vectorial.

**Por qué existe:** separar medir de graficar es lo que hace que regenerar una
figura sea instantáneo y que dos personas con el mismo CSV obtengan exactamente
la misma imagen. **No corre ninguna búsqueda**: lo único que calcula es h(s₀)
para el eje X de la figura 2, que es evaluar una función en un estado.

**La decisión importante:** `CreationDate=None` al guardar el PDF. Sin eso
matplotlib le estampa la fecha de generación y dos corridas con el mismo CSV
producirían archivos distintos, que es exactamente lo que el criterio 3 prohíbe.
Es una línea y es la diferencia entre "idempotente" y "parece idempotente".

### `verificaciones/verificar_fase8.py`

**Qué hace:** regenera las figuras dos veces, compara los bytes, contrasta el
barrido contra la matriz de la Fase 6 y revisa la política de barras de error.

**Por qué existe:** de las cinco comprobaciones de la fase, tres no se pueden
hacer mirando las imágenes. Que regenerar sea idempotente exige generar dos veces
y hashear; que el barrido no esté midiendo otra cosa exige compararlo contra
números medidos por otro código; y que no haya barras de error sobre datos
determinísticos se verifica **sobre los datos**, recorriendo el CSV, no sobre los
píxeles.

**La decisión importante:** la comprobación 5, la de legibilidad, **informa y no
decide**. El script reescala los PNG al 50 % y dice el tamaño resultante, pero
deja escrito que si los rótulos se leen lo decide una persona. Un script que
dijera "legibilidad OK" estaría certificando algo que no puede medir.

### `experimentos/__init__.py`

**Qué hace:** marca el directorio como paquete, para poder correr los dos scripts
con `python3 -m` desde la raíz sin tocar `sys.path`.

## Archivos modificados

| Archivo | Qué cambió y por qué |
|---|---|
| `docs/fases/FASE_8_GRAFICOS.md` | Estado a "terminada". |
| `docs/resumenes/README.md` | Fase 8 a "escrito". |

Ningún archivo de `niveles/`, ningún número congelado, y nada de `src/`. Esta
fase **sólo lee**: no toca el motor, ni las heurísticas, ni la poda, ni el
reproductor.

## Cuentas que se hacen acá

### El barrido de w

- **Qué calcula:** para cada `w`, el costo de la solución y el esfuerzo de
  búsqueda con `f(n) = (1−w)·g(n) + w·h(n)`.
- **Por qué el quiebre está en `w = 0,5`, antes de medir nada:** dividir `f` por
  `(1−w)` no cambia el orden de la frontera y deja `g + [w/(1−w)]·h`. Para
  `w ≤ 0,5` ese factor es `≤ 1`, o sea que es A\* con `h' = c·h` con `c ≤ 1`: si
  `h` es admisible, `h'` también, y la solución sigue siendo óptima. Para
  `w > 0,5` el factor pasa de 1 y la garantía se cae. **El quiebre no es un
  hallazgo empírico: es el punto donde se pierde la admisibilidad.**
- **Las dos anclas que lo hacen auditable:** en `w = 0,5` el HPA **es** A\* —la
  prioridad `(g+h)/2` ordena igual que `g+h`, con el mismo desempate y la misma
  política— y en `w = 1` **es** Greedy, porque el peso de `g` se anula y la
  política pasa a `cerrado`. Los seis pares reproducen exactamente el CSV de la
  Fase 6.
- **Qué se descartó:** reusar el runner de la Fase 6, cuyas tuplas no tienen
  dimensión `w`; y repetir cada `w` para promediar.

### La informatividad del eje X de la figura 2

- **Qué calcula:** `h(s₀) / óptimo publicado`. 0 es h₀, que no informa nada; 1
  sería la heurística perfecta.
- **Por qué es correcta:** el numerador se obtiene evaluando la heurística en el
  estado inicial y el denominador es verdad externa. **No se resuelve nada**:
  construir las tablas de un nivel son unos pocos BFS sobre 12 a 41 celdas.
- **Por qué las dos no admisibles quedan afuera:** para una heurística que
  sobreestima, ese cociente pasa de 1 y deja de significar "qué fracción del
  costo real captura". Mezclarlas en el mismo eje sería comparar dos cosas
  distintas con la misma vara.

### El espacio de estados del eje X de la figura 4

- **Fórmula:** `celdas × C(celdas, cajas)`, la de `docs/03_NUMEROS_DE_ORO.md`.
  Cuenta dónde puede estar el jugador por dónde puede estar cada conjunto de
  cajas.
- **Por qué es una estimación y no un tamaño:** sobreestima, porque incluye
  configuraciones inalcanzables. Sirve igual, porque lo que se compara son
  órdenes de magnitud. La implementación reproduce los dos valores que el
  documento ya traía —9,8 × 10⁵ para N4 y 3,7 × 10⁹ para el nivel descartado—,
  que es el control de que la cuenta es la misma.

### La política de barras de error, que es una cuenta que NO se hace

Sobre las 225 configuraciones del CSV, **ninguna** varía su costo, sus empujes,
sus nodos ni su memoria entre las cinco corridas. Poner una barra de error encima
sería decorar con una incertidumbre que no existe.

La variabilidad real está en dos lugares y en ninguno más:

- **El tiempo**, que varía en 55 de las 105 configuraciones repetidas. No se
  grafica en ninguna figura.
- **DFS**, que depende del orden de sucesores. La Fase 6 corrió las **24
  permutaciones** de `DIRECCIONES`, así que la figura 1 le pone bigotes. Y hay un
  matiz que conviene decir en el oral: esas 24 son la **población completa**, no
  una muestra. El bigote no es un intervalo de confianza ni una estimación: es el
  rango exacto de lo que puede pasar.

## Verificación

**Cómo se comprueba que está bien:**

```
python3 -m experimentos.barrido_w
python3 -m experimentos.graficos
python3 -m verificaciones.verificar_fase8
```

**Salida obtenida** (`verificar_fase8`):

```
=== Comprobación 1 — las cuatro figuras, en PNG y en PDF ===
  presentacion/figuras/figura_1_metodos.png      347 KB   ¿cuánto aporta cada método?
  presentacion/figuras/figura_2_dominancia.png   274 KB   ¿una heurística más informada expande menos nodos?
  presentacion/figuras/figura_3_barrido_w.png    354 KB   ¿cuánto se paga por apurar la búsqueda?
  presentacion/figuras/figura_4_el_muro.png      185 KB   ¿por qué hay un límite y dónde está?

=== Comprobación 3 — regenerar es idempotente ===
  8 archivos, mismos bytes en las dos corridas   OK

=== Comprobación 2 — el barrido de w y sus dos anclas ===
  63 corridas en experimentos/barrido_w.csv
  w=0.50 vs A*     n2_akk04         45 /     4.460   contra    45 /     4.460   OK
  w=0.50 vs A*     n3_caminata     104 /     1.702   contra   104 /     1.702   OK
  w=0.50 vs A*     n4_matching      70 /    43.628   contra    70 /    43.628   OK
  w=1.00 vs Greedy n2_akk04        103 /     1.565   contra   103 /     1.565   OK
  w=1.00 vs Greedy n3_caminata     108 /     1.243   contra   108 /     1.243   OK
  w=1.00 vs Greedy n4_matching      95 /       219   contra    95 /       219   OK
  corridas con w <= 0,5 y costo distinto del óptimo publicado: 0   OK

=== Comprobación 4 — barras de error sólo donde hay variabilidad ===
  225 configuraciones, ninguna varía sus 5 columnas entre corridas   OK
  DFS en n1_micro      24 permutaciones, de 8 a 56 nodos
  DFS en n2_akk04      24 permutaciones, de 1.329 a 8.358 nodos
  DFS en n3_caminata   24 permutaciones, de 408 a 1.412 nodos
  DFS en n4_matching   24 permutaciones, de 339 a 5.533 nodos
  DFS en n5_limite     24 permutaciones, de 294.796 a 381.328 nodos

4/4 figuras OK. Las 5 comprobaciones pasan.
```

Y el control cruzado que no está en el script: las alturas de BFS con poda
completa de la figura 1 coinciden con los cinco números congelados en
`tests/conftest.py` desde la Fase 5 — 35 · 9.839 · 1.816 · 60.410 · 429.817. La
suite sigue en verde: `pytest -q -m "not lento"` da 265 passed en 5,90 s.

**Legibilidad al 50 %:** las cuatro figuras se abrieron reescaladas a la mitad y
los rótulos se leen. La única salvedad honesta es la figura 2, donde en el panel
derecho las etiquetas h₃, h₄ y h₅ se amontonan en los niveles donde esas tres
heurísticas tienen la **misma** informatividad —en `n1_micro`, h₂, h₃ y h₄ valen
las tres 5/8— y ahí los rótulos se superponen. Es una limitación del dato, no del
gráfico: son tres puntos en la misma coordenada.

## Números nuevos

### El barrido de w — `experimentos/barrido_w.csv`, 63 corridas

| w | n2 costo | n2 nodos | n3 costo | n3 nodos | n4 costo | n4 nodos |
|---|---|---|---|---|---|---|
| 0,00 | 45 | 9.642 | 104 | 1.806 | 70 | 60.308 |
| 0,25 | 45 | 7.976 | 104 | 1.790 | 70 | 55.060 |
| **0,50** | **45** | **4.460** | **104** | **1.702** | **70** | **43.628** |
| 0,70 | 45 | 1.001 | 104 | 1.665 | 70 | 16.086 |
| 0,75 | 45 | 684 | 104 | 1.691 | 70 | 6.390 |
| 0,80 | 47 | 608 | 104 | 1.782 | 81 | 1.206 |
| 0,85 | 49 | 554 | 104 | 1.986 | 87 | 466 |
| 0,90 | 49 | 1.847 | 104 | 2.233 | 95 | 232 |
| 0,95 | 101 | 4.711 | 104 | 2.379 | 95 | 225 |
| **1,00** | **103** | **1.565** | **108** | **1.243** | **95** | **219** |

En negrita los dos puntos que coinciden con A\* y con Greedy del CSV de la Fase 6.

### Lo que la escalera compra, relativo a A\*(h₀)

| nivel | A\*(h₀) | A\*(h₅) | fracción |
|---|---|---|---|
| n1_micro | 35 | 8 | 0,23 |
| n2_akk04 | 9.839 | 4.460 | 0,45 |
| n3_caminata | 1.816 | 1.702 | **0,94** |
| n4_matching | 60.410 | 43.628 | 0,72 |
| n5_limite | 429.817 | 426.808 | **0,99** |

Todos con poda completa, que es lo que hace comparables las dos columnas.

---

# El análisis, figura por figura

## Figura 1 — Nodos expandidos por método y nivel

**Qué se ve.** Cinco grupos, uno por nivel, con los cinco métodos. En azul los
que devuelven el óptimo publicado, en arena los que no. La escala es logarítmica
porque el rango real va de 8 nodos a 3.000.000.

**Qué lo causa.** Tres cosas distintas, y conviene no mezclarlas:

- **A\*(h₅) contra BFS**: 4.460 contra 9.839 en N2 y 43.628 contra 60.410 en N4,
  **con el mismo costo**. La heurística cambia el esfuerzo, no la calidad.
- **Greedy** es el más barato en cuatro de los cinco niveles —219 nodos en N4
  contra 43.628 de A\*, casi 200 veces menos— y devuelve 95 movimientos donde el
  óptimo es 70. Paga velocidad con calidad, y el precio no es parejo: +4 % en N3
  y +129 % en N2.
- **IDDFS** expande 27,6 veces más que BFS en N2 y **195 veces más** en N3, y en
  N4 y N5 agota el límite de 3.000.000 sin encontrar nada. Su barra está marcada
  "sin solución" porque dibujarla como las demás diría que resolvió el nivel con
  3.000.000 de nodos, que es falso.

**Qué conclusión se saca.** Que la comparación entre métodos sea justa no es un
resultado: es una consecuencia de la arquitectura de la Fase 2, donde los cinco
corren el mismo bucle y sólo cambia la frontera. Lo que la figura muestra es que
**la elección del método cambia el esfuerzo entre dos y cinco órdenes de
magnitud, y que sólo tres de los cinco compran ese ahorro sin perder la
optimalidad.**

## Figura 2 — Dominancia empírica de las heurísticas

**Qué se ve.** Dos paneles. El izquierdo tiene los nodos absolutos, y ahí cada
nivel vive en su propia banda del eje: las cinco trayectorias parecen planas. El
derecho divide por A\*(h₀) del mismo nivel, y recién ahí se ve cuánto compra cada
eslabón de la escalera.

**Por qué hay dos paneles y no uno.** Porque la pregunta de la figura —¿una
heurística más informada expande menos nodos?— no se puede contestar mirando el
panel izquierdo: la variación dentro de un nivel es de un 25 % sobre un eje que
abarca cinco órdenes de magnitud. Normalizar contra h₀ es lo que pone la pregunta
en escala. Los dos paneles están porque **el izquierdo da las magnitudes reales y
el derecho da la respuesta**, y sacar cualquiera de los dos empobrece la figura.

**Qué lo causa.** La escalera baja monótonamente en los cinco niveles: más
informatividad, menos nodos, siempre. Pero **cuánto** baja depende del nivel, y
mucho: de 0,23 en N1 a 0,99 en N5.

**Qué conclusión se saca.** La dominancia teórica se verifica empíricamente —una
heurística que domina en valor expande menos nodos, con el mismo costo— **pero el
retorno se derrumba justo donde más falta hace**. En N5, el nivel más grande,
toda la escalera h₁ → h₅ ahorra un 1 %. La causa está en la figura siguiente y en
la conclusión 3.

## Figura 3 — El barrido de w

**Qué se ve.** Tres paneles, uno por nivel. En cada uno, el costo de la solución
sobre el eje izquierdo y los nodos expandidos —logarítmicos— sobre el derecho,
contra `w`. Marcados los tres puntos que corresponden a costo uniforme, A\* y
Greedy.

**Qué lo causa, y qué salió distinto de lo esperado.** La especificación de la
fase anticipaba que al crecer `w` los nodos bajarían y el costo subiría, con un
quiebre alrededor de 0,5. Salió a medias, y las tres desviaciones son lo mejor de
la figura:

1. **La garantía se pierde en 0,5 pero el costo aguanta hasta 0,75.** En N2 y N4
   el costo sigue siendo el óptimo publicado hasta `w = 0,75` inclusive, y recién
   se rompe en 0,80. Es el mismo fenómeno que la Fase 4 midió con 2·h₄: perder la
   admisibilidad pierde la **garantía**, no necesariamente la respuesta. Y el
   punto donde efectivamente se rompe **depende del nivel**, así que no se puede
   elegir un `w > 0,5` "seguro" sin conocer la respuesta de antemano, que es
   justamente lo que no se tiene.
2. **Los nodos no bajan de forma monótona.** En N2 bajan hasta 554 en `w = 0,85`
   y después suben a 4.711 en 0,95. Dos causas se suman: una `h` muy pesada
   compromete la búsqueda con una rama equivocada y desandarla cuesta más de lo
   que ahorró —lo mismo que la Fase 4 midió con 2·h₄ en N5—, y además en `w = 1`
   la política cambia de `mejor_g` a `cerrado`, así que ese último punto no es
   comparable con sus vecinos y hay que decirlo.
3. **N3 casi no se mueve**: 1.806 a 1.665 nodos en todo el barrido, un 8 %, y da
   el óptimo hasta `w = 0,95`.

**Qué conclusión se saca.** Que el compromiso entre calidad y esfuerzo es real y
**continuo**, pero que la zona útil es angosta y su borde no se conoce sin
resolver el problema. Y que apretar más el acelerador después de cierto punto no
sólo empeora la respuesta: puede además ser **más lento**.

## Figura 4 — El muro

**Qué se ve.** Dispersión log-log: espacio de estados estimado contra nodos
expandidos por BFS sin poda. Los cinco niveles alineados, y el nivel descartado
—ABHT 02·03, 5 cajas, 89 celdas— arriba a la derecha con una flecha hacia arriba.

**Por qué el punto descartado es una flecha y no un punto.** De ese nivel no
tenemos un número de BFS: tenemos que A\* con matching y poda expandió 3.000.000
de nodos sin terminar. Como A\* con poda expande **menos** que BFS, el número de
BFS sería todavía mayor. Lo único que se puede afirmar es "≥ 3.000.000", y la
flecha dice exactamente eso.

**Qué lo causa.** El eje X crece con `C(celdas, cajas)`, que es combinatorio en la
cantidad de cajas. N3 tiene 35 celdas y **2** cajas: 20.825. N4 tiene menos celdas
—31— y **4** cajas: 975.415, casi cincuenta veces más.

**Qué conclusión se saca.** El límite es combinatorio y lo pone la **cantidad de
cajas**, no el largo de la solución. N3 resuelve una solución de 104 movimientos
con 6.360 nodos; N5 resuelve una de 306 con 2.028.239. La diferencia no es que la
solución sea tres veces más larga: es que hay el doble de cajas.

---

## Las conclusiones

1. **La información heurística cambia el esfuerzo, no la calidad.** BFS y A\* con
   cualquier heurística admisible devuelven el mismo costo en los cinco niveles;
   lo que cambia es cuántos nodos hay que abrir. Figura 1.
2. **La dominancia se verifica empíricamente.** Una heurística que domina a otra
   en valor expande menos nodos, con el mismo costo, en los cinco niveles.
   Figura 2.
3. **Optimizar movimientos limita a las heurísticas, y está medido cuánto.**
   Todas estiman empujes, pero en N3 el 79 % de los movimientos de la solución
   óptima son caminata del jugador. Se ve dos veces: la escalera completa ahorra
   apenas un 6 % en ese nivel (figura 2), y todo el barrido de `w` lo mueve un
   8 % (figura 3). Es la causa medida de que A\* rinda mucho menos acá que en el
   8-puzzle.
4. **El muro es combinatorio, no de largo de solución.** Figura 4.
5. **IDDFS no compró lo que promete, y hay que contarlo igual.** El de manual usa
   memoria lineal porque no guarda visitados; en Sokoban eso es impracticable
   —`iddfs_puro` sólo termina en N1—, así que le agregamos detección de repetidos
   y con eso perdimos la ventaja. Medido con poda completa: **0,87× la memoria de
   BFS en N2 y 0,99× en N3**, pagando 27,6× y 195× más nodos. Y en N4 y N5
   directamente no termina.

Y una sexta que salió de esta fase y no estaba prevista:

6. **Perder la admisibilidad no es un interruptor.** Entre `w = 0,5` —donde se
   cae la garantía— y `w = 0,80` —donde empieza a caerse la respuesta— hay una
   franja en la que A\* sigue devolviendo el óptimo sin ninguna razón para
   hacerlo. Es tentador quedarse ahí, y es exactamente lo que no se puede hacer:
   el borde de esa franja depende del nivel y sólo se conoce después de resolver.

## Preguntas que esta fase habilita en el oral

- **¿Por qué el barrido de w es un experimento válido y "cajas contra tiempo" no
  lo sería?** Porque en el barrido se mueve un parámetro y todo lo demás es
  literalmente el mismo código y los mismos datos. Comparar cajas contra tiempo
  mezclando niveles confunde el efecto de las cajas con el del tamaño y la
  topología del tablero.
- **¿Cómo saben que el barrido no está midiendo otra cosa?** Porque en `w = 0,5`
  el HPA **es** A\* y en `w = 1` **es** Greedy, y los seis pares reproducen
  exactamente los valores que el runner de la Fase 6 midió con otro código.
- **¿Por qué la figura 1 usa BFS con poda si los números de oro son sin poda?**
  Porque en esa figura se compara el método, y BFS es el único que en el CSV
  tiene las cuatro capas. Poner el BFS sin poda contra un A\* con poda mezclaría
  el efecto del método con el de la poda en una sola barra.
- **¿Por qué sólo DFS tiene barras de error?** Porque es el único con
  variabilidad real. Las 225 configuraciones del CSV no varían sus nodos entre
  corridas, así que una barra de error ahí sería inventar una incertidumbre. Y
  las de DFS no son un intervalo de confianza: son el rango exacto de las 24
  permutaciones, que es la población completa.
- **En la figura 3, ¿por qué el costo no empeora en 0,5 si ahí se pierde la
  garantía?** Porque perder la garantía y perder la respuesta son cosas
  distintas. La garantía se cae exactamente en 0,5 —ahí `w/(1−w)` pasa de 1 y la
  heurística escalada deja de ser admisible—; que el óptimo aguante hasta 0,75 es
  suerte del nivel, y en otro nivel podría romperse antes.
- **¿Por qué la figura 2 tiene un panel normalizado? ¿No es maquillar el dato?**
  Al revés: el panel absoluto está al lado y da las magnitudes reales. Sin
  normalizar, la variación dentro de un nivel es invisible sobre un eje que
  abarca cinco órdenes de magnitud, y la figura no contestaría su propia
  pregunta.

## Qué quedó pendiente

- **El PDF de las diapositivas.** Lo arma el grupo por fuera y se versiona en
  `docs/presentacion/`. Esta fase aporta los insumos, no las diapositivas.
- **Los tiempos no se grafican en ninguna figura.** Están medidos y en el CSV, con
  cinco corridas por configuración, pero varían hasta un factor 3 con idénticos
  nodos: cualquier figura de tiempos diría más sobre la máquina que sobre el
  algoritmo. Si se quisiera, la única honesta sería nodos contra tiempo en una
  sola máquina, para mostrar que son proporcionales.
- **El barrido corrió sobre tres niveles y no sobre los cinco.** N1 es demasiado
  chico para que la curva diga algo y N5 multiplicaba por cuatro el tiempo del
  experimento. Los tres elegidos cubren un nivel donde el barrido funciona (N4),
  uno donde funciona a medias (N2) y uno donde casi no hace nada (N3).

## Ideas para más adelante

- Un barrido de `w` **sobre N5**, que es donde el compromiso importa de verdad y
  donde la escalera de heurísticas ya no compra nada. La sospecha es que la curva
  se parezca a la de N3 —plana— por el mismo motivo, y confirmarlo o desmentirlo
  cerraría el argumento de la conclusión 3.
- **El nivel descartado con poda completa.** La Fase 5 midió que la poda ahorra
  4,7× en N5; si en ABHT 02·03 ahorrara algo parecido, el punto de la figura 4
  podría pasar de "no resuelto" a "resuelto", y la figura del muro cambiaría de
  "acá está el límite" a "acá estaba el límite antes de podar", que es una
  historia mejor.
- La figura 1 mezcla en un mismo color a IDDFS, que **es** un método óptimo, con
  sus dos barras donde no encontró nada. Se resuelve con la marca "sin solución",
  pero un tercer color para "óptimo cuando termina" sería más limpio si alguna
  vez se rehace.
