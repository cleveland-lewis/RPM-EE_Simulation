# RPM-EE

RPM-EE is a cognitive simulation and validation framework for running multi-agent
experiments, generating behavioral/physiological metrics, and comparing model
outputs to empirical data.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m config.batch_runner --preset default --runs 1 --ticks 1000 --seed 123
```

Results are written under `results/` with run metadata (including seeds and
provenance). See `docs/getting_started.md` for more examples.

## Reproducibility and Standards

- Deterministic seeds are supported across CLI and API flows.
- Each run records metadata including version, seeds, config hash, and a
  provenance block (git commit, python/platform, dependency versions).
- Validation metrics implement preregistered hypotheses documented in
  `docs/literature/validation_protocol.md`.
- Data/metadata structures align with current neuroscience data standards and
  open-science practices (see `docs/standards_alignment.md`).

## Data Export (BIDS/NWB)

Use `src/exporters.py` to generate BIDS/NWB scaffold exports for downstream
conversion workflows.
