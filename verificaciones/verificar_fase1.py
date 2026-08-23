"""Verificación de la Fase 1 — el modelo del problema."""

import sys
from pathlib import Path

from src.modelo import Estado, NivelInvalido, Problema, Tablero
from src.modelo import leer_archivo, leer_texto
from src.modelo.tablero import ABAJO, ARRIBA, DERECHA, NOMBRE_DIR

RAIZ = Path(__file__).resolve().parent.parent
NIVELES = RAIZ / 'niveles'

ESPERADO = (
    ('n1_micro.sok', 1, 12),
    ('n2_akk04.sok', 4, 32),
    ('n3_caminata.sok', 2, 35),
    ('n4_matching.sok', 4, 31),
    ('n5_limite.sok', 4, 41),
)

SOLUCION_N1 = (DERECHA, DERECHA, ARRIBA, DERECHA, ABAJO, ABAJO, ABAJO, ABAJO)
ESTADOS_N1 = len(SOLUCION_N1) + 1
EMPUJES_N1 = 5


def _verificar_ida_y_vuelta(tablero: Tablero, estado: Estado) -> list[str]:
    """Dibuja el estado inicial, lo vuelve a parsear y compara todo."""
    errores = []
    texto = tablero.dibujar(estado)
    try:
        tablero2, estado2 = leer_texto(texto, nombre=tablero.nombre)
    except NivelInvalido as e:
        return [f'el tablero dibujado no vuelve a parsear: {e}']

    if (tablero2.alto, tablero2.ancho) != (tablero.alto, tablero.ancho):
        errores.append(
            f'las dimensiones cambian al reparsear: '
            f'{tablero.alto}x{tablero.ancho} -> {tablero2.alto}x{tablero2.ancho}'
        )
    if tablero2.paredes != tablero.paredes:
        errores.append('las paredes cambian al reparsear')
    if tablero2.metas != tablero.metas:
        errores.append('las metas cambian al reparsear')
    if estado2 != estado:
        errores.append(f'el estado cambia al reparsear: {estado} -> {estado2}')
    if not errores and tablero2.dibujar(estado2) != texto:
        errores.append('dibujar no es idempotente: el segundo dibujo difiere del primero')
    return errores


def _verificar_sucesores(tablero: Tablero, estado: Estado,
                         problema: Problema) -> tuple[int, list[str]]:
    """Genera los sucesores del estado inicial y controla que sean legales."""
    errores = []
    sucesores = list(problema.sucesores(estado))
    acciones_vistas = set()

    for accion, siguiente, hubo_empuje in sucesores:
        nombre = NOMBRE_DIR[accion]

        if accion in acciones_vistas:
            errores.append(f'la acción {nombre} aparece repetida entre los sucesores')
        acciones_vistas.add(accion)

        destino = tablero.mover[estado.jugador][accion]
        if destino == -1:
            errores.append(f'la acción {nombre} llevaría al jugador a una pared o fuera del tablero')
            continue
        if siguiente.jugador != destino:
            errores.append(
                f'la acción {nombre} deja al jugador en {siguiente.jugador} '
                f'y debería dejarlo en {destino}'
            )
        if siguiente.jugador in tablero.paredes:
            errores.append(f'la acción {nombre} mete al jugador dentro de una pared')
        if siguiente.jugador in siguiente.cajas:
            errores.append(f'la acción {nombre} deja al jugador encima de una caja')
        if len(siguiente.cajas) != len(estado.cajas):
            errores.append(
                f'la acción {nombre} pasa de {len(estado.cajas)} a '
                f'{len(siguiente.cajas)} cajas: se superpusieron o se perdió una'
            )
        cajas_en_pared = siguiente.cajas & tablero.paredes
        if cajas_en_pared:
            errores.append(f'la acción {nombre} deja cajas dentro de paredes: {sorted(cajas_en_pared)}')

        salieron = estado.cajas - siguiente.cajas
        entraron = siguiente.cajas - estado.cajas
        if hubo_empuje:
            if salieron != {destino} or len(entraron) != 1:
                errores.append(
                    f'la acción {nombre} dice que hubo empuje pero movió '
                    f'{sorted(salieron)} -> {sorted(entraron)}'
                )
            else:
                atras = tablero.mover[destino][accion]
                if next(iter(entraron)) != atras:
                    errores.append(
                        f'la acción {nombre} manda la caja a {sorted(entraron)} '
                        f'y en esa dirección debería ir a {atras}'
                    )
        elif salieron or entraron:
            errores.append(f'la acción {nombre} dice que no hubo empuje pero las cajas cambiaron')

    return len(sucesores), errores


def verificar_nivel(archivo: str, cajas_esperadas: int, celdas_esperadas: int) -> bool:
    """Corre las cinco comprobaciones sobre un nivel. Imprime una línea y devuelve si pasó."""
    ruta = NIVELES / archivo
    try:
        tablero, inicial = leer_archivo(ruta)
    except (NivelInvalido, OSError) as e:
        print(f'{archivo:<17} NO SE PUDO LEER: {e}')
        return False

    errores = []
    if len(inicial.cajas) != cajas_esperadas:
        errores.append(f'tiene {len(inicial.cajas)} cajas y la tabla dice {cajas_esperadas}')
    if len(tablero.metas) != cajas_esperadas:
        errores.append(f'tiene {len(tablero.metas)} metas y la tabla dice {cajas_esperadas}')
    if len(tablero.transitables) != celdas_esperadas:
        errores.append(
            f'tiene {len(tablero.transitables)} celdas transitables y la tabla dice {celdas_esperadas}'
        )
    if len(inicial.cajas) != len(tablero.metas):
        errores.append(f'{len(inicial.cajas)} cajas contra {len(tablero.metas)} metas')

    errores_ida_y_vuelta = _verificar_ida_y_vuelta(tablero, inicial)
    errores += errores_ida_y_vuelta

    problema = Problema(tablero, inicial)
    cantidad_sucesores, errores_sucesores = _verificar_sucesores(tablero, inicial, problema)
    errores += errores_sucesores

    ida_y_vuelta = 'OK' if not errores_ida_y_vuelta else 'FALLA'
    plural = 'sucesor válido' if cantidad_sucesores == 1 else 'sucesores válidos'
    print(f'{archivo:<17}{len(inicial.cajas):>2} cajas {len(tablero.metas):>3} metas '
          f'{len(tablero.transitables):>4} celdas   ida y vuelta {ida_y_vuelta}'
          f'   {cantidad_sucesores} {plural}')
    for error in errores:
        print(f'    FALLA: {error}')
    return not errores


def verificar_solucion_n1() -> bool:
    """Ejecuta la solución de N1 y comprueba que llegue a meta con 5 empujes."""
    archivo = 'n1_micro.sok'
    tablero, inicial = leer_archivo(NIVELES / archivo)
    problema = Problema(tablero, inicial)
    camino = ''.join(NOMBRE_DIR[accion] for accion in SOLUCION_N1)

    try:
        estados = problema.reconstruir_estados(SOLUCION_N1)
    except ValueError as e:
        print(f'{archivo:<17} solución {camino}: NO ES EJECUTABLE')
        print(f'    FALLA: {e}')
        return False

    empujes = sum(1 for antes, despues in zip(estados, estados[1:])
                  if antes.cajas != despues.cajas)
    llega_a_meta = problema.es_meta(estados[-1])

    errores = []
    if len(estados) != ESTADOS_N1:
        errores.append(f'genera {len(estados)} estados y deberían ser {ESTADOS_N1}')
    if not llega_a_meta:
        errores.append('la secuencia no termina en meta')
    if empujes != EMPUJES_N1:
        errores.append(f'tiene {empujes} empujes y el récord publicado son {EMPUJES_N1}')

    meta_texto = 'termina en meta' if llega_a_meta else 'NO termina en meta'
    veredicto = 'OK' if not errores else 'FALLA'
    print(f'{archivo:<17} solución {camino}: {len(estados)} estados, '
          f'{meta_texto}, {empujes} empujes   {veredicto}')
    for error in errores:
        print(f'    FALLA: {error}')
    return not errores


def main() -> int:
    print(f'Verificación de la Fase 1 — modelo del problema ({len(ESPERADO)} niveles)\n')
    resultados = [verificar_nivel(*nivel) for nivel in ESPERADO]
    print()
    solucion_ok = verificar_solucion_n1()

    ok = sum(resultados)
    print()
    if ok == len(resultados) and solucion_ok:
        print(f'{ok}/{len(resultados)} niveles OK.')
        return 0
    if ok != len(resultados):
        print(f'{ok}/{len(resultados)} niveles OK. Hay {len(resultados) - ok} con fallas.')
    else:
        print(f'{ok}/{len(resultados)} niveles OK, pero falló la solución de N1.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
