"""Un estado dibujado como imagen, pensado para verse proyectado."""

from PIL import Image, ImageDraw, ImageFont

LADO = 48
MARGEN = 12

FONDO = (250, 249, 246)
PARED = (60, 63, 70)
PISO = (250, 249, 246)
CUADRICULA = (222, 220, 214)
META = (96, 99, 108)
CAJA = (226, 168, 68)
CAJA_BORDE = (140, 96, 16)
CAJA_EN_META = (38, 104, 170)
CAJA_EN_META_BORDE = (20, 58, 100)
JUGADOR = (28, 28, 32)
TEXTO = (44, 46, 52)

_FUENTES = {}


def alto_encabezado(lado):
    """La banda de texto crece con la celda, en vez de ser una constante."""
    return max(18, lado * 3 // 4)


def fuente(tamanio):
    """La fuente por defecto de Pillow al tamaño pedido, cacheada."""
    if tamanio not in _FUENTES:
        _FUENTES[tamanio] = ImageFont.load_default(size=tamanio)
    return _FUENTES[tamanio]


def _rombo(dibujo, x, y, radio, relleno=None, contorno=None, grosor=2):
    """La marca de meta: un rombo centrado en (x, y)."""
    dibujo.polygon([(x, y - radio), (x + radio, y), (x, y + radio), (x - radio, y)],
                   fill=relleno, outline=contorno, width=grosor)


def dibujar(tablero, estado, encabezado='', lado=LADO):
    """Devuelve la `Image` de un estado sobre su tablero."""
    banda = alto_encabezado(lado) if encabezado else 0
    ancho_imagen = tablero.ancho * lado + 2 * MARGEN
    alto_imagen = tablero.alto * lado + 2 * MARGEN + banda
    imagen = Image.new('RGB', (ancho_imagen, alto_imagen), FONDO)
    dibujo = ImageDraw.Draw(imagen)

    if encabezado:
        dibujo.text((MARGEN, MARGEN // 2), encabezado,
                    font=fuente(banda - banda // 4), fill=TEXTO)

    borde_caja = max(2, lado // 16)
    for p in range(tablero.alto * tablero.ancho):
        fila, columna = tablero.coordenadas(p)
        x0 = MARGEN + columna * lado
        y0 = MARGEN + banda + fila * lado
        celda = (x0, y0, x0 + lado, y0 + lado)
        centro_x, centro_y = x0 + lado / 2, y0 + lado / 2

        if p in tablero.paredes:
            dibujo.rectangle(celda, fill=PARED)
            continue

        dibujo.rectangle(celda, fill=PISO, outline=CUADRICULA)

        if p in estado.cajas:
            en_meta = p in tablero.metas
            margen_caja = lado // 6
            dibujo.rectangle((x0 + margen_caja, y0 + margen_caja,
                              x0 + lado - margen_caja, y0 + lado - margen_caja),
                             fill=CAJA_EN_META if en_meta else CAJA,
                             outline=CAJA_EN_META_BORDE if en_meta else CAJA_BORDE,
                             width=borde_caja)
            if en_meta:
                _rombo(dibujo, centro_x, centro_y, lado // 6, relleno=FONDO)
            continue

        if p in tablero.metas:
            _rombo(dibujo, centro_x, centro_y, lado // 4, contorno=META,
                   grosor=max(3, lado // 16))

        if p == estado.jugador:
            radio = lado // 2 - lado // 5
            dibujo.ellipse((centro_x - radio, centro_y - radio,
                            centro_x + radio, centro_y + radio), fill=JUGADOR)

    return imagen
