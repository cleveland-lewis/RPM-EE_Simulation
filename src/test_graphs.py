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
import json
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

def test_chartjs_data_format():
    """
    Verify that histogram data can be formatted into a Chart.js-compatible
    JSON structure with labels and datasets.
    """
    # Run simulation to get log data
    logs = run_simulation(total_ticks=500, bin_size=1)

    # Extract a sample array (e.g., attunement scores)
    arr = np.array([e["attunement_score"] for e in logs])

    # Generate histogram and bin edges
    counts, bin_edges = np.histogram(arr, bins=20)

    # Build Chart.js-compatible data
    labels = [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" for i in range(len(counts))]
    chart_data = {
        "labels": labels,
        "datasets": [
            {"label": "Attunement Score Distribution", "data": counts.tolist()}
        ]
    }

    # Ensure JSON serialization works
    json_str = json.dumps(chart_data)
    assert isinstance(json_str, str), "Chart data is not JSON serializable"

    # Validate structure
    assert len(chart_data["labels"]) == len(counts), "Label count mismatch"
    assert all(isinstance(lbl, str) for lbl in chart_data["labels"]), "Labels must be strings"
    assert all(isinstance(val, int) for val in chart_data["datasets"][0]["data"]), "Data values must be integers"

def test_chartjs_low_data_point():
    """
    Edge case: a single data point. Ensure histogram bins still sum correctly.
    """
    logs = run_simulation(total_ticks=1, bin_size=1)
    arr = np.array([e["attunement_score"] for e in logs])
    counts, bin_edges = np.histogram(arr, bins=20)
    labels = [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" for i in range(len(counts))]
    chart_data = {
        "labels": labels,
        "datasets": [
            {"label": "Low Data Point", "data": counts.tolist()}
        ]
    }

    # Sum of counts should equal the single entry
    assert sum(chart_data["datasets"][0]["data"]) == 1, "Histogram sum should be 1 for single data point"
    # Labels and data lengths must match
    assert len(chart_data["labels"]) == len(counts), "Label count should match bin count"

def test_chartjs_custom_bins():
    """
    Custom bin count edge case: use non-default bin size.
    """
    logs = run_simulation(total_ticks=23, bin_size=1)
    arr = np.array([e["attunement_score"] for e in logs])
    # Use 5 bins
    counts, bin_edges = np.histogram(arr, bins=5)
    labels = [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" for i in range(len(counts))]
    chart_data = {
        "labels": labels,
        "datasets": [
            {"label": "Custom Bin Count", "data": counts.tolist()}
        ]
    }

    # Ensure correct number of bins
    assert len(chart_data["labels"]) == 5, "Should have 5 labels for 5 bins"
    # Total counts equals number of data points
    assert sum(chart_data["datasets"][0]["data"]) == len(arr), "Histogram sum mismatch for custom bins"