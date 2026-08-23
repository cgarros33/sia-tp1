"""Verificación de la Fase 4 — la escalera de heurísticas."""

import sys
from pathlib import Path

from main import cargar_config
from src.busqueda import a_estrella, bfs
from src.heuristicas import construir
from src.heuristicas.distancias import celdas_muertas
from src.modelo import Problema, leer_archivo
from verificaciones.admisibilidad import informatividad, verificar_heuristica

RAIZ = Path(__file__).resolve().parent.parent
NIVELES = RAIZ / 'niveles'

ESPERADO = (
    ('n1_micro.sok', 8, 5),
    ('n2_akk04.sok', 45, 18),
    ('n3_caminata.sok', 104, 22),
    ('n4_matching.sok', 70, 22),
    ('n5_limite.sok', 306, 99),
)

ESCALERA = ('h0', 'h1', 'h2', 'h3', 'h4', 'h5')

NO_ADMISIBLES = ('hna', 'hna4')

CADENA = ('h1', 'h2', 'h3', 'h4', 'h5')

NIVEL_DEL_CRITERIO = 'n4_matching.sok'

MAX_NODOS = cargar_config(RAIZ / 'config.json')['max_nodos']


def _n(valor) -> str:
    """Entero con puntos de miles, como se escribe en castellano."""
    if valor is None:
        return '—'
    return f'{valor:,}'.replace(',', '.')


def _d(valor: float, decimales: int = 3) -> str:
    """Decimal con coma, como se escribe en castellano."""
    return f'{valor:.{decimales}f}'.replace('.', ',')


def verificar_nivel(archivo, costo_optimo, empujes_optimos):
    """Corre las ocho heurísticas sobre un nivel y devuelve los errores."""
    tablero, inicial = leer_archivo(NIVELES / archivo)
    problema = Problema(tablero, inicial)
    errores, advertencias = [], []

    muertas = celdas_muertas(tablero)
    print(f'=== {archivo}  (óptimo publicado: {costo_optimo} mov / '
          f'{empujes_optimos} empujes) ===')
    print(f'  celdas muertas: {len(muertas)} de {len(tablero.transitables)} '
          f'transitables — subproducto de h4, la poda es la Fase 5')

    if inicial.cajas & muertas:
        errores.append(
            f'hay cajas del estado inicial en celdas muertas '
            f'({sorted(inicial.cajas & muertas)}): el nivel sería irresoluble y '
            f'BFS igual encuentra el óptimo, así que el detector está mal.'
        )

    r_bfs = bfs(problema, max_nodos=MAX_NODOS, nivel=archivo)
    if not r_bfs.exito or r_bfs.costo != costo_optimo:
        errores.append(f'BFS no reprodujo el óptimo publicado ({r_bfs.motivo_fin}). '
                       f'La Fase 2 está rota: no tiene sentido medir heurísticas.')
        print()
        return errores, advertencias, {}
    camino_optimo = problema.reconstruir_estados(r_bfs.acciones)

    print(f'  BFS: {_n(r_bfs.nodos_expandidos)} nodos expandidos, camino óptimo de '
          f'{len(camino_optimo)} estados')
    print(f'  {"heurística":<11}{"h(s0)":>7}{"h(s0)/ópt":>11}{"admisible":>11}'
          f'{"consistente":>13}{"costo":>7}{"expandidos":>13}{"vs BFS":>9}  nota')

    medidas = {}
    for nombre in ESCALERA + NO_ADMISIBLES:
        h = construir(nombre, problema)
        fallos_adm, fallos_cons = verificar_heuristica(problema, h, camino_optimo)
        r = a_estrella(problema, h, nombre, max_nodos=MAX_NODOS, nivel=archivo)
        es_admisible = not fallos_adm

        nota = ''
        if not r.exito:
            nota = f'FALLA: {r.motivo_fin}'
            errores.append(f'A*({nombre}) no encontró solución ({r.motivo_fin})')
        elif nombre in ESCALERA:
            if fallos_adm:
                nota = 'FALLA: sobreestima'
                errores.append(f'{nombre}: {fallos_adm[0]}')
            elif fallos_cons:
                nota = 'admisible pero no consistente'
                advertencias.append(
                    f'{archivo}: {nombre} no es consistente ({len(fallos_cons)} '
                    f'violaciones). A* sigue siendo óptimo con la política '
                    f'mejor_g, que reabre nodos: por eso el motor no la asume.')
            if r.costo != costo_optimo:
                nota = f'FALLA: el óptimo publicado es {costo_optimo}'
                errores.append(
                    f'A*({nombre}) da costo {r.costo} y el óptimo es {costo_optimo}. '
                    f'Con una heurística admisible A* tiene que ser óptimo: o la '
                    f'demostración está mal, o la implementación no es la que se '
                    f'demostró.')
            elif not nota:
                nota = 'OK'
        else:
            if es_admisible:
                nota = 'no violó admisibilidad en este nivel'
            elif r.costo > costo_optimo:
                exceso = 100 * (r.costo / costo_optimo - 1)
                nota = (f'subóptimo: {r.costo} contra {costo_optimo} '
                        f'(+{exceso:.0f} %)')
            else:
                nota = 'no admisible pero devolvió el óptimo igual'

        print(f'  {nombre:<11}{h(camino_optimo[0]):>7}'
              f'{_d(informatividad(h, camino_optimo)):>11}'
              f'{("OK" if es_admisible else "FALLA"):>11}'
              f'{("OK" if not fallos_cons else "FALLA"):>13}'
              f'{_n(r.costo):>7}{_n(r.nodos_expandidos):>13}'
              f'{_d(r_bfs.nodos_expandidos / r.nodos_expandidos, 2) + "x":>9}  {nota}')

        medidas[nombre] = (h(camino_optimo[0]),
                           informatividad(h, camino_optimo),
                           r.nodos_expandidos, r.costo, es_admisible)

    valores = [medidas[nombre][0] for nombre in CADENA]
    if valores != sorted(valores):
        errores.append(
            f'la cadena de dominancia en valor no se cumple: '
            + ' <= '.join(f'{n}={v}' for n, v in zip(CADENA, valores)))
    print(f'  dominancia en valor:  ' + ' <= '.join(
        f'{n}={v}' for n, v in zip(CADENA, valores))
        + ('  OK' if valores == sorted(valores) else '  FALLA'))

    nodos = [medidas[nombre][2] for nombre in CADENA[1:]]
    orden = list(CADENA[1:])
    quiebres = [f'A*({orden[i]})={_n(nodos[i])} < A*({orden[i + 1]})={_n(nodos[i + 1])}'
                for i in range(len(nodos) - 1) if nodos[i] < nodos[i + 1]]
    print(f'  dominancia en nodos:  ' + ' >= '.join(
        f'{n}={_n(v)}' for n, v in zip(orden, nodos))
        + ('  OK' if not quiebres else '  ver advertencia'))
    if quiebres:
        advertencias.append(
            f'{archivo}: la dominancia en nodos no se cumple en {"; ".join(quiebres)}. '
            f'NO es necesariamente un bug: dominar en valor garantiza expandir a lo '
            f'sumo los mismos nodos sólo bajo ciertas condiciones.')

    if archivo == NIVEL_DEL_CRITERIO:
        n2, n3 = medidas['h2'][2], medidas['h3'][2]
        if n3 < n2 and medidas['h2'][3] == medidas['h3'][3] == costo_optimo:
            print(f'  CRITERIO DE LA FASE:  A*(h3)={_n(n3)} < A*(h2)={_n(n2)} '
                  f'con el mismo costo {costo_optimo}  OK')
        else:
            errores.append(
                f'CRITERIO DE LA FASE: en {archivo} A*(h3) expandió {_n(n3)} y '
                f'A*(h2) expandió {_n(n2)}. Se pide que h3 expanda menos, con el '
                f'mismo costo.')

    print()
    return errores, advertencias, medidas


def main() -> int:
    print('Verificación de la Fase 4 — la escalera de heurísticas')
    print(f'Límite de nodos por corrida: {_n(MAX_NODOS)} (config.json), el mismo '
          f'para todas.')
    print('La columna "vs BFS" es cuántas veces menos nodos que BFS expandió A*.\n')

    errores, advertencias = [], []
    tabla = {}
    for archivo, costo, empujes in ESPERADO:
        e, a, medidas = verificar_nivel(archivo, costo, empujes)
        errores += [f'{archivo}: {x}' for x in e]
        advertencias += a
        tabla[archivo] = medidas

    print('=== Comprobación 5 — informatividad h(s0)/óptimo ===')
    print('Es el eje horizontal de la figura 2 de la Fase 8: 0 es h0, que no informa')
    print('nada, y 1 sería la heurística perfecta.\n')
    print(f'{"heurística":<11}' + ''.join(f'{a.replace(".sok", ""):>14}' for a, _, _ in ESPERADO))
    for nombre in ESCALERA + NO_ADMISIBLES:
        fila = ''.join(
            f'{_d(tabla[a][nombre][1]):>14}' if tabla[a] else f'{"—":>14}'
            for a, _, _ in ESPERADO)
        print(f'{nombre:<11}{fila}')

    print('\n=== Nodos expandidos por A*, por heurística y nivel ===')
    print(f'{"heurística":<11}' + ''.join(f'{a.replace(".sok", ""):>14}' for a, _, _ in ESPERADO))
    for nombre in ESCALERA + NO_ADMISIBLES:
        fila = ''.join(
            f'{_n(tabla[a][nombre][2]):>14}' if tabla[a] else f'{"—":>14}'
            for a, _, _ in ESPERADO)
        print(f'{nombre:<11}{fila}')
    print('Son métricas de NUESTRA implementación, no verdad externa.\n')

    for nombre in NO_ADMISIBLES:
        niveles_que_fallan = [a for a, _, _ in ESPERADO
                              if tabla[a] and not tabla[a][nombre][4]]
        if not niveles_que_fallan:
            errores.append(
                f'{nombre} NO violó admisibilidad en ningún nivel. Está en el '
                f'registro para mostrar qué se rompe: si no se rompe nada, no '
                f'estamos demostrando nada.')
        else:
            print(f'{nombre}: viola admisibilidad en {len(niveles_que_fallan)} de '
                  f'{len(ESPERADO)} niveles — es lo que se espera.')

    suboptimos = [(a, tabla[a]['hna4'][3], costo) for a, costo, _ in ESPERADO
                  if tabla[a] and tabla[a]['hna4'][3] > costo]
    if suboptimos:
        detalle = '; '.join(f'{a.replace(".sok", "")}: {c} contra {o}'
                            for a, c, o in suboptimos)
        print(f'hna4: devuelve solución SUBÓPTIMA en {len(suboptimos)} niveles — {detalle}')
        print('Es el contraejemplo que pide la fase: la admisibilidad no es un')
        print('tecnicismo, es la garantía de optimalidad.')
    else:
        errores.append(
            'hna4 devolvió el óptimo en los cinco niveles: la fase se queda sin el '
            'contraejemplo de solución subóptima que pide el criterio 4.')

    optimos_igual = [a.replace('.sok', '') for a, costo, _ in ESPERADO
                     if tabla[a] and tabla[a]['hna'][3] == costo]
    if optimos_igual:
        print(f'hna: NO es admisible y aun así devolvió el óptimo en '
              f'{len(optimos_igual)} de {len(ESPERADO)} niveles ({", ".join(optimos_igual)}).')
        print('Perder la admisibilidad pierde la GARANTÍA, no necesariamente la respuesta.')
    print()

    if advertencias:
        print(f'{len(advertencias)} ADVERTENCIAS (no son fallas, son resultados a explicar):')
        for a in advertencias:
            print(f'  {a}')
        print()

    if not errores:
        print(f'{len(ESPERADO)}/{len(ESPERADO)} niveles OK. Las 5 comprobaciones pasan.')
        return 0
    print(f'HAY {len(errores)} FALLAS:')
    for e in errores:
        print(f'  {e}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
