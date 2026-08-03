# SPDX-License-Identifier: MIT
"""Export RPM-EE results to CSV/JSON for R analysis.

This module provides a small, dependency-light utility to export the
runtime results of RPM-EE simulations (episodes, presets, RT, accuracy, etc.)
into CSV/JSON formats consumable by an R-based analysis/visualization
workflow (see docs/analysis_r.md, scripts/analysis_r.R).

Usage (programmatic):
    from analysis.export_results_for_r import export_results_for_r
    export_results_for_r(results, "results/export/rpm_ee_results.csv",
                          "results/export/rpm_ee_results.json")

Usage (CLI):
    python -m analysis.export_results_for_r --input results.json \
        --output_csv results.csv --output_json results.json
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, cast


def _normalize_results(data: Any) -> list[dict[str, Any]]:
    """Normalize different shapes into a list of dict rows.

    Supported shapes:
    - {"logs": [ ... ]}
    - [ { ... }, ... ]
    - { ... } a single dict row will be wrapped into a list
    """
    if isinstance(data, dict) and isinstance(data.get("logs"), list):
        return cast("list[dict[str, Any]]", data["logs"])
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    msg = "Unsupported results format for export: expected dict/list of dicts"
    raise ValueError(msg)


def _make_safe(value: Any) -> Any:
    """Convert numpy scalar types (or similar) to native Python types."""
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            return value
    return value


def export_results_for_r(results: Any, csv_path: str, json_path: str | None = None) -> None:
    """Export results (as list of dicts) to CSV and optionally JSON.

    Args:
    ----
        results: Iterable of dict-like rows or a dict containing a
            "logs" list.
        csv_path: Path to write the CSV file.
        json_path: Optional path to write a JSON file.

    """
    rows = _normalize_results(results)
    csv_out = Path(csv_path)
    csv_out.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        csv_out.write_text("")
        if json_path:
            Path(json_path).write_text(json.dumps([], indent=2))
        return

    first = rows[0]
    if not isinstance(first, dict):
        msg = "Each result row must be a dict of fields"
        raise TypeError(msg)
    headers = list(first.keys())

    with csv_out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            if not isinstance(row, dict):
                msg = "Each result row must be a dict of fields"
                raise TypeError(msg)
            writer.writerow({k: _make_safe(v) for k, v in row.items()})

    if json_path:
        Path(json_path).write_text(json.dumps(rows, indent=2))


def _load_input_path(path: str) -> Any:
    with Path(path).open() as f:
        return json.load(f)


def main_cli() -> None:
    """Parse CLI args and export the given input JSON to CSV/JSON."""
    parser = argparse.ArgumentParser(
        prog="export_results_for_r",
        description="Export RPM-EE results for R analysis",
    )
    parser.add_argument(
        "--input", required=True, help="Path to a JSON results file (the RPM-EE run output)."
    )
    parser.add_argument(
        "--output_csv", required=True, help="Path to write the CSV output for R input."
    )
    parser.add_argument(
        "--output_json",
        default=None,
        help="Optional path to write the JSON output (for R testing).",
    )
    args = parser.parse_args()

    data = _load_input_path(args.input)
    export_results_for_r(data, args.output_csv, args.output_json)


if __name__ == "__main__":
    main_cli()
