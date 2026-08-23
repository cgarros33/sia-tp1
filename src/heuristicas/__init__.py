"""Las heurísticas, como instrumentos de medición del motor.

La escalera de la Fase 4 —Manhattan, matching óptimo, distancias reales de
empuje, término del jugador— se arma acá. `registro.py` es el índice de nombres;
cada heurística de h₂ en adelante vive en su propio archivo junto con su
demostración de admisibilidad, porque esa demostración es el entregable de la
fase tanto como el código.
"""

from .distancias import celdas_muertas, distancias_manhattan
from .h2_manhattan import h2
from .h3_matching_manhattan import h3
from .h4_matching_real import h4
from .h5_con_jugador import h5
from .hna_sobreestimada import hna, hna4
from .registro import HEURISTICAS, construir, h0, h1

__all__ = ['HEURISTICAS', 'celdas_muertas', 'construir', 'distancias_manhattan',
           'h0', 'h1', 'h2', 'h3', 'h4', 'h5', 'hna', 'hna4']
