"""Verificación de la Fase 5 — la poda de deadlocks.

Se corre desde la raíz del repositorio:

    python3 -m verificaciones.verificar_fase5

Son 60 corridas —5 niveles x 3 métodos x 4 capas de poda— y varias rondan el
millón de nodos, así que tarda más que la verificación de la Fase 4. Va
imprimiendo cada nivel a medida que lo termina.

LAS CINCO COMPROBACIONES DEL CRITERIO DE ACEPTACIÓN

  1. Ninguna capa poda un estado del camino óptimo. Todos los estados de un
     camino óptimo tienen solución por definición, así que un solo positivo acá
     es un FALSO POSITIVO seguro. Es la comprobación que sostiene toda la fase.
  2. El costo no cambia: los tres métodos, con las cuatro capas, devuelven el
     costo y los empujes publicados en los cinco niveles.
  3. Los nodos bajan y en ningún caso suben: `ninguno >= estaticos >= completo` y
     `ninguno >= congelados >= completo`. `estaticos` y `congelados` NO son
     comparables entre sí.
  4. La solución que devuelve BFS es exactamente la misma con y sin poda, no sólo
     del mismo costo.
  5. Cuántas celdas muertas tiene cada nivel y ninguna caja arranca en una, que
     es un control cruzado contra la Fase 2. Se reporta al lado cuántos rincones
     hay y cuántos de ellos no son celda muerta: es la medida de cuánto se
     solapan las dos reglas con una sola caja en juego.

LA ASIMETRÍA QUE HAY QUE TENER EN LA CABEZA AL LEER ESTA SALIDA
    Un falso negativo —no ver un deadlock— cuesta nodos. Un falso positivo —podar
    un estado con solución— rompe la optimalidad y puede declarar irresoluble un
    nivel que no lo es. Por eso la comprobación 1 y la 2 son fallas, y todo lo
    demás se reporta.

Todos los métodos se cortan por LÍMITE DE NODOS, nunca por reloj, por el mismo
motivo que en las fases anteriores: un límite de nodos es determinístico y el
reloj no.

Termina con código de salida 0 si todo pasa y 1 si algo falla.
"""

import sys
from pathlib import Path

from main import cargar_config
from src.busqueda import a_estrella, bfs
from src.deadlocks import construir as construir_detector, cuadrados_por_celda
from src.heuristicas import construir
from src.heuristicas.distancias import celdas_muertas
from src.modelo import Problema, leer_archivo

RAIZ = Path(__file__).resolve().parent.parent
NIVELES = RAIZ / 'niveles'

# (archivo, movimientos óptimos, empujes óptimos). Verdad externa: son los
# récords publicados por jugadores humanos en game-sokoban.com, los mismos de
# docs/03_NUMEROS_DE_ORO.md.
ESPERADO = (
    ('n1_micro.sok', 8, 5),
    ('n2_akk04.sok', 45, 18),
    ('n3_caminata.sok', 104, 22),
    ('n4_matching.sok', 70, 22),
    ('n5_limite.sok', 306, 99),
)

#: Las capas, de menos a más poda. `'ninguno'` es la referencia: es la corrida de
#: las Fases 2 a 4, sin detector.
CAPAS = ('ninguno', 'estaticos', 'congelados', 'completo')

#: (etiqueta, heurística). BFS no mira ninguna, y los dos A* son los más
#: informados de la Fase 4: interesa ver si la poda todavía aporta cuando la
#: heurística ya está haciendo buena parte del trabajo.
METODOS = (('BFS', None), ('A*(h4)', 'h4'), ('A*(h5)', 'h5'))

MAX_NODOS = cargar_config(RAIZ / 'config.json')['max_nodos']


def _n(valor) -> str:
    """Entero con puntos de miles, como se escribe en castellano."""
    if valor is None:
        return '—'
    return f'{valor:,}'.replace(',', '.')


def _d(valor: float, decimales: int = 2) -> str:
    """Decimal con coma, como se escribe en castellano."""
    return f'{valor:.{decimales}f}'.replace('.', ',')


def _lanzar(problema, heuristica, archivo):
    if heuristica is None:
        return bfs(problema, max_nodos=MAX_NODOS, nivel=archivo)
    return a_estrella(problema, construir(heuristica, problema), heuristica,
                      max_nodos=MAX_NODOS, nivel=archivo)


def _empujes_del_camino(camino):
    """(cajas, caja_movida) de cada empuje, tal como se lo consulta el motor."""
    for anterior, siguiente in zip(camino, camino[1:]):
        movidas = siguiente.cajas - anterior.cajas
        if movidas:
            yield siguiente.cajas, next(iter(movidas))


def verificar_nivel(archivo, costo_optimo, empujes_optimos):
    """Corre los tres métodos con las cuatro capas, imprime la tabla y devuelve errores.

    Devuelve `(errores, medidas)`, donde `medidas` es
    `(metodo, capa) -> nodos expandidos` para las tablas del final.
    """
    tablero, inicial = leer_archivo(NIVELES / archivo)
    errores = []

    muertas = celdas_muertas(tablero)
    # Un cuadrado sin requisitos es un rincón: la regla de 2x2 lo declara
    # deadlock con una sola caja, sin mirar dónde están las demás. Interesa
    # cuántos de ésos NO son celdas muertas, porque ésa es la única parte de la
    # regla dinámica que se solapa con la estática.
    rincones = {celda for celda, candidatos in cuadrados_por_celda(tablero).items()
                if any(not requisitos for requisitos in candidatos)}

    print(f'=== {archivo}  (óptimo publicado: {costo_optimo} mov / '
          f'{empujes_optimos} empujes) ===')
    print(f'  celdas muertas: {len(muertas)} de {len(tablero.transitables)} '
          f'transitables   ·   rincones: {len(rincones)}, de los cuales '
          f'{len(rincones - muertas)} no son celda muerta')

    # Comprobación 5: una caja del estado inicial en una celda muerta volvería el
    # nivel irresoluble, y BFS encuentra el óptimo publicado. Si esto salta, el
    # detector está mal, no el nivel.
    if inicial.cajas & muertas:
        errores.append(
            f'hay cajas del estado inicial en celdas muertas '
            f'({sorted(inicial.cajas & muertas)}): el nivel sería irresoluble y '
            f'BFS igual encuentra el óptimo, así que el detector está mal.')

    sin_poda = Problema(tablero, inicial)
    r_referencia = bfs(sin_poda, max_nodos=MAX_NODOS, nivel=archivo)
    if not r_referencia.exito or r_referencia.costo != costo_optimo:
        errores.append(f'BFS sin poda no reprodujo el óptimo publicado '
                       f'({r_referencia.motivo_fin}). La Fase 2 está rota: no '
                       f'tiene sentido medir la poda.')
        print()
        return errores, {}
    camino_optimo = sin_poda.reconstruir_estados(r_referencia.acciones)
    empujes_del_camino = list(_empujes_del_camino(camino_optimo))

    # --- comprobación 1: el camino óptimo sobrevive a las tres capas ---
    for capa in CAPAS[1:]:
        detectar = construir_detector(capa, tablero)
        podados = [i for i, (cajas, movida) in enumerate(empujes_del_camino)
                   if detectar(cajas, movida)]
        if podados:
            errores.append(
                f'{capa} poda {len(podados)} empujes del camino óptimo '
                f'(posiciones {podados[:5]}). Todos los estados de un camino '
                f'óptimo tienen solución: es un FALSO POSITIVO y rompe la '
                f'optimalidad.')
    if not errores:
        print(f'  el camino óptimo ({len(camino_optimo)} estados, '
              f'{len(empujes_del_camino)} empujes) sobrevive a las tres capas   OK')

    print(f'  {"método":<9}{"poda":<12}{"costo":>7}{"empujes":>9}'
          f'{"expandidos":>13}{"generados":>13}{"memoria":>12}{"vs sin poda":>13}')

    medidas = {}
    for etiqueta, heuristica in METODOS:
        referencia = None
        for capa in CAPAS:
            problema = Problema(tablero, inicial,
                                detector_deadlocks=construir_detector(capa, tablero))
            r = _lanzar(problema, heuristica, archivo)
            if capa == 'ninguno':
                referencia = r
            medidas[(etiqueta, capa)] = r.nodos_expandidos

            nota = ''
            if not r.exito:
                nota = f'FALLA: {r.motivo_fin}'
                errores.append(f'{etiqueta} con poda {capa} no encontró solución '
                               f'({r.motivo_fin})')
            else:
                # Comprobación 2: la poda no puede cambiar el costo. Los empujes
                # se miran también porque son la otra mitad de la verdad externa.
                if r.costo != costo_optimo or r.empujes != empujes_optimos:
                    nota = f'FALLA: el óptimo publicado es {costo_optimo}/{empujes_optimos}'
                    errores.append(
                        f'{etiqueta} con poda {capa} da {r.costo}/{r.empujes} y el '
                        f'óptimo publicado es {costo_optimo}/{empujes_optimos}. La '
                        f'poda sacó estados que sí tenían solución.')
                # Comprobación 3: podar sólo saca sucesores, así que no puede
                # agregar trabajo.
                elif r.nodos_expandidos > referencia.nodos_expandidos:
                    nota = 'FALLA: expande MÁS que sin poda'
                    errores.append(
                        f'{etiqueta} con poda {capa} expande '
                        f'{_n(r.nodos_expandidos)} y sin poda '
                        f'{_n(referencia.nodos_expandidos)}. Podar sólo saca '
                        f'sucesores: no puede agregar trabajo.')
                # Comprobación 4: no sólo el mismo costo, el mismo camino.
                elif etiqueta == 'BFS' and r.acciones != referencia.acciones:
                    nota = 'FALLA: devuelve otra solución'
                    errores.append(
                        f'BFS con poda {capa} devuelve una solución distinta a la '
                        f'de sin poda, con el mismo costo. Un estado sin solución '
                        f'tiene todos sus sucesores sin solución, así que ningún '
                        f'nodo del camino a la meta pudo haberse descubierto a '
                        f'través de uno podado.')

            ahorro = referencia.nodos_expandidos / r.nodos_expandidos
            print(f'  {etiqueta:<9}{capa:<12}{_n(r.costo):>7}{_n(r.empujes):>9}'
                  f'{_n(r.nodos_expandidos):>13}{_n(r.nodos_generados):>13}'
                  f'{_n(r.memoria_maxima):>12}{_d(ahorro) + "x":>13}  {nota}')

    # Comprobación 3, la parte que compara las capas entre sí. `completo` poda
    # todo lo que poda cada regla suelta; las dos reglas sueltas NO son
    # comparables entre sí y por eso no se las compara.
    for etiqueta, _ in METODOS:
        for capa in ('estaticos', 'congelados'):
            if medidas[(etiqueta, 'completo')] > medidas[(etiqueta, capa)]:
                errores.append(
                    f'{etiqueta}: la poda completa expande '
                    f'{_n(medidas[(etiqueta, "completo")])} y {capa} sola expande '
                    f'{_n(medidas[(etiqueta, capa)])}. La completa poda todo lo '
                    f'que poda cada regla: no puede expandir más.')

    print()
    return errores, medidas


def main() -> int:
    print('Verificación de la Fase 5 — la poda de deadlocks')
    print(f'Límite de nodos por corrida: {_n(MAX_NODOS)} (config.json), el mismo '
          f'para todas.')
    print('La columna "vs sin poda" es cuántas veces menos nodos expandió esa capa.\n')

    errores = []
    tabla = {}
    for archivo, costo, empujes in ESPERADO:
        e, medidas = verificar_nivel(archivo, costo, empujes)
        errores += [f'{archivo}: {x}' for x in e]
        tabla[archivo] = medidas

    print('=== Nodos expandidos por capa de poda, método y nivel ===')
    print('Son métricas de NUESTRA implementación, no verdad externa.\n')
    for etiqueta, _ in METODOS:
        print(f'{etiqueta}')
        print(f'  {"poda":<12}' + ''.join(f'{a.replace(".sok", ""):>14}'
                                          for a, _, _ in ESPERADO))
        for capa in CAPAS:
            fila = ''.join(f'{_n(tabla[a].get((etiqueta, capa))):>14}'
                           for a, _, _ in ESPERADO)
            print(f'  {capa:<12}{fila}')
        print()

    # Las dos reglas no se dominan entre sí, y ése es el motivo por el que son
    # dos capas medibles y no una sola. Se imprime cuál gana en cada nivel en vez
    # de afirmarlo: si en algún momento una empezara a ganar siempre, se vería.
    print('=== Cuál de las dos reglas poda más, por nivel (BFS) ===')
    for archivo, _, _ in ESPERADO:
        if not tabla[archivo]:
            continue
        estaticos = tabla[archivo][('BFS', 'estaticos')]
        congelados = tabla[archivo][('BFS', 'congelados')]
        if estaticos < congelados:
            gana = f'estaticos ({_n(estaticos)} contra {_n(congelados)})'
        elif congelados < estaticos:
            gana = f'congelados ({_n(congelados)} contra {_n(estaticos)})'
        else:
            gana = f'empatan en {_n(estaticos)}'
        print(f'  {archivo.replace(".sok", ""):<14}{gana}')
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
