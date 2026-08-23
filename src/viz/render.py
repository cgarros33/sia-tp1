"""Un estado dibujado como imagen, pensado para verse proyectado.

QUÉ REPRESENTA
    La misma información que `Tablero.dibujar()`, que devuelve texto XSB, pero en
    píxeles. El texto sirve para depurar y para los tests; esto sirve para la
    diapositiva.

LA DECISIÓN DE DISEÑO — la diferencia entre caja y caja sobre meta se nota por
FORMA, no sólo por color
    Es el dato más importante del fotograma: es lo que dice cuánto falta. Si la
    única diferencia fuera el color, en un proyector con luz ambiente —o para
    alguien que no distingue dos colores entre sí— la imagen dejaría de decir lo
    único que tiene que decir. Por eso una caja sobre meta además lleva un rombo
    adentro, que es la misma marca con la que se dibuja una meta vacía: se lee
    "esta caja está sobre una de esas".

    Por el mismo motivo la paleta no usa el par rojo/verde en ningún lado.

QUÉ SE DESCARTÓ
    Usar `matplotlib`, que era la otra opción de la especificación. Un tablero de
    Sokoban son rectángulos, rombos y círculos, o sea exactamente lo que hace
    `ImageDraw`, y dibujarlo directo da control exacto del tamaño en píxeles —que
    es lo que mantiene los GIF en decenas de KB, como pide el criterio 5— sin
    pasar por una figura, unos ejes y un writer de animación. Además matplotlib
    depende de Pillow, así que elegirlo habría sido agregar una dependencia
    grande para terminar usando ésta por dentro.
"""

from PIL import Image, ImageDraw, ImageFont

#: Píxeles por celda. 48 da tableros de entre 400 y 600 píxeles de lado en los
#: cinco niveles: se proyecta bien y el GIF pesa poco.
LADO = 48
MARGEN = 12

# Paleta de alto contraste. Ningún par de elementos se distingue sólo por
# rojo/verde: caja y caja sobre meta son arena y azul, que se separan también en
# luminosidad, y encima llevan formas distintas.
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
    """La banda de texto crece con la celda, en vez de ser una constante.

    La tira de fotogramas dibuja los mismos tableros a la mitad de tamaño: con
    una banda fija, el encabezado de un fotograma chico ocuparía casi tanto como
    el tablero. Así la proporción entre texto y tablero es la misma siempre.
    """
    return max(18, lado * 3 // 4)


def fuente(tamanio):
    """La fuente por defecto de Pillow al tamaño pedido, cacheada.

    Se usa la que trae Pillow y no una del sistema a propósito: una ruta a una
    tipografía instalada funciona en la máquina de quien la escribió y falla en
    la de los otros tres.
    """
    if tamanio not in _FUENTES:
        _FUENTES[tamanio] = ImageFont.load_default(size=tamanio)
    return _FUENTES[tamanio]


def _rombo(dibujo, x, y, radio, relleno=None, contorno=None, grosor=2):
    """La marca de meta: un rombo centrado en (x, y).

    Es la misma forma dibujada hueca sobre el piso —meta vacía— y rellena dentro
    de una caja —caja sobre meta—, para que las dos cosas se lean como lo mismo.
    """
    dibujo.polygon([(x, y - radio), (x + radio, y), (x, y + radio), (x - radio, y)],
                   fill=relleno, outline=contorno, width=grosor)


def dibujar(tablero, estado, encabezado='', lado=LADO):
    """Devuelve la `Image` de un estado sobre su tablero.

    `encabezado` es texto libre y se dibuja arriba del tablero; el reproductor le
    pasa "paso 5/8 · empuje". La función no sabe qué es un paso ni un empuje: eso
    es información del camino, no del estado, y mezclarla acá obligaría a pasarle
    media solución para dibujar un tablero.
    """
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

        # La cuadrícula tenue no es decoración: con ella se pueden contar los
        # casilleros que recorre el jugador mirando el GIF, que es justamente lo
        # que se quiere mostrar en n3_caminata.
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
            # El círculo es más chico que la celda para que, si el jugador está
            # parado sobre una meta, el rombo de abajo siga asomando.
            radio = lado // 2 - lado // 5
            dibujo.ellipse((centro_x - radio, centro_y - radio,
                            centro_x + radio, centro_y + radio), fill=JUGADOR)

    return imagen
