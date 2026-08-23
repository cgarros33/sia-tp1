"""hₙₐ — las heurísticas no admisibles, a propósito."""

from .h4_matching_real import h4


def _h4_escalada(problema, factor):
    """h₄ multiplicada por una constante. El cuerpo compartido de las dos."""
    empujes_que_faltan = h4(problema)

    def calcular(estado):
        return factor * empujes_que_faltan(estado)

    return calcular


def hna(problema):
    """2·h₄. NO ADMISIBLE. Devolvió el óptimo igual en los cinco niveles."""
    return _h4_escalada(problema, 2)


def hna4(problema):
    """4·h₄. NO ADMISIBLE. Devuelve soluciones subóptimas en n2_akk04 y n4_matching."""
    return _h4_escalada(problema, 4)
