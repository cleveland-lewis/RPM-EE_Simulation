#!/usr/bin/env python3
"""
test_graphs.py

Back-end verification that the numerical data used by front-end Chart.js
histograms are present and well-formed.

We don’t render charts here—that’s done in the browser—but we replicate
the binning logic in Python to ensure the data arrays yield valid
histograms (no NaNs, counts sum correctly, etc.).
"""

import numpy as np
from src.simulation import run_simulation

def get_histogram_counts(arr, bins=20):
    """Replicate the JS binning logic with numpy.histogram."""
    hist, _ = np.histogram(arr, bins=bins)
    return hist

def test_histogram_data_integrity():
    # Run a quick simulation (vectorised) to get log data
    logs = run_simulation(total_ticks=500, bin_size=1)

    # Pull arrays that the front-end histograms use
    att = np.array([e["attunement_score"] for e in logs])
    stress = np.array([e["schema_stress"] for e in logs])
    st = np.array([e["memory_stats"]["short_term_size"] for e in logs])
    lt = np.array([e["memory_stats"]["long_term_size"] for e in logs])

    for name, arr in [
        ("attunement", att),
        ("stress", stress),
        ("short_term_size", st),
        ("long_term_size", lt),
    ]:
        # Basic sanity checks
        assert arr.dtype.kind in "fi", f"{name} array is not numeric"
        assert len(arr) == len(logs), f"{name} length mismatch"

        # Build histogram
        counts = get_histogram_counts(arr, bins=20)

        # Counts should sum to the number of entries
        assert counts.sum() == len(arr), f"{name} histogram count mismatch"

        # No negative bins, and at least one bin non-zero
        assert (counts >= 0).all(), f"{name} histogram contains negatives"
        assert counts.max() > 0, f"{name} histogram all zeros"