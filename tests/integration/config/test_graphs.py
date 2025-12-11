import json

import numpy as np

from src.simulation import run_simulation


def _logs(total_ticks: int = 500):
    result = run_simulation(total_ticks=total_ticks, bin_size=1)
    if isinstance(result, dict):
        return result.get("logs", [])
    return result


def test_histogram_data_integrity():
    """Ensure attunement and stress series produce sane histogram data."""
    logs = _logs(500)
    att = np.array([e["attunement_score"] for e in logs], dtype=float)
    stress = np.array([e["schema_stress"] for e in logs], dtype=float)

    for name, arr in [("attunement", att), ("stress", stress)]:
        assert arr.dtype.kind == "f", f"{name} array is not float"
        assert len(arr) == len(logs), f"{name} length mismatch"
        counts, _ = np.histogram(arr, bins=20)
        assert counts.sum() == len(arr), f"{name} histogram count mismatch"
        assert (counts >= 0).all(), f"{name} histogram contains negatives"
        assert counts.max() > 0, f"{name} histogram all zeros"


def test_chartjs_data_format():
    """Verify we can build a Chart.js-compatible JSON payload from attunement histogram."""
    logs = _logs(500)
    arr = np.array([e["attunement_score"] for e in logs], dtype=float)
    counts, bin_edges = np.histogram(arr, bins=20)
    labels = [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" for i in range(len(counts))]

    chart_data = {
        "labels": labels,
        "datasets": [
            {"label": "Attunement Score Distribution", "data": counts.tolist()},
        ],
    }

    json_str = json.dumps(chart_data)
    assert isinstance(json_str, str)
    assert len(chart_data["labels"]) == len(counts), "Label count mismatch"
    assert all(isinstance(lbl, str) for lbl in chart_data["labels"]), "Labels must be strings"
    assert all(isinstance(v, int) for v in chart_data["datasets"][0]["data"]), "Data values must be integers"
