# Results Directory Schema

This project stores simulation outputs under `results/` (configurable via `RPMEE_OUTPUT_ROOT`). Each run/batch records metadata to keep runs reproducible and discoverable.

## Layout

```
results/
  <run_label>/                    # Top-level run or batch label (timestamped by default)
    run_meta.json                 # Run-level metadata (preset/seed/version/date) when present
    batch_meta.json               # Batch metadata (grid spec, seeds, version, date, config hash)
    batch_<id> or batch_*/        # Per-batch folders (for sweeps)
      batch_meta.json             # Same as above if nested
      run<idx>__<combo>/          # Per-run folders within a batch
        run_config.json           # Run-level metadata (preset/seed/version/date/config_hash/batch/run)
        summary.json / summary.csv# One-row summaries for the run
        trials.json               # Optional trial-level logs (when saving trials)
        plots/...                 # Optional quick plots
```

- `run_label` defaults to a UTC timestamped name; override with `--output`/`--label` or `RPMEE_OUTPUT_ROOT`.
- `batch_meta.json` and `run_config.json` always include: `preset`, `seed`, `version`, `date`, and `config_hash`.
- Both also include optional `provenance` (git commit, python/platform, and package versions) for reproducibility.
- `run_meta.json` is used by non-batch entry points to capture the same fields.

## Indexing outputs

Use the new index helper to summarize stored runs:

```bash
PYTHONPATH=. python - <<'PY'
from src.path_utils import write_results_index_csv
print(write_results_index_csv("results"))
PY
```

This writes `results/index.csv` with one row per `run_config.json`, including paths, preset/seed/version/date, config hashes, and any missing required fields.
