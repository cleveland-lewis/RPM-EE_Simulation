import json
from pathlib import Path

from src.path_utils import index_results, write_results_index_csv


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f)


def test_index_results_collects_run_and_batch_metadata(tmp_path):
    root = tmp_path / "results"
    run_dir = root / "batch_0" / "run0__combo"
    _write_json(
        run_dir / "run_config.json",
        {
            "preset": "test_preset",
            "seed": 123,
            "version": "0.1.0",
            "date": "2025-01-01T00:00:00",
            "config_hash": "abc",
            "batch": 0,
            "run": 0,
            "run_label": "batch_0__20250101",
        },
    )
    _write_json(
        root / "batch_0" / "batch_meta.json",
        {"preset": "test_preset", "seed": 123, "version": "0.1.0", "date": "2025-01-01T00:00:00", "config_hash": "abc", "batch_id": "batch_0", "run_label": "batch_0__20250101"},
    )

    entries = index_results(root)

    assert len(entries) == 1
    entry = entries[0]
    assert entry["preset"] == "test_preset"
    assert entry["seed"] == 123
    assert entry["config_hash"] == "abc"
    assert entry["batch_meta"] is not None
    assert entry.get("missing_fields") in ([], None)


def test_write_results_index_csv_creates_file(tmp_path):
    root = tmp_path / "results"
    run_dir = root / "batch_1" / "run1"
    _write_json(
        run_dir / "run_config.json",
        {
            "preset": "p2",
            "seed": 999,
            "version": "0.2.0",
            "date": "2025-02-02T00:00:00",
            "config_hash": "def",
        },
    )

    csv_path = write_results_index_csv(root)
    assert csv_path.exists()
    content = csv_path.read_text().strip().splitlines()
    assert len(content) == 2  # header + one row
