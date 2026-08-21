"""El bucle de búsqueda. UNO SOLO, para los cinco métodos.

QUÉ REPRESENTA
    El algoritmo genérico de búsqueda en grafos: inicializar la frontera con la
    raíz, sacar un nodo, ver si es meta, expandirlo, insertar sus sucesores,
    repetir. Todo lo que distingue a un método de otro está afuera: en la
    frontera (qué nodo sale) y en la política de repetidos (cuál se vuelve a
    insertar).

LAS TRES DECISIONES QUE SE DEFIENDEN EN EL ORAL

    1. El chequeo de meta se hace al EXTRAER, no al generar. Es obligatorio
       para la optimalidad de A*: un nodo meta generado temprano puede no ser
       el más barato, porque puede haber en la frontera otro camino a la meta
       con menor f todavía sin extraer. Con BFS y costo uniforme daría lo
       mismo, pero mantenemos un único criterio para los cinco métodos: si no,
       la comparación de nodos expandidos entre ellos no sería homogénea.

    2. Los estados repetidos se detectan al GENERAR, no al expandir. Un estado
       ya conocido ni siquiera entra a la frontera. Eso achica la frontera
       —que es memoria— y no cambia qué se expande, porque igual habría sido
       descartado al salir.

    3. Hay dos políticas de repetidos, no una. Ver `POLITICAS` más abajo: es la
       parte más delicada de la fase.

QUÉ SE DESCARTÓ
    Un bucle por método. Es lo que sale más natural y arruina el experimento:
    cualquier diferencia medida entre dos métodos quedaría contaminada por
    diferencias de implementación. Acá los cinco comparten hasta el contador de
    nodos, así que las diferencias son atribuibles a la política de la frontera
    y a nada más.
"""

import time
from dataclasses import dataclass, field

from .nodo import Nodo

# --- políticas de estados repetidos -----------------------------------------
#
# 'cerrado': un estado visto no se vuelve a insertar NUNCA. Vale cuando la
#     primera vez que llegamos a un estado ya fue por el camino más barato, que
#     es el caso de BFS con costo uniforme. También lo usa Greedy: no garantiza
#     optimalidad de todas formas, así que reabrir nodos sólo agregaría trabajo.
#
# 'mejor_g': se guarda el mejor g conocido de cada estado y se reabre si se
#     llega por un camino más barato. Lo necesitan dos métodos por razones
#     completamente distintas:
#
#     - A*, porque si la heurística es admisible pero NO consistente, un estado
#       puede expandirse antes de haber encontrado su camino óptimo, y sin
#       reapertura se perdería la optimalidad. Las heurísticas de la Fase 4 van
#       a ser consistentes, pero el motor no puede asumirlo.
#     - IDDFS, porque un estado cerrado a profundidad 20 puede ser alcanzable a
#       profundidad 12 por otra rama: cerrarlo definitivamente haría PERDER
#       soluciones que sí entran en el límite. Es un error clásico.
#
# 'camino': NO se guarda ninguna estructura de visitados. Sólo se evita repetir
#     un estado que ya está en el camino actual, subiendo por los padres. Es el
#     IDDFS "de manual", el que tiene memoria lineal en la profundidad. Cuesta
#     O(profundidad) por sucesor y, sobre todo, vuelve a expandir cada
#     transposición: en Sokoban, donde el jugador puede dar vueltas sin empujar
#     nada, eso explota. Existe para poder MEDIR ese intercambio, no para usarlo.
CERRADO = 'cerrado'
MEJOR_G = 'mejor_g'
CAMINO = 'camino'
POLITICAS = (CERRADO, MEJOR_G, CAMINO)

MOTIVOS = ('meta', 'sin_solucion', 'timeout', 'max_nodos')


@dataclass
class Resultado:
    """Todo lo que pide el enunciado, más lo que necesita el análisis."""

    # --- lo que pide el enunciado ---
    exito: bool
    costo: int | None
    nodos_expandidos: int
    frontera_final: int
    acciones: list[int]
    tiempo_s: float

    # --- lo que necesita el análisis ---
    # frontera_maxima es el pico a lo largo de la corrida: es EL número que
    # describe el consumo de memoria del método, y el que hace visible por qué
    # IDDFS existe. frontera_final, en cambio, es sólo lo que quedó sin
    # expandir al terminar.
    frontera_maxima: int
    # El pico de frontera + estructura de visitados, o sea LA MEMORIA DEL
    # MÉTODO. La frontera sola engaña: IDDFS tiene una frontera diminuta pero
    # mantiene un diccionario de visitados del mismo orden que el de BFS, así
    # que comparar frontera contra frontera diría que ahorra 55 veces cuando en
    # realidad no ahorra nada. Ver el resumen de la fase.
    memoria_maxima: int
    nodos_generados: int
    estados_visitados: int
    empujes: int | None
    profundidad: int | None
    # Distinguir "no hay solución" de "me quedé sin tiempo" es obligatorio: son
    # resultados cualitativamente distintos y confundirlos en la presentación
    # sería un error grave.
    motivo_fin: str
    metodo: str
    heuristica: str
    nivel: str

    # Cuántos nodos se descartaron por llegar al límite de profundidad. Si vale
    # 0 y no hubo solución, el espacio quedó agotado: no hay solución, punto.
    # Si vale más de 0, sólo sabemos que no hay solución DENTRO del límite. Es
    # lo que le permite a IDDFS decidir si vale la pena otra iteración.
    podados_por_limite: int = 0
    # (límite, nodos expandidos en esa iteración). Sólo lo llena IDDFS: es el
    # dato que muestra el crecimiento geométrico entre iteraciones y explica por
    # qué el trabajo repetido es tolerable.
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
    # Si la frontera no mira h, ni se llama a la heurística: en BFS, DFS e
    # IDDFS el valor se descartaría y evaluarla cuesta tiempo real.
    calcular_h = heuristica if frontera.usa_heuristica else None

    raiz = Nodo(inicial)
    frontera.agregar(raiz, calcular_h(inicial) if calcular_h is not None else 0.0)

    # Con 'mejor_g' hace falta el g de cada estado, así que es un dict; con
    # 'cerrado' alcanza con saber si se lo vio, y un set es más chico y más
    # rápido. Con millones de estados esa diferencia se paga en memoria.
    mejor_g = {inicial: 0} if usa_mejor_g else None
    visitados = None if (usa_mejor_g or usa_camino) else {inicial}
    # La estructura de visitados, sea cual sea. Con 'camino' es None: ésa es
    # exactamente la diferencia que se quiere medir.
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

        # Entrada obsoleta: llegamos a este estado por un camino más barato
        # después de haber encolado éste. El nodo sigue en la cola porque heapq
        # no permite borrar del medio; se lo saltea sin expandir. Sólo puede
        # pasar con 'mejor_g'.
        if usa_mejor_g and nodo.g > mejor_g[nodo.estado]:
            continue

        if problema.es_meta(nodo.estado):
            nodo_meta = nodo
            motivo_fin = 'meta'
            break

        # El nodo en el límite igual se testeó como meta: lo que no se hace es
        # expandirlo. Podarlo antes del test perdería soluciones que están
        # exactamente en el límite.
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
                # Sin estructura de visitados: lo único que se evita es volver a
                # un estado que ya está en el camino actual, subiendo por los
                # padres. Cuesta O(profundidad) por sucesor, y las
                # transposiciones —llegar al mismo estado por otra rama— se
                # vuelven a expandir enteras.
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
        # La memoria del método es la frontera MÁS la estructura de visitados.
        # Medir sólo la frontera hace parecer que IDDFS ahorra memoria cuando en
        # realidad la mudó de la pila al diccionario.
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
