"""El barrido del parámetro w: el único experimento nuevo de la Fase 8."""

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

PASOS = 20

NIVELES_DEL_BARRIDO = (
    ('n2_akk04', 45),
    ('n3_caminata', 104),
    ('n4_matching', 70),
)

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
        problema = Problema(tablero, inicial,
                            detector_deadlocks=construir_detector(DEADLOCKS, tablero))

        for w in valores_de_w():
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
