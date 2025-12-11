# Test Layout

- **Canonical smoke/regression**: `tests/test_canonical.py` (required per AGENTS.md; minimum run).
- **Integration**: `tests/integration/`
  - `test_deep.py`, `test_sensory_contract.py`
  - Legacy config/CLI coverage under `tests/integration/config/` (moved from `config/tests/` + `config/test_simulation.py`)
- **Unit**: `tests/unit/` (reserved for future fine-grained unit cases)

# Quick commands

- Canonical (required): `PYTHONPATH=. pytest tests/test_canonical.py`
- Integration sweep: `PYTHONPATH=. pytest tests/integration`
- Config-focused integration only: `PYTHONPATH=. pytest tests/integration/config`

# Notes

- Canonical tests remain lightweight and deterministic for CI.
- Integration tests cover deep signal checks, sensory contracts, and legacy config/CLI behavior without changing the canonical entry point.
- Hints in canonical failures still point to deeper cases (now under `tests/integration/`).
