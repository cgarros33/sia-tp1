"""Verificación de la Fase 7 — el reproductor estado por estado."""

import sys
from pathlib import Path

from PIL import Image

from main import cargar_config
from src.busqueda import bfs
from src.modelo import Problema, leer_archivo
from src.viz import generar_gif, generar_tira
from src.viz.reproductor import indices_de_la_tira

RAIZ = Path(__file__).resolve().parent.parent
NIVELES = RAIZ / 'niveles'
ANIMACIONES = RAIZ / 'presentacion' / 'animaciones'
TIRAS = RAIZ / 'presentacion' / 'tiras'

LIMITE_BYTES = 2 * 1024 * 1024

PLAN = (
    ('n1_micro.sok', 8, 5, 400, 'todos'),
    ('n2_akk04.sok', 45, 18, 300, None),
    ('n3_caminata.sok', 104, 22, 200, None),
    ('n4_matching.sok', 70, 22, 100, None),
    ('n5_limite.sok', 306, 99, 100, None),
)

MAX_NODOS = cargar_config(RAIZ / 'config.json')['max_nodos']


def _n(valor) -> str:
    """Entero con puntos de miles, como se escribe en castellano."""
    return f'{valor:,}'.replace(',', '.')


def _kb(bytes_) -> str:
    return f'{bytes_ / 1024:.1f} KB'.replace('.', ',')


def _tira_ascii(tablero, estados, pasos, total, por_fila=5) -> str:
    """La tira, pero en texto XSB, para revisarla sin abrir ningún archivo."""
    bloques = []
    for paso in pasos:
        empuje = paso > 0 and estados[paso].cajas != estados[paso - 1].cajas
        titulo = f'paso {paso}/{total}' + (' *' if empuje else '')
        bloques.append([titulo] + tablero.dibujar(estados[paso]).split('\n'))

    ancho = max(len(linea) for bloque in bloques for linea in bloque) + 3
    lineas = []
    for inicio in range(0, len(bloques), por_fila):
        grupo = bloques[inicio:inicio + por_fila]
        alto = max(len(bloque) for bloque in grupo)
        for i in range(alto):
            lineas.append(''.join(
                (bloque[i] if i < len(bloque) else '').ljust(ancho)
                for bloque in grupo).rstrip())
        lineas.append('')
    return '\n'.join(lineas)


def verificar_nivel(archivo, costo, empujes, ms_por_paso, criterio):
    """Genera y verifica lo que le toca a un nivel. Devuelve la lista de errores."""
    nombre = archivo.replace('.sok', '')
    tablero, inicial = leer_archivo(NIVELES / archivo)
    problema = Problema(tablero, inicial)
    errores = []

    resultado = bfs(problema, max_nodos=MAX_NODOS, nivel=archivo)
    if not resultado.exito or resultado.costo != costo or resultado.empujes != empujes:
        errores.append(
            f'BFS devolvió {resultado.costo}/{resultado.empujes} y el récord '
            f'publicado es {costo}/{empujes}. No tiene sentido dibujar un camino '
            f'que no es el óptimo.')
        return errores, None

    print(f'=== {nombre}  ({costo} movimientos / {empujes} empujes) ===')

    if ms_por_paso is not None:
        gif = generar_gif(problema, resultado.acciones,
                          ANIMACIONES / f'{nombre}.gif',
                          ms_por_paso=ms_por_paso, titulo=nombre)

        try:
            with Image.open(gif.ruta) as abierto:
                fotogramas_en_disco = abierto.n_frames
        except Exception as e:
            fotogramas_en_disco = None
            errores.append(f'el GIF no se puede abrir: {e}')

        if fotogramas_en_disco is not None and fotogramas_en_disco != costo + 1:
            errores.append(
                f'el GIF tiene {fotogramas_en_disco} fotogramas y la solución '
                f'tiene {costo} movimientos: tendría que haber {costo + 1}, uno '
                f'por estado.')
        if gif.empujes != empujes:
            errores.append(
                f'el GIF marca {gif.empujes} fotogramas como empuje y el motor '
                f'reportó {empujes}. El reproductor está leyendo mal la solución.')
        if not gif.ultimo_es_meta:
            errores.append('el último estado del GIF no tiene todas las cajas '
                           'sobre metas.')
        if gif.bytes > LIMITE_BYTES:
            errores.append(f'el GIF pesa {_kb(gif.bytes)}, más que el límite de '
                           f'{_kb(LIMITE_BYTES)}. Bajar la resolución.')

        segundos = (gif.fotogramas - 1) * ms_por_paso / 1000
        print(f'  GIF   {gif.fotogramas:>4} fotogramas · {gif.empujes} empujes · '
              f'{ms_por_paso} ms/paso ≈ {segundos:.0f} s · {_kb(gif.bytes)}'
              f'   {gif.ruta.relative_to(RAIZ)}')

    if criterio is not None:
        tira = generar_tira(problema, resultado.acciones, TIRAS / f'{nombre}.png',
                            criterio=criterio,
                            titulo=f'{nombre} · {costo} movimientos · {empujes} empujes')
        if tira.empujes != empujes:
            errores.append(
                f'la tira marca {tira.empujes} fotogramas como empuje y el motor '
                f'reportó {empujes}.')
        if not tira.ultimo_es_meta:
            errores.append('el último estado de la tira no es meta.')
        print(f'  tira  {tira.fotogramas:>4} fotogramas · criterio {criterio!r} · '
              f'{_kb(tira.bytes)}   {tira.ruta.relative_to(RAIZ)}')

    return errores, (problema, resultado)


def main() -> int:
    print('Verificación de la Fase 7 — el reproductor estado por estado')
    print(f'Las soluciones salen de BFS, con límite de {_n(MAX_NODOS)} nodos, '
          f'porque es el método\ncuyos movimientos y empujes están contrastados '
          f'contra los récords publicados.\n')

    errores = []
    n1 = None
    for archivo, costo, empujes, ms_por_paso, criterio in PLAN:
        e, contexto = verificar_nivel(archivo, costo, empujes, ms_por_paso, criterio)
        errores += [f'{archivo}: {x}' for x in e]
        if archivo == 'n1_micro.sok':
            n1 = contexto
        print()

    if n1 is not None:
        problema, resultado = n1
        estados = problema.reconstruir_estados(resultado.acciones)
        print('=== La tira de N1 en texto, para revisarla sin abrir nada ===')
        print('El asterisco marca los pasos que son empuje.\n')
        print(_tira_ascii(problema.tablero, estados,
                          indices_de_la_tira(estados, 'todos'), resultado.costo))

    if not errores:
        print(f'{len(PLAN)}/{len(PLAN)} niveles OK. Las 5 comprobaciones pasan.')
        return 0
    print(f'HAY {len(errores)} FALLAS:')
    for e in errores:
        print(f'  {e}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
