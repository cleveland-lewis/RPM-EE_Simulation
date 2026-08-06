# SimulationClusterArbiter Design

**Module:** `src/arbiter.py`
**Tests:** `tests/test_arbiter.py`

## Purpose

`SimulationClusterArbiter` ranks the candidate simulations produced earlier
in the pipeline (`src/rpm.py`, `src/encoder.py`, `src/fatigue.py`) by
computing a single `final_score` per simulation, then sorting by that score.
Downstream code (`SelfModel.evaluate_simulations`, `src/simulation.py`'s
`step()`) treats the top-ranked simulation as the one the system "believes"
or acts on for that tick.

## Components

Each simulation dict carries three raw signals that `score_simulations`
combines into `final_score`:

- **`plausibility`** (t1, ~[0.5, 1.0]) — physical/perceptual realism of the
  simulated event (`rpm.py`)
- **`emotional_prediction`** (t2, [-1, 1]) — predicted emotional valence of
  the outcome (see `td_learning.py`)
- **`reward_distortion`** (t3, unbounded above 0) — how much the simulation
  over-predicts reward relative to plausibility

```text
final_score = alpha * t1 + beta * t2 + gamma * t3
```

These three signals are **not on a common scale** by default (see
`ARBITER_WEIGHT_PRESETS` note below and `normalize_inputs`) — that's a
known property of the upstream signals, not a bug, but it means weight
tuning should account for it.

## Weighting strategy: `alpha` / `beta` / `gamma` and presets

`alpha`, `beta`, `gamma` are constructor arguments (defaults `0.5`, `0.3`,
`0.2` — the arbiter's original hard-coded weights). Rather than pass raw
numbers, prefer `SimulationClusterArbiter.configure_from_preset(name)`,
which builds an arbiter from a named, documented weight combination in
`ARBITER_WEIGHT_PRESETS`:

- **`neutral`** (`0.5 / 0.3 / 0.2`) — the default. Plausibility leads;
  matches the arbiter's original behavior.
- **`emotion_biased`** (`0.3 / 0.5 / 0.2`) — weights `emotional_prediction`
  most heavily. Use for validation scenarios emphasizing affective realism
  over physical plausibility (e.g. MDD/ASD presets where emotional response
  is the primary clinical signal under test).
- **`distortion_averse`** (`0.3 / 0.2 / 0.5`) — weights `reward_distortion`
  most heavily. Use when the priority is detecting/penalizing cognitive
  distortion, e.g. validating ADHD/MDD presets' distortion-suppression
  behavior against the literature in `docs/EVIDENCE_TABLE.md`.

All three presets sum to `1.0` so scores stay comparable across presets.
`configure_from_preset` also accepts any other constructor kwarg (including
`alpha`/`beta`/`gamma` overrides) to layer on top of a preset:

```python
arbiter = SimulationClusterArbiter.configure_from_preset(
    "distortion_averse", normalize_inputs=True, verbose=True
)
```

Calling `SimulationClusterArbiter()` directly with no arguments is
unaffected by any of this — it's identical to `configure_from_preset
("neutral")` and preserves the arbiter's original behavior for existing
callers.

## Fatigue suppression rule

Once a simulation has been fatigue-flagged (`fatigue_flag=True`, set
upstream by `src/fatigue.py` after repeated replay/failure),
`reward_distortion` is zeroed out **only if it's still above
`fatigue_distortion_suppress_threshold`** (default `0.5`, the midpoint of
`reward_distortion`'s nominal `[0, 1]` scale — see the constructor docstring
in `src/arbiter.py`). Below the threshold, a fatigued simulation's
distortion is treated as no longer meaningfully distorted and left alone;
above it, the distortion signal is judged stuck/unreliable and suppressed
so it can't dominate `final_score`. The threshold is a constructor
argument, so it can be recalibrated per validation scenario without a code
change.

## Input normalization (`normalize_inputs`)

Because `plausibility`, `emotional_prediction`, and `reward_distortion`
aren't on a common scale upstream, `normalize_inputs=True` (default
`False`, preserving existing behavior) makes `score_simulations` min-max
scale each component to `[0, 1]` across the batch passed in before
weighting. An all-equal batch maps to a neutral `0.5` rather than dividing
by zero. The fatigue-suppression threshold check runs on the (possibly
normalized) `t3`, so its `[0, 1]`-midpoint rationale holds either way.

## Required-key validation (`validate_keys`)

Missing `plausibility`/`emotional_prediction`/`reward_distortion` silently
default to `0.0`, which can mask an upstream pipeline problem behind a
plausible-looking score. `validate_keys=True` (default `False`) checks
every simulation in the batch before scoring and either warns (naming the
missing keys and the sim's index, `on_missing_keys="warn"`, the default) or
raises `ValueError` (`on_missing_keys="raise"`). `fatigue_flag` is
intentionally exempt — its absence is a legitimate "not fatigued" state,
not a data-quality problem.

## Debug logging (`verbose`)

`verbose=True` (default `False`, no extra cost when off) attaches an
`arbiter_score_debug` dict to each sim: `t1`/`t2`/`t3` as actually used in
the weighted sum (post-normalization and post-suppression, whichever
applied), whether fatigue suppression fired, and `final_score`. This key is
deliberately named `arbiter_score_debug`, not `arbiter_debug`, to avoid
colliding with `SelfModel`'s own `arbiter_debug` payload, which is attached
later in the same pipeline (`src/simulation.py`'s `step()` runs
`arbiter.score_simulations()` before `self_model.evaluate_simulations()`).

## Deterministic ordering (`sort_simulations`)

Ties on `final_score` are broken by higher `plausibility`, then higher
`emotional_prediction` — both baked into the sort key, not left to Python's
stable-sort input-order preservation, which is only deterministic if
upstream ordering itself is deterministic. Fully-tied simulations (equal on
all three) still fall back to input order.

## Validating changes to this module

When calibrating weights, thresholds, or deciding whether to enable
`normalize_inputs`, cross-reference:

- `docs/EVIDENCE_TABLE.md` for the literature backing each clinical preset's
  parameters — a weighting change that shifts which simulations rank
  highest should still be consistent with the preset's documented clinical
  profile.
- `VALIDATION_ACTION_PLAN.md` for the broader validation methodology this
  module's output feeds into.
- `tests/test_arbiter.py` for the current behavioral contract — any weight
  or threshold change should keep existing tests passing (or update them
  deliberately, not incidentally).
