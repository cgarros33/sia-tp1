"""Dibujo de tableros: lo que la cátedra pidió ver, no lo que se mide."""

from .render import dibujar
from .reproductor import Reproduccion, generar_gif, generar_tira

__all__ = ['Reproduccion', 'dibujar', 'generar_gif', 'generar_tira']
