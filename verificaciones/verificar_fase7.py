"""Verificación de la Fase 7 — el reproductor estado por estado.

Se corre desde la raíz del repositorio:

    python3 -m verificaciones.verificar_fase7

Genera todos los archivos de `presentacion/` y los verifica. Tarda unos minutos,
casi todos gastados en resolver `n5_limite` con BFS.

LAS CINCO COMPROBACIONES DEL CRITERIO DE ACEPTACIÓN

  1. El GIF de N1 existe y SE ABRE. No alcanza con que el archivo esté: se lo
     vuelve a leer con Pillow y se cuentan sus fotogramas. Un GIF corrupto pesa
     y existe igual.
  2. La cantidad de fotogramas de cada GIF es `costo + 1`, uno por estado,
     contando el inicial y el final. Se comprueba contra el archivo releído, no
     contra la lista que se usó para escribirlo.
  3. El último estado tiene todas las cajas sobre metas. Se verifica sobre los
     estados, antes de renderizar: si el camino no termina en meta, el problema
     no es del dibujo.
  4. La cantidad de fotogramas marcados como empuje coincide con los empujes que
     reportó el motor, que son los récords publicados: 5 · 18 · 22 · 22 · 99. Es
     la comprobación de que el reproductor lee la solución y no la inventa.
  5. Los archivos pesan poco. Un GIF que pase de 2 MB va a un repositorio que
     usan cuatro personas y no entra en ninguna diapositiva.

POR QUÉ LAS SOLUCIONES SALEN DE BFS Y NO DE A\\*
    A\\* con h₅ y poda resolvería `n5_limite` en 426.808 nodos en vez de
    2.028.239, y la verificación tardaría bastante menos. Pero un nivel puede
    tener varias soluciones óptimas distintas, con el mismo costo y DISTINTA
    cantidad de empujes, y BFS es el método cuyo costo Y empujes están
    contrastados contra el récord publicado en game-sokoban.com. Es lo que hace
    que la comprobación 4 valga contra la tabla de `docs/03_NUMEROS_DE_ORO.md` y
    no sólo contra sí misma.

Termina con código de salida 0 si todo pasa y 1 si algo falla.
"""

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

#: Un GIF más pesado que esto no entra en una diapositiva ni en un repositorio
#: compartido. Es el criterio 5, escrito como número.
LIMITE_BYTES = 2 * 1024 * 1024

# Qué se genera por nivel, con el costo y los empujes publicados. Sale de la
# tabla "Qué generar" de la especificación.
#
# Los milisegundos por paso bajan a medida que la solución se alarga: 400 ms es
# cómodo para mirar 8 movimientos y son 42 segundos de GIF para los 104 de N3,
# que es más de lo que dura la diapositiva. N4 y N5 no llevan GIF: 306
# movimientos no se muestran animados de ninguna manera.
PLAN = (
    # archivo, costo, empujes, ms por paso (None = sin GIF), criterio de la tira
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
    """La tira, pero en texto XSB, para revisarla sin abrir ningún archivo.

    Es la forma más rápida de que alguien controle que el reproductor dibuja lo
    que dice dibujar: `Tablero.dibujar()` existe desde la Fase 1 y es una
    implementación distinta de la de `render.py`, así que si las dos coinciden,
    coinciden por el estado y no por el código.
    """
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

        # Comprobaciones 1 y 2: el archivo se relee y se cuentan SUS fotogramas.
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
        # Comprobación 4.
        if gif.empujes != empujes:
            errores.append(
                f'el GIF marca {gif.empujes} fotogramas como empuje y el motor '
                f'reportó {empujes}. El reproductor está leyendo mal la solución.')
        # Comprobación 3.
        if not gif.ultimo_es_meta:
            errores.append('el último estado del GIF no tiene todas las cajas '
                           'sobre metas.')
        # Comprobación 5.
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
