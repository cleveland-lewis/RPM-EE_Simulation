# RPM-EE R analysis workflow

Companion R-based analysis track for RPM-EE simulation results (GitHub issue
[#24](https://github.com/cleveland-lewis/RPM-EE_Simulation/issues/24),
"Option A"). This is a clean separation from the core Python simulation: the
Python side runs simulations and exports a stable CSV/JSON schema; the R
side only ever reads that export. Neither side calls into the other's
runtime.

```text
Python simulation (src/simulation.py)
        |
        v
src/analysis/export_results_for_r.py   -- CSV/JSON export
        |
        v
scripts/analysis_r.R                   -- summary stats + plots (PNG/CSV)
docs/analysis_r_report.Rmd             -- same analysis, rendered to HTML/PDF
```

## Data format

The exporter (`src/analysis/export_results_for_r.py`) accepts:

- `{"logs": [ {...}, {...} ]}` -- the shape of `RPMEESimulation.logs` after
  wrapping in a dict with a `logs` key (the common case: one dict per
  simulated episode/step)
- `[ {...}, {...} ]` -- a bare list of dict rows
- `{ ... }` -- a single dict row, wrapped into a one-row list

The header of the output CSV is derived from the first row's keys, so all
rows must share the same schema. Fields produced by `RPMEESimulation.step()`
that the R workflow (`scripts/analysis_r.R`, `docs/analysis_r_report.Rmd`)
consumes:

| field | meaning |
|---|---|
| `preset` | clinical preset name (`neurotypical`, `adhd_typical`, `asd_typical`, `mdd_typical`) |
| `rt_mean` | mean DDM reaction time (ms) across that episode's simulations |
| `rt_std` | RT standard deviation for that episode |
| `accuracy` | mean accuracy for that episode, in `[0, 1]`; `NA`/`null` for episodes with only neutral-evidence simulations (no correct answer defined -- see `src/ddm.py`'s `predict_action` docstring) |

Other logged fields (`clock`, `state`, `replay_mode`, `schema_stress`,
`vigilance`, `precision_ratio`, `volatility`, ...) pass through the export
unchanged and are available for further R analysis, but aren't used by the
default script/report.

## Step 1: Export results from Python

Run simulations and collect each preset's `.logs` (a list of dicts), then
export:

```python
import sys, json
sys.path.insert(0, "src")
from simulation import RPMEESimulation

all_logs = []
for preset in ["neurotypical", "adhd_typical", "asd_typical", "mdd_typical"]:
    sim = RPMEESimulation(preset=preset)
    sim.run(episodes=200)
    all_logs.extend(sim.logs)

with open("/tmp/rpm_ee_run.json", "w") as f:
    json.dump({"logs": all_logs}, f, indent=2)
```

Then export to the stable CSV/JSON schema:

```bash
python -m analysis.export_results_for_r \
  --input /tmp/rpm_ee_run.json \
  --output_csv results/export/rpm_ee_results.csv \
  --output_json results/export/rpm_ee_results.json
```

(Run from `src/`, or with `src/` on `PYTHONPATH` -- e.g.
`PYTHONPATH=src python -m analysis.export_results_for_r ...`.)

## Step 2: Analyze in R

Requires `tidyverse` (`readr`, `dplyr`, `ggplot2`, `tidyr`):

```bash
Rscript -e 'install.packages(c("tidyverse"))'   # one-time setup
Rscript scripts/analysis_r.R results/export/rpm_ee_results.csv results/r_analysis
```

This writes to `results/r_analysis/`:

- `summary_by_preset.csv` -- n, mean/SD of `rt_mean` and `accuracy` per preset
- `rt_distribution_by_preset.png` -- overlaid RT histograms by preset
- `accuracy_distribution_by_preset.png` -- accuracy boxplots by preset
- `effect_sizes_vs_neurotypical.csv` and `effect_size_calibration.png` --
  Cohen's d for `rt_mean`/`accuracy` of each non-baseline preset relative to
  `neurotypical`, as a quick check of whether clinical differentiation is in
  the expected direction/magnitude (compare against
  `scripts/predictive_validation.py`'s `EXPECTED_PATTERNS`)

## Step 3: Render the report

```bash
Rscript -e 'rmarkdown::render("docs/analysis_r_report.Rmd", params = list(data_path = "results/export/rpm_ee_results.csv"))'
```

Renders `docs/analysis_r_report.html` (add `output_format = "pdf_document"`
for PDF, which additionally requires a LaTeX distribution such as `tinytex`:
`Rscript -e 'tinytex::install_tinytex()'`).

## Developer notes

- **Schema stability**: the exporter derives CSV headers from the first
  row's keys and assumes uniform rows (`export_results_for_r`'s docstring in
  `src/analysis/export_results_for_r.py`). If `RPMEESimulation.step()`'s
  logged fields change, both `scripts/analysis_r.R` and
  `docs/analysis_r_report.Rmd` only reference `preset`, `rt_mean`, and
  `accuracy` by name, so additive changes (new fields) are backward
  compatible; renaming/removing those three fields requires updating both R
  files.
- **Extending the analysis**: add new summaries/plots directly in
  `scripts/analysis_r.R` (for the scripted path) and mirror them as a chunk
  in `docs/analysis_r_report.Rmd` (for the rendered-report path) -- keep the
  two in sync since they're meant to produce the same analysis via two
  entry points (batch script vs. narrative report).
- **Non-goals**: this workflow is intentionally one-way (Python produces
  data, R only consumes it) and does not import Python packages into R or
  vice versa. A future cross-language bridge (`reticulate`/`rpy2`) is
  tracked separately -- see the "Optional (future) bridge" follow-up issue,
  not implemented here.
