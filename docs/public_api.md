# RPM-EE Public API Surface

Use only the entry points below to depend on RPM-EE. Everything else in `src/` or `config/` is internal and may change without notice.

## Installation & environment
- Install pinned deps: `python -m pip install -r requirements.txt` (Python 3.11 recommended).
- Optional accelerators: uncomment `jax`/`jaxlib` in `requirements.txt` for GPU/TPU execution; falls back to NumPy/Numba CPU paths otherwise.
- Avoid BLAS oversubscription on multi-core runs: export `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1`.
- Set `PYTHONPATH=.` when running CLI/examples from the repo root.

## Core simulation
- Import from the package root: `from src import run_simulation, parameter_sweep, fit_nc_mcm`.
- `run_simulation(**kwargs)` returns logs/stats/diagnostics for a single run.
- `parameter_sweep(param_grid, base_kwargs)` performs coarse sensitivity sweeps.
- `fit_nc_mcm(data, config)` drives the NC-MCM fitting pipeline.

## Presets
- `from src import PRESETS, get_preset_params, list_presets`.
- `PRESETS['default']` and clinical variants are the calibrated parameter dictionaries.
- `get_preset_params(name)` returns a copy safe for mutation; `list_presets()` lists available keys.
- To run with presets: `run_simulation(**get_preset_params('default'), seed=123)`.

## Trial wrappers
- `from src import TrialSimulator, DualTaskSimulator, quick_trial`.
- `TrialSimulator` converts tick-based runs into trial-level summaries; `DualTaskSimulator` extends it for dual-task paradigms.
- `quick_trial(preset='default', duration=200, seed=0)` runs a single trial and returns a summary dict.

## Validation metrics
- Import metrics directly: `from src import compute_all_endpoints` (preferred) or specific functions such as `compute_convergent_validity`, `compute_action_execution_auc`, `compute_icc`, `compute_lagged_omission_prediction`, `generate_calibration_plot`.
- `compute_all_endpoints(model_outputs_df, empirical_df, config)` runs the preregistered battery; other helpers remain available for targeted analyses.

## Batch/CLI runner
- Programmatic entry: `from config.batch_runner import main` (CLI interface) and invoke with an `argparse.Namespace` as produced by the CLI parser.
- Typical CLI usage: `python config/batch_runner.py --preset default --runs 5 --total_ticks 500`.
- Only `main` is stable; all other functions in `config/batch_runner.py` are internal support utilities.

## Stable surface definition
- Modules now declare `__all__` to mark supported imports; anything not listed is internal.
- Prefer importing from `src` (or `config.batch_runner` for the CLI) rather than reaching into submodules.
- If additional surfaces are needed, add them to `__all__` first and document them here.
