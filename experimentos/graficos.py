"""Las cuatro figuras de la presentación, generadas desde los CSV."""

import csv
from pathlib import Path

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
FIGURAS = RAIZ / 'presentacion' / 'figuras'
CSV_MATRIZ = RAIZ / 'resultados.csv'
CSV_BARRIDO = RAIZ / 'experimentos' / 'barrido_w.csv'

AZUL = '#2668AA'
ARENA = '#E2A844'
GRIS = '#5C6068'
TINTA = '#2C2E34'

POR_NIVEL = ('#0072B2', '#E69F00', '#009E73', '#CC79A7', '#56B4E9')
MARCADORES = ('o', 's', '^', 'D', 'v')

NIVELES = (
    ('n1_micro', 8),
    ('n2_akk04', 45),
    ('n3_caminata', 104),
    ('n4_matching', 70),
    ('n5_limite', 306),
)


def aplicar_estilo():
    """Tipografía y trazos pensados para un proyector, no para una pantalla."""
    plt.rcParams.update({
        'font.size': 13,
        'axes.titlesize': 15,
        'axes.labelsize': 13,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12,
        'lines.linewidth': 2.6,
        'lines.markersize': 8,
        'axes.linewidth': 1.2,
        'axes.grid': True,
        'grid.alpha': 0.25,
        'grid.linewidth': 0.8,
        'figure.constrained_layout.use': True,
    })


def leer(ruta):
    """Las filas de un CSV como diccionarios. La única lectura de datos del módulo."""
    with open(ruta, encoding='utf-8') as archivo:
        return list(csv.DictReader(archivo))


def guardar(figura, nombre):
    """Escribe la figura en PNG de proyección y en PDF vectorial."""
    FIGURAS.mkdir(parents=True, exist_ok=True)
    png, pdf = FIGURAS / f'{nombre}.png', FIGURAS / f'{nombre}.pdf'
    figura.savefig(png, dpi=200)
    figura.savefig(pdf, metadata={'CreationDate': None})
    plt.close(figura)
    return png, pdf


METODOS_FIGURA_1 = (
    ('BFS', 'BFS', '—', True, ''),
    ('IDDFS', 'IDDFS', '—', True, '..'),
    ('A*(h₅)', 'A*', 'h5', True, '//'),
    ('Greedy(h₅)', 'Greedy', 'h5', False, 'xx'),
    ('DFS', 'DFS', '—', False, '\\\\'),
)


def figura_1_metodos():
    """Cuánto cuesta cada método, nivel por nivel."""
    filas = [f for f in leer(CSV_MATRIZ) if f['deadlocks'] == 'completo']
    figura, panel = plt.subplots(figsize=(14, 6.4))
    ancho = 0.16

    for i, (etiqueta, metodo, heuristica, optimo, relleno) in enumerate(METODOS_FIGURA_1):
        alturas, errores, sin_solucion = [], [[], []], []
        for j, (nivel, _) in enumerate(NIVELES):
            corridas = [f for f in filas if f['nivel'] == nivel
                        and f['metodo'] == metodo and f['heuristica'] == heuristica]
            nodos = [int(f['nodos_expandidos']) for f in corridas]
            altura = sum(nodos) / len(nodos)
            alturas.append(altura)
            errores[0].append(altura - min(nodos))
            errores[1].append(max(nodos) - altura)
            if any(f['motivo_fin'] != 'meta' for f in corridas):
                sin_solucion.append((j, altura))

        posiciones = [j + (i - 2) * ancho for j in range(len(NIVELES))]
        barras = panel.bar(
            posiciones, alturas, ancho * 0.92,
            yerr=errores if metodo == 'DFS' else None,
            capsize=5 if metodo == 'DFS' else 0,
            color=AZUL if optimo else ARENA, edgecolor=TINTA, linewidth=0.9,
            hatch=relleno, label=etiqueta,
            error_kw=dict(ecolor=TINTA, elinewidth=1.6))

        for j, altura in sin_solucion:
            barras[j].set_hatch('***')
            panel.annotate('sin\nsolución', xy=(posiciones[j], altura * 1.15),
                           ha='center', va='bottom', fontsize=10, color=TINTA,
                           linespacing=0.95)

    panel.set_yscale('log')
    panel.set_xticks(range(len(NIVELES)))
    panel.set_xticklabels([n for n, _ in NIVELES])
    panel.set_xlabel('nivel')
    panel.set_ylabel('nodos expandidos (escala log)')
    panel.set_ylim(top=2.5e7)
    panel.set_title('Figura 1 — Nodos expandidos por método y nivel'
                    '   ·   h₅ y poda completa en los cinco métodos', fontsize=16)
    panel.grid(axis='x', visible=False)

    manijas, etiquetas = panel.get_legend_handles_labels()
    manijas.append(plt.Rectangle((0, 0), 1, 1, facecolor='white', edgecolor=TINTA))
    etiquetas.append('azul: devuelve el óptimo · arena: no\n'
                     'bigotes en DFS: rango exacto de las 24 permutaciones')
    panel.legend(manijas, etiquetas, ncol=3, loc='upper left', framealpha=0.95)
    return guardar(figura, 'figura_1_metodos')


ESCALERA = ('h0', 'h1', 'h2', 'h3', 'h4', 'h5')


def figura_2_dominancia():
    """¿Una heurística más informada expande menos nodos?"""
    from src.deadlocks import construir as construir_detector
    from src.heuristicas import construir as construir_heuristica
    from src.modelo import Problema, leer_archivo

    filas = [f for f in leer(CSV_MATRIZ)
             if f['metodo'] == 'A*' and f['deadlocks'] == 'completo'
             and f['corrida'] == '1']

    figura, (absoluto, relativo) = plt.subplots(1, 2, figsize=(16, 6.6))
    for (nivel, optimo), color, marcador in zip(NIVELES, POR_NIVEL, MARCADORES):
        tablero, inicial = leer_archivo(RAIZ / 'niveles' / f'{nivel}.sok')
        problema = Problema(tablero, inicial,
                            detector_deadlocks=construir_detector('completo', tablero))
        x, y = [], []
        for nombre in ESCALERA:
            h = construir_heuristica(nombre, problema)
            x.append(h(inicial) / optimo)
            y.append(int(next(f['nodos_expandidos'] for f in filas
                              if f['nivel'] == nivel and f['heuristica'] == nombre)))

        absoluto.plot(x, y, marker=marcador, color=color, label=nivel, linewidth=1.8)
        relativo.plot(x, [yi / y[0] for yi in y], marker=marcador, color=color,
                      label=nivel, linewidth=1.8)
        for i, (xi, yi, nombre) in enumerate(zip(x, y, ESCALERA)):
            desplazamiento = (5, 7) if i % 2 == 0 else (5, -14)
            relativo.annotate(nombre, xy=(xi, yi / y[0]), xytext=desplazamiento,
                              textcoords='offset points', fontsize=10, color=GRIS)

    absoluto.set_yscale('log')
    absoluto.set_xlabel('informatividad   h(s₀) / óptimo publicado')
    absoluto.set_ylabel('nodos expandidos por A* (escala log)')
    absoluto.set_title('Nodos absolutos: cada nivel vive en su propia banda')

    relativo.axhline(1.0, color=GRIS, linestyle=':', linewidth=1.6)
    relativo.set_xlabel('informatividad   h(s₀) / óptimo publicado')
    relativo.set_ylabel('nodos expandidos ÷ los de A*(h₀) en el mismo nivel')
    relativo.set_ylim(0, 1.12)
    relativo.set_title('Relativo a A*(h₀): acá se ve cuánto compra cada eslabón')
    relativo.legend(title='nivel', loc='lower left', ncol=2)

    figura.suptitle('Figura 2 — Dominancia empírica: la escalera h₀ → h₅ como trayectoria'
                    '   ·   A* con poda completa', fontsize=16)
    return guardar(figura, 'figura_2_dominancia')


GEOMETRIA = (
    ('n1_micro', 12, 1),
    ('n2_akk04', 32, 4),
    ('n3_caminata', 35, 2),
    ('n4_matching', 31, 4),
    ('n5_limite', 41, 4),
)
DESCARTADO = ('ABHT 02·03', 89, 5)
DESCARTADO_NODOS = 3_000_000


def _combinatorio(n, k):
    resultado = 1
    for i in range(k):
        resultado = resultado * (n - i) // (i + 1)
    return resultado


def espacio_de_estados(celdas, cajas):
    """`celdas × C(celdas, cajas)`, la fórmula de `docs/03_NUMEROS_DE_ORO.md`."""
    return celdas * _combinatorio(celdas, cajas)


def figura_4_el_muro():
    """Dónde está el límite del método, y por qué es combinatorio."""
    bfs = {f['nivel']: int(f['nodos_expandidos']) for f in leer(CSV_MATRIZ)
           if f['metodo'] == 'BFS' and f['deadlocks'] == 'ninguno' and f['corrida'] == '1'}

    figura, panel = plt.subplots(figsize=(12, 7))
    x = [espacio_de_estados(c, k) for _, c, k in GEOMETRIA]
    y = [bfs[nivel] for nivel, _, _ in GEOMETRIA]

    ROTULOS = {'n2_akk04': (11, 10, 'bottom'), 'n4_matching': (11, -8, 'top')}
    for (nivel, celdas, cajas), xi, yi in zip(GEOMETRIA, x, y):
        panel.scatter(xi, yi, s=190, color=AZUL, edgecolor=TINTA, zorder=3,
                      marker='o' if cajas == 4 else 's')
        cajas_texto = '1 caja' if cajas == 1 else f'{cajas} cajas'
        dx, dy, alineacion = ROTULOS.get(nivel, (11, 4, 'bottom'))
        panel.annotate(f'{nivel}\n{cajas_texto} · {celdas} celdas',
                       xy=(xi, yi), xytext=(dx, dy), textcoords='offset points',
                       fontsize=11, va=alineacion)

    nombre, celdas, cajas = DESCARTADO
    x_descartado = espacio_de_estados(celdas, cajas)
    panel.scatter(x_descartado, DESCARTADO_NODOS, s=230, marker='^',
                  color=ARENA, edgecolor=TINTA, zorder=3)
    panel.annotate('', xy=(x_descartado, DESCARTADO_NODOS * 6),
                   xytext=(x_descartado, DESCARTADO_NODOS),
                   arrowprops=dict(arrowstyle='-|>', color=ARENA, linewidth=2.4))
    panel.annotate(f'{nombre}\n{cajas} cajas · {celdas} celdas\nNO RESUELTO  (≥ 3.000.000)',
                   xy=(x_descartado, DESCARTADO_NODOS), xytext=(-14, -46),
                   textcoords='offset points', fontsize=11, ha='right', va='top',
                   color=TINTA)

    panel.set_xscale('log')
    panel.set_yscale('log')
    panel.set_xlabel('tamaño estimado del espacio de estados   '
                     'celdas × C(celdas, cajas)   (escala log)')
    panel.set_ylabel('nodos expandidos por BFS sin poda (escala log)')
    panel.set_title('Figura 4 — El muro: el límite es combinatorio, no de largo de solución',
                    fontsize=16)
    panel.set_ylim(bottom=6, top=DESCARTADO_NODOS * 30)
    panel.set_xlim(right=x_descartado * 25)
    panel.annotate('N3 resuelve 104 movimientos con 6.360 nodos;\n'
                   'N5 resuelve 306 con 2.028.239.\n'
                   'La diferencia no es el largo: es 2 cajas contra 4.',
                   xy=(0.03, 0.96), xycoords='axes fraction', va='top', fontsize=12,
                   bbox=dict(facecolor='white', edgecolor=GRIS, boxstyle='round,pad=0.5'))
    return guardar(figura, 'figura_4_el_muro')


def figura_3_barrido():
    """El compromiso entre calidad de la solución y esfuerzo de búsqueda."""
    filas = leer(CSV_BARRIDO)
    niveles = sorted({f['nivel'] for f in filas},
                     key=lambda n: [x[0] for x in NIVELES].index(n))

    figura, paneles = plt.subplots(1, len(niveles), figsize=(16, 5.2))
    for panel, nivel in zip(paneles, niveles):
        del_nivel = sorted((f for f in filas if f['nivel'] == nivel),
                           key=lambda f: float(f['w']))
        w = [float(f['w']) for f in del_nivel]
        costo = [int(f['costo']) for f in del_nivel]
        nodos = [int(f['nodos_expandidos']) for f in del_nivel]
        optimo = int(del_nivel[0]['costo_optimo'])

        panel.plot(w, costo, color=AZUL, marker='o', label='costo (movimientos)',
                   zorder=3)
        panel.axhline(optimo, color=AZUL, linestyle=':', linewidth=2,
                      alpha=0.7, zorder=2)
        panel.annotate(f'óptimo = {optimo}', xy=(0.02, optimo), xytext=(0, 5),
                       textcoords='offset points', va='bottom', color=AZUL,
                       fontsize=11)
        panel.set_ylim(0, max(costo) * 1.22)
        panel.set_xlabel('w   en   f = (1−w)·g + w·h')
        panel.set_ylabel('costo de la solución (movimientos)', color=AZUL)
        panel.tick_params(axis='y', labelcolor=AZUL)
        panel.set_title(nivel, pad=30)

        exceso = 100 * (costo[-1] / optimo - 1)
        panel.annotate(f'Greedy: {costo[-1]} contra {optimo}   ({exceso:+.0f} %)',
                       xy=(0.5, 1.015), xycoords='axes fraction', ha='center',
                       va='bottom', fontsize=11, color=TINTA)

        derecho = panel.twinx()
        derecho.plot(w, nodos, color=ARENA, marker='s', linestyle='--',
                     label='nodos expandidos', zorder=3)
        derecho.set_yscale('log')
        derecho.set_ylabel('nodos expandidos (escala log)', color=ARENA)
        derecho.tick_params(axis='y', labelcolor=ARENA)
        derecho.grid(False)

        for x, etiqueta, alineacion in ((0.0, 'costo uniforme', 'left'),
                                        (0.5, 'A*', 'center'),
                                        (1.0, 'Greedy', 'right')):
            panel.axvline(x, color=GRIS, linewidth=1.1, alpha=0.55, zorder=1)
            panel.annotate(etiqueta, xy=(x, 0.99), xycoords=('data', 'axes fraction'),
                           ha=alineacion, va='top', fontsize=11, color=GRIS,
                           bbox=dict(facecolor='white', alpha=0.8, edgecolor='none',
                                     boxstyle='square,pad=0.15'))

    figura.legend(handles=[
        plt.Line2D([], [], color=AZUL, marker='o', label='costo (movimientos), eje izq.'),
        plt.Line2D([], [], color=ARENA, marker='s', linestyle='--',
                   label='nodos expandidos, eje der. (log)'),
        plt.Line2D([], [], color=AZUL, linestyle=':', label='óptimo publicado'),
    ], loc='outside lower center', ncol=3)
    figura.suptitle('Figura 3 — Barrido de w: qué se paga por apurar la búsqueda'
                    '   ·   h₅, poda completa', fontsize=16)
    return guardar(figura, 'figura_3_barrido_w')


def main() -> int:
    aplicar_estilo()
    generadas = []
    for figura in (figura_1_metodos, figura_2_dominancia, figura_3_barrido,
                   figura_4_el_muro):
        generadas += list(figura())
    for ruta in generadas:
        print(f'  {ruta.relative_to(RAIZ)}  ({ruta.stat().st_size / 1024:.1f} KB)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
