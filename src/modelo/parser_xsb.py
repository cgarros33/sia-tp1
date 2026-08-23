"""Lector de niveles en formato XSB, el estándar de Sokoban."""

from pathlib import Path

from .estado import Estado
from .tablero import Tablero

PARED = '#'
META = '.'
CAJA = '$'
CAJA_EN_META = '*'
JUGADOR = '@'
JUGADOR_EN_META = '+'
PISO = ' '

CARACTERES_VALIDOS = frozenset(
    (PARED, META, CAJA, CAJA_EN_META, JUGADOR, JUGADOR_EN_META, PISO)
)


class NivelInvalido(Exception):
    """El texto no describe un nivel de Sokoban jugable."""


def _extraer_filas(texto: str) -> list[str]:
    """Se queda con las líneas del tablero y descarta todo lo demás."""
    limpias = []
    for linea in texto.splitlines():
        if linea.lstrip().startswith(';'):
            continue
        limpias.append(linea.rstrip())

    inicio = 0
    while inicio < len(limpias) and not limpias[inicio]:
        inicio += 1
    fin = inicio
    while fin < len(limpias) and limpias[fin]:
        fin += 1
    return limpias[inicio:fin]


def leer_texto(texto: str, nombre: str = '') -> tuple[Tablero, Estado]:
    """Convierte un nivel en formato XSB en (Tablero, Estado inicial)."""
    filas = _extraer_filas(texto)
    if not filas:
        raise NivelInvalido(f'{nombre or "nivel"}: no hay ninguna fila de tablero.')

    alto = len(filas)
    ancho = max(len(fila) for fila in filas)

    paredes, metas, cajas = set(), set(), set()
    jugadores = []

    for f, fila in enumerate(filas):
        for c in range(ancho):
            caracter = fila[c] if c < len(fila) else PARED
            if caracter not in CARACTERES_VALIDOS:
                raise NivelInvalido(
                    f'{nombre or "nivel"}: carácter {caracter!r} no válido '
                    f'en la fila {f}, columna {c}.'
                )
            p = f * ancho + c
            if caracter == PARED:
                paredes.add(p)
            elif caracter == META:
                metas.add(p)
            elif caracter == CAJA:
                cajas.add(p)
            elif caracter == CAJA_EN_META:
                cajas.add(p)
                metas.add(p)
            elif caracter == JUGADOR:
                jugadores.append(p)
            elif caracter == JUGADOR_EN_META:
                jugadores.append(p)
                metas.add(p)

    if len(jugadores) != 1:
        raise NivelInvalido(
            f'{nombre or "nivel"}: hay {len(jugadores)} jugadores y tiene que haber 1.'
        )
    if not cajas:
        raise NivelInvalido(f'{nombre or "nivel"}: no hay ninguna caja.')
    if len(cajas) != len(metas):
        raise NivelInvalido(
            f'{nombre or "nivel"}: hay {len(cajas)} cajas y {len(metas)} metas. '
            f'Con distinta cantidad el nivel no tiene solución posible.'
        )

    tablero = Tablero(alto, ancho, frozenset(paredes), frozenset(metas), nombre)
    return tablero, Estado(jugadores[0], frozenset(cajas))


def leer_archivo(ruta) -> tuple[Tablero, Estado]:
    """Lee un `.sok` del disco. El nombre del archivo queda como nombre del nivel."""
    ruta = Path(ruta)
    texto = ruta.read_text(encoding='utf-8')
    return leer_texto(texto, nombre=ruta.name)
