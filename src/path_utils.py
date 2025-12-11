"""
Path and output directory helpers shared across CLI and API entry points.

These utilities normalize user-provided output directories (including env
overrides), ensure directories exist, and stamp small metadata sidecars.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Tuple, List, Dict, Optional
import json
import hashlib

DEFAULT_OUTPUT_ROOT = "results"
RUN_META_FILE = "run_meta.json"
_REQUIRED_INDEX_FIELDS = ("preset", "seed", "version", "date", "config_hash")


def ensure_dir(path: str | Path) -> Path:
    """Return an absolute Path with the directory created."""
    p = Path(path).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def resolve_output_root(base_dir: str | Path | None = None, run_label: str | None = None) -> Tuple[Path, str]:
    """
    Resolve the root directory for a run, honoring env override RPMEE_OUTPUT_ROOT.
    A timestamp is appended to the run_label to avoid collisions.
    """
    base = base_dir or os.environ.get("RPMEE_OUTPUT_ROOT") or DEFAULT_OUTPUT_ROOT
    root = ensure_dir(base)
    label = run_label or "run"
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    full_label = f"{label}_{ts}"
    run_root = ensure_dir(root / full_label)
    return run_root, full_label


def write_metadata(path: str | Path, payload: Mapping[str, Any]) -> Path:
    """Write JSON metadata to the given path, ensuring parent exists."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(payload, f, indent=2)
    return p


def stamp_run_metadata(run_root: Path, *, preset: str | None, mode: str, runs: int, batches: int, workers: int, base_seed: int | None, run_label: str, version: str) -> Path:
    """Create a small run-level metadata file with versioning for traceability."""
    payload = {
        "preset": preset,
        "mode": mode,
        "runs": runs,
        "batches": batches,
        "workers": workers,
        "base_seed": base_seed,
        "version": version,
        "date": datetime.utcnow().isoformat(),
        "run_label": run_label,
    }
    return write_metadata(run_root / RUN_META_FILE, payload)


def _load_json_if_exists(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return None


def index_results(root: str | Path = DEFAULT_OUTPUT_ROOT) -> List[Dict[str, Any]]:
    """
    Scan a results directory for batch/run metadata and return a summary list.

    Each entry corresponds to a `run_config.json` with optional batch metadata
    alongside it. Missing required fields are reported in `missing_fields`.
    """
    root_path = Path(root).expanduser().resolve()
    entries: List[Dict[str, Any]] = []
    if not root_path.exists():
        return entries

    for run_cfg_path in sorted(root_path.rglob("run_config.json")):
        run_dir = run_cfg_path.parent
        run_cfg = _load_json_if_exists(run_cfg_path) or {}

        # Locate nearest batch_meta.json above the run directory (if present)
        batch_meta_path: Optional[Path] = None
        for ancestor in [run_dir] + list(run_dir.parents):
            if root_path not in ancestor.parents and ancestor != root_path:
                continue
            candidate = ancestor / "batch_meta.json"
            if candidate.exists():
                batch_meta_path = candidate
                break

        batch_meta = _load_json_if_exists(batch_meta_path) if batch_meta_path else {}

        entry = {
            "run_dir": str(run_dir),
            "run_config": str(run_cfg_path),
            "batch_meta": str(batch_meta_path) if batch_meta_path else None,
            "batch_id": run_cfg.get("batch") or batch_meta.get("batch_id"),
            "run": run_cfg.get("run"),
            "preset": run_cfg.get("preset") or batch_meta.get("preset"),
            "seed": run_cfg.get("seed"),
            "version": run_cfg.get("version") or batch_meta.get("version"),
            "date": run_cfg.get("date") or batch_meta.get("date"),
            "config_hash": run_cfg.get("config_hash"),
            "batch_config_hash": batch_meta.get("config_hash"),
            "run_label": run_cfg.get("run_label") or batch_meta.get("run_label") or run_dir.parent.name,
        }
        missing = [k for k in _REQUIRED_INDEX_FIELDS if not entry.get(k)]
        if missing:
            entry["missing_fields"] = missing
        entries.append(entry)

    return entries


def write_results_index_csv(root: str | Path = DEFAULT_OUTPUT_ROOT, dest: str | Path | None = None) -> Path:
    """
    Write a CSV index of all run_config.json files under the results root.

    Returns the path to the written CSV.
    """
    rows = index_results(root)
    if dest is None:
        dest_path = Path(root).expanduser().resolve() / "index.csv"
    else:
        dest_path = Path(dest).expanduser().resolve()
        dest_path.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "run_dir",
        "run_config",
        "batch_meta",
        "run_label",
        "batch_id",
        "run",
        "preset",
        "seed",
        "version",
        "date",
        "config_hash",
        "batch_config_hash",
        "missing_fields",
    ]

    with open(dest_path, "w") as f:
        f.write(",".join(headers) + "\n")
        for row in rows:
            def _fmt(val: Any) -> str:
                if val is None:
                    return ""
                if isinstance(val, list):
                    return ";".join(str(v) for v in val)
                return str(val)

            f.write(",".join(_fmt(row.get(h, "")) for h in headers) + "\n")

    return dest_path


def hash_file(path: str | Path) -> str:
    """Return the SHA256 hex digest of a file (empty string if missing)."""
    p = Path(path)
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
