# Standards Alignment

This repository is aligned with current neuroscience research standards and
open-science practices through the following concrete mechanisms.

## Reproducibility and Provenance (FAIR-aligned)
- Deterministic seeding across CLI and API flows.
- Run metadata includes `version`, `config_hash`, and `provenance` (git commit,
  python/platform, package versions, requirements hash).
- Validation metrics are versioned via `METRICS_SCHEMA_VERSION`.

## Data Standards (BIDS/NWB-Compatible)
- Outputs are stored with structured metadata under `results/` to enable
  downstream export to BIDS- or NWB-compatible formats.
- Adapters in `src/adapters.py` provide normalization and schema validation for
  empirical datasets before comparisons.
- Export scaffolds are provided in `src/exporters.py` to map runs into BIDS/NWB
  conversion workflows.

## Validation and Reporting
- Preregistered hypotheses and validation protocols live in
  `docs/literature/validation_protocol.md`.
- `src/validation_metrics.py` enforces schema checks and computes metrics with
  reproducible settings.

## Packaging and Tooling
- `requirements.txt` provides a deterministic dependency manifest.
- Tests cover simulation, configuration, and validation paths under `tests/`.

## Next Optional Enhancements
- Add explicit BIDS/NWB export utilities.
- Add CI automation for tests + style checks.
- Provide a `CITATION.cff` and LICENSE once publication/author details are set.
