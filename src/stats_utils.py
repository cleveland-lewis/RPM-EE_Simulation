from pathlib import Path
import numpy as np
import json

def summarize_array(x):
    """
    Compute descriptive statistics for an array of values.

    Args:
        x: Array-like of numeric values

    Returns:
        Dictionary containing n, mean, std, min, max, and percentiles
    """
    x = np.array(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {"n": 0}
    percentiles = np.percentile(x, [1, 5, 25, 50, 75, 95, 99])
    return {
        "n": int(len(x)),
        "mean": float(np.mean(x)),
        "std": float(np.std(x)),
        "min": float(np.min(x)),
        "max": float(np.max(x)),
        "percentiles": {
            "p1": float(percentiles[0]),
            "p5": float(percentiles[1]),
            "p25": float(percentiles[2]),
            "p50": float(percentiles[3]),
            "p75": float(percentiles[4]),
            "p95": float(percentiles[5]),
            "p99": float(percentiles[6]),
        },
    }

def write_batch_summary(batch_dir, **data_series):
    """
    Save summaries (mean, std, percentiles) for any arrays you pass in.

    Args:
        batch_dir: Directory path where summary will be saved
        **data_series: Named arrays of data to summarize

    Returns:
        Path to the created summary file
    """
    batch_dir = Path(batch_dir)
    batch_dir.mkdir(parents=True, exist_ok=True)
    summary = {name: summarize_array(values) for name, values in data_series.items()}
    out_path = batch_dir / "distribution_summary.json"
    out_path.write_text(json.dumps(summary, indent=2))
    return out_path
