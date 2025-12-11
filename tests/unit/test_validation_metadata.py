import json
from pathlib import Path

from src.path_utils import hash_file


def test_hash_file_returns_sha256(tmp_path):
    file_path = tmp_path / "data.csv"
    file_path.write_text("hello")
    assert hash_file(file_path) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


def test_validation_meta_includes_hashes(tmp_path, monkeypatch):
    # Prepare small CSVs
    out_dir = tmp_path / "validation_output" / "test_run"
    out_dir.mkdir(parents=True)
    model_path = out_dir / "model_outputs.csv"
    empirical_path = out_dir / "empirical_data.csv"
    model_path.write_text("x,y\n1,2\n")
    empirical_path.write_text("a,b\n3,4\n")

    metadata = {
        "preset": "default",
        "seed": 1,
        "run_label": "test_run",
        "version": "0.0.0",
        "model_outputs_hash": hash_file(model_path),
        "empirical_data_hash": hash_file(empirical_path),
    }

    meta_path = out_dir / "validation_meta.json"
    with open(meta_path, "w") as fmeta:
        json.dump(metadata, fmeta)

    loaded = json.loads(meta_path.read_text())
    assert loaded["model_outputs_hash"] == metadata["model_outputs_hash"]
    assert loaded["empirical_data_hash"] == metadata["empirical_data_hash"]
    assert loaded["run_label"] == "test_run"
