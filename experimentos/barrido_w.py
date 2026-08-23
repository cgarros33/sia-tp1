"""El barrido del parámetro w: el único experimento nuevo de la Fase 8.

    f(n) = (1 - w) · g(n) + w · h(n)

    w = 0     costo uniforme
    w = 0,5   A*
    w = 1     Greedy

Se corre desde la raíz del repositorio:

    python3 -m experimentos.barrido_w

POR QUÉ ES EL EXPERIMENTO MÁS FUERTE DEL TP
    La cátedra advirtió que si se analiza cómo se relacionan dos variables, las
    variables tienen que tener sentido, y una correlación sirve cuando se mueve
    UNA variable y todo lo demás queda fijo.

    Acá se mueve exactamente un parámetro. Entre dos filas del mismo nivel, el
    código ejecutado es literalmente el mismo y los datos también: el nivel, la
    heurística, la capa de poda, el límite de nodos, el orden de DIRECCIONES y
    el criterio de desempate no cambian. Lo único distinto son los dos números
    que pesan g y h. Todo lo que se observe es atribuible a eso y a nada más.

    El contraejemplo, que conviene tener a mano: "cantidad de cajas contra
    tiempo" mezclando niveles distintos confunde el efecto de las cajas con el
    del tamaño y la topología del tablero. Ése es el análisis que NO se hace.

UNA SOLA CORRIDA POR (nivel, w), Y NO ES PEREZA
    Los dos ejes que va a graficar la figura 3 —costo y nodos expandidos— son
    determinísticos. No se asume: está medido sobre las 645 filas de
    `resultados.csv`, donde ninguna configuración varía sus nodos entre sus
    cinco corridas. Promediar daría el mismo número y las barras de error
    darían cero, que es exactamente la clase de decoración por la que la cátedra
    pregunta. El tiempo sí varía, se guarda igual, y NO se grafica.

POR QUÉ EL QUIEBRE ESTÁ EN w = 0,5, ANTES DE MEDIR NADA
    Dividir f por (1 - w) no cambia el orden de la frontera y deja
    g + [w/(1-w)] · h. Para w <= 0,5 ese factor es <= 1, o sea que es A* con una
    heurística h' = c·h con c <= 1: si h es admisible, h' también lo es y la
    solución sigue siendo óptima. Para w > 0,5 el factor pasa de 1 y la garantía
    se cae. El quiebre no es un hallazgo empírico: es el punto donde se pierde
    la admisibilidad.

QUÉ SE DESCARTÓ
    Reusar el runner de la Fase 6. Sus tuplas son (nivel, método, heurística,
    poda, corrida, orden) y no tienen dimensión `w`: agregarla obligaría a tocar
    un entregable ya verificado de otra fase para un experimento que corre una
    sola vez.
"""

import csv
import sys
import time
from pathlib import Path

from main import cargar_config
from src.busqueda import hpa
from src.deadlocks import construir as construir_detector
from src.heuristicas import construir as construir_heuristica
from src.modelo import Problema, leer_archivo

RAIZ = Path(__file__).resolve().parent.parent
NIVELES = RAIZ / 'niveles'
SALIDA = RAIZ / 'experimentos' / 'barrido_w.csv'

#: 21 valores. Se generan como i/20 y no sumando 0,05 repetidamente: sumar
#: flotantes veinte veces da 0,30000000000000004 y ensucia la columna del CSV.
PASOS = 20

#: Los tres niveles del barrido, con su óptimo publicado al lado para que el CSV
#: se pueda auditar sin abrir otro archivo.
NIVELES_DEL_BARRIDO = (
    ('n2_akk04', 45),
    ('n3_caminata', 104),
    ('n4_matching', 70),
)

#: Todo lo que se mantiene fijo mientras se mueve w.
HEURISTICA = 'h5'
DEADLOCKS = 'completo'

COLUMNAS = [
    'nivel', 'w', 'heuristica', 'deadlocks', 'exito', 'motivo_fin',
    'costo', 'costo_optimo', 'empujes', 'nodos_expandidos', 'nodos_generados',
    'frontera_maxima', 'memoria_maxima', 'tiempo_s',
]


def valores_de_w(pasos=PASOS):
    """w = 0, 0,05, ..., 1 como fracciones exactas de `pasos`."""
    return [i / pasos for i in range(pasos + 1)]


def correr_barrido(salida=SALIDA, max_nodos=None):
    """Corre el barrido completo y escribe el CSV. Devuelve las filas."""
    if max_nodos is None:
        max_nodos = cargar_config(RAIZ / 'config.json')['max_nodos']

    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    filas = []

    for nombre, optimo in NIVELES_DEL_BARRIDO:
        tablero, inicial = leer_archivo(NIVELES / f'{nombre}.sok')
        # El problema se construye UNA vez por nivel y se comparte entre los 21
        # valores de w: es parte de lo que se mantiene fijo.
        problema = Problema(tablero, inicial,
                            detector_deadlocks=construir_detector(DEADLOCKS, tablero))

        for w in valores_de_w():
            # La heurística se construye de nuevo en cada corrida a propósito.
            # h5 memoriza por configuración de cajas, y compartir esa memoria
            # entre dos valores de w haría que la segunda corrida arrancara con
            # trabajo ya hecho por la primera: los nodos no cambiarían, pero el
            # tiempo sí, y el tiempo también se guarda.
            heuristica = construir_heuristica(HEURISTICA, problema)
            comienzo = time.perf_counter()
            r = hpa(problema, heuristica, w=w, nombre_heuristica=HEURISTICA,
                    max_nodos=max_nodos, nivel=nombre)
            fila = {
                'nivel': nombre,
                'w': f'{w:.2f}',
                'heuristica': HEURISTICA,
                'deadlocks': DEADLOCKS,
                'exito': r.exito,
                'motivo_fin': r.motivo_fin,
                'costo': r.costo if r.costo is not None else '',
                'costo_optimo': optimo,
                'empujes': r.empujes if r.empujes is not None else '',
                'nodos_expandidos': r.nodos_expandidos,
                'nodos_generados': r.nodos_generados,
                'frontera_maxima': r.frontera_maxima,
                'memoria_maxima': r.memoria_maxima,
                'tiempo_s': f'{time.perf_counter() - comienzo:.3f}',
            }
            filas.append(fila)
            print(f'  {nombre:<14} w={w:.2f}  costo {str(r.costo):>4}  '
                  f'expandidos {r.nodos_expandidos:>9,}'.replace(',', '.'))

    with open(salida, 'w', encoding='utf-8', newline='') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
        escritor.writeheader()
        escritor.writerows(filas)

    return filas


def main() -> int:
    print(f'Barrido de w — heurística {HEURISTICA}, poda {DEADLOCKS}, '
          f'{PASOS + 1} valores de w por nivel')
    print('Lo único que cambia entre dos filas del mismo nivel es w.\n')
    filas = correr_barrido()
    print(f'\n{len(filas)} corridas. Salida: {SALIDA.relative_to(RAIZ)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
