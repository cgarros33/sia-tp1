"""Comprobación empírica de admisibilidad y consistencia de una heurística.

POR QUÉ EXISTE Y POR QUÉ ES REUTILIZABLE
    La Fase 4 tiene seis heurísticas y cada una necesita su demostración de
    admisibilidad. La demostración se escribe a mano —son dos renglones y van a
    la presentación—, pero una demostración que nadie contrastó contra el código
    es una demostración de la heurística que creímos escribir. Estas dos
    funciones contrastan la que escribimos de verdad.

LA IDEA, QUE ES LO QUE HAY QUE PODER EXPLICAR
    Verificar admisibilidad en general es caro: h(n) <= h*(n) exige conocer el
    costo óptimo restante DESDE CADA ESTADO, o sea resolver el nivel una vez por
    estado. Pero sobre un camino óptimo s0, s1, ..., sL ese costo se conoce
    gratis: si el camino completo es óptimo, entonces el tramo que va de si a sL
    también lo es, y por lo tanto

        h*(si) = L - i     exactamente.

    (Si existiera un camino más corto de si a la meta, pegándolo al tramo s0..si
    daría una solución de menos de L movimientos, y L era el óptimo.)

    Entonces alcanza con comprobar h(si) <= L - i en cada uno de los L+1 estados
    del camino. Son L+1 estados verificados por el precio de una búsqueda.

QUÉ NO ES
    No es una demostración. Es una condición NECESARIA: si falla, la heurística
    no es admisible, seguro. Si pasa, sólo sabemos que no falla en los estados
    del camino óptimo. La demostración sigue siendo el argumento escrito. Esto
    es la red que atrapa el error de implementación —un signo cambiado, un
    factor de más— que el argumento no puede atrapar porque el argumento habla
    de la heurística ideal, no del código.
"""


def verificar_admisibilidad(problema, h, camino_optimo) -> list[str]:
    """h(si) <= L - i en todos los estados de un camino óptimo.

    `camino_optimo` es la lista completa de estados s0..sL, tal como la devuelve
    `problema.reconstruir_estados(acciones)` sobre una solución óptima.

    Devuelve la lista de violaciones encontradas: vacía significa que pasó.
    """
    errores = []
    largo = len(camino_optimo) - 1

    for i, estado in enumerate(camino_optimo):
        restante = largo - i
        valor = h(estado)
        if valor > restante:
            errores.append(
                f'estado {i} del camino óptimo: h = {valor} pero el costo real '
                f'restante es {restante}. Sobreestima: NO es admisible.'
            )
        if valor < 0:
            errores.append(
                f'estado {i} del camino óptimo: h = {valor} es negativo. Una '
                f'heurística es una estimación de costo y el costo no es negativo.'
            )

    # En la meta el costo restante es 0, así que una heurística admisible y no
    # negativa vale forzosamente 0 ahí. Se comprueba aparte porque un h(meta)
    # distinto de 0 es el error más común y el más fácil de leer en la salida.
    if camino_optimo and h(camino_optimo[-1]) != 0:
        errores.append(
            f'h(meta) = {h(camino_optimo[-1])} y tiene que ser 0.'
        )
    return errores


def verificar_consistencia(problema, h, camino_optimo) -> list[str]:
    """h(n) - h(n') <= c(n, n') = 1 para todo sucesor n' de los estados del camino.

    Con costo unitario, la desigualdad triangular se reduce a que h no puede
    bajar más de 1 en un solo movimiento. Es una condición más fuerte que la
    admisibilidad: si se cumple en todo el espacio, A* nunca necesita reabrir un
    estado, porque el primer camino con el que lo alcanza ya es el óptimo.

    Igual que la de admisibilidad, se comprueba sobre los estados del camino
    óptimo y sus sucesores directos, no sobre todo el espacio.

    Devuelve la lista de violaciones: vacía significa que pasó.
    """
    errores = []
    for i, estado in enumerate(camino_optimo):
        valor = h(estado)
        for accion, siguiente, _ in problema.sucesores(estado):
            valor_siguiente = h(siguiente)
            if valor - valor_siguiente > 1:
                errores.append(
                    f'estado {i} del camino óptimo: h baja de {valor} a '
                    f'{valor_siguiente} en un solo movimiento (acción {accion}). '
                    f'NO es consistente.'
                )
    return errores


def verificar_heuristica(problema, h, camino_optimo) -> tuple[list[str], list[str]]:
    """Corre las dos comprobaciones. Es lo que va a llamar la Fase 4, una por heurística."""
    return (verificar_admisibilidad(problema, h, camino_optimo),
            verificar_consistencia(problema, h, camino_optimo))


def informatividad(h, camino_optimo) -> float:
    """h(s0) / L: qué fracción del costo real captura la heurística en el inicial.

    No es una comprobación, es información. 0 es h0, que no informa nada; 1 sería
    la heurística perfecta. Es lo que ordena la escalera de la Fase 4 y el eje
    horizontal del gráfico de dominancia empírica de la Fase 8.

    Deliberadamente NO se usa el margen mínimo sobre todo el camino, que sería la
    medida intuitiva: en la meta toda heurística admisible vale 0 y el costo
    restante es 0, así que ese mínimo da 0 siempre y no distingue nada.
    """
    largo = len(camino_optimo) - 1
    if largo <= 0:
        return 0.0
    return h(camino_optimo[0]) / largo
