"""Una solución convertida en archivos: el GIF animado y la tira de fotogramas.

POR QUÉ LA SALIDA ES DOBLE
    El GIF es para la presentación: se inserta en la diapositiva y corre solo, sin
    demo en vivo que pueda fallar ni terminal que abrir. Con 25 a 30 minutos y
    cuatro personas hablando, una demo interactiva que tarda veinte segundos en
    arrancar es tiempo regalado.

    La tira es para el PDF, que no anima. Es una grilla con los estados
    importantes de la solución, numerados.

LA DECISIÓN DE DISEÑO — el reproductor no vuelve a aplicar las reglas del juego
    Los estados salen de `problema.reconstruir_estados()`, que reaplica las
    acciones pasando por `sucesores()`. Tener acá una segunda implementación de
    "qué pasa cuando el jugador se mueve" sería la forma más fácil de dibujar un
    camino que no es el que recorrió la búsqueda, y el error sería invisible:
    saldría un GIF perfectamente prolijo de otra cosa.

    De ahí sale también que un paso sea empuje si el conjunto de cajas cambió
    respecto del anterior. El motor lo sabe —`sucesores()` devuelve
    `hubo_empuje`— pero no lo guarda en los estados, y pedírselo obligaría a
    pasarle al reproductor el `Resultado` entero además del camino. Leerlo de dos
    estados consecutivos da el mismo número y no acopla nada; la verificación
    comprueba que coincida con lo que reportó el motor.

QUÉ SE DESCARTÓ
    Reconstruir el camino a mano. `reconstruir_estados()` ignora la poda de
    deadlocks desde la Fase 1 justamente por esto: la poda es una optimización de
    la búsqueda, no una regla del juego, y si el detector de la Fase 5 tuviera un
    bug y descartara un estado legal, un reproductor que podara cortaría el camino
    a la mitad con un error de "acción no legal", que apunta al lugar equivocado.
    Acá es donde se cobra aquella decisión, y no hay nada que hacer para
    aprovecharla: alcanza con no escribir el recorrido.
"""

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from . import render

#: Los estados que entran en la tira. 'empujes' es el criterio por defecto: en
#: una imagen estática dos pasos de caminata consecutivos son casi el mismo
#: dibujo, porque lo único que se movió es el jugador. 'todos' es para las
#: soluciones cortas, donde la tira completa entra sin problema.
CRITERIOS = ('empujes', 'todos')


@dataclass
class Reproduccion:
    """Lo que salió de generar un archivo, para no tener que volver a medirlo.

    La verificación de la fase necesita exactamente estos números y los quiere
    del mismo lugar que produjo el archivo: contarlos por separado sería
    verificar una cuenta contra sí misma.
    """

    ruta: Path
    fotogramas: int
    empujes: int
    ultimo_es_meta: bool
    bytes: int


def es_empuje(anterior, siguiente) -> bool:
    """True si el paso movió una caja. Ver la decisión de diseño del módulo."""
    return anterior.cajas != siguiente.cajas


def encabezado_de(paso, total, empuje, titulo='') -> str:
    """"n1_micro · paso 5/8 · empuje". El texto que va arriba de cada fotograma."""
    partes = [titulo] if titulo else []
    partes.append(f'paso {paso}/{total}')
    if empuje:
        partes.append('empuje')
    return ' · '.join(partes)


def _dibujar_pasos(problema, estados, pasos, titulo, lado):
    """Las imágenes de los pasos elegidos, y cuántos de ellos son empuje."""
    total = len(estados) - 1
    imagenes, empujes = [], 0
    for paso in pasos:
        # El paso 0 no viene de ninguna acción, así que no es empuje de nada.
        empuje = paso > 0 and es_empuje(estados[paso - 1], estados[paso])
        imagenes.append(render.dibujar(
            problema.tablero, estados[paso],
            encabezado=encabezado_de(paso, total, empuje, titulo), lado=lado))
        empujes += empuje
    return imagenes, empujes


def _resumen(problema, estados, ruta, fotogramas, empujes) -> Reproduccion:
    return Reproduccion(
        ruta=ruta,
        fotogramas=fotogramas,
        empujes=empujes,
        ultimo_es_meta=problema.es_meta(estados[-1]),
        bytes=ruta.stat().st_size,
    )


def generar_gif(problema, acciones, salida, ms_por_paso=400, titulo='',
                lado=render.LADO) -> Reproduccion:
    """Escribe el GIF animado de una solución, un fotograma por estado.

    `ms_por_paso` es configurable porque 400 ms es cómodo para las soluciones
    cortas y absurdo para las largas: en `n5_limite`, con 306 movimientos, serían
    dos minutos de GIF.

    El último fotograma dura cinco veces más que los demás. No es un adorno: el
    GIF se repite en bucle, y sin esa pausa el tablero resuelto —que es
    justamente lo que hay que ver— aparece 400 ms y se va.
    """
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)

    estados = problema.reconstruir_estados(acciones)
    imagenes, empujes = _dibujar_pasos(problema, estados, range(len(estados)),
                                       titulo, lado)

    # El GIF es un formato de paleta, así que la conversión ocurre sí o sí:
    # hacerla acá, con una paleta chica, es lo que mantiene el archivo en decenas
    # de KB. Los fotogramas usan los mismos nueve colores, así que la paleta
    # adaptativa da la misma en todos y no hay parpadeo entre cuadros.
    imagenes = [imagen.convert('P', palette=Image.ADAPTIVE, colors=16)
                for imagen in imagenes]
    duraciones = [ms_por_paso] * len(imagenes)
    duraciones[-1] = ms_por_paso * 5
    imagenes[0].save(salida, save_all=True, append_images=imagenes[1:],
                     duration=duraciones, loop=0, optimize=True)

    return _resumen(problema, estados, salida, len(imagenes), empujes)


def indices_de_la_tira(estados, criterio='empujes') -> list[int]:
    """Qué estados entran en la tira.

    'empujes' es el criterio que se defiende: **el estado inicial, el estado justo
    después de cada empuje, y el final**. Los pasos de caminata quedan afuera
    porque en una imagen estática no se distinguen del anterior: cambió de lugar
    el jugador y nada más. Y de cada empuje interesa el estado de DESPUÉS, que es
    el que muestra dónde quedó la caja.

    El inicial y el final se agregan siempre, aunque no sean empujes: una tira que
    no arranca en el tablero de partida ni termina en el resuelto no se entiende
    sola.
    """
    if criterio not in CRITERIOS:
        raise ValueError(f'Criterio desconocido: {criterio!r}. Opciones: {CRITERIOS}')
    if criterio == 'todos':
        return list(range(len(estados)))
    elegidos = {0, len(estados) - 1}
    elegidos.update(paso for paso in range(1, len(estados))
                    if es_empuje(estados[paso - 1], estados[paso]))
    return sorted(elegidos)


def generar_tira(problema, acciones, salida, criterio='empujes', titulo='',
                 lado=render.LADO // 2, columnas=None) -> Reproduccion:
    """Escribe la grilla de fotogramas clave de una solución.

    La grilla queda lo más cuadrada posible salvo que se pida otra cosa: con 100
    fotogramas, una sola fila sería ilegible y una sola columna, imposible de
    imprimir.

    El título va una vez arriba de la hoja y no en cada fotograma, que ya lleva su
    número de paso: repetir el nombre del nivel cien veces gasta espacio en lo
    único que no cambia.
    """
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)

    estados = problema.reconstruir_estados(acciones)
    pasos = indices_de_la_tira(estados, criterio)
    miniaturas, empujes = _dibujar_pasos(problema, estados, pasos, '', lado)

    columnas = columnas or math.ceil(math.sqrt(len(miniaturas)))
    filas = math.ceil(len(miniaturas) / columnas)
    ancho, alto = miniaturas[0].size
    banda = render.alto_encabezado(lado) if titulo else 0

    hoja = Image.new('RGB', (columnas * ancho + render.MARGEN * (columnas + 1),
                             filas * alto + render.MARGEN * (filas + 1) + banda),
                     render.CUADRICULA)
    if titulo:
        ImageDraw.Draw(hoja).text((render.MARGEN, render.MARGEN // 2), titulo,
                                  font=render.fuente(banda - banda // 4),
                                  fill=render.TEXTO)

    for posicion, miniatura in enumerate(miniaturas):
        fila, columna = divmod(posicion, columnas)
        hoja.paste(miniatura, (render.MARGEN + columna * (ancho + render.MARGEN),
                               render.MARGEN + banda + fila * (alto + render.MARGEN)))
    hoja.save(salida, optimize=True)

    return _resumen(problema, estados, salida, len(miniaturas), empujes)
