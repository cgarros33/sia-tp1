"""Las heurísticas, como instrumentos de medición del motor."""

from .distancias import celdas_muertas, distancias_manhattan
from .h3_manhattan import h3
from .h4_matching_manhattan import h4
from .h5_matching_real import h5
from .h6_con_jugador import h6
from .hna_sobreestimada import hna, hna4
from .registro import HEURISTICAS, construir, h0, h1, h2

__all__ = ['HEURISTICAS', 'celdas_muertas', 'construir', 'distancias_manhattan',
           'h0', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hna', 'hna4']
