"""Verificación de la Fase 6 — Runner, configuración y CSV."""

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from runner.runner import COLUMNAS_CSV, ejecutar_matriz

NUMEROS_DE_ORO = {
    "n1_micro": {"costo": 8, "empujes": 5},
    "n2_akk04": {"costo": 45, "empujes": 18},
    "n3_caminata": {"costo": 104, "empujes": 22},
    "n4_matching": {"costo": 70, "empujes": 22},
    "n5_limite": {"costo": 306, "empujes": 99},
}

HEURISTICAS_ADMISIBLES = ("h0", "h1", "h2", "h3", "h4", "h5", "h6")


def verificar_csv_valido() -> list[str]:
    """1. El runner produce un CSV válido con config reducida."""
    print("1. Comprobando generación de CSV válido (config reducida)...")
    errores = []

    config_test = {
        "runs": 1,
        "separador_decimal": ".",
        "encoding": "utf-8",
        "intervalo_progreso_s": 999,
        "matriz": [
            {
                "metodo": "bfs",
                "niveles": ["n1_micro"],
                "deadlocks": ["completo"],
            },
            {
                "metodo": "dfs",
                "niveles": ["n1_micro"],
                "deadlocks": ["completo"],
                "todas_las_direcciones": True,
            },
            {
                "metodo": "iddfs",
                "niveles": ["n1_micro"],
                "deadlocks": ["completo"],
            },
            {
                "metodo": "greedy",
                "heuristicas": ["h2"],
                "niveles": ["n1_micro"],
                "deadlocks": ["completo"],
            },
            {
                "metodo": "astar",
                "heuristicas": ["h2"],
                "niveles": ["n1_micro"],
                "deadlocks": ["completo"],
            },
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_path = tmp_path / "config_test.json"
        csv_path = tmp_path / "salida_test.csv"

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_test, f)

        filas_totales, _ = ejecutar_matriz(config_path, csv_path)

        if not csv_path.exists():
            return ["El archivo CSV no fue creado por el runner."]

        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)

            if header != COLUMNAS_CSV:
                errores.append(
                    f"Encabezado del CSV incorrecto.\n  Esperado: {COLUMNAS_CSV}\n  Obtenido: {header}"
                )

            filas = list(reader)
            if len(filas) != filas_totales:
                errores.append(
                    f"Se esperaban {filas_totales} filas en el CSV y se leyeron {len(filas)}."
                )

            for i, row in enumerate(filas, 1):
                if len(row) != len(COLUMNAS_CSV):
                    errores.append(
                        f"Fila {i} tiene {len(row)} columnas (se esperaban {len(COLUMNAS_CSV)})."
                    )

    if not errores:
        print("   CSV válido: 17 columnas, formato y filas OK.")
    return errores


def verificar_costos_y_dfs() -> list[str]:
    """2, 3 y 4. Costos óptimos, 24 permutaciones DFS e IDDFS max_nodos."""
    print("\n2. Comprobando exactitud de costos y comportamientos esperados...")
    errores = []

    config_verif = {
        "runs": 1,
        "separador_decimal": ".",
        "encoding": "utf-8",
        "intervalo_progreso_s": 999,
        "matriz": [
            {
                "metodo": "bfs",
                "niveles": ["n1_micro", "n2_akk04", "n3_caminata"],
                "deadlocks": ["completo"],
            },
            {
                "metodo": "dfs",
                "niveles": ["n1_micro", "n2_akk04"],
                "deadlocks": ["completo"],
                "todas_las_direcciones": True,
            },
            {
                "metodo": "iddfs",
                "niveles": ["n1_micro", "n2_akk04", "n3_caminata", "n4_matching", "n5_limite"],
                "deadlocks": ["completo"],
            },
            {
                "metodo": "astar",
                "heuristicas": list(HEURISTICAS_ADMISIBLES),
                "niveles": ["n1_micro", "n2_akk04", "n3_caminata"],
                "deadlocks": ["completo"],
            },
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_path = tmp_path / "config_verif.json"
        csv_path = tmp_path / "salida_verif.csv"

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_verif, f)

        ejecutar_matriz(config_path, csv_path)

        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            filas = list(reader)

    filas_optimas = [
        r
        for r in filas
        if r["exito"] == "True"
        and (
            r["metodo"] in ("BFS", "IDDFS")
            or (r["metodo"] == "A*" and r["heuristica"] in HEURISTICAS_ADMISIBLES)
        )
    ]

    costos_ok = 0
    for r in filas_optimas:
        niv = r["nivel"]
        costo = int(r["costo"])
        empujes = int(r["empujes"])
        esperado_c = NUMEROS_DE_ORO[niv]["costo"]
        esperado_e = NUMEROS_DE_ORO[niv]["empujes"]

        if costo != esperado_c or empujes != esperado_e:
            errores.append(
                f"Método óptimo {r['metodo']} ({r['heuristica']}) en {niv} dio costo/empujes {costo}/{empujes}, esperado {esperado_c}/{esperado_e}."
            )
        else:
            costos_ok += 1

    print(f"   Métodos óptimos: {costos_ok}/{len(filas_optimas)} corridas validadas contra números de oro.")

    dfs_n1 = [r for r in filas if r["metodo"] == "DFS" and r["nivel"] == "n1_micro"]
    dfs_n2 = [r for r in filas if r["metodo"] == "DFS" and r["nivel"] == "n2_akk04"]

    if len(dfs_n1) != 24 or len(set(r["orden_sucesores"] for r in dfs_n1)) != 24:
        errores.append(f"DFS en n1_micro no produjo 24 permutaciones únicas (obtenidas: {len(dfs_n1)}).")
    else:
        print("   DFS en n1_micro: 24 permutaciones distintas generadas  OK")

    if len(dfs_n2) != 24 or len(set(r["orden_sucesores"] for r in dfs_n2)) != 24:
        errores.append(f"DFS en n2_akk04 no produjo 24 permutaciones únicas (obtenidas: {len(dfs_n2)}).")
    else:
        costos_dfs_n2 = set(int(r["costo"]) for r in dfs_n2 if r["exito"] == "True")
        print(f"   DFS en n2_akk04: 24 permutaciones distintas, {len(costos_dfs_n2)} costos distintos  OK")

    iddfs_n4 = [r for r in filas if r["metodo"] == "IDDFS" and r["nivel"] == "n4_matching"]
    iddfs_n5 = [r for r in filas if r["metodo"] == "IDDFS" and r["nivel"] == "n5_limite"]

    if not iddfs_n4 or iddfs_n4[0]["motivo_fin"] != "max_nodos" or iddfs_n4[0]["exito"] != "False":
        errores.append("IDDFS en n4_matching debía finalizar por 'max_nodos' con exito=False.")
    else:
        print("   IDDFS en n4_matching: motivo_fin='max_nodos'  OK")

    if not iddfs_n5 or iddfs_n5[0]["motivo_fin"] != "max_nodos" or iddfs_n5[0]["exito"] != "False":
        errores.append("IDDFS en n5_limite debía finalizar por 'max_nodos' con exito=False.")
    else:
        print("   IDDFS en n5_limite: motivo_fin='max_nodos'  OK")

    return errores


def verificar_pytest() -> list[str]:
    """5. Verifica que la suite de pytest sigue pasando."""
    print("\n3. Ejecutando la suite de regresión pytest...")
    res = subprocess.run([sys.executable, "-m", "pytest", "-q", "-m", "not lento"], capture_output=True, text=True)
    if res.returncode != 0:
        return [f"pytest falló con código {res.returncode}:\n{res.stdout}\n{res.stderr}"]
    print("   pytest (-m 'not lento'): suite en verde  OK")
    return []


def main() -> int:
    print("Verificación de la Fase 6 — Runner, configuración y CSV\n")

    errores = []
    errores.extend(verificar_csv_valido())
    errores.extend(verificar_costos_y_dfs())
    errores.extend(verificar_pytest())

    print("\n==========================================")
    if not errores:
        print("VERIFICACIÓN COMPLETA — TODOS LOS CHECKS EN VERDE")
        return 0
    else:
        print(f"SE ENCONTRARON {len(errores)} ERRORES:")
        for e in errores:
            print(f" - {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
