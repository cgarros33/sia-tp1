"""Tests para el runner de la Fase 6."""

import csv
import json
import tempfile
from pathlib import Path

import pytest

from runner.runner import COLUMNAS_CSV, ejecutar_matriz
from tests.conftest import ESPERADO


def _crear_y_ejecutar(config_dict: dict, tmp_path: Path) -> list[dict]:
    """Escribe una config temporal, corre el runner y devuelve las filas del CSV."""
    cfg_file = tmp_path / "cfg.json"
    csv_file = tmp_path / "out.csv"
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(config_dict, f)
    ejecutar_matriz(cfg_file, csv_file)
    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def test_csv_valido(tmp_path):
    """Verifica que el runner genere un CSV con las 17 columnas y valores válidos."""
    config = {
        "runs": 1,
        "matriz": [
            {
                "metodo": "bfs",
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
    filas = _crear_y_ejecutar(config, tmp_path)
    assert len(filas) == 2
    for r in filas:
        assert set(r.keys()) == set(COLUMNAS_CSV)
        assert r["exito"] == "True"
        assert int(r["costo"]) == ESPERADO["n1_micro"]["costo"]
        assert int(r["empujes"]) == ESPERADO["n1_micro"]["empujes"]


@pytest.mark.parametrize("nivel", ["n1_micro", "n2_akk04", "n3_caminata"])
def test_costos_optimos_light(nivel, tmp_path):
    """Verifica que BFS y A*(h6) encuentren el costo publicado en N1-N3."""
    config = {
        "runs": 1,
        "matriz": [
            {"metodo": "bfs", "niveles": [nivel], "deadlocks": ["completo"]},
            {"metodo": "astar", "heuristicas": ["h6"], "niveles": [nivel], "deadlocks": ["completo"]},
        ],
    }
    filas = _crear_y_ejecutar(config, tmp_path)
    assert len(filas) == 2
    for r in filas:
        assert r["exito"] == "True"
        assert int(r["costo"]) == ESPERADO[nivel]["costo"]
        assert int(r["empujes"]) == ESPERADO[nivel]["empujes"]


def test_dfs_24_ordenes_light(tmp_path):
    """Verifica que DFS con todas_las_direcciones genere las 24 permutaciones en N1."""
    config = {
        "matriz": [
            {
                "metodo": "dfs",
                "niveles": ["n1_micro"],
                "deadlocks": ["completo"],
                "todas_las_direcciones": True,
            }
        ]
    }
    filas = _crear_y_ejecutar(config, tmp_path)
    assert len(filas) == 24
    ordenes = set(r["orden_sucesores"] for r in filas)
    assert len(ordenes) == 24
    assert all(r["exito"] == "True" for r in filas)


@pytest.mark.lento
@pytest.mark.parametrize("nivel", ["n4_matching", "n5_limite"])
def test_costos_optimos_medium(nivel, tmp_path):
    """Verifica que A*(h6) encuentre el costo óptimo publicado en N4 y N5."""
    config = {
        "runs": 1,
        "matriz": [
            {"metodo": "astar", "heuristicas": ["h6"], "niveles": [nivel], "deadlocks": ["completo"]}
        ],
    }
    filas = _crear_y_ejecutar(config, tmp_path)
    assert len(filas) == 1
    r = filas[0]
    assert r["exito"] == "True"
    assert int(r["costo"]) == ESPERADO[nivel]["costo"]
    assert int(r["empujes"]) == ESPERADO[nivel]["empujes"]


@pytest.mark.lento
@pytest.mark.parametrize("nivel", ["n4_matching", "n5_limite"])
def test_iddfs_max_nodos(nivel, tmp_path):
    """Verifica que IDDFS agote los nodos (max_nodos) en N4 y N5."""
    config = {
        "runs": 1,
        "matriz": [
            {"metodo": "iddfs", "niveles": [nivel], "deadlocks": ["completo"]}
        ],
    }
    filas = _crear_y_ejecutar(config, tmp_path)
    assert len(filas) == 1
    r = filas[0]
    assert r["exito"] == "False"
    assert r["motivo_fin"] == "max_nodos"


@pytest.mark.lento
@pytest.mark.parametrize("nivel", ["n4_matching", "n5_limite"])
def test_dfs_24_ordenes_medium(nivel, tmp_path):
    """Verifica las 24 permutaciones de DFS en N4 y N5."""
    config = {
        "matriz": [
            {
                "metodo": "dfs",
                "niveles": [nivel],
                "deadlocks": ["completo"],
                "todas_las_direcciones": True,
            }
        ]
    }
    filas = _crear_y_ejecutar(config, tmp_path)
    assert len(filas) == 24
    ordenes = set(r["orden_sucesores"] for r in filas)
    assert len(ordenes) == 24


@pytest.mark.lento
@pytest.mark.completo
@pytest.mark.parametrize("nivel", ["n4_matching", "n5_limite"])
def test_costos_bfs_completo(nivel, tmp_path):
    """Verifica BFS sin poda en N4 y N5 (operación pesada)."""
    config = {
        "runs": 1,
        "matriz": [
            {"metodo": "bfs", "niveles": [nivel], "deadlocks": ["ninguno"]}
        ],
    }
    filas = _crear_y_ejecutar(config, tmp_path)
    assert len(filas) == 1
    r = filas[0]
    assert r["exito"] == "True"
    assert int(r["costo"]) == ESPERADO[nivel]["costo"]
