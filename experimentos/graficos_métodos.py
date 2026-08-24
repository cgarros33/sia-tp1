"""Las figuras y tablas centradas en la comparación entre métodos."""

from pathlib import Path

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402

from .graficos import (ARENA, AZUL, CSV_MATRIZ, GRIS, NIVELES, RAIZ,  # noqa: E402
                       TINTA, aplicar_estilo, guardar, leer)

METODOS = (
    ('BFS', 'BFS', '—', True, ''),
    ('IDDFS', 'IDDFS', '—', True, '..'),
    ('A*(h₆)', 'A*', 'h6', True, '//'),
    ('Greedy(h₆)', 'Greedy', 'h6', False, 'xx'),
    ('DFS', 'DFS', '—', False, '\\\\'),
)

ESCALERA = ('h0', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hna', 'hna4')

ADMISIBLES = {'h0': True, 'h1': True, 'h2': True, 'h3': True, 'h4': True,
              'h5': True, 'h6': True, 'hna': False, 'hna4': False}

QUE_CALCULA = {
    'h0': '0',
    'h1': '1 si queda alguna caja fuera',
    'h2': 'cajas fuera de meta',
    'h3': 'Σ Manhattan a la meta más cercana',
    'h4': 'matching óptimo con Manhattan',
    'h5': 'matching con empujes reales',
    'h6': 'h₅ + término del jugador',
    'hna': '2·h₅',
    'hna4': '4·h₅',
}

LIMITE_NODOS = 3_000_000

NIVEL_CORTO = {'n1_micro': 'n1', 'n2_akk04': 'n2', 'n3_caminata': 'n3',
               'n4_matching': 'n4', 'n5_limite': 'n5'}


def corridas_de(filas, nivel, metodo, heuristica):
    """Las corridas de una configuración, con poda completa."""
    return [f for f in filas if f['nivel'] == nivel
            and f['metodo'] == metodo and f['heuristica'] == heuristica]


def resumen(corridas):
    """Los valores de una configuración: únicos si es determinística, rango si es DFS."""
    def enteros(columna):
        return [int(f[columna]) for f in corridas if f[columna] not in ('', 'None')]

    termino = all(f['motivo_fin'] == 'meta' for f in corridas)
    tiempos = [1000 * float(f['tiempo_s']) for f in corridas]
    return {
        'termino': termino,
        'costo': enteros('costo'),
        'expandidos': enteros('nodos_expandidos'),
        'frontera': enteros('frontera_maxima'),
        'memoria': enteros('memoria_maxima'),
        'tiempos': tiempos,
        'tiempo_ms': sum(tiempos) / len(tiempos),
    }


def barras_por_metodo(panel, altura_de, ancho=0.16, error_para_todos=False):
    """El esqueleto compartido de las figuras de barras: cinco métodos por nivel."""
    filas = [f for f in leer(CSV_MATRIZ) if f['deadlocks'] == 'completo']
    for i, (etiqueta, metodo, heuristica, optimo, relleno) in enumerate(METODOS):
        alturas, errores, cortadas = [], [[], []], []
        con_error = error_para_todos or metodo == 'DFS'
        for j, (nivel, referencia) in enumerate(NIVELES):
            datos = resumen(corridas_de(filas, nivel, metodo, heuristica))
            valores = altura_de(datos, referencia)
            altura = sum(valores) / len(valores) if valores else 0.0
            alturas.append(altura)
            errores[0].append(altura - min(valores) if con_error and valores else 0.0)
            errores[1].append(max(valores) - altura if con_error and valores else 0.0)
            if not datos['termino']:
                cortadas.append((j, altura))

        posiciones = [j + (i - 2) * ancho for j in range(len(NIVELES))]
        barras = panel.bar(
            posiciones, alturas, ancho * 0.92,
            yerr=errores if con_error else None,
            capsize=4 if con_error else 0,
            color=AZUL if optimo else ARENA, edgecolor=TINTA, linewidth=0.9,
            hatch=relleno, label=etiqueta,
            error_kw=dict(ecolor=TINTA, elinewidth=1.3))

        for j, altura in cortadas:
            barras[j].set_hatch('***')
            barras[j].set_alpha(0.5)
            panel.annotate('no terminó', xy=(posiciones[j], altura), xytext=(0, 7),
                           textcoords='offset points', ha='center', va='bottom',
                           fontsize=9, color=TINTA, rotation=90,
                           bbox=dict(facecolor='white', edgecolor='none', pad=0.8))

    panel.set_xticks(range(len(NIVELES)))
    panel.set_xticklabels([NIVEL_CORTO[n] for n, _ in NIVELES])
    panel.set_xlabel('nivel')
    panel.grid(axis='x', visible=False)


def costos_por_barra():
    """El costo crudo de cada barra, en el mismo orden en que se dibujan."""
    filas = [f for f in leer(CSV_MATRIZ) if f['deadlocks'] == 'completo']
    valores = []
    for _, metodo, heuristica, _, _ in METODOS:
        for nivel, _ in NIVELES:
            datos = resumen(corridas_de(filas, nivel, metodo, heuristica))
            valores.append(datos['costo'][0] if datos['costo'] else None)
    return valores


def tiempos_por_barra():
    """El tiempo medio crudo de cada barra y si esa corrida terminó, en orden de dibujo."""
    filas = [f for f in leer(CSV_MATRIZ) if f['deadlocks'] == 'completo']
    valores = []
    for _, metodo, heuristica, _, _ in METODOS:
        for nivel, _ in NIVELES:
            datos = resumen(corridas_de(filas, nivel, metodo, heuristica))
            valores.append((datos['tiempo_ms'], datos['termino']))
    return valores


def formatear_ms(valor):
    """Un tiempo en ms, con el mismo formato que la Tabla 1."""
    return '< 0,1' if valor < 0.05 else decimal(valor, 1)


TECHO_FIGURA_5 = 8.6


def figura_5_costo():
    """¿Qué calidad de solución devuelve cada método?"""
    figura, panel = plt.subplots(figsize=(14, 6.4))
    barras_por_metodo(panel, lambda d, optimo: [c / optimo for c in d['costo']])

    for barra, costo in zip(panel.patches, costos_por_barra()):
        if costo is None:
            continue
        altura = barra.get_height()
        x = barra.get_x() + barra.get_width() / 2
        if altura > TECHO_FIGURA_5:
            texto = f'{miles(costo)}\n({decimal(altura, 1)}×)'
            panel.annotate(texto, xy=(x, TECHO_FIGURA_5), xytext=(0, -48),
                           textcoords='offset points', ha='center',
                           fontsize=10.5, fontweight='bold', color=TINTA, linespacing=1.3,
                           bbox=dict(facecolor='white', edgecolor='none', pad=1.5))
        elif altura > 1.005:
            texto = f'{miles(costo)}\n({decimal(altura, 2)}×)'
            panel.annotate(texto, xy=(x, altura), xytext=(0, 4),
                           textcoords='offset points', ha='center',
                           fontsize=8.5, color=TINTA, linespacing=1.3)
        else:
            panel.annotate(miles(costo), xy=(x, altura), xytext=(0, 4),
                           textcoords='offset points', ha='center',
                           fontsize=8.5, color=GRIS)

    panel.axhline(1.0, color=AZUL, linestyle=':', linewidth=2.2, alpha=0.85, zorder=1)
    panel.annotate('óptimo', xy=(-0.45, 1.0), xytext=(0, 6),
                   textcoords='offset points', va='bottom', color=AZUL, fontsize=12)
    panel.set_ylabel('costo ÷ óptimo publicado')
    panel.set_ylim(0, TECHO_FIGURA_5)
    panel.set_title('Calidad de la solución', fontsize=16)
    panel.legend(ncol=5, loc='upper left', framealpha=0.95)
    return guardar(figura, 'figura_5_costo')


def figura_6_memoria():
    """¿Cuántos nodos hay que tener en memoria a la vez, según el método?"""
    figura, panel = plt.subplots(figsize=(14, 6.4))
    barras_por_metodo(panel, lambda d, _: d['frontera'])
    panel.set_yscale('log')
    panel.set_ylabel('nodos en la frontera, máximo (escala log)')
    panel.set_title('Tamaño de la frontera', fontsize=16)
    panel.legend(ncol=5, loc='upper left', framealpha=0.95)
    return guardar(figura, 'figura_6_memoria')


def figura_7_tiempo():
    """¿Cuánto tarda cada método, y cuánto varía entre corridas?"""
    figura, panel = plt.subplots(figsize=(14, 6.4))
    barras_por_metodo(panel, lambda d, _: d['tiempos'], error_para_todos=True)
    panel.set_yscale('log')
    panel.set_ylim(bottom=0.35, top=panel.get_ylim()[1] * 4)
    panel.set_ylabel('tiempo de procesamiento, ms (escala log)')
    panel.set_title('Tiempo de procesamiento', fontsize=16)

    piso = panel.get_ylim()[0]
    for barra, (tiempo_ms, termino) in zip(panel.patches, tiempos_por_barra()):
        if not termino:
            continue  # ya lleva la marca "no terminó"
        x = barra.get_x() + barra.get_width() / 2
        altura = barra.get_height()
        texto = formatear_ms(tiempo_ms)
        if altura > 0:
            panel.annotate(texto, xy=(x, altura), xytext=(0, 4),
                           textcoords='offset points', ha='center',
                           fontsize=8, color=GRIS, rotation=90 if altura < piso * 3 else 0)
        else:
            panel.annotate(texto, xy=(x, piso), xytext=(0, 3),
                           textcoords='offset points', ha='center', va='bottom',
                           fontsize=8, color=GRIS, rotation=90)

    panel.legend(ncol=5, loc='upper left', framealpha=0.95)
    return guardar(figura, 'figura_7_tiempo')


def miles(valor):
    """Un entero con punto como separador de miles."""
    return f'{valor:,}'.replace(',', '.')


def decimal(valor, cifras=1):
    """Un número con punto de miles y coma decimal, como se escribe en castellano."""
    entero, _, fraccion = f'{valor:,.{cifras}f}'.partition('.')
    return f"{entero.replace(',', '.')},{fraccion}"


def rango(valores):
    """Un valor solo, o el rango mínimo–máximo si la configuración varía."""
    if min(valores) == max(valores):
        return miles(valores[0])
    return f'{miles(min(valores))}–{miles(max(valores))}'


def dibujar_tabla(panel, encabezados, filas, colores, anchos):
    """Una tabla de matplotlib con el estilo de las figuras, anclada arriba."""
    tabla = panel.table(cellText=filas, colLabels=encabezados, colWidths=anchos,
                        cellLoc='center', loc='upper center')
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(11)
    tabla.scale(1, 1.55)
    for (fila, columna), celda in tabla.get_celld().items():
        celda.set_edgecolor('#D6D8DC')
        celda.set_linewidth(0.8)
        if fila == 0:
            celda.set_facecolor(TINTA)
            celda.set_text_props(color='white', fontweight='bold')
        else:
            celda.set_facecolor(colores[fila - 1])
    panel.axis('off')
    return tabla


def tabla_1_metricas():
    """Todos los números que pide el enunciado, en una sola diapositiva."""
    filas_csv = [f for f in leer(CSV_MATRIZ) if f['deadlocks'] == 'completo']
    filas, colores = [], []

    for nivel, optimo in NIVELES:
        for etiqueta, metodo, heuristica, _, _ in METODOS:
            datos = resumen(corridas_de(filas_csv, nivel, metodo, heuristica))
            tiempo = decimal(datos['tiempo_ms']) if datos['tiempo_ms'] >= 0.05 else '< 0,1'
            if not datos['termino']:
                filas.append([nivel, etiqueta, 'FRACASO', f'cortado en {miles(LIMITE_NODOS)}',
                              miles(LIMITE_NODOS), rango(datos['frontera']),
                              rango(datos['memoria']), tiempo])
                colores.append('#F5E1E1')
                continue
            es_optimo = max(datos['costo']) == optimo
            filas.append([
                nivel, etiqueta, 'ÉXITO', rango(datos['costo']),
                rango(datos['expandidos']), rango(datos['frontera']),
                rango(datos['memoria']), tiempo,
            ])
            colores.append('#E8F0F8' if es_optimo else '#FBF1DF')

    figura, panel = plt.subplots(figsize=(17, 9.8))
    tabla = dibujar_tabla(
        panel,
        ['nivel', 'método', 'resultado', 'costo\n(movimientos)', 'nodos\nexpandidos',
         'frontera\nmáxima', 'memoria\nmáxima', 'tiempo\n(ms)'],
        filas, colores,
        [0.13, 0.11, 0.09, 0.15, 0.14, 0.12, 0.14, 0.09])

    for fila in range(len(METODOS) + 1, len(filas) + 1, len(METODOS)):
        for columna in range(8):
            tabla[fila, columna].visible_edges = 'LRT'
            tabla[fila, columna].set_edgecolor(GRIS)

    panel.set_title('Tabla 1 — La matriz completa', fontsize=17, pad=16)
    figura.text(0.5, 0.035, 'DFS: rango de las 24 permutaciones',
                ha='center', fontsize=11, color=GRIS)
    return guardar(figura, 'tabla_1_metricas')


def tabla_2_heuristicas():
    """La escalera de heurísticas: qué informa cada una y qué le ahorra a A*."""
    from src.deadlocks import construir as construir_detector
    from src.heuristicas import construir as construir_heuristica
    from src.modelo import Problema, leer_archivo

    filas_csv = [f for f in leer(CSV_MATRIZ)
                 if f['metodo'] == 'A*' and f['deadlocks'] == 'completo'
                 and f['corrida'] == '1']

    iniciales = {}
    for nivel, _ in NIVELES:
        tablero, inicial = leer_archivo(RAIZ / 'niveles' / f'{nivel}.sok')
        problema = Problema(tablero, inicial,
                            detector_deadlocks=construir_detector('completo', tablero))
        iniciales[nivel] = (problema, inicial)

    filas, colores = [], []
    for nombre in ESCALERA:
        fila = [nombre, QUE_CALCULA[nombre], 'sí' if ADMISIBLES[nombre] else 'NO']
        subóptima = False
        for nivel, optimo in NIVELES:
            problema, inicial = iniciales[nivel]
            h = construir_heuristica(nombre, problema)(inicial)
            del_nivel = next(f for f in filas_csv
                             if f['nivel'] == nivel and f['heuristica'] == nombre)
            costo = int(del_nivel['costo'])
            expandidos = miles(int(del_nivel['nodos_expandidos']))
            marca = '' if costo == optimo else f'   ✗ costo {costo}'
            subóptima = subóptima or costo != optimo
            fila.append(f"{h}   ({decimal(h / optimo, 2)})\n{expandidos}{marca}")
        filas.append(fila)
        colores.append('#FBF1DF' if not ADMISIBLES[nombre] else '#E8F0F8')

    figura, panel = plt.subplots(figsize=(18, 4.6))
    dibujar_tabla(
        panel,
        ['heurística', 'qué calcula', 'admisible'] + [n for n, _ in NIVELES],
        filas, colores,
        [0.075, 0.19, 0.075] + [0.132] * 5)
    panel.set_title('Tabla 2 — La escalera de heurísticas   ·   A* con poda completa',
                    fontsize=17, pad=16)
    figura.text(0.5, 0.055, 'celda:  h(s₀)  (÷ óptimo)  ·  nodos de A*        ✗ costo subóptimo',
                ha='center', fontsize=11, color=GRIS)
    return guardar(figura, 'tabla_2_heuristicas')


def main() -> int:
    aplicar_estilo()
    generadas = []
    for salida in (figura_5_costo, figura_6_memoria, figura_7_tiempo,
                  tabla_1_metricas, tabla_2_heuristicas):
        generadas += list(salida())
    for ruta in generadas:
        print(f'  {ruta.relative_to(RAIZ)}  ({ruta.stat().st_size / 1024:.1f} KB)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
