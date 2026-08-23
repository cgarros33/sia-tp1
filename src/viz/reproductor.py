"""Una solución convertida en archivos: el GIF animado y la tira de fotogramas."""

import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from . import render

CRITERIOS = ('empujes', 'todos')


@dataclass
class Reproduccion:
    """Lo que salió de generar un archivo, para no tener que volver a medirlo."""

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
    """Escribe el GIF animado de una solución, un fotograma por estado."""
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)

    estados = problema.reconstruir_estados(acciones)
    imagenes, empujes = _dibujar_pasos(problema, estados, range(len(estados)),
                                       titulo, lado)

    imagenes = [imagen.convert('P', palette=Image.ADAPTIVE, colors=16)
                for imagen in imagenes]
    duraciones = [ms_por_paso] * len(imagenes)
    duraciones[-1] = ms_por_paso * 5
    imagenes[0].save(salida, save_all=True, append_images=imagenes[1:],
                     duration=duraciones, loop=0, optimize=True)

    return _resumen(problema, estados, salida, len(imagenes), empujes)


def indices_de_la_tira(estados, criterio='empujes') -> list[int]:
    """Qué estados entran en la tira."""
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
    """Escribe la grilla de fotogramas clave de una solución."""
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
