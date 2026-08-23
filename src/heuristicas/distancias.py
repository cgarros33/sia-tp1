"""Las tablas de distancias que las heurísticas precalculan una vez por nivel.

QUÉ REPRESENTA
    Todo lo que una heurística necesita saber sobre la GEOMETRÍA del nivel y que
    no depende del estado. Las paredes y las metas no cambian nunca, así que la
    distancia de una celda a una meta tampoco: calcularla en cada evaluación
    sería recalcular millones de veces un número que ya está fijo desde que se
    leyó el archivo.

LA DECISIÓN DE DISEÑO — por qué este módulo existe aparte
    Podría estar adentro de cada heurística. Está afuera porque las tablas se
    COMPARTEN: h₄, h₅ y las dos no admisibles usan exactamente la misma matriz de
    distancias de empuje, y la Fase 5 va a usar el conjunto de celdas muertas que
    sale de esa misma cuenta. Tenerlo en un solo lugar es lo que hace que "la
    heurística y la poda de deadlocks salen del mismo cálculo" sea un hecho del
    código y no una frase de la presentación.

    Las funciones reciben un `Tablero` y devuelven estructuras nuevas, sin
    guardar nada global. Construir todas las tablas de un nivel cuesta unos pocos
    BFS sobre 12 a 41 celdas: es instantáneo, así que no hace falta ninguna caché
    entre heurísticas y el módulo queda sin estado, que es más fácil de testear.

QUÉ SE DESCARTÓ
    Colgar las tablas del `Tablero` como atributos. Sería cómodo y ensuciaría la
    separación de la Fase 1: `Tablero` es el nivel, no lo que las heurísticas
    piensan del nivel. Además obligaría a que todo nivel pague el cálculo aunque
    se lo resuelva con BFS, que no usa ninguna heurística.
"""

from collections import deque

from ..modelo.tablero import DIRECCIONES

#: Costo que se pone en la matriz de asignación cuando una caja NO puede llegar a
#: una meta. `scipy.optimize.linear_sum_assignment` necesita una matriz finita, así
#: que "infinito" tiene que ser un número; se elige grande para que cualquier
#: asignación que use una de esas entradas sea peor que cualquier asignación
#: totalmente finita, y redondo para que se reconozca de un vistazo en la salida.
#:
#: LO QUE HAY QUE SABER PARA DEFENDERLO: una heurística que devuelve un valor
#: >= INALCANZABLE está diciendo que ese estado NO TIENE SOLUCIÓN. Sobreestimar un
#: estado sin solución no rompe la admisibilidad, porque ahí h* = infinito y
#: cualquier valor finito sigue siendo menor. Lo que sí puede romper es la
#: consistencia, y por eso el motor de la Fase 2 usa la política `mejor_g`, que
#: reabre nodos y no asume consistencia.
INALCANZABLE = 10 ** 6


def metas_ordenadas(tablero) -> tuple[int, ...]:
    """Las metas en un orden fijo, para que sirvan de columnas de una matriz.

    `Tablero.metas` es un `frozenset` y el orden de iteración de un conjunto no
    es parte de su contrato. h₃ y h₄ arman una matriz de costos donde la columna
    j ES la meta j: si el orden cambiara entre dos llamadas, la matriz sería otra.
    Ordenar por posición fija ese orden de una vez y hace que la matriz sea
    reproducible y comparable entre corridas.
    """
    return tuple(sorted(tablero.metas))


def distancias_manhattan_por_meta(tablero) -> dict[int, tuple[int, ...]]:
    """Para cada celda transitable, la distancia de Manhattan a CADA meta.

    Es la matriz de costos de h₃, precalculada por celda en vez de por estado:
    la fila que le toca a una caja depende sólo de dónde está la caja, no del
    resto del estado, así que se calcula una vez por nivel y durante la búsqueda
    armar la matriz es juntar tantas filas como cajas haya.

    El orden de las columnas es el de `metas_ordenadas`.
    """
    ancho = tablero.ancho
    metas = [divmod(meta, ancho) for meta in metas_ordenadas(tablero)]
    tabla = {}
    for celda in tablero.transitables:
        fila, columna = divmod(celda, ancho)
        tabla[celda] = tuple(
            abs(fila - fila_meta) + abs(columna - columna_meta)
            for fila_meta, columna_meta in metas
        )
    return tabla


def distancias_manhattan(tablero) -> dict[int, int]:
    """Para cada celda transitable, la mínima distancia de Manhattan a una meta.

    Manhattan es |Δfila| + |Δcolumna|: los pasos que costaría en un tablero sin
    paredes. Se precalcula para TODA celda transitable, no sólo para las que
    ocupan las cajas del estado inicial, porque durante la búsqueda una caja
    puede terminar en cualquiera de ellas.

    Devuelve un `dict` y no una tupla indexada por posición porque las posiciones
    incluyen las paredes: una tupla obligaría a reservar `alto * ancho` lugares
    para consultar sólo las transitables. Con 12 a 41 celdas por nivel la
    diferencia es irrelevante en memoria, pero un `dict` que sólo tiene las
    celdas válidas falla ruidosamente si alguna vez se lo consulta con una
    pared, en vez de devolver un número inventado.

    Es el mínimo por filas de `distancias_manhattan_por_meta`, y se escribe así
    —sobre la otra tabla y no repitiendo la cuenta— para que quede explícito que
    la única diferencia entre h₂ y h₃ es qué se hace con esas mismas 16
    distancias: h₂ toma el mínimo de cada fila por separado y h₃ resuelve la
    asignación. Toda la escalera se apoya en que esa sea la única diferencia.
    """
    return {
        celda: min(distancias)
        for celda, distancias in distancias_manhattan_por_meta(tablero).items()
    }


def distancias_de_empuje(tablero) -> tuple[dict[int, int], ...]:
    """Cuántos EMPUJES cuesta como mínimo llevar una caja de cada celda a cada meta.

    Devuelve una tabla por meta, en el orden de `metas_ordenadas`. Cada tabla
    tiene sólo las celdas desde las que esa meta es alcanzable: una celda ausente
    significa "desde acá no se llega", no "distancia 0".

    CAMINAR Y EMPUJAR NO SON LO MISMO, y ésta es la diferencia. Un BFS de
    adyacencia sobre las celdas de piso da distancia de CAMINO: cuántos pasos hay
    de una celda a otra. Pero para que una caja pase de q a p el tablero exige
    dos cosas, no una: que p esté libre y que el jugador quepa en la celda de
    ATRÁS. Una caja en un rincón lo muestra de un vistazo: se llega caminando y
    no se sale empujando.

    Por eso el BFS es HACIA ATRÁS desde la meta, recorriendo "tirones": si la
    caja está en p, pudo haber llegado empujada desde q, y para eso el jugador
    tenía que estar en la celda siguiente a q en esa misma dirección. Se retrocede
    de p a q sólo si las dos están libres.

    El bucle se lee "hacia adelante" —`q` se busca con `mover[p][d]` y el jugador
    con `mover[q][d]`, la misma dirección dos veces— porque retroceder un empuje
    hecho en la dirección opuesta a `d` es avanzar dos celdas en `d`. Como `d`
    recorre las cuatro direcciones, quedan cubiertos los cuatro empujes posibles,
    y así no hace falta ninguna tabla de direcciones opuestas.

    Se ignoran las demás cajas y si el jugador puede llegar de verdad hasta esa
    celda esquivándolas. Son restricciones que sólo pueden ALARGAR el recorrido
    real, nunca acortarlo, así que ignorarlas mantiene el resultado como cota
    inferior — que es lo único que la admisibilidad necesita. Además es lo que
    permite que esto sea una tabla ESTÁTICA, calculada una vez por nivel: la
    distancia de empuje exacta dependería del estado y habría que recalcularla en
    cada evaluación.
    """
    mover = tablero.mover
    tablas = []
    for meta in metas_ordenadas(tablero):
        distancia = {meta: 0}
        pendientes = deque([meta])
        while pendientes:
            p = pendientes.popleft()
            for d in DIRECCIONES:
                q = mover[p][d]
                if q == -1:
                    continue  # la caja no pudo venir de ahí: es pared o borde
                if mover[q][d] == -1:
                    continue  # el jugador no tendría dónde pararse para empujar
                if q not in distancia:
                    distancia[q] = distancia[p] + 1
                    pendientes.append(q)
        tablas.append(distancia)
    return tuple(tablas)


def celdas_muertas(tablero) -> frozenset[int]:
    """Las celdas desde las que NINGUNA meta es alcanzable a empujones.

    Una caja que llega a una de estas celdas vuelve el nivel irresoluble para
    siempre, porque no hay ninguna secuencia de empujes que la saque de ahí y la
    lleve a una meta. El caso típico es un rincón, pero también entran los
    pasillos contra una pared donde la caja sólo puede moverse en la dirección
    equivocada.

    SALE GRATIS de `distancias_de_empuje`: es exactamente el conjunto de celdas
    transitables que no aparecen en ninguna de las tablas. La heurística y la
    poda de deadlocks estáticos salen del mismo cálculo, que es un lindo hallazgo
    para la presentación.

    NADIE LA USA EN LA FASE 4. Está acá, escrita y verificada, porque es lo que
    necesita el detector de la Fase 5. Podar es la Fase 5.
    """
    tablas = distancias_de_empuje(tablero)
    return frozenset(
        celda for celda in tablero.transitables
        if not any(celda in tabla for tabla in tablas)
    )


def costos_de_empuje_por_celda(tablero) -> dict[int, tuple[int, ...]]:
    """Para cada celda transitable, los empujes hasta CADA meta. La matriz de h₄.

    Misma forma que `distancias_manhattan_por_meta` —una fila por celda, una
    columna por meta, en el orden de `metas_ordenadas`— para que h₃ y h₄ difieran
    únicamente en de dónde sacan la matriz y en nada más. Las entradas
    inalcanzables valen `INALCANZABLE`: ver el comentario de esa constante.
    """
    tablas = distancias_de_empuje(tablero)
    return {
        celda: tuple(tabla.get(celda, INALCANZABLE) for tabla in tablas)
        for celda in tablero.transitables
    }


def distancias_libres(tablero) -> dict[int, dict[int, int]]:
    """Distancia de camino entre TODOS los pares de celdas transitables.

    Es el recorrido del jugador: pasos de una celda a otra sobre el piso,
    ignorando dónde están las cajas. Lo usa el término de h₅.

    Se ignoran las cajas por el mismo motivo que en `distancias_de_empuje`: son
    obstáculos que sólo pueden ALARGAR el recorrido del jugador, nunca acortarlo,
    así que ignorarlas mantiene el número como cota inferior, que es lo único que
    la admisibilidad necesita.

    Se calculan todos los pares y no sólo los que salen de la posición inicial
    porque el jugador cambia de celda en cada movimiento: es la posición del
    JUGADOR la que varía, no un puñado de orígenes fijos. Son entre 12 y 41
    celdas por nivel, o sea entre 12 y 41 BFS diminutos que se corren una vez;
    la alternativa —un BFS por evaluación de la heurística— serían cientos de
    miles.
    """
    mover = tablero.mover
    tablas = {}
    for origen in tablero.transitables:
        distancia = {origen: 0}
        pendientes = deque([origen])
        while pendientes:
            p = pendientes.popleft()
            for d in DIRECCIONES:
                vecino = mover[p][d]
                if vecino != -1 and vecino not in distancia:
                    distancia[vecino] = distancia[p] + 1
                    pendientes.append(vecino)
        tablas[origen] = distancia
    return tablas
