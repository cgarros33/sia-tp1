"""Comprobación empírica de admisibilidad y consistencia de una heurística."""


def verificar_admisibilidad(problema, h, camino_optimo) -> list[str]:
    """h(si) <= L - i en todos los estados de un camino óptimo."""
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

    if camino_optimo and h(camino_optimo[-1]) != 0:
        errores.append(
            f'h(meta) = {h(camino_optimo[-1])} y tiene que ser 0.'
        )
    return errores


def verificar_consistencia(problema, h, camino_optimo) -> list[str]:
    """h(n) - h(n') <= c(n, n') = 1 para todo sucesor n' de los estados del camino."""
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
    """h(s0) / L: qué fracción del costo real captura la heurística en el inicial."""
    largo = len(camino_optimo) - 1
    if largo <= 0:
        return 0.0
    return h(camino_optimo[0]) / largo
