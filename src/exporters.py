"""Export utilities for interoperability with neuroscience data standards."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def _ensure_dir(path: str | Path) -> Path:
    p = Path(path).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def export_to_bids(*, run_dir: str | Path, out_dir: str | Path) -> Path:
    """
    Create a minimal BIDS-aligned export scaffold for a run.

    This does not attempt full neuroimaging BIDS compliance; it emits a structured
    sidecar with pointers to RPM-EE run artifacts for downstream tooling.
    """
    run_path = Path(run_dir).expanduser().resolve()
    out_path = _ensure_dir(out_dir)
    payload = {
        "bids_version": "1.9.0",
        "source_run_dir": str(run_path),
        "files": {
            "run_config": str(run_path / "run_config.json"),
            "summary": str(run_path / "summary.json"),
            "diagnostics": str(run_path / "diagnostics.json"),
        },
        "notes": "Scaffold export; map to full BIDS structure as needed.",
    }
    export_path = out_path / "bids_export.json"
    with open(export_path, "w") as f:
        json.dump(payload, f, indent=2)
    return export_path


def export_to_nwb(*, run_dir: str | Path, out_dir: str | Path) -> Path:
    """
    Create a minimal NWB-aligned export scaffold for a run.

    This does not write a full NWB file; it records structured pointers for
    downstream conversion to NWB using pynwb when/if desired.
    """
    run_path = Path(run_dir).expanduser().resolve()
    out_path = _ensure_dir(out_dir)
    payload = {
        "nwb_version": "2.x",
        "source_run_dir": str(run_path),
        "files": {
            "run_config": str(run_path / "run_config.json"),
            "summary": str(run_path / "summary.json"),
            "diagnostics": str(run_path / "diagnostics.json"),
        },
        "notes": "Scaffold export; convert to NWB with pynwb if needed.",
    }
    export_path = out_path / "nwb_export.json"
    with open(export_path, "w") as f:
        json.dump(payload, f, indent=2)
    return export_path


def build_export_manifest(*, run_dir: str | Path) -> Mapping[str, Any]:
    """Return a simple manifest of common run artifacts for exporters."""
    run_path = Path(run_dir).expanduser().resolve()
    return {
        "run_dir": str(run_path),
        "run_config": str(run_path / "run_config.json"),
        "summary": str(run_path / "summary.json"),
        "diagnostics": str(run_path / "diagnostics.json"),
    }


__all__ = ["export_to_bids", "export_to_nwb", "build_export_manifest"]
