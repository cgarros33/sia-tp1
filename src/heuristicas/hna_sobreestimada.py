"""hₙₐ — las heurísticas no admisibles, a propósito."""

from .h5_matching_real import h5


def _h5_escalada(problema, factor):
    """h₅ multiplicada por una constante. El cuerpo compartido de las dos."""
    empujes_que_faltan = h5(problema)

    def calcular(estado):
        return factor * empujes_que_faltan(estado)

    return calcular


def hna(problema):
    """2·h₅. NO ADMISIBLE. Devolvió el óptimo igual en los cinco niveles."""
    return _h5_escalada(problema, 2)


def hna4(problema):
    """4·h₅. NO ADMISIBLE. Devuelve soluciones subóptimas en n2_akk04 y n4_matching."""
    return _h5_escalada(problema, 4)
