# FASE 7 — Reproductor estado por estado

**Dueño:** Leo · **Estado:** terminada

Al terminar, existe un GIF animado por cada solución que queramos mostrar, y una
tira de fotogramas para el PDF.

---

## Por qué esta fase existe

La cátedra fue explícita: en la presentación hay que **mostrar la secuencia de
estados que lleva a la solución**, no el resultado final. No alcanza con decir
"lo resolvimos en 8 movimientos": hay que verlo.

---

## Archivos a crear

```
src/viz/__init__.py
src/viz/render.py          (un estado -> una imagen)
src/viz/reproductor.py     (una solución -> GIF y tira de fotogramas)
verificaciones/verificar_fase7.py
```

Salida en `presentacion/animaciones/` y `presentacion/tiras/`.

---

## Salida doble, y por qué

**GIF animado**, para la presentación. Se inserta en la diapositiva y **corre
solo**: no hay demo en vivo que pueda fallar, ni terminal que abrir, ni tiempo
perdido en el escenario. Con 25 a 30 minutos y cuatro personas hablando, una
demo interactiva que tarda veinte segundos en arrancar es tiempo regalado.

**Tira de fotogramas clave**, para el PDF. El PDF que va al repositorio no
anima, así que necesita una versión estática: una grilla con los estados más
importantes de la solución, numerados.

Para N1 la tira puede ser la solución completa (9 estados). Para N5, con 307
estados, hay que elegir. Un criterio razonable: **el estado inicial, el estado
justo después de cada empuje, y el final**. Los movimientos de caminata del
jugador no aportan a la lectura estática. Documentá el criterio que uses.

---

## `render.py` — un estado a imagen

Dibuja un `Estado` sobre un `Tablero`. Elementos: pared, piso, meta, caja, caja
sobre meta, jugador, jugador sobre meta.

Requisitos:

- **Legible proyectado.** Se va a ver en un proyector, probablemente con luz
  ambiente. Contraste alto, elementos grandes, sin detalles finos.
- **Caja sobre meta claramente distinta de caja fuera de meta.** Es la
  información más importante de la imagen: es lo que dice cuánto falta.
- **Nada de colores que dependan de distinguir rojo de verde.** Que la diferencia
  se note también por forma o por relleno, no sólo por color.
- Un encabezado por fotograma con el número de paso, el total, y si ese paso fue
  empuje: `paso 5/8 · empuje`.

Usar `matplotlib`, que ya está autorizado, o `Pillow`. No hace falta `pygame`:
no queremos interactividad, queremos archivos.

---

## `reproductor.py` — una solución a archivos

Entrada: un problema, una lista de acciones y un nombre de salida.
Salida: el GIF y la tira.

```python
def generar_gif(problema, acciones, salida, ms_por_paso=400)
def generar_tira(problema, acciones, salida, criterio='empujes')
```

### Detalle importante: ignorar el detector de deadlocks

`problema.reconstruir_estados()` reaplica las acciones pasando por
`sucesores()`, y desde la Fase 5 `sucesores()` **poda estados**.

Con un detector correcto eso nunca debería afectar a un camino solución, porque
un camino solución no atraviesa deadlocks por definición. Pero si el detector
tuviera un bug, el reproductor fallaría de forma confusa —"no encuentro la
acción"— en vez de mostrar el camino.

**El reproductor tiene que reconstruir el camino sin consultar el detector.**
Quedó anotado como decisión desde la Fase 1; acá es donde se cobra.

### Velocidad

400 ms por paso para las soluciones cortas. Para N5, con 306 movimientos, eso
son dos minutos: demasiado. Que el parámetro sea configurable y que para las
soluciones largas se pueda acelerar o generar sólo el tramo de los empujes.

---

## Qué generar

| Nivel | Qué | Para qué |
|---|---|---|
| **N1** | GIF completo, 8 movimientos | La demo principal. Es el caso donde se ve todo |
| **N2** | GIF completo, 45 movimientos | Un nivel real de 4 cajas |
| **N3** | GIF completo o acelerado, 104 movimientos | Muestra la caminata: 82 de los 104 pasos son el jugador moviéndose sin empujar. Es la evidencia visual del punto ciego de las heurísticas |
| **N4** | Tira de fotogramas | Referencia estática |
| **N5** | Tira de fotogramas | La solución de 306 movimientos no se puede mostrar animada |

**El GIF de N3 es el más valioso de la presentación.** Ahí se ve, sin explicar
nada, por qué una heurística que sólo estima empujes no alcanza: el 79 % de los
pasos son el jugador caminando y ninguna heurística los ve.

---

## Criterio de aceptación

**1. Existe el GIF de N1** con sus 8 movimientos, y se abre.

**2. La cantidad de fotogramas es `costo + 1`** en todos los GIF generados.
Un fotograma por estado, incluyendo el inicial y el final.

**3. El último fotograma muestra todas las cajas sobre metas.** Verificable
programáticamente sobre los estados, antes de renderizar.

**4. La cantidad de fotogramas marcados como empuje coincide con los empujes
reportados** por el motor: 5 en N1, 18 en N2, 22 en N3. Es la comprobación de
que el reproductor está leyendo bien la solución y no inventando.

**5. Los archivos pesan poco.** Un GIF de N1 debería estar en decenas de KB.
Si un GIF pasa de un par de MB, bajar la resolución: van a un repositorio que
usan cuatro personas.

---

## Cosas que NO van en esta fase

- Las figuras de análisis (barras, curvas) → Fase 8. Acá se dibujan **tableros**,
  no gráficos.
- Interactividad, controles de reproducción, jugar a mano. No hace falta y suma
  riesgo.

---

## Al terminar

1. Corré la verificación y mostrá la salida, con el tamaño de cada archivo.
2. Mostrá la tira de fotogramas de N1 como texto ASCII en la terminal, además
   de la imagen: es la forma más rápida de que alguien la revise sin abrir nada.
3. Escribí `docs/resumenes/FASE_7_RESUMEN.md`, incluyendo el criterio que usaste
   para elegir los fotogramas clave de las soluciones largas.
4. Listá los archivos creados y **esperá**. No commitees.