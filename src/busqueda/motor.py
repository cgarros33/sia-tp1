"""El bucle de búsqueda: uno solo para los cinco métodos."""

import time
from dataclasses import dataclass, field

from .nodo import Nodo

CERRADO = 'cerrado'
MEJOR_G = 'mejor_g'
CAMINO = 'camino'
POLITICAS = (CERRADO, MEJOR_G, CAMINO)

MOTIVOS = ('meta', 'sin_solucion', 'timeout', 'max_nodos')


@dataclass
class Resultado:
    """Todo lo que pide el enunciado, más lo que necesita el análisis.

    `memoria_maxima` es el pico de (frontera + visitados): el pico de la suma, no
    la suma de los picos, así que no coincide con sumar las dos columnas.
    """

    exito: bool
    costo: int | None
    nodos_expandidos: int
    frontera_final: int
    acciones: list[int]
    tiempo_s: float

    frontera_maxima: int
    memoria_maxima: int
    nodos_generados: int
    estados_visitados: int
    empujes: int | None
    profundidad: int | None
    motivo_fin: str
    metodo: str
    heuristica: str
    nivel: str

    podados_por_limite: int = 0
    iteraciones: list[tuple[int, int]] = field(default_factory=list)

    @property
    def optimo_desconocido(self) -> bool:
        """True si la corrida no terminó por sí misma (timeout o max_nodos)."""
        return self.motivo_fin in ('timeout', 'max_nodos')


def buscar(problema, frontera, politica: str = CERRADO, heuristica=None,
           limite_profundidad: int | None = None,
           max_nodos: int | None = None,
           timeout_s: float | None = None,
           metodo: str = '', nombre_heuristica: str = '',
           nivel: str = '') -> Resultado:
    """Los seis pasos del algoritmo genérico, para cualquier frontera."""
    if politica not in POLITICAS:
        raise ValueError(f'Política desconocida: {politica!r}. Opciones: {POLITICAS}')

    comienzo = time.perf_counter()
    inicial = problema.inicial
    usa_mejor_g = politica == MEJOR_G
    usa_camino = politica == CAMINO
    calcular_h = heuristica if frontera.usa_heuristica else None

    raiz = Nodo(inicial)
    frontera.agregar(raiz, calcular_h(inicial) if calcular_h is not None else 0.0)

    mejor_g = {inicial: 0} if usa_mejor_g else None
    visitados = None if (usa_mejor_g or usa_camino) else {inicial}
    estructura = mejor_g if usa_mejor_g else visitados

    nodos_expandidos = 0
    nodos_generados = 0
    podados_por_limite = 0
    frontera_maxima = 1
    memoria_maxima = 1 if estructura is None else 2
    motivo_fin = 'sin_solucion'
    nodo_meta = None

    while not frontera.vacia():
        if max_nodos is not None and nodos_expandidos >= max_nodos:
            motivo_fin = 'max_nodos'
            break
        if timeout_s is not None and time.perf_counter() - comienzo >= timeout_s:
            motivo_fin = 'timeout'
            break

        nodo = frontera.sacar()

        if usa_mejor_g and nodo.g > mejor_g[nodo.estado]:
            continue

        if problema.es_meta(nodo.estado):
            nodo_meta = nodo
            motivo_fin = 'meta'
            break

        if limite_profundidad is not None and nodo.profundidad >= limite_profundidad:
            podados_por_limite += 1
            continue

        nodos_expandidos += 1
        g_hijo = nodo.g + 1
        profundidad_hijo = nodo.profundidad + 1

        for accion, siguiente, hubo_empuje in problema.sucesores(nodo.estado):
            nodos_generados += 1
            if usa_mejor_g:
                conocido = mejor_g.get(siguiente)
                if conocido is not None and conocido <= g_hijo:
                    continue
                mejor_g[siguiente] = g_hijo
            elif usa_camino:
                ancestro = nodo
                repetido = False
                while ancestro is not None:
                    if ancestro.estado == siguiente:
                        repetido = True
                        break
                    ancestro = ancestro.padre
                if repetido:
                    continue
            else:
                if siguiente in visitados:
                    continue
                visitados.add(siguiente)
            hijo = Nodo(siguiente, nodo, accion, g_hijo, profundidad_hijo, hubo_empuje)
            frontera.agregar(hijo, calcular_h(siguiente) if calcular_h is not None else 0.0)

        en_frontera = len(frontera)
        if en_frontera > frontera_maxima:
            frontera_maxima = en_frontera
        memoria = en_frontera if estructura is None else en_frontera + len(estructura)
        if memoria > memoria_maxima:
            memoria_maxima = memoria

    tiempo_s = time.perf_counter() - comienzo
    estados_visitados = 0 if estructura is None else len(estructura)

    if nodo_meta is not None:
        return Resultado(
            exito=True,
            costo=nodo_meta.g,
            nodos_expandidos=nodos_expandidos,
            frontera_final=len(frontera),
            acciones=nodo_meta.camino_acciones(),
            tiempo_s=tiempo_s,
            frontera_maxima=frontera_maxima,
            memoria_maxima=memoria_maxima,
            nodos_generados=nodos_generados,
            estados_visitados=estados_visitados,
            empujes=nodo_meta.cantidad_empujes(),
            profundidad=nodo_meta.profundidad,
            motivo_fin=motivo_fin,
            metodo=metodo,
            heuristica=nombre_heuristica,
            nivel=nivel,
            podados_por_limite=podados_por_limite,
        )

    return Resultado(
        exito=False,
        costo=None,
        nodos_expandidos=nodos_expandidos,
        frontera_final=len(frontera),
        acciones=[],
        tiempo_s=tiempo_s,
        frontera_maxima=frontera_maxima,
        memoria_maxima=memoria_maxima,
        nodos_generados=nodos_generados,
        estados_visitados=estados_visitados,
        empujes=None,
        profundidad=None,
        motivo_fin=motivo_fin,
        metodo=metodo,
        heuristica=nombre_heuristica,
        nivel=nivel,
        podados_por_limite=podados_por_limite,
    )
