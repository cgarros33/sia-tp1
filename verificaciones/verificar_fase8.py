"""Verificación de la Fase 8 — gráficos y análisis."""

import collections
import csv
import hashlib
import sys
from pathlib import Path

from experimentos import graficos

RAIZ = Path(__file__).resolve().parent.parent

FIGURAS = (
    ('figura_1_metodos', '¿cuánto aporta cada método?'),
    ('figura_2_dominancia', '¿una heurística más informada expande menos nodos?'),
    ('figura_3_barrido_w', '¿cuánto se paga por apurar la búsqueda?'),
    ('figura_4_el_muro', '¿por qué hay un límite y dónde está?'),
)

COLUMNAS_DETERMINISTICAS = ('costo', 'empujes', 'nodos_expandidos',
                            'nodos_generados', 'memoria_maxima')


def _n(valor) -> str:
    return f'{valor:,}'.replace(',', '.')


def _huellas():
    """El hash de cada archivo de `presentacion/figuras/`."""
    return {ruta.name: hashlib.sha256(ruta.read_bytes()).hexdigest()
            for ruta in sorted(graficos.FIGURAS.glob('figura_*'))}


def comprobar_1_y_3():
    """Genera las figuras dos veces y compara los bytes."""
    errores = []
    graficos.aplicar_estilo()
    for figura in (graficos.figura_1_metodos, graficos.figura_2_dominancia,
                   graficos.figura_3_barrido, graficos.figura_4_el_muro):
        figura()
    primera = _huellas()

    for figura in (graficos.figura_1_metodos, graficos.figura_2_dominancia,
                   graficos.figura_3_barrido, graficos.figura_4_el_muro):
        figura()
    segunda = _huellas()

    print('=== Comprobación 1 — las cuatro figuras, en PNG y en PDF ===')
    for nombre, pregunta in FIGURAS:
        for extension in ('png', 'pdf'):
            ruta = graficos.FIGURAS / f'{nombre}.{extension}'
            if not ruta.exists():
                errores.append(f'falta {ruta.relative_to(RAIZ)}')
                continue
            print(f'  {str(ruta.relative_to(RAIZ)):<44}'
                  f'{_n(ruta.stat().st_size // 1024):>6} KB'
                  + (f'   {pregunta}' if extension == 'png' else ''))

    print('\n=== Comprobación 3 — regenerar es idempotente ===')
    distintas = [nombre for nombre in primera
                 if primera[nombre] != segunda.get(nombre)]
    if distintas:
        errores.append(
            f'estas figuras cambian al regenerarlas con el mismo CSV: {distintas}. '
            f'Dos personas con los mismos datos obtendrían imágenes distintas.')
    else:
        print(f'  {len(primera)} archivos, mismos bytes en las dos corridas   OK')
    return errores


def comprobar_2():
    """El barrido existe y sus dos anclas coinciden con el CSV de la Fase 6."""
    errores = []
    print('\n=== Comprobación 2 — el barrido de w y sus dos anclas ===')
    if not graficos.CSV_BARRIDO.exists():
        errores.append(f'no existe {graficos.CSV_BARRIDO.relative_to(RAIZ)}: '
                       f'correr `python3 -m experimentos.barrido_w`.')
        return errores

    barrido = graficos.leer(graficos.CSV_BARRIDO)
    matriz = [f for f in graficos.leer(graficos.CSV_MATRIZ)
              if f['deadlocks'] == 'completo' and f['heuristica'] == 'h5'
              and f['corrida'] == '1']
    print(f'  {len(barrido)} corridas en {graficos.CSV_BARRIDO.relative_to(RAIZ)}')

    for w, metodo in (('0.50', 'A*'), ('1.00', 'Greedy')):
        for fila in (f for f in barrido if f['w'] == w):
            referencia = next(f for f in matriz if f['nivel'] == fila['nivel']
                              and f['metodo'] == metodo)
            medido = (fila['costo'], fila['nodos_expandidos'])
            esperado = (referencia['costo'], referencia['nodos_expandidos'])
            estado = 'OK' if medido == esperado else 'FALLA'
            print(f'  w={w} vs {metodo:<7}{fila["nivel"]:<14}'
                  f'{medido[0]:>5} / {_n(int(medido[1])):>9}   contra '
                  f'{esperado[0]:>5} / {_n(int(esperado[1])):>9}   {estado}')
            if medido != esperado:
                errores.append(
                    f'el barrido en w={w} sobre {fila["nivel"]} da '
                    f'{medido} y {metodo}(h5) da {esperado}. En ese punto el HPA '
                    f'ES ese método, así que tienen que coincidir exactamente.')

    subóptimas = [f for f in barrido
                  if float(f['w']) <= 0.5 and f['costo'] != f['costo_optimo']]
    print(f'  corridas con w <= 0,5 y costo distinto del óptimo publicado: '
          f'{len(subóptimas)}   {"OK" if not subóptimas else "FALLA"}')
    if subóptimas:
        errores.append('con w <= 0,5 el HPA es A* con una heurística admisible: '
                       'no puede devolver una solución subóptima.')
    return errores


def comprobar_4():
    """Ninguna figura pone barras de error sobre algo determinístico."""
    errores = []
    print('\n=== Comprobación 4 — barras de error sólo donde hay variabilidad ===')
    grupos = collections.defaultdict(list)
    for fila in graficos.leer(graficos.CSV_MATRIZ):
        clave = (fila['nivel'], fila['metodo'], fila['heuristica'],
                 fila['deadlocks'], fila['orden_sucesores'])
        grupos[clave].append(fila)

    con_variabilidad = collections.Counter()
    for clave, filas in grupos.items():
        for columna in COLUMNAS_DETERMINISTICAS:
            if len({f[columna] for f in filas}) > 1:
                con_variabilidad[clave[1]] += 1

    if con_variabilidad:
        errores.append(
            f'hay configuraciones que varían entre corridas: {dict(con_variabilidad)}. '
            f'Las figuras 1, 2 y 3 las grafican sin barra de error.')
    else:
        print(f'  {len(grupos)} configuraciones, ninguna varía sus '
              f'{len(COLUMNAS_DETERMINISTICAS)} columnas entre corridas   OK')

    dfs = collections.defaultdict(list)
    for fila in graficos.leer(graficos.CSV_MATRIZ):
        if fila['metodo'] == 'DFS':
            dfs[fila['nivel']].append(int(fila['nodos_expandidos']))
    for nivel, nodos in dfs.items():
        print(f'  DFS en {nivel:<14}{len(nodos)} permutaciones, '
              f'de {_n(min(nodos))} a {_n(max(nodos))} nodos')
    print('  Las 24 permutaciones son la población completa, no una muestra: el')
    print('  bigote de la figura 1 es el rango exacto y no un intervalo estimado.')
    return errores


def comprobar_5():
    """Reescala cada PNG al 50 % e informa el tamaño resultante."""
    from PIL import Image
    print('\n=== Comprobación 5 — prueba de legibilidad al 50 % ===')
    for nombre, _ in FIGURAS:
        ruta = graficos.FIGURAS / f'{nombre}.png'
        if not ruta.exists():
            continue
        with Image.open(ruta) as imagen:
            ancho, alto = imagen.size
        print(f'  {nombre:<24}{ancho}x{alto} px  →  al 50 %: {ancho // 2}x{alto // 2} px')
    print('  Que los rótulos se sigan leyendo a ese tamaño lo decide una persona,')
    print('  no este script. Abrir los PNG al 50 % antes de dar la fase por cerrada.')
    return []


def main() -> int:
    print('Verificación de la Fase 8 — gráficos y análisis')
    print('No corre ninguna búsqueda: las figuras salen de los CSV ya medidos.\n')

    errores = comprobar_1_y_3() + comprobar_2() + comprobar_4() + comprobar_5()

    print()
    if not errores:
        print(f'{len(FIGURAS)}/{len(FIGURAS)} figuras OK. Las 5 comprobaciones pasan.')
        return 0
    print(f'HAY {len(errores)} FALLAS:')
    for e in errores:
        print(f'  {e}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
