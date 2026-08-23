"""hₙₐ — las no admisibles, a propósito. La única entrada de la fase sin demostración.

    hna(s)  = 2 · h₄(s)
    hna4(s) = 4 · h₄(s)

Ninguna de las dos es admisible, y ése es todo el punto: existen para mostrar
QUÉ SE ROMPE cuando se pierde la admisibilidad. No llevan demostración, llevan
CONTRAEJEMPLO.

POR QUÉ MULTIPLICAR, Y NO ROMPERLA DE OTRA MANERA
    Una heurística no admisible se fabrica de muchas formas: asignación golosa en
    vez de matching, sumar el recorrido completo del jugador, contar cada caja
    fuera de meta como 2. Multiplicar es la mejor para el experimento porque
    AÍSLA LA VARIABLE: hna tiene exactamente la misma información que h₄, el
    mismo orden relativo entre estados, la misma forma. Lo único que cambia es la
    escala, así que todo lo que se observe es atribuible a haber perdido la
    admisibilidad y a nada más.

    Es la advertencia de la cátedra sobre correlaciones aplicada al diseño del
    experimento: se mueve una variable y se deja el resto fijo.

    (Para el oral: f = g + 2·h es lo mismo que ponderar h frente a g, así que
    estas dos son dos puntos del barrido de w de la Fase 8. Acá se ven como
    heurísticas; allá, como un parámetro continuo.)

POR QUÉ NO SON ADMISIBLES
    h₄ ya es una cota inferior ajustada de los empujes que faltan. Duplicarla
    rompe h ≤ h* apenas h₄ pasa la mitad del costo restante, y eso ocurre siempre
    cerca del final del camino: con una caja a un empuje de su meta, h₄ = 1 y
    2·h₄ = 2 cuando falta 1 movimiento. Medido sobre el camino óptimo, hna viola
    admisibilidad en los cinco niveles y hna4 también.

LOS TRES RESULTADOS — y por qué son DOS heurísticas y no una
    El criterio de la fase pide un nivel donde A* devuelva un costo mayor al
    óptimo. Con 2·h₄ NO PASA: devuelve el costo publicado en los CINCO niveles,
    porque h₄ subestima tanto —entre 0,21 y 0,63 del óptimo— que duplicarla la
    deja igual por debajo del costo real casi en todas partes. Por eso además
    está 4·h₄, que sí rompe la optimalidad.

        nivel          ópt.    A*(h₄)      A*(2·h₄)         A*(4·h₄)
        n1_micro          8        12     8 /     11     8 /        11
        n2_akk04         45     7.145    45 /  1.783    47 /     1.563
        n3_caminata     104     1.951   104 /  1.899   104 /     1.845
        n4_matching      70    54.754    70 / 32.584    82 /     1.661
        n5_limite       306   605.520   306 / 637.656   306 / 1.820.141

    1. Perder la admisibilidad pierde la GARANTÍA, no necesariamente la
       respuesta. 2·h₄ devolvió el óptimo en los cinco niveles, y nadie podía
       saberlo de antemano: si el resultado hubiera dependido de eso, habríamos
       entregado un número sin saber si era correcto.
    2. Cuando la pierde, la pierde caro. 4·h₄ en n4_matching termina 33x más
       rápido y devuelve 82 movimientos donde el óptimo es 70: 17 % peor.
    3. Sobreestimar TAMPOCO garantiza ir más rápido. En n5_limite, 2·h₄ expande
       MÁS nodos que h₄ (637.656 contra 605.520) y 4·h₄ expande el triple
       (1.820.141), y las tres devuelven 306. Una h inflada empuja a A* a
       comprometerse temprano con una rama equivocada, y desandarla cuesta más
       de lo que ahorró.

QUÉ SE DESCARTÓ
    1. Dejar sólo 4·h₄. Cumpliría el criterio con lo mínimo y se perdería el
       resultado 1, que es el más interesante de los tres.
    2. Dejar sólo 2·h₄ y reportar que el criterio no se cumple. Honesto y pobre:
       la fase se quedaría sin contraejemplo.
    3. Multiplicar h₅ en vez de h₄. Mezclaría dos cosas: h₅ tiene el término del
       jugador, que se comporta distinto. h₄ es el último eslabón cuya cuenta es
       puramente de empujes, así que es el que deja el experimento limpio.
"""

from .h4_matching_real import h4


def _h4_escalada(problema, factor):
    """h₄ multiplicada por una constante. El cuerpo compartido de las dos."""
    empujes_que_faltan = h4(problema)

    def calcular(estado):
        return factor * empujes_que_faltan(estado)

    return calcular


def hna(problema):
    """2·h₄. NO ADMISIBLE. Devolvió el óptimo igual en los cinco niveles.

    Es la mitad interesante del par: muestra que una heurística no admisible
    puede dar la respuesta correcta y que eso no prueba nada, porque lo que se
    perdió es la garantía de que la vaya a dar.
    """
    return _h4_escalada(problema, 2)


def hna4(problema):
    """4·h₄. NO ADMISIBLE. Devuelve soluciones subóptimas en n2_akk04 y n4_matching.

    Es el contraejemplo que pide el criterio de aceptación de la fase: 47 contra
    un óptimo de 45 en n2, y 82 contra 70 en n4, terminando 33x más rápido.
    """
    return _h4_escalada(problema, 4)
