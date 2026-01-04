"""Provenance helpers for reproducible runs."""

from __future__ import annotations

import hashlib
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional

try:
    from importlib import metadata as importlib_metadata
except ImportError:  # pragma: no cover - Python <3.8 fallback
    import importlib_metadata  # type: ignore


def _hash_file(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit(root: Path) -> Optional[str]:
    env_commit = os.environ.get("RPMEE_GIT_COMMIT")
    if env_commit:
        return env_commit
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def _pkg_version(name: str) -> Optional[str]:
    try:
        return importlib_metadata.version(name)
    except Exception:
        return None


def _find_project_root(start: Path) -> Path:
    for candidate in [start] + list(start.parents):
        if (candidate / "requirements.txt").exists():
            return candidate
    return start


def collect_provenance(project_root: str | Path | None = None) -> dict:
    """Return a compact, JSON-serializable provenance record."""
    root = Path(project_root) if project_root else Path.cwd()
    root = _find_project_root(root)
    req_hash = _hash_file(root / "requirements.txt")
    pkg_versions = {
        "numpy": _pkg_version("numpy"),
        "scipy": _pkg_version("scipy"),
        "pandas": _pkg_version("pandas"),
        "pydantic": _pkg_version("pydantic"),
        "fastapi": _pkg_version("fastapi"),
    }
    return {
        "git_commit": _git_commit(root),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "requirements_hash": req_hash,
        "package_versions": {k: v for k, v in pkg_versions.items() if v},
    }


__all__ = ["collect_provenance"]
