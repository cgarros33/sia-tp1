"""Las heurísticas, como instrumentos de medición del motor.

En esta fase hay sólo dos. La escalera completa —Manhattan, matching óptimo,
distancias reales de empuje— es la Fase 4.
"""

from .registro import HEURISTICAS, construir, h0, h1

__all__ = ['HEURISTICAS', 'construir', 'h0', 'h1']
