"""Verificación de la Fase 2 — motor genérico y los cinco métodos.

Se corre desde la raíz del repositorio:

    python -m verificaciones.verificar_fase2

Tarda dos o tres minutos: N5 con BFS son dos millones de nodos, y la tabla
completa corre seis configuraciones por nivel. Va imprimiendo cada nivel a
medida que lo termina.

Las cinco comprobaciones del criterio de aceptación:

  1. BFS reproduce los números de oro: costo y empujes exactos contra
     docs/03_NUMEROS_DE_ORO.md.
  2. A*(h0) es idéntico a BFS: mismo costo y MISMA CANTIDAD EXACTA de nodos
     expandidos. Es la invariante que separa bugs del motor de bugs de
     heurísticas, y el primer test que hay que correr cuando algo no cierra.
  3. Las soluciones son ejecutables: pasarlas por reconstruir_estados() termina
     en meta y da costo + 1 estados.
  4. Los métodos no óptimos se comportan como se espera: DFS nunca por debajo
     del óptimo, Greedy expande menos que BFS con costo mayor o igual.
  5. IDDFS expande muchos más nodos que BFS y mantiene una frontera mucho más
     chica — pero su MEMORIA TOTAL (frontera + visitados) no es menor en
     ningún nivel de forma apreciable. Ver el resumen de la fase: es el
     resultado más interesante que dio esta verificación.

Todos los métodos se cortan por LÍMITE DE NODOS, nunca por reloj. Un límite de
nodos es determinístico y el reloj no: con timeout, dos corridas de IDDFS en N4
daban 3.453.866 y 1.798.624 nodos. El límite sale de config.json, así que es el
mismo número para todos los métodos y está en un archivo versionado.

Y además, porque la Fase 4 las va a necesitar seis veces: admisibilidad y
consistencia de h0 y h1 sobre el camino óptimo de los cinco niveles.

Termina con código de salida 0 si todo pasa y 1 si algo falla.
"""

import sys
from pathlib import Path

from main import cargar_config
from src.busqueda import a_estrella, bfs, dfs, greedy, iddfs, iddfs_puro
from src.heuristicas import construir
from src.modelo import Problema, leer_archivo
from verificaciones.admisibilidad import informatividad, verificar_heuristica

RAIZ = Path(__file__).resolve().parent.parent
NIVELES = RAIZ / 'niveles'

# (archivo, movimientos óptimos, empujes óptimos, exigir DFS estrictamente
#  peor, correr el IDDFS sin visitados)
#
# Los dos números salen de docs/03_NUMEROS_DE_ORO.md y son verdad externa: son
# los récords publicados por jugadores humanos en game-sokoban.com.
#
# N1 es la excepción del test de DFS y está documentada: es un pasillo de 12
# celdas donde la topología deja un solo camino, así que DFS cae en el óptimo
# sin buscarlo. Corriendo DFS con los 24 órdenes posibles de DIRECCIONES, N1 da
# 8 en los 24. En N2 el rango de esos mismos 24 órdenes es 113-181 contra un
# óptimo de 45, y en N3 es 164-448 contra 104: ahí el test estricto es seguro.
#
# El IDDFS sin visitados sólo se corre en N1: es el único de la suite donde
# termina. Que no termine en los otros cuatro es justamente lo que se quiere
# mostrar, y correrlo ahí sería quemar el límite de nodos para no aprender nada
# que no sepamos ya.
ESPERADO = (
    ('n1_micro.sok', 8, 5, False, True),
    ('n2_akk04.sok', 45, 18, True, False),
    ('n3_caminata.sok', 104, 22, True, False),
    ('n4_matching.sok', 70, 22, True, False),
    ('n5_limite.sok', 306, 99, True, False),
)

# El techo es el MISMO para todos los métodos y sale de config.json, no de una
# constante escondida acá: así el número que corta las corridas es un dato
# versionado del proyecto y no una decisión de este script. Se espera que IDDFS
# lo alcance en N4 y N5, y eso ES un resultado del TP.
MAX_NODOS = cargar_config(RAIZ / 'config.json')['max_nodos']


def _n(valor) -> str:
    """Entero con puntos de miles, como se escribe en castellano."""
    if valor is None:
        return '—'
    return f'{valor:,}'.replace(',', '.')


def _factor(valor: float) -> str:
    """Un factor multiplicativo legible: sin decimales si es grande, con uno si no."""
    return f'{valor:.0f}' if valor >= 10 else f'{valor:.1f}'


def _fila(metodo, resultado, nota=''):
    costo = _n(resultado.costo)
    empujes = _n(resultado.empujes)
    print(f'{metodo:<12}{costo:>6}{empujes:>9}{_n(resultado.nodos_expandidos):>12}'
          f'{_n(resultado.frontera_maxima):>11}{_n(resultado.memoria_maxima):>11}'
          f'{resultado.tiempo_s:>8.2f} s  {nota}')


def _verificar_ejecutable(problema, resultado) -> list[str]:
    """Comprobación 3: la secuencia de acciones lleva de verdad del inicial a la meta.

    Atrapa errores en la reconstrucción del camino, que el costo por sí solo no
    detecta: un `padre` mal enganchado puede dar un número correcto y un camino
    que no se puede caminar.
    """
    if not resultado.exito:
        return []
    try:
        estados = problema.reconstruir_estados(resultado.acciones)
    except ValueError as e:
        return [f'{resultado.metodo}: la solución no es ejecutable ({e})']

    errores = []
    if not problema.es_meta(estados[-1]):
        errores.append(f'{resultado.metodo}: la solución no termina en meta')
    if len(estados) != resultado.costo + 1:
        errores.append(
            f'{resultado.metodo}: la solución tiene {len(estados)} estados y '
            f'debería tener costo + 1 = {resultado.costo + 1}'
        )
    return errores


def _verificar_heuristicas(problema, camino_optimo) -> list[str]:
    """Admisibilidad y consistencia de h0 y h1 sobre el camino óptimo del nivel."""
    errores = []
    print(f'  admisibilidad y consistencia sobre el camino óptimo '
          f'({len(camino_optimo)} estados):')
    for nombre in ('h0', 'h1'):
        h = construir(nombre, problema)
        fallos_adm, fallos_cons = verificar_heuristica(problema, h, camino_optimo)
        estado_adm = 'OK' if not fallos_adm else 'FALLA'
        estado_cons = 'OK' if not fallos_cons else 'FALLA'
        print(f'    {nombre}   admisible {estado_adm:<6} consistente {estado_cons:<6}'
              f' h(s0)/óptimo = {informatividad(h, camino_optimo):.3f}')
        errores += [f'{nombre}: {e}' for e in fallos_adm + fallos_cons]
    return errores


def verificar_nivel(archivo, costo_optimo, empujes_optimos, dfs_estricto,
                    corre_iddfs_puro=False):
    """Corre las seis configuraciones sobre un nivel, imprime la tabla y devuelve errores."""
    tablero, inicial = leer_archivo(NIVELES / archivo)
    problema = Problema(tablero, inicial)
    h0 = construir('h0', problema)
    h1 = construir('h1', problema)
    errores = []

    print(f'=== {archivo}  (óptimo publicado: {costo_optimo} mov / '
          f'{empujes_optimos} empujes) ===')
    print(f'{"método":<12}{"costo":>6}{"empujes":>9}{"expandidos":>12}'
          f'{"front.máx":>11}{"memoria":>11}{"tiempo":>10}  resultado')

    # --- 1. BFS contra los números de oro ---
    r_bfs = bfs(problema, max_nodos=MAX_NODOS, nivel=archivo)
    nota = 'OK'
    if not r_bfs.exito:
        nota = f'FALLA: {r_bfs.motivo_fin}'
        errores.append(f'BFS no encontró solución ({r_bfs.motivo_fin})')
    else:
        if r_bfs.costo != costo_optimo:
            nota = f'FALLA: el óptimo publicado es {costo_optimo}'
            errores.append(f'BFS da costo {r_bfs.costo} y el récord publicado es {costo_optimo}')
        elif r_bfs.empujes != empujes_optimos:
            nota = f'FALLA: los empujes publicados son {empujes_optimos}'
            errores.append(f'BFS da {r_bfs.empujes} empujes y el récord publicado es {empujes_optimos}')
    _fila('BFS', r_bfs, nota)
    errores += _verificar_ejecutable(problema, r_bfs)
    if not r_bfs.exito:
        print()
        return errores, None

    # --- 2. el test de control del motor: A*(h0) tiene que ser BFS ---
    r_h0 = a_estrella(problema, h0, 'h0', max_nodos=MAX_NODOS, nivel=archivo)
    identico = (r_h0.exito and r_h0.costo == r_bfs.costo
                and r_h0.nodos_expandidos == r_bfs.nodos_expandidos)
    if identico:
        nota = 'OK  ≡ BFS'
    else:
        nota = 'FALLA: NO coincide con BFS'
        errores.append(
            f'A*(h0) expandió {r_h0.nodos_expandidos} nodos con costo {r_h0.costo} '
            f'y BFS expandió {r_bfs.nodos_expandidos} con costo {r_bfs.costo}. '
            f'Con h = 0 A* degenera en costo uniforme, que con costo unitario es '
            f'BFS: si diferen, el bug está en el motor.'
        )
    _fila('A*(h0)', r_h0, nota)
    errores += _verificar_ejecutable(problema, r_h0)

    # --- A*(h1): sigue siendo óptimo, y se ve cuánto (poco) ayuda h1 ---
    r_h1 = a_estrella(problema, h1, 'h1', max_nodos=MAX_NODOS, nivel=archivo)
    if r_h1.exito and r_h1.costo == costo_optimo:
        ahorro = 100 * (1 - r_h1.nodos_expandidos / r_bfs.nodos_expandidos)
        nota = f'OK  {ahorro:.1f} % menos nodos que BFS'
    else:
        nota = 'FALLA: no reprodujo el óptimo'
        errores.append(f'A*(h1) da costo {r_h1.costo} y el óptimo es {costo_optimo}. '
                       f'Con una heurística admisible A* tiene que ser óptimo.')
    _fila('A*(h1)', r_h1, nota)
    errores += _verificar_ejecutable(problema, r_h1)

    # --- 4a. Greedy: más rápido, peor solución ---
    r_greedy = greedy(problema, h1, 'h1', max_nodos=MAX_NODOS, nivel=archivo)
    if not r_greedy.exito:
        nota = f'FALLA: {r_greedy.motivo_fin}'
        errores.append(f'Greedy(h1) no encontró solución ({r_greedy.motivo_fin})')
    else:
        problemas = []
        if r_greedy.costo < costo_optimo:
            problemas.append(f'costo {r_greedy.costo} por DEBAJO del óptimo {costo_optimo}')
        if r_greedy.nodos_expandidos >= r_bfs.nodos_expandidos:
            problemas.append('no expandió menos nodos que BFS')
        if problemas:
            nota = 'FALLA: ' + '; '.join(problemas)
            errores.append(f'Greedy(h1): {"; ".join(problemas)}')
        elif r_greedy.costo == costo_optimo:
            nota = 'OK  óptimo por casualidad, sin garantía'
        else:
            factor = r_bfs.nodos_expandidos / r_greedy.nodos_expandidos
            nota = f'subóptimo (esperado), {_factor(factor)}x menos nodos que BFS'
    _fila('Greedy(h1)', r_greedy, nota)
    errores += _verificar_ejecutable(problema, r_greedy)

    # --- 4b. DFS: encuentra UNA solución, no la mejor ---
    r_dfs = dfs(problema, max_nodos=MAX_NODOS, nivel=archivo)
    if not r_dfs.exito:
        nota = f'FALLA: {r_dfs.motivo_fin}'
        errores.append(f'DFS no encontró solución ({r_dfs.motivo_fin})')
    elif r_dfs.costo < costo_optimo:
        nota = f'FALLA: costo por debajo del óptimo {costo_optimo}'
        errores.append(f'DFS da costo {r_dfs.costo}, por debajo del óptimo {costo_optimo}: '
                       f'eso es imposible y significa que hay un bug.')
    elif dfs_estricto and r_dfs.costo == costo_optimo:
        nota = 'FALLA: se esperaba estrictamente peor que el óptimo'
        errores.append(f'DFS da exactamente el óptimo ({costo_optimo}) en un nivel donde '
                       f'no debería: revisar el orden de sucesores o el nivel.')
    elif r_dfs.costo == costo_optimo:
        nota = 'óptimo por topología del nivel (esperado, ver ESPERADO)'
    else:
        nota = f'subóptimo (esperado), {_factor(r_dfs.costo / costo_optimo)}x el óptimo'
    _fila('DFS', r_dfs, nota)
    errores += _verificar_ejecutable(problema, r_dfs)

    # --- 5. IDDFS: la memoria de DFS con la optimalidad de BFS ---
    r_iddfs = iddfs(problema, max_nodos=MAX_NODOS, nivel=archivo)
    if not r_iddfs.exito:
        nota = f'{r_iddfs.motivo_fin} (esperado en N4 y N5), {len(r_iddfs.iteraciones)} iteraciones'
    elif r_iddfs.costo != costo_optimo:
        nota = f'FALLA: costo {r_iddfs.costo} y el óptimo es {costo_optimo}'
        errores.append(f'IDDFS da costo {r_iddfs.costo} y el óptimo es {costo_optimo}. '
                       f'Con costo uniforme IDDFS tiene que ser óptimo.')
    else:
        problemas = []
        if r_iddfs.frontera_maxima >= r_bfs.frontera_maxima:
            problemas.append(f'frontera máxima {r_iddfs.frontera_maxima} no es menor '
                             f'que la de BFS ({r_bfs.frontera_maxima})')
        if r_iddfs.nodos_expandidos <= r_bfs.nodos_expandidos:
            problemas.append('no expandió más nodos que BFS')
        if problemas:
            nota = 'FALLA: ' + '; '.join(problemas)
            errores.append(f'IDDFS: {"; ".join(problemas)}')
        else:
            # La frontera se compara aparte de la memoria total A PROPÓSITO: es
            # la diferencia entre lo que promete el método y lo que entrega
            # cuando se le agrega detección de repetidos.
            frontera = r_bfs.frontera_maxima / r_iddfs.frontera_maxima
            trabajo = r_iddfs.nodos_expandidos / r_bfs.nodos_expandidos
            memoria = r_iddfs.memoria_maxima / r_bfs.memoria_maxima
            nota = (f'OK  frontera {_factor(frontera)}x menor, '
                    f'{_factor(trabajo)}x más nodos, '
                    f'pero memoria TOTAL {memoria:.2f}x la de BFS')
    _fila('IDDFS', r_iddfs, nota)
    errores += _verificar_ejecutable(problema, r_iddfs)
    if r_iddfs.iteraciones:
        ultimas = ', '.join(f'{limite}: {_n(nodos)}' for limite, nodos in r_iddfs.iteraciones[-3:])
        print(f'  IDDFS, últimas iteraciones (límite: nodos expandidos) — {ultimas}')

    # --- IDDFS "de manual", sin estructura de visitados ---
    # Sólo se corre donde puede terminar. En los demás niveles no termina, y ESO
    # es el dato: sin tabla de transposiciones, Sokoban es impracticable.
    if corre_iddfs_puro:
        r_puro = iddfs_puro(problema, max_nodos=MAX_NODOS, nivel=archivo)
        if not r_puro.exito:
            nota = f'{r_puro.motivo_fin} — sin visitados no termina (esperado)'
        elif r_puro.costo != costo_optimo:
            nota = f'FALLA: costo {r_puro.costo} y el óptimo es {costo_optimo}'
            errores.append(f'IDDFS puro da costo {r_puro.costo} y el óptimo es {costo_optimo}')
        else:
            memoria = r_bfs.memoria_maxima / r_puro.memoria_maxima
            trabajo = r_puro.nodos_expandidos / r_bfs.nodos_expandidos
            nota = (f'OK  memoria {_factor(memoria)}x menor que BFS de verdad, '
                    f'pagando {_factor(trabajo)}x más nodos')
        _fila('IDDFS puro', r_puro, nota)
        errores += _verificar_ejecutable(problema, r_puro)

    # --- las heurísticas, sobre el camino óptimo que acaba de dar BFS ---
    camino_optimo = problema.reconstruir_estados(r_bfs.acciones)
    errores += _verificar_heuristicas(problema, camino_optimo)
    print()
    return errores, r_bfs


def main() -> int:
    print('Verificación de la Fase 2 — motor genérico y los cinco métodos')
    print(f'Límite de nodos por corrida: {_n(MAX_NODOS)} (config.json), el mismo '
          f'para todos los métodos.')
    print('La columna memoria es frontera + visitados: la memoria real del método.\n')

    errores_totales = []
    resultados_bfs = []
    for archivo, costo, empujes, dfs_estricto, puro in ESPERADO:
        errores, r_bfs = verificar_nivel(archivo, costo, empujes, dfs_estricto, puro)
        for error in errores:
            errores_totales.append(f'{archivo}: {error}')
        if r_bfs is not None:
            resultados_bfs.append((archivo, r_bfs))

    print('=== Nodos expandidos por BFS — VALORES A CONGELAR EN LA FASE 3 ===')
    print(f'{"nivel":<17}{"costo":>6}{"empujes":>9}{"expandidos":>13}'
          f'{"generados":>13}{"front.máx":>11}{"visitados":>12}{"memoria":>12}')
    for archivo, r in resultados_bfs:
        print(f'{archivo:<17}{r.costo:>6}{r.empujes:>9}{_n(r.nodos_expandidos):>13}'
              f'{_n(r.nodos_generados):>13}{_n(r.frontera_maxima):>11}'
              f'{_n(r.estados_visitados):>12}{_n(r.memoria_maxima):>12}')
    print('Son métricas de NUESTRA implementación, no verdad externa: dependen del')
    print('orden de sucesores, del desempate de la frontera y de la política de')
    print('repetidos. Se congelan en la Fase 3 y si cambian hay que entender por qué.\n')

    if not errores_totales:
        print(f'{len(ESPERADO)}/{len(ESPERADO)} niveles OK.')
        return 0
    print(f'HAY {len(errores_totales)} FALLAS:')
    for error in errores_totales:
        print(f'  {error}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
