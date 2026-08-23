"""Las cuatro figuras de la presentación, generadas desde los CSV.

Se corre desde la raíz del repositorio:

    python3 -m experimentos.graficos

NO CORRE NINGUNA BÚSQUEDA. Lee `resultados.csv` —la matriz de la Fase 6— y
`experimentos/barrido_w.csv` —el experimento de esta fase— y escribe en
`presentacion/figuras/`. Que graficar y medir estén separados es lo que hace que
regenerar una figura sea instantáneo y que dos personas con el mismo CSV
obtengan exactamente la misma imagen.

LO QUE ORGANIZA TODAS LAS FIGURAS: la advertencia de la cátedra
    Si se analiza cómo se relacionan dos variables, las variables tienen que
    tener sentido, y una correlación sirve cuando se mueve una variable y el
    resto queda fijo. Cada figura de acá lleva escrito, en el docstring de su
    función, qué va en cada eje y QUÉ SE MANTIENE FIJO. Donde no se puede
    mantener fijo —comparar niveles distintos— se usan paneles separados en vez
    de un eje compartido, para no sugerir una comparación que no es válida.

BARRAS DE ERROR: SÓLO DONDE HAY VARIABILIDAD REAL
    Nodos expandidos, costo y memoria son DETERMINÍSTICOS. No se asume: está
    medido sobre las 645 filas de `resultados.csv`, donde ninguna configuración
    varía sus nodos entre sus cinco corridas. Poner una barra de error encima
    sería decorar con una incertidumbre que no existe.

    La variabilidad real del proyecto está en dos lugares y en ninguno más: el
    TIEMPO, que varía hasta un factor 3 con idénticos nodos, y DFS, que depende
    del orden de sucesores. La figura 1 usa esa segunda, con las 24
    permutaciones que corrió la Fase 6.

LEGIBLE PROYECTADO
    Fuentes grandes, líneas gruesas, sin grilla cargada, y ningún par de series
    que se distinga sólo por color: siempre hay además marcador, relleno o
    trazo distinto.
"""

import csv
from pathlib import Path

import matplotlib

# Backend sin pantalla: esto escribe archivos, no abre ventanas. Va antes de
# importar pyplot o matplotlib elige otro y falla en una máquina sin entorno
# gráfico, que es justo donde alguien va a querer regenerar las figuras.
matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
FIGURAS = RAIZ / 'presentacion' / 'figuras'
CSV_MATRIZ = RAIZ / 'resultados.csv'
CSV_BARRIDO = RAIZ / 'experimentos' / 'barrido_w.csv'

#: Paleta segura: ningún par se distingue sólo por rojo/verde, y son los mismos
#: dos colores con los que el reproductor de la Fase 7 dibuja las cajas, así que
#: las figuras y los GIF de la presentación se leen como una sola cosa.
AZUL = '#2668AA'
ARENA = '#E2A844'
GRIS = '#5C6068'
TINTA = '#2C2E34'

#: Para las figuras con una serie por nivel. Es la paleta de Okabe-Ito, elegida
#: porque NO contiene un par rojo/verde: el rojo directamente no está. Igual cada
#: serie lleva además su propio marcador, así que la figura se lee en escala de
#: grises.
POR_NIVEL = ('#0072B2', '#E69F00', '#009E73', '#CC79A7', '#56B4E9')
MARCADORES = ('o', 's', '^', 'D', 'v')

#: Los cinco niveles en el orden de la narrativa, con su óptimo publicado.
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
    """Escribe la figura en PNG de proyección y en PDF vectorial.

    `CreationDate=None` en el PDF no es un detalle: sin eso matplotlib le estampa
    la fecha de generación y dos corridas con el mismo CSV producirían archivos
    distintos, que es exactamente lo que el criterio 3 de la fase prohíbe.
    """
    FIGURAS.mkdir(parents=True, exist_ok=True)
    png, pdf = FIGURAS / f'{nombre}.png', FIGURAS / f'{nombre}.pdf'
    figura.savefig(png, dpi=200)
    figura.savefig(pdf, metadata={'CreationDate': None})
    plt.close(figura)
    return png, pdf


# --- figura 1 — nodos expandidos por método y nivel -------------------------

#: (etiqueta, método en el CSV, heurística, ¿devuelve el óptimo?, relleno). El
#: relleno acompaña al color: ninguna serie se distingue SÓLO por color.
METODOS_FIGURA_1 = (
    ('BFS', 'BFS', '—', True, ''),
    ('IDDFS', 'IDDFS', '—', True, '..'),
    ('A*(h₅)', 'A*', 'h5', True, '//'),
    ('Greedy(h₅)', 'Greedy', 'h5', False, 'xx'),
    ('DFS', 'DFS', '—', False, '\\\\'),
)


def figura_1_metodos():
    """Cuánto cuesta cada método, nivel por nivel.

    EJES
        X: el nivel, categórico, en el orden de la narrativa N1 a N5.
        Y: nodos expandidos, LOGARÍTMICO. El rango real va de 8 a 3.000.000.

    QUÉ SE MANTIENE FIJO
        h₅ en los dos métodos informados y poda `completo` en los cinco. Lo
        segundo es una decisión: en el CSV, BFS es el único método con las cuatro
        capas, y comparar el BFS SIN poda (44.124 nodos en n2) contra un A* CON
        poda (4.460) mezclaría el efecto del método con el de la poda en una sola
        barra. Con todos en `completo`, la única diferencia entre dos barras del
        mismo grupo es la política de la frontera, que es lo que la Fase 2 diseñó
        para que fuera así.

        Los niveles NO se comparan entre sí: son grupos separados. La pregunta
        "por qué N5 necesita más que N3" la contesta la figura 4.

    BARRAS DE ERROR SÓLO EN DFS
        Es el único método con variabilidad real, porque depende del orden de
        sucesores. La barra va a la media de las 24 permutaciones de DIRECCIONES
        y los bigotes al mínimo y al máximo.

        Y no son un intervalo de confianza: las 24 permutaciones son la POBLACIÓN
        COMPLETA, no una muestra, así que el bigote es el rango exacto de lo que
        puede pasar. Los otros cuatro métodos no llevan bigote porque sus cinco
        corridas dan exactamente el mismo número.
    """
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
        # Sólo DFS lleva bigotes: es el único cuyo mínimo y máximo difieren.
        barras = panel.bar(
            posiciones, alturas, ancho * 0.92,
            yerr=errores if metodo == 'DFS' else None,
            capsize=5 if metodo == 'DFS' else 0,
            color=AZUL if optimo else ARENA, edgecolor=TINTA, linewidth=0.9,
            hatch=relleno, label=etiqueta,
            error_kw=dict(ecolor=TINTA, elinewidth=1.6))

        # Un método que agotó el límite de nodos NO resolvió el nivel. Dibujar su
        # barra igual que las demás diría "IDDFS resolvió N5 con 3.000.000 de
        # nodos", que es falso.
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


# --- figura 2 — dominancia empírica de las heurísticas -----------------------

#: La escalera de la Fase 4, en orden. Las dos no admisibles quedan afuera: el
#: eje X es "qué fracción del costo real captura la heurística", y para una que
#: sobreestima ese número pasa de 1 y deja de significar lo mismo.
ESCALERA = ('h0', 'h1', 'h2', 'h3', 'h4', 'h5')


def figura_2_dominancia():
    """¿Una heurística más informada expande menos nodos?

    EJES
        X: informatividad h(s₀)/óptimo. 0 es h₀, que no informa nada; 1 sería la
           heurística perfecta.
        Y: nodos expandidos por A*, LOGARÍTMICO.

    QUÉ SE MANTIENE FIJO
        El método (A*), la poda (`completo`), el nivel dentro de cada serie y el
        motor. Lo único que cambia entre dos puntos de una misma línea es la
        heurística, que es justamente la variable del eje X.

        Cada nivel es una SERIE PROPIA, unida por una línea. La línea no
        interpola nada —entre h₂ y h₃ no hay heurísticas intermedias— y está para
        que la escalera se lea como una trayectoria y no como seis puntos
        sueltos. Los niveles no se comparan entre sí en el eje Y.

    LA INFORMATIVIDAD SE CALCULA ACÁ, Y NO ES UNA BÚSQUEDA
        h(s₀) se obtiene evaluando la heurística en el estado inicial: cuesta
        construir las tablas del nivel, que son unos pocos BFS sobre 12 a 41
        celdas. El denominador es el óptimo publicado. No se resuelve nada.
    """
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
        # El panel derecho divide por A*(h0), que es el mismo nivel sin ninguna
        # información heurística. Sin eso la pregunta de la figura no se puede
        # contestar mirando: en el panel izquierdo cada nivel vive en su propia
        # banda del eje y las cinco trayectorias parecen planas.
        relativo.plot(x, [yi / y[0] for yi in y], marker=marcador, color=color,
                      label=nivel, linewidth=1.8)
        for i, (xi, yi, nombre) in enumerate(zip(x, y, ESCALERA)):
            # Los rótulos alternan arriba y abajo: h₃, h₄ y h₅ caen casi encima
            # unos de otros en varios niveles y con un solo offset se pisan.
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


# --- figura 4 — el muro ------------------------------------------------------

#: (nivel, celdas transitables, cajas). Los cinco de la suite más el descartado.
GEOMETRIA = (
    ('n1_micro', 12, 1),
    ('n2_akk04', 32, 4),
    ('n3_caminata', 35, 2),
    ('n4_matching', 31, 4),
    ('n5_limite', 41, 4),
)
#: ABHT 02 · 03 (lid 37955). No entra en la batería: ver docs/03_NUMEROS_DE_ORO.md.
DESCARTADO = ('ABHT 02·03', 89, 5)
#: Lo que expandió A* con matching y poda antes de agotarse en ese nivel. Como
#: A* con poda expande MENOS que BFS, el número real de BFS es todavía mayor:
#: se dibuja como cota inferior, no como medición.
DESCARTADO_NODOS = 3_000_000


def _combinatorio(n, k):
    resultado = 1
    for i in range(k):
        resultado = resultado * (n - i) // (i + 1)
    return resultado


def espacio_de_estados(celdas, cajas):
    """`celdas × C(celdas, cajas)`, la fórmula de `docs/03_NUMEROS_DE_ORO.md`.

    Cuenta dónde puede estar el jugador por dónde puede estar cada conjunto de
    cajas. Sobreestima —incluye configuraciones inalcanzables— y por eso es una
    ESTIMACIÓN del tamaño del espacio, no su tamaño.
    """
    return celdas * _combinatorio(celdas, cajas)


def figura_4_el_muro():
    """Dónde está el límite del método, y por qué es combinatorio.

    EJES
        X: tamaño estimado del espacio de estados, `celdas × C(celdas, cajas)`,
           LOGARÍTMICO.
        Y: nodos expandidos por BFS, LOGARÍTMICO.

    QUÉ SE MANTIENE FIJO
        El método —BFS, sin poda— en los seis puntos. Se usa BFS y no A* porque
        es el único que no depende de ninguna heurística: mide el tamaño del
        problema, no lo bien que lo atacamos. Y se usa SIN poda por lo mismo, que
        es la versión cuyos números están congelados desde la Fase 3.

        Acá los niveles SÍ se comparan entre sí, y es válido justamente porque el
        eje X es lo que los distingue: la variable que cambia está en el gráfico
        en vez de estar escondida.

    EL PUNTO DESCARTADO ES UNA COTA, NO UNA MEDICIÓN
        De ABHT 02·03 no tenemos un número de BFS: tenemos que A* con matching y
        poda expandió 3.000.000 de nodos sin terminar. Como A* con poda expande
        MENOS que BFS, el número de BFS sería todavía mayor. Se dibuja con una
        flecha hacia arriba: lo que se afirma es "≥ 3.000.000", que es lo único
        que se puede afirmar.
    """
    bfs = {f['nivel']: int(f['nodos_expandidos']) for f in leer(CSV_MATRIZ)
           if f['metodo'] == 'BFS' and f['deadlocks'] == 'ninguno' and f['corrida'] == '1'}

    figura, panel = plt.subplots(figsize=(12, 7))
    x = [espacio_de_estados(c, k) for _, c, k in GEOMETRIA]
    y = [bfs[nivel] for nivel, _, _ in GEOMETRIA]

    # La posición del rótulo se elige a mano por nivel: n2 y n4 tienen un vecino
    # arriba a la derecha y el rótulo por defecto le pasa por encima al marcador.
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
    # La comparación que cierra el argumento: mismo largo de solución no es mismo
    # esfuerzo, y el que manda es la cantidad de cajas.
    panel.annotate('N3 resuelve 104 movimientos con 6.360 nodos;\n'
                   'N5 resuelve 306 con 2.028.239.\n'
                   'La diferencia no es el largo: es 2 cajas contra 4.',
                   xy=(0.03, 0.96), xycoords='axes fraction', va='top', fontsize=12,
                   bbox=dict(facecolor='white', edgecolor=GRIS, boxstyle='round,pad=0.5'))
    return guardar(figura, 'figura_4_el_muro')


# --- figura 3 — el barrido de w ---------------------------------------------

def figura_3_barrido():
    """El compromiso entre calidad de la solución y esfuerzo de búsqueda.

    EJES
        X:            w, de 0 a 1.
        Y izquierdo:  costo de la solución en MOVIMIENTOS, lineal, con el óptimo
                      publicado como línea horizontal punteada.
        Y derecho:    nodos expandidos, LOGARÍTMICO — en n4 el rango va de 219 a
                      60.308.

    QUÉ SE MANTIENE FIJO
        Dentro de cada panel, todo salvo w: el nivel, h₅, la poda completa, el
        límite de nodos, el orden de DIRECCIONES, el desempate de la frontera y
        el motor. Es el experimento controlado del TP.

        Los tres niveles van en PANELES SEPARADOS y no en un eje compartido:
        comparar los 60.308 nodos de n4 contra los 1.806 de n3 en el mismo eje
        sugeriría que la diferencia la hace w, cuando la hace el nivel.

    POR QUÉ LAS DOS SERIES VAN JUNTAS
        Por separado ninguna contesta la pregunta. Los nodos solos dicen "más w
        es mejor" y el costo solo dice "más w es peor"; lo que interesa es cuánto
        se paga por apurar la búsqueda, y eso es la relación entre las dos.
    """
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
        # El eje de costo arranca en CERO. Con autoescala, en n3 iría de 104 a
        # 108 y una penalización de 4 movimientos sobre 104 —un 3,8 %— se vería
        # como un salto vertical enorme. El costo tiene un cero con significado,
        # así que empezar ahí es lo que hace que los tres paneles se puedan leer
        # con la misma vara.
        panel.set_ylim(0, max(costo) * 1.22)
        panel.set_xlabel('w   en   f = (1−w)·g + w·h')
        panel.set_ylabel('costo de la solución (movimientos)', color=AZUL)
        panel.tick_params(axis='y', labelcolor=AZUL)
        panel.set_title(nivel, pad=30)

        # Cuánto peor es la solución de Greedy que el óptimo. Es EL número de la
        # figura y leerlo del gráfico exige mirar dos veces; escrito, no. Va
        # ARRIBA del área de datos y no adentro: adentro lo tapaba la curva de
        # nodos en n2, justo en el panel donde el número es más grande.
        exceso = 100 * (costo[-1] / optimo - 1)
        panel.annotate(f'Greedy: {costo[-1]} contra {optimo}   ({exceso:+.0f} %)',
                       xy=(0.5, 1.015), xycoords='axes fraction', ha='center',
                       va='bottom', fontsize=11, color=TINTA)

        # El segundo eje comparte X y no Y: son magnitudes distintas y una de las
        # dos es logarítmica.
        derecho = panel.twinx()
        derecho.plot(w, nodos, color=ARENA, marker='s', linestyle='--',
                     label='nodos expandidos', zorder=3)
        derecho.set_yscale('log')
        derecho.set_ylabel('nodos expandidos (escala log)', color=ARENA)
        derecho.tick_params(axis='y', labelcolor=ARENA)
        derecho.grid(False)

        # Los tres puntos que la spec pide marcar. Son los que conectan el
        # barrido con los métodos que ya se midieron por separado.
        for x, etiqueta, alineacion in ((0.0, 'costo uniforme', 'left'),
                                        (0.5, 'A*', 'center'),
                                        (1.0, 'Greedy', 'right')):
            panel.axvline(x, color=GRIS, linewidth=1.1, alpha=0.55, zorder=1)
            panel.annotate(etiqueta, xy=(x, 0.99), xycoords=('data', 'axes fraction'),
                           ha=alineacion, va='top', fontsize=11, color=GRIS,
                           bbox=dict(facecolor='white', alpha=0.8, edgecolor='none',
                                     boxstyle='square,pad=0.15'))

    # Una sola leyenda para los tres paneles: la codificación es la misma en
    # todos y repetirla tres veces gasta espacio en lo único que no cambia.
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
