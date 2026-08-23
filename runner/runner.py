"""Ejecutor automatizado de la matriz de experimentos de Sokoban (Fase 6)."""

import argparse
import json
import sys
import time
from itertools import permutations
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from main import cargar_config
from src.busqueda import METODOS, METODOS_INFORMADOS, resolver
from src.deadlocks import DETECTORES, construir as construir_detector
from src.heuristicas import HEURISTICAS, construir as construir_heuristica
from src.modelo import Problema, leer_archivo
from src.modelo.tablero import DIRECCIONES, NOMBRE_DIR

CAMPOS_CONFIG_GLOBAL = {
    "runs",
    "separador_decimal",
    "encoding",
    "intervalo_progreso_s",
    "matriz",
}

CAMPOS_CONFIG_MATRIZ = {
    "metodo",
    "niveles",
    "heuristicas",
    "deadlocks",
    "runs",
    "todas_las_direcciones",
}

COLUMNAS_CSV = [
    "nivel",
    "metodo",
    "heuristica",
    "deadlocks",
    "corrida",
    "orden_sucesores",
    "exito",
    "motivo_fin",
    "costo",
    "empujes",
    "nodos_expandidos",
    "nodos_generados",
    "frontera_maxima",
    "frontera_final",
    "estados_visitados",
    "memoria_maxima",
    "tiempo_s",
]


def cargar_config_runner(ruta_config: Path) -> dict:
    """Carga y valida el archivo de configuración del runner."""
    if not ruta_config.exists():
        raise FileNotFoundError(f"No existe el archivo de configuración: {ruta_config}")

    with open(ruta_config, "r", encoding="utf-8") as f:
        config = json.load(f)

    config_limpia = {k: v for k, v in config.items() if not k.startswith("_")}

    claves_desconocidas = set(config_limpia.keys()) - CAMPOS_CONFIG_GLOBAL
    if claves_desconocidas:
        raise ValueError(
            f"Claves desconocidas en el archivo de configuración global: {sorted(claves_desconocidas)}"
        )

    runs_global = config_limpia.get("runs", 5)
    separador_decimal = config_limpia.get("separador_decimal", ".")
    encoding = config_limpia.get("encoding", "utf-8")
    intervalo_progreso_s = config_limpia.get("intervalo_progreso_s", 15)

    if separador_decimal not in (".", ","):
        raise ValueError(
            f"separador_decimal inválido: {separador_decimal!r}. Debe ser '.' o ','"
        )

    matriz = config_limpia.get("matriz", [])
    if not isinstance(matriz, list) or not matriz:
        raise ValueError("El campo 'matriz' debe ser una lista no vacía de experimentos.")

    for i, bloque in enumerate(matriz):
        claves_bloque = set(bloque.keys()) - CAMPOS_CONFIG_MATRIZ
        if claves_bloque:
            raise ValueError(
                f"Claves desconocidas en el bloque {i} de la matriz: {sorted(claves_bloque)}"
            )

        metodo = bloque.get("metodo")
        if not metodo or metodo not in METODOS:
            raise ValueError(
                f"Bloque {i}: método inválido {metodo!r}. Opciones: {sorted(METODOS)}"
            )

        niveles = bloque.get("niveles", [])
        if not niveles or not isinstance(niveles, list):
            raise ValueError(f"Bloque {i}: 'niveles' debe ser una lista no vacía.")
        for niv in niveles:
            ruta_sok = RAIZ / "niveles" / f"{niv}.sok"
            if not ruta_sok.exists():
                raise FileNotFoundError(f"Bloque {i}: Nivel no encontrado: {ruta_sok}")

        deadlocks = bloque.get("deadlocks", ["completo"])
        for d in deadlocks:
            if d not in DETECTORES:
                raise ValueError(
                    f"Bloque {i}: Detector de deadlocks desconocido {d!r}. Opciones: {sorted(DETECTORES)}"
                )

        heuristicas = bloque.get("heuristicas", [])
        for h in heuristicas:
            if h not in HEURISTICAS:
                raise ValueError(
                    f"Bloque {i}: Heurística desconocida {h!r}. Opciones: {sorted(HEURISTICAS)}"
                )

        if metodo in METODOS_INFORMADOS and not heuristicas:
            raise ValueError(
                f"Bloque {i}: El método informado {metodo!r} requiere al menos una heurística."
            )

        if metodo not in METODOS_INFORMADOS and heuristicas:
            print(
                f"Warning: Bloque {i}: El método {metodo!r} no utiliza heurísticas; se ignorará el campo 'heuristicas'.",
                file=sys.stderr,
            )

        todas_las_dir = bloque.get("todas_las_direcciones", False)
        if todas_las_dir and metodo != "dfs":
            print(
                f"Warning: Bloque {i}: 'todas_las_direcciones' sólo aplica a DFS; se ignorará para {metodo!r}.",
                file=sys.stderr,
            )

    return {
        "runs": runs_global,
        "separador_decimal": separador_decimal,
        "encoding": encoding,
        "intervalo_progreso_s": intervalo_progreso_s,
        "matriz": matriz,
    }


def generar_tuplas_ejecucion(config: dict) -> list[tuple]:
    """Genera todas las tuplas individuales de corrida a partir de la matriz de configuración."""
    runs_global = config["runs"]
    tuplas = []
    vistas = set()

    for bloque in config["matriz"]:
        metodo = bloque["metodo"]
        niveles = bloque["niveles"]
        deadlocks = bloque.get("deadlocks", ["completo"])
        todas_las_dir = bloque.get("todas_las_direcciones", False) and metodo == "dfs"
        runs = bloque.get("runs", runs_global)

        if todas_las_dir:
            perms = list(permutations(DIRECCIONES))
            for niv in niveles:
                for d_capa in deadlocks:
                    for perm in perms:
                        codigo_orden = "".join(NOMBRE_DIR[d] for d in perm)
                        tupla = (niv, metodo, None, d_capa, 1, perm, codigo_orden)
                        identificador = (niv, metodo, None, d_capa, 1, codigo_orden)
                        if identificador in vistas:
                            print(
                                f"Warning: Tupla duplicada encontrada: {identificador}",
                                file=sys.stderr,
                            )
                        vistas.add(identificador)
                        tuplas.append(tupla)
        else:
            heuristicas = (
                bloque.get("heuristicas", []) if metodo in METODOS_INFORMADOS else [None]
            )
            for niv in niveles:
                for h_nombre in heuristicas:
                    for d_capa in deadlocks:
                        for run_i in range(1, runs + 1):
                            tupla = (niv, metodo, h_nombre, d_capa, run_i, None, "—")
                            identificador = (niv, metodo, h_nombre, d_capa, run_i, "—")
                            if identificador in vistas:
                                print(
                                    f"Warning: Tupla duplicada encontrada: {identificador}",
                                    file=sys.stderr,
                                )
                            vistas.add(identificador)
                            tuplas.append(tupla)

    return tuplas


def formatear_tiempo(segundos: float) -> str:
    """Formatea segundos en una cadena legible M m S s o S s."""
    total_sec = int(segundos)
    mins, secs = divmod(total_sec, 60)
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


def ejecutar_matriz(
    ruta_config_runner: Path, ruta_salida_csv: Path
) -> tuple[int, float]:
    """Ejecuta toda la matriz de experimentos y escribe inmediatamente el CSV."""
    config_runner = cargar_config_runner(ruta_config_runner)
    config_proyecto = cargar_config(RAIZ / "config.json")

    max_nodos = config_proyecto.get("max_nodos")
    timeout_s = config_proyecto.get("timeout_s")

    tuplas = generar_tuplas_ejecucion(config_runner)
    total_corridas = len(tuplas)

    separador_decimal = config_runner["separador_decimal"]
    encoding = config_runner["encoding"]
    intervalo_progreso = config_runner["intervalo_progreso_s"]

    ruta_salida_csv.parent.mkdir(parents=True, exist_ok=True)

    inicio_global = time.perf_counter()
    ultimo_reporte = inicio_global

    ancho_num = len(str(total_corridas))

    with open(ruta_salida_csv, "w", encoding=encoding, newline="") as f_csv:
        f_csv.write(",".join(COLUMNAS_CSV) + "\n")
        f_csv.flush()

        for idx, (niv, metodo, h_nombre, d_capa, corrida_i, perm, codigo_orden) in enumerate(
            tuplas, 1
        ):
            ahora = time.perf_counter()
            if (ahora - ultimo_reporte >= intervalo_progreso) or (idx == 1):
                transcurrido = formatear_tiempo(ahora - inicio_global)
                h_repr = f"({h_nombre})" if h_nombre else ""
                print(
                    f"[{idx:>{ancho_num}}/{total_corridas}]  ejecutando: {niv} · {metodo}{h_repr} · {d_capa} · corrida {corrida_i}    ({transcurrido})",
                    file=sys.stderr,
                )
                ultimo_reporte = ahora

            tablero, inicial = leer_archivo(RAIZ / "niveles" / f"{niv}.sok")
            detector = construir_detector(d_capa, tablero)
            problema = Problema(
                tablero,
                inicial,
                detector_deadlocks=detector,
                orden_direcciones=perm,
            )

            h_func = construir_heuristica(h_nombre, problema) if h_nombre else None

            resultado = resolver(
                problema,
                metodo,
                heuristica=h_func,
                nombre_heuristica=h_nombre or "",
                max_nodos=max_nodos,
                timeout_s=timeout_s,
                nivel=niv,
            )

            costo_str = (
                str(resultado.costo)
                if resultado.exito and resultado.costo is not None
                else ""
            )
            empujes_str = (
                str(resultado.empujes)
                if resultado.exito and resultado.empujes is not None
                else ""
            )
            h_csv = h_nombre if h_nombre else "—"
            tiempo_str = f"{resultado.tiempo_s:.3f}".replace(".", separador_decimal)

            fila = [
                niv,
                resultado.metodo,
                h_csv,
                d_capa,
                str(corrida_i),
                codigo_orden,
                str(resultado.exito),
                resultado.motivo_fin,
                costo_str,
                empujes_str,
                str(resultado.nodos_expandidos),
                str(resultado.nodos_generados),
                str(resultado.frontera_maxima),
                str(resultado.frontera_final),
                str(resultado.estados_visitados),
                str(resultado.memoria_maxima),
                tiempo_str,
            ]

            f_csv.write(",".join(fila) + "\n")
            f_csv.flush()

    tiempo_total = time.perf_counter() - inicio_global
    tiempo_fmt = formatear_tiempo(tiempo_total)
    print(
        f"{total_corridas}/{total_corridas} corridas completadas en {tiempo_fmt}. Salida: {ruta_salida_csv} ({total_corridas} filas).",
        file=sys.stderr,
    )

    return total_corridas, tiempo_total


def main():
    parser = argparse.ArgumentParser(
        description="Runner de experimentos para Sokoban (Fase 6)."
    )
    parser.add_argument(
        "config",
        nargs="?",
        default="runner/config_runner.json",
        help="Ruta al JSON de configuración del runner.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="resultados.csv",
        help="Ruta al archivo CSV de salida.",
    )

    args = parser.parse_args()

    ruta_config = Path(args.config)
    ruta_salida = Path(args.output)

    try:
        ejecutar_matriz(ruta_config, ruta_salida)
    except Exception as e:
        print(f"Error al ejecutar el runner: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
