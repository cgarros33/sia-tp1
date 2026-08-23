"""La poda de los estados que ya no admiten solución.

QUÉ REPRESENTA
    Un detector responde una sola pregunta: después de este empuje, ¿el nivel
    quedó irrecuperable? Si dice que sí, ese sucesor ni se construye.

LA ASIMETRÍA QUE ORGANIZA EL MÓDULO — los dos errores no cuestan lo mismo
    Un FALSO NEGATIVO —no ver un deadlock que existe— cuesta nodos y nada más.
    Un FALSO POSITIVO —declarar muerto un estado que sí tenía solución— rompe la
    optimalidad, y en el peor caso hace que un nivel resoluble devuelva "sin
    solución". Por eso, ante la duda, no se poda: una regla que poda de menos es
    una regla floja, y una que poda de más es un bug difícil de ver, porque el
    programa termina igual y devuelve un número que parece razonable.

POR QUÉ PODAR NO ROMPE LA OPTIMALIDAD
    Si un estado no admite ninguna solución, entonces ningún camino de la raíz a
    una meta pasa por él. Sacarlo del grafo no saca ninguna solución: el conjunto
    de soluciones queda idéntico, y el mínimo sobre un conjunto idéntico es el
    mismo número.

    El argumento no dice nada sobre el detector: toda la carga está en la
    hipótesis "este estado no admite ninguna solución". Por eso cada regla lleva
    su propia demostración de que marca ÚNICAMENTE estados sin solución, igual
    que cada heurística de la Fase 4 lleva la suya de admisibilidad.

CADA DETECTOR ES UNA FÁBRICA, igual que cada heurística
    Recibe el nivel y devuelve la función que el motor va a llamar, con las
    tablas ya adentro. La firma la fijó la Fase 1:

        detector(cajas: frozenset[int], caja_movida: int) -> bool

    La fábrica recibe el `Tablero` y no el `Problema`, que es la única diferencia
    con las heurísticas. Por dos motivos: un deadlock es geometría del nivel y no
    depende del estado inicial, y sobre todo porque el `Problema` se construye
    CON el detector adentro — pedirle el problema a la fábrica sería un
    huevo-y-gallina.

    `Problema.sucesores()` la consulta sólo después de un empuje —un movimiento
    que no empuja nada no puede crear un deadlock, las cajas quedaron donde
    estaban— y antes de construir el `Estado`, así que un sucesor podado no paga
    ni el objeto ni el hash.

QUÉ SE DESCARTÓ
    Que la poda fuera un parámetro del motor. Obligaría a tocar `src/busqueda/`
    para algo que es una regla del problema y no del algoritmo de búsqueda, y el
    gancho del `Problema` existe desde la Fase 1 justamente para no hacerlo.
"""

from .heuristicas.distancias import celdas_muertas

#: Los cuatro cuadrados de 2x2 que contienen a una celda, dados por dónde queda
#: su esquina superior izquierda respecto de esa celda.
ESQUINAS_DEL_CUADRADO = ((-1, -1), (-1, 0), (0, -1), (0, 0))


def sin_poda(tablero):
    """Ningún detector. Devuelve `None`, no una función que siempre dice que no.

    Parece un detalle y no lo es. `sucesores()` pregunta `if detectar is not
    None` una vez por empuje: con `None` esa rama ni se toca, y sobre todo la
    corrida sin poda es EXACTAMENTE la misma corrida de las Fases 2 a 4, no una
    versión equivalente. Los números congelados en `tests/conftest.py` no se
    pueden mover, y así no hay forma de que se muevan.
    """
    return None


def deadlocks_estaticos(tablero):
    """Una caja en una celda desde la que ninguna meta es alcanzable a empujones.

    POR QUÉ NO TIENE FALSOS POSITIVOS
        El BFS de tirones de `distancias.celdas_muertas` arma el grafo de todos
        los empujes geométricamente posibles, ignorando las otras cajas y si el
        jugador puede llegar: es MÁS permisivo que el juego real. Si en ese grafo
        permisivo no hay camino de la celda a ninguna meta, en el juego real
        tampoco lo hay. Una caja ahí no llega nunca a una meta, y sin todas las
        cajas en metas no hay solución.

    El conjunto sale del mismo cálculo que la matriz de costos de h₄, y se
    importa en vez de recalcularlo: serían dos implementaciones de la misma
    cuenta, y el día que una cambie la otra queda vieja en silencio. Que la
    heurística y la poda salgan del mismo BFS deja de ser una frase de la
    presentación y pasa a ser un import.
    """
    muertas = celdas_muertas(tablero)

    def detectar(cajas, caja_movida):
        return caja_movida in muertas

    return detectar


def cuadrados_por_celda(tablero) -> dict[int, tuple[tuple[int, ...], ...]]:
    """Para cada celda de piso, qué haría falta para congelar un 2x2 que la contenga.

    Devuelve, por celda, una tupla con los cuadrados que podrían ser deadlock, y
    cada cuadrado reducido a LAS CELDAS DE PISO QUE FALTA OCUPAR: las paredes ya
    están ocupadas y no hay nada que preguntarles. Un cuadrado sin requisitos
    —tres paredes alrededor— es deadlock apenas la caja llega.

    Lo que cae fuera del rectángulo cuenta como pared, porque una caja nunca
    puede salir del tablero.

    SE DESCARTAN ACÁ los cuadrados cuyas celdas de piso son TODAS metas: cuando
    uno de ésos se llena, todas sus cajas están sobre metas y no es un deadlock.
    Es una decisión del nivel, no del estado, así que se toma una vez al
    construir en lugar de una vez por empuje. Sin este descarte el detector
    podaría el estado meta de `n4_matching`, cuyas cuatro metas forman un bloque
    de 2x2.
    """
    metas = tablero.metas
    paredes = tablero.paredes
    cuadrados = {}

    for celda in tablero.transitables:
        fila, columna = tablero.coordenadas(celda)
        candidatos = []
        for desplazamiento_fila, desplazamiento_columna in ESQUINAS_DEL_CUADRADO:
            piso = []
            for f in (fila + desplazamiento_fila, fila + desplazamiento_fila + 1):
                for c in (columna + desplazamiento_columna,
                          columna + desplazamiento_columna + 1):
                    if 0 <= f < tablero.alto and 0 <= c < tablero.ancho:
                        p = tablero.indice(f, c)
                        if p not in paredes:
                            piso.append(p)
            if all(p in metas for p in piso):
                continue
            candidatos.append(tuple(p for p in piso if p != celda))
        cuadrados[celda] = tuple(candidatos)

    return cuadrados


def deadlocks_congelados(tablero):
    """Un cuadrado de 2x2 lleno de paredes y cajas, con alguna caja fuera de meta.

    POR QUÉ NO TIENE FALSOS POSITIVOS
        Tomemos una caja de un cuadrado de 2x2 lleno. Su vecina horizontal dentro
        del cuadrado está ocupada y su vecina vertical también. Para empujarla a
        la derecha hace falta que la celda de la derecha esté libre; para
        empujarla a la izquierda, que el jugador quepa a su derecha. Las dos
        cosas piden la misma celda, y esa celda está ocupada: la caja no se mueve
        en horizontal. El mismo argumento en vertical, y por simetría vale para
        las cuatro celdas del cuadrado. Ninguna de esas cajas se mueve nunca más,
        así que si alguna no está sobre una meta el nivel no se puede completar.

    ES LA REGLA QUE LA ESTÁTICA NO PUEDE TENER: dos cajas pegadas contra una
    pared, cada una en una celda perfectamente viva, son un estado muerto que
    depende de dónde están LAS OTRAS cajas. Las dos reglas no se dominan entre
    sí, y por eso se miden por separado.

    ALCANZA CON REVISAR LA CAJA RECIÉN EMPUJADA, que es para lo que la Fase 1 la
    puso en la firma: si después del empuje hay un cuadrado lleno que no la
    contiene, ese cuadrado ya estaba lleno antes —las otras cajas y las paredes
    no se movieron— y se detectó en el empuje anterior.
    """
    cuadrados = cuadrados_por_celda(tablero)

    def detectar(cajas, caja_movida):
        return any(all(celda in cajas for celda in requisitos)
                   for requisitos in cuadrados[caja_movida])

    return detectar


def deadlocks_completo(tablero):
    """Las dos reglas. Primero la estática, que es una pertenencia a un conjunto.

    Se compone a partir de las otras dos fábricas en vez de repetir las dos
    cuentas, por el mismo motivo por el que h₅ reutiliza h₄: que el código diga
    literalmente "es una regla más la otra" es parte de lo que se defiende, y si
    una de las dos cambia, ésta cambia con ella. El `or` corta apenas la primera
    dice que sí, así que el orden es el de costo creciente.
    """
    estatico = deadlocks_estaticos(tablero)
    congelado = deadlocks_congelados(tablero)

    def detectar(cajas, caja_movida):
        return estatico(cajas, caja_movida) or congelado(cajas, caja_movida)

    return detectar


#: Nombre -> fábrica. `config.json` usa estos nombres, igual que con las
#: heurísticas. El orden es el de la medición de la fase: cada capa se compara
#: contra la corrida sin poda, y `completo` contra las dos capas sueltas.
DETECTORES = {
    'ninguno': sin_poda,
    'estaticos': deadlocks_estaticos,
    'congelados': deadlocks_congelados,
    'completo': deadlocks_completo,
}


def construir(nombre, tablero):
    """Devuelve el detector del nombre pedido, ya atado a este tablero."""
    if nombre not in DETECTORES:
        raise ValueError(
            f'Detector de deadlocks desconocido: {nombre!r}. '
            f'Opciones: {sorted(DETECTORES)}'
        )
    return DETECTORES[nombre](tablero)
