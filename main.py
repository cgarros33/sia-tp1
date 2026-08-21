"""Punto de entrada: resuelve UN nivel con UN método, según un archivo de configuración.

    python main.py                          usa config.json
    python main.py mi_config.json           usa otro archivo
    python main.py --metodo bfs             pisa una clave puntual

QUÉ DECISIÓN ENCIERRA
    El enunciado pide configuración POR ARCHIVO, no hardcodeada. Los flags de
    línea de comandos existen igual, pero son para probar rápido mientras se
    trabaja: los experimentos que van a la presentación se corren siempre desde
    un archivo, porque un archivo se commitea y un comando tipeado a mano no.
    Si un número de la presentación no se puede reproducir con un archivo de
    configuración del repositorio, ese número no debería estar en la
    presentación.

QUÉ SE DESCARTÓ
    Aceptar claves desconocidas en el JSON ignorándolas en silencio. Un
    `"heuristica": "h2"` mal tipeado, o una clave que quedó de otra prueba,
    daría una corrida perfectamente exitosa que no es la que se pidió. Acá
    aborta y dice cuál es la clave que sobra.

La matriz completa de experimentos —todos los niveles por todos los métodos,
con repeticiones y CSV— es la Fase 6. Esto resuelve una configuración por vez.
"""

import argparse
import json
import sys
from pathlib import Path

from src.busqueda import METODOS, METODOS_INFORMADOS, resolver
from src.heuristicas import HEURISTICAS, construir
from src.modelo import NivelInvalido, Problema, leer_archivo
from src.modelo.tablero import NOMBRE_DIR

RAIZ = Path(__file__).resolve().parent
CONFIG_POR_DEFECTO = RAIZ / 'config.json'

CLAVES = {
    'nivel', 'metodo', 'heuristica', 'timeout_s', 'max_nodos',
    'limite_profundidad', 'w', 'mostrar_solucion',
}

VALORES_POR_DEFECTO = {
    'nivel': 'niveles/n1_micro.sok',
    'metodo': 'bfs',
    'heuristica': 'h1',
    'timeout_s': 300,
    # El mismo número que config.json: el límite de nodos es el corte
    # determinístico de todas las corridas del proyecto.
    'max_nodos': 3_000_000,
    'limite_profundidad': None,
    'w': 0.5,
    'mostrar_solucion': True,
}


class ConfigInvalida(Exception):
    """El archivo de configuración no describe una corrida ejecutable."""


def cargar_config(ruta) -> dict:
    """Lee el JSON, valida las claves y completa lo que falte con los defaults."""
    ruta = Path(ruta)
    if not ruta.exists():
        raise ConfigInvalida(f'No existe el archivo de configuración {ruta}.')
    try:
        datos = json.loads(ruta.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        raise ConfigInvalida(f'{ruta} no es JSON válido: {e}') from e

    sobrantes = set(datos) - CLAVES
    if sobrantes:
        raise ConfigInvalida(
            f'{ruta} tiene claves que no existen: {sorted(sobrantes)}. '
            f'Las válidas son {sorted(CLAVES)}.'
        )

    config = dict(VALORES_POR_DEFECTO)
    config.update(datos)
    return config


def _parsear_argumentos(argv):
    parser = argparse.ArgumentParser(
        description='Resuelve un nivel de Sokoban con un método de búsqueda.')
    parser.add_argument('config', nargs='?', default=str(CONFIG_POR_DEFECTO),
                        help='archivo de configuración (por defecto config.json)')
    parser.add_argument('--nivel', help='ruta al .sok')
    parser.add_argument('--metodo', choices=METODOS)
    parser.add_argument('--heuristica', choices=sorted(HEURISTICAS))
    parser.add_argument('--timeout', type=float, dest='timeout_s')
    parser.add_argument('--max-nodos', type=int, dest='max_nodos')
    parser.add_argument('--limite-profundidad', type=int, dest='limite_profundidad')
    parser.add_argument('--w', type=float)
    parser.add_argument('--sin-solucion', action='store_true',
                        help='no imprimir la secuencia de movimientos')
    return parser.parse_args(argv)


def _n(valor) -> str:
    if valor is None:
        return '—'
    return f'{valor:,}'.replace(',', '.')


def imprimir_resultado(resultado, problema, config):
    """Imprime todo lo que pide el enunciado, en castellano y en un formato legible."""
    tablero = problema.tablero
    print(f'Nivel:       {config["nivel"]}  '
          f'({len(problema.inicial.cajas)} cajas, {len(tablero.transitables)} celdas)')
    linea_metodo = f'Método:      {config["metodo"]}'
    if config['metodo'] in METODOS_INFORMADOS:
        linea_metodo += f'   heurística: {config["heuristica"]}'
    if config['metodo'] == 'hpa':
        linea_metodo += f'   w = {config["w"]}'
    print(linea_metodo)
    print('-' * 64)

    if resultado.exito:
        print(f'Resultado:              ÉXITO')
        print(f'Costo de la solución:   {resultado.costo} movimientos '
              f'({resultado.empujes} empujes)')
    else:
        motivos = {
            'sin_solucion': 'FRACASO — el espacio se agotó: el nivel no tiene solución',
            'timeout': f'FRACASO — se acabó el tiempo ({config["timeout_s"]} s)',
            'max_nodos': f'FRACASO — se alcanzó el límite de nodos ({_n(config["max_nodos"])})',
        }
        print(f'Resultado:              {motivos.get(resultado.motivo_fin, resultado.motivo_fin)}')
        print(f'Costo de la solución:   —')

    print(f'Nodos expandidos:       {_n(resultado.nodos_expandidos)}')
    print(f'Nodos generados:        {_n(resultado.nodos_generados)}')
    print(f'Nodos en la frontera:   {_n(resultado.frontera_final)} al terminar   '
          f'({_n(resultado.frontera_maxima)} como máximo)')
    print(f'Estados visitados:      {_n(resultado.estados_visitados)}')
    # La memoria del método es frontera + visitados. La frontera sola engaña:
    # ver el resumen de la Fase 2 sobre IDDFS.
    print(f'Memoria máxima:         {_n(resultado.memoria_maxima)} nodos '
          f'(frontera + visitados)')
    print(f'Tiempo de procesamiento: {resultado.tiempo_s:.3f} s')

    if resultado.iteraciones:
        print(f'Iteraciones de IDDFS:   {len(resultado.iteraciones)} '
              f'(último límite {resultado.iteraciones[-1][0]})')

    if resultado.exito and config['mostrar_solucion']:
        movimientos = ''.join(NOMBRE_DIR[a] for a in resultado.acciones)
        print(f'\nSolución ({resultado.costo} movimientos):')
        for inicio in range(0, len(movimientos), 60):
            print(f'  {movimientos[inicio:inicio + 60]}')
        print('\n(La reproducción estado por estado del tablero es la Fase 7.)')


def main(argv=None) -> int:
    argumentos = _parsear_argumentos(argv)
    try:
        config = cargar_config(argumentos.config)
    except ConfigInvalida as e:
        print(f'Error de configuración: {e}', file=sys.stderr)
        return 2

    # Los flags pisan al archivo, no al revés: el archivo es la configuración
    # reproducible y el flag es el experimento de prueba de este momento.
    for clave in ('nivel', 'metodo', 'heuristica', 'timeout_s', 'max_nodos',
                  'limite_profundidad', 'w'):
        valor = getattr(argumentos, clave, None)
        if valor is not None:
            config[clave] = valor
    if argumentos.sin_solucion:
        config['mostrar_solucion'] = False

    try:
        tablero, inicial = leer_archivo(RAIZ / config['nivel'])
    except (NivelInvalido, OSError) as e:
        print(f'Error leyendo el nivel: {e}', file=sys.stderr)
        return 2

    problema = Problema(tablero, inicial)
    heuristica = None
    if config['metodo'] in METODOS_INFORMADOS:
        try:
            heuristica = construir(config['heuristica'], problema)
        except ValueError as e:
            print(f'Error de configuración: {e}', file=sys.stderr)
            return 2

    try:
        resultado = resolver(
            problema, config['metodo'],
            heuristica=heuristica, nombre_heuristica=config['heuristica'],
            w=config['w'], limite_profundidad=config['limite_profundidad'],
            max_nodos=config['max_nodos'], timeout_s=config['timeout_s'],
            nivel=config['nivel'],
        )
    except ValueError as e:
        print(f'Error de configuración: {e}', file=sys.stderr)
        return 2

    imprimir_resultado(resultado, problema, config)
    return 0 if resultado.exito else 1


if __name__ == '__main__':
    sys.exit(main())
