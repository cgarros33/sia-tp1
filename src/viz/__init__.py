"""Dibujo de tableros: lo que la cátedra pidió ver, no lo que se mide.

La cátedra fue explícita en que hay que mostrar la SECUENCIA de estados que lleva
a la solución y no el resultado final. Este paquete produce los archivos que se
insertan en la diapositiva y en el PDF.

Es la única parte de `src/` que no participa de la búsqueda: es entrada/salida.
Por eso es también la única que usa una biblioteca fuera de `numpy` y `scipy`
—`Pillow`, autorizada en `docs/01_REGLAS_DE_TRABAJO.md` exclusivamente acá—, y
por eso nada de `src/modelo/` ni de `src/busqueda/` la importa: el motor no sabe
que existe.

Las figuras de análisis —barras, curvas, dominancia— son la Fase 8 y no van acá.
Acá se dibujan TABLEROS.
"""

from .render import dibujar
from .reproductor import Reproduccion, generar_gif, generar_tira

__all__ = ['Reproduccion', 'dibujar', 'generar_gif', 'generar_tira']
