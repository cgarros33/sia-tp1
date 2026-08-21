# 03 — Los números de oro

La tabla de verificación del proyecto. Todo cambio en `src/` tiene que seguir
reproduciéndola.

---

## Nivel 1 de exigencia: verdad externa. No se negocia.

Estos valores **no salen de nuestro código**. Son los récords publicados por
jugadores humanos en game-sokoban.com, y nuestro solver los reprodujo
exactamente durante la transcripción de los niveles.

| Nivel | Archivo | Colección | Cajas | Celdas | Movimientos | Empujes |
|---|---|---|---|---|---|---|
| N1 | `n1_micro.sok` | ABHT 02 · 01 (lid 37953) | 1 | 12 | **8** | **5** |
| N2 | `n2_akk04.sok` | A.K.K. · 04 (lid 29619) | 4 | 32 | **45** | **18** |
| N3 | `n3_caminata.sok` | Microban · 29 (lid 953) | 2 | 35 | **104** | **22** |
| N4 | `n4_matching.sok` | A.K.K. · 02 (lid 29617) | 4 | 31 | **70** | **22** |
| N5 | `n5_limite.sok` | Sasquatch XII · 06 (lid 8602) | 4 | 41 | **306** | **99** |

**Si un método óptimo (BFS, IDDFS, A\* con heurística admisible) devuelve un
costo distinto al de esta tabla, hay un bug.** No hay otra explicación posible:
o el motor está mal, o la heurística no es admisible, o el nivel se rompió.

Que coincidan **los dos** números —movimientos y empujes— es lo que da
confianza en la transcripción. Con una sola pared mal puesta, el óptimo daría
distinto.

## Nivel 2 de exigencia: regresión interna

Los **nodos expandidos** son una métrica de nuestra implementación. No hay
verdad externa contra la cual compararlos: dependen del orden en que se generan
los sucesores, del criterio de desempate de la frontera y de la política de
estados repetidos.

Por eso el procedimiento es:

1. Terminada la Fase 2, medir los nodos expandidos por BFS en los cinco niveles.
2. Congelar esos valores en `tests/test_regresion.py`.
3. A partir de ahí, **si cambian, hay que entender por qué antes de actualizar
   el número esperado**.

Valores de referencia obtenidos durante la verificación de los niveles, con una
implementación equivalente a la especificada. Sirven como orden de magnitud
esperado, **no** como valor exacto a alcanzar:

| Nivel | Nodos BFS (orden esperado) | Tiempo aproximado |
|---|---|---|
| N1 | decenas | instantáneo |
| N2 | ~4 × 10⁴ | < 1 s |
| N3 | ~6 × 10³ | < 1 s |
| N4 | ~6 × 10⁵ | segundos |
| N5 | ~2 × 10⁶ | decenas de segundos |

Si al medir sale algo del mismo orden, está bien. Si sale un orden de magnitud
distinto, algo del motor no está haciendo lo que creemos.

## Test de control del motor

Independiente de los valores concretos, esta invariante siempre tiene que
cumplirse:

> **A\* con h = 0 debe expandir exactamente la misma cantidad de nodos que BFS**,
> y devolver el mismo costo, en los cinco niveles.

El motivo: con h = 0, A\* degenera en búsqueda de costo uniforme, y con costo
unitario la búsqueda de costo uniforme es BFS. Si difieren, el bug está en el
**motor** (orden de la frontera, control de repetidos, o el momento en que se
verifica la condición de meta) y no en ninguna heurística.

Es el primer test que hay que correr cuando algo no cierra.

## Otras invariantes que valen como test

| Invariante | Por qué |
|---|---|
| La solución es ejecutable: aplicar la secuencia de acciones desde el inicial termina en meta | Atrapa errores en la reconstrucción del camino, que el costo solo no detecta |
| Dibujar el estado inicial y volver a parsearlo da el mismo problema | Si falla, el reproductor de la Fase 7 va a mostrar tableros mal |
| DFS encuentra solución pero con costo estrictamente mayor al óptimo | Documenta que no es óptimo, que es justamente lo que se quiere mostrar |
| Greedy expande menos nodos que BFS y su costo es mayor o igual | Documenta el compromiso velocidad contra optimalidad |
| IDDFS usa mucha menos memoria máxima que BFS y expande más nodos | Es su razón de existir |
| Activar la poda de deadlocks no cambia el costo, pero baja los nodos | Prueba que la poda preserva optimalidad |
| A\*(h₃) expande menos nodos que A\*(h₂) con el mismo costo | Verificación empírica de la dominancia |

## Fuera de alcance, documentado a propósito

**ABHT 02 · 03** (lid 37955): 5 cajas, 89 celdas transitables, óptimo publicado
de 155 movimientos y 60 empujes.

Espacio de estados ≈ 3,7 × 10⁹, contra 9,8 × 10⁵ de N4: unas 3.700 veces más
grande. A\* con matching y poda de deadlocks expandió 3.000.000 de nodos en 47
segundos y su frontera todavía iba por **f = 76** cuando el óptimo es 155.

No entra en la batería de experimentos. Sirve como evidencia del muro en la
Fase 8.

## Cómo estimar si un nivel nuevo entra

```
espacio ≈ celdas_transitables × C(celdas_transitables, cajas)
```

| Cajas | Cómodo (≤10⁷) | Nivel difícil (≤10⁸) |
|---|---|---|
| 2 | hasta 271 celdas | 399 |
| 3 | 88 | 157 |
| 4 | 48 | 76 |
| 5 | 34 | 49 |
| 6 | 27 | 37 |

El número de movimientos de la solución **no** es un buen predictor. N3 tiene
una solución de 104 movimientos y se resuelve en 6.000 nodos; N5 tiene 306
movimientos y necesita 2 millones. La diferencia no está en el largo de la
solución sino en la cantidad de cajas.
