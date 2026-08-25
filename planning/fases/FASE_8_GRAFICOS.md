# FASE 8 — Gráficos, análisis y material de presentación

**Dueño:** Leo · **Estado:** pendiente

La última fase con código. Al terminar, existen las figuras que se van a
proyectar y el análisis escrito que las acompaña.

---

## Archivos a crear

```
experimentos/barrido_w.py       (el único experimento nuevo de esta fase)
experimentos/graficos.py
presentacion/figuras/           (salida, se versiona)
verificaciones/verificar_fase8.py
```

Los gráficos salen del `resultados.csv` de la Fase 6. **No se vuelve a correr
ninguna búsqueda para graficar**, salvo el barrido de `w`, que es un experimento
nuevo.

---

## El experimento nuevo: barrido del parámetro w

El motor ya tiene, desde la Fase 2, la frontera parametrizada:

```
f(n) = (1−w)·g(n) + w·h(n)
```

| `w` | Qué es |
|---|---|
| 0 | Búsqueda de costo uniforme (equivale a BFS con costo unitario) |
| 0,5 | A\* |
| 1 | Greedy |

Barrer `w` de 0 a 1 en pasos de 0,05, con h₄ o h₅, sobre dos o tres niveles.
Se obtiene **en una sola familia de experimentos** el compromiso completo entre
calidad de la solución y esfuerzo de búsqueda.

**Por qué es el experimento más fuerte del TP.** La cátedra advirtió que si se
analiza cómo se relacionan dos variables, las variables tienen que tener
sentido. Una correlación sirve cuando **se mueve una variable y todo lo demás
queda fijo**. Acá se mueve exactamente un parámetro, sobre el mismo nivel, con
la misma heurística y el mismo motor. Es el ejemplo de manual de un experimento
controlado.

Guardá el resultado en su propio CSV.

> **Lo esperable:** al crecer `w`, los nodos expandidos bajan y el costo de la
> solución sube, con un quiebre alrededor de `w = 0,5`. Si sale otra cosa,
> **reportá lo que salga** y buscá la explicación. Un resultado inesperado bien
> explicado vale más que uno esperado.

---

## Las cuatro figuras

### Figura 1 — Nodos expandidos por método y nivel

Barras agrupadas, **escala logarítmica** (el rango va de decenas a millones).
Los métodos que hallan el óptimo en un color, los subóptimos en otro, con
leyenda.

Responde: *¿cuánto aporta cada método?*

### Figura 2 — Dominancia empírica de las heurísticas

Dispersión. Eje X: informatividad `h(s₀)/óptimo`. Eje Y: nodos expandidos,
escala logarítmica. Un punto por heurística, un panel o color por nivel.

Responde: *¿una heurística más informada expande menos nodos?* Y permite
mostrar la cadena h₁ → h₅ como una trayectoria, no como una tabla.

Los valores de h₀ y h₁ ya están medidos: h₁ da 0,125 · 0,089 · 0,019 · 0,057 ·
0,013 en los cinco niveles.

### Figura 3 — El barrido de w

Dos ejes Y sobre el mismo eje X (`w` de 0 a 1): costo de la solución y nodos
expandidos. Marcar dónde caen costo uniforme, A\* y Greedy.

Responde: *¿cuánto se paga por apurar la búsqueda?* Es la figura que conecta
todo el trabajo con la teoría de la Clase 4.

### Figura 4 — El muro

Dispersión log-log. Eje X: tamaño estimado del espacio de estados,
`celdas × C(celdas, cajas)`. Eje Y: nodos expandidos por BFS.

Incluir los cinco niveles **y el nivel descartado** (ABHT 02 · 03, 5 cajas, 89
celdas, espacio de 3,7 × 10⁹), marcado como no resuelto.

Responde: *¿por qué hay un límite y dónde está?* Es la figura de cierre.

### Requisitos comunes

- **Legibles proyectadas:** fuentes grandes, líneas gruesas, sin grillas
  cargadas.
- **Que no dependan de distinguir colores** para leerse: usar también marcadores
  o rellenos distintos.
- **Ejes rotulados con unidades** y escala indicada cuando es logarítmica.
- **Barras de error sólo donde hay variabilidad real**, o sea sólo en DFS y en
  los tiempos. Poner barras de error sobre un valor determinístico es decorar
  con una incertidumbre que no existe, y es exactamente el tipo de cosa por la
  que preguntan.
- Exportar en PNG a resolución de proyección y en un formato vectorial.

---

## El análisis escrito

Las figuras sin lectura no dicen nada. En el resumen de la fase, **una sección
por figura** con: qué se ve, qué lo causa, y qué conclusión se saca.

Cuatro conclusiones que los datos ya recogidos permiten sostener, para usar como
guía:

1. **La información heurística cambia el esfuerzo, no la calidad.** BFS y A\*
   con heurística admisible devuelven el mismo costo; lo que cambia es cuántos
   nodos hay que abrir.
2. **La dominancia se verifica empíricamente.** Una heurística que domina a otra
   en valor expande menos nodos, con el mismo costo.
3. **Optimizar movimientos limita a las heurísticas.** Todas estiman empujes,
   pero en N3 el 79 % de los movimientos de la solución óptima son caminata del
   jugador, y ninguna heurística los ve. Es la causa medida de que A\* rinda
   mucho menos acá que en el 8-puzzle.
4. **El muro es combinatorio, no de largo de solución.** N3 tiene una solución
   de 104 movimientos y se resuelve en 6.360 nodos; N5 tiene 306 movimientos y
   necesita 2.028.239. La diferencia no es el largo: es que N5 tiene 4 cajas y
   N3 tiene 2.

Y una que hay que contar aunque incomode:

5. **IDDFS no compró lo que promete.** El de manual usa memoria lineal porque no
   guarda visitados; en Sokoban eso es impracticable, así que le agregamos
   detección de repetidos y con eso perdimos la ventaja. Medido: 0,87× la
   memoria de BFS en N2 y 0,98× en N3, pagando 158× más nodos en N3.

---

## Material de presentación

Carpeta `presentacion/`:

```
presentacion/
  figuras/          las cuatro figuras en resolución de proyección
  animaciones/      los GIF de la Fase 7
  tiras/            las tiras de fotogramas de la Fase 7
```

El PDF de las diapositivas lo arma el grupo por fuera y se versiona en
`docs/presentacion/`. Esta fase aporta los insumos, no las diapositivas.

---

## Criterio de aceptación

**1. Las cuatro figuras se generan con un comando**, desde el CSV, sin correr
búsquedas de nuevo (salvo el barrido de `w`, que tiene su propio comando).

**2. El barrido de `w` está corrido** y su CSV versionado.

**3. Regenerar es idempotente:** correr `graficos.py` dos veces produce las
mismas imágenes a partir del mismo CSV.

**4. Ninguna figura tiene barras de error sobre datos determinísticos.**
Revisalo explícitamente y decilo en el resumen.

**5. Prueba de legibilidad:** abrir cada figura al 50 % de su tamaño y verificar
que los rótulos se siguen leyendo. Es la aproximación más barata a verla
proyectada desde el fondo del aula.

---

## Al terminar

1. Mostrá la salida de la verificación y listá las figuras con su tamaño.
2. Escribí `docs/resumenes/FASE_8_RESUMEN.md` con el análisis escrito: una
   sección por figura y las conclusiones.
3. Listá los archivos creados y **esperá**. No commitees. Las figuras y los CSV
   los commitea Leo junto con el resto.
