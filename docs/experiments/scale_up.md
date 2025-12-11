# Scale-Up Guide (Compute)

This guide summarizes how to push RPM-EE onto higher-power hardware while keeping runs reproducible.

## Baseline prerequisites
- Python 3.11 with the pinned dependencies in `requirements.txt`.
- Optional accelerators: install `jax`/`jaxlib` for GPU/TPU or keep NumPy/Numba CPU paths.
- Ensure the working directory is this repository root (`PYTHONPATH=.` when running commands).

## Controls to tune
- **Process workers**: `--workers` on `config/batch_runner.py` and `--workers/--cores` on `src/nc_mcm_model.py` choose the process count. Default is `os.cpu_count()`.
- **Thread caps**: set `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1` to prevent BLAS oversubscription when using many processes.
- **Output root**: set `RPMEE_OUTPUT_ROOT=/abs/path` to write results to a fast volume (e.g., NVMe on a compute node).
- **Accelerators**: install `jax`/`jaxlib` and, if desired, set `JAX_PLATFORM_NAME=gpu` to force GPU execution; otherwise the code automatically prefers JAX for very large `total_ticks`.

## Multi-core batch runs (continuous mode)
Example for an 8-core workstation pushing parallel runs while keeping artifacts tidy:

```bash
PYTHONPATH=. \\
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \\
python config/batch_runner.py \\
  --preset default \\
  --runs 8 \\
  --batches 1 \\
  --workers 8 \\
  --total-ticks 5000 \\
  --summary-name scale_up_demo \\
  --output results
```

Notes:
- Adjust `--total-ticks`, `--runs`, and `--workers` based on core/RAM availability.
- Use `--dry-run` first to confirm the configuration without executing.
- Artifact paths land under `results/<run_label>/batch_<id>/run*/` with metadata stamped by `path_utils`.

## NC-MCM sampling on larger machines
For NC-MCM fitting with multiple chains/cores:

```bash
PYTHONPATH=. \\
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \\
python -m src.nc_mcm_model \\
  --runs 4 \\
  --workers 4 \\
  --draws 1000 \\
  --tune 1000 \\
  --chains 4 \\
  --cores 4 \\
  --seed 123
```

- Use `--fast` during iterations (600/600 draws/tune, fewer chains/cores) before scaling up.
- Keep thread caps in place to avoid BLAS thrashing when PyMC uses multiple cores.

## Quick smoke on a multi-core node
Use this tiny run to verify the configuration and metadata stamping without heavy compute:

```bash
PYTHONPATH=. \\
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \\
python config/batch_runner.py \\
  --preset default \\
  --runs 1 \\
  --batches 1 \\
  --workers 2 \\
  --total-ticks 10 \\
  --summary-name scale_up_smoke \\
  --output results/scale_up_smoke
```

Outputs land under `results/scale_up_smoke_<timestamp>/` and can be deleted after verification.
