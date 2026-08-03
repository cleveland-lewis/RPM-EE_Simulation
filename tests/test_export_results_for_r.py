"""
Unit tests for the Python->R results exporter (src/analysis/export_results_for_r.py).

Covers GitHub issue #24 (R analysis workflow) / #25 (exporter): the exported
CSV/JSON must be a stable, round-trippable schema for scripts/analysis_r.R
and docs/analysis_r_report.Rmd to read.
"""

import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analysis.export_results_for_r import export_results_for_r  # noqa: E402


def _read_csv_rows(path: Path) -> list:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


class TestExportResultsForR:
    def test_exports_logs_shaped_input(self, tmp_path):
        results = {
            "logs": [
                {"preset": "neurotypical", "rt_mean": 450.0, "accuracy": 0.9},
                {"preset": "adhd_typical", "rt_mean": 620.0, "accuracy": 0.7},
            ]
        }
        csv_path = tmp_path / "out.csv"
        json_path = tmp_path / "out.json"

        export_results_for_r(results, str(csv_path), str(json_path))

        rows = _read_csv_rows(csv_path)
        assert len(rows) == 2
        assert rows[0]["preset"] == "neurotypical"
        assert rows[0]["rt_mean"] == "450.0"

        with json_path.open() as f:
            data = json.load(f)
        assert data == results["logs"]

    def test_exports_bare_list_input(self, tmp_path):
        results = [{"preset": "neurotypical", "rt_mean": 450.0, "accuracy": 0.9}]
        csv_path = tmp_path / "out.csv"

        export_results_for_r(results, str(csv_path))

        rows = _read_csv_rows(csv_path)
        assert len(rows) == 1
        assert rows[0]["preset"] == "neurotypical"

    def test_exports_single_dict_row(self, tmp_path):
        results = {"preset": "neurotypical", "rt_mean": 450.0, "accuracy": 0.9}
        csv_path = tmp_path / "out.csv"

        export_results_for_r(results, str(csv_path))

        rows = _read_csv_rows(csv_path)
        assert len(rows) == 1
        assert rows[0]["preset"] == "neurotypical"

    def test_empty_logs_writes_empty_csv_and_json(self, tmp_path):
        csv_path = tmp_path / "out.csv"
        json_path = tmp_path / "out.json"

        export_results_for_r({"logs": []}, str(csv_path), str(json_path))

        assert csv_path.read_text() == ""
        with json_path.open() as f:
            assert json.load(f) == []

    def test_unsupported_shape_raises(self, tmp_path):
        with pytest.raises(ValueError):
            export_results_for_r("not a dict or list", str(tmp_path / "out.csv"))

    def test_creates_output_directory(self, tmp_path):
        nested_csv = tmp_path / "nested" / "dir" / "out.csv"
        export_results_for_r([{"a": 1}], str(nested_csv))
        assert nested_csv.exists()
