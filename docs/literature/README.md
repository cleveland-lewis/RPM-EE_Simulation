

# RPM-EE v1.1.0 Simulation

Recursive Predictive Modeling with Emotional Encoding (RPM‑EE) is a **computational cognitive neuroscience** framework. It models how recursive prediction, **emotion-as-modulator**, and **salience-based processing** interact to shape attention, memory, replay, and action selection. This repo contains the reference simulation engine and batch tooling.

---

## Repository Layout

- `src/` – Python source code for the simulation
- `config/` – YAML configuration for logging
- `logs/` – Output folder for logs and data
- `docs/` – Architecture notes, diagrams, and study designs
- `results/` – Auto‑generated summaries and (optional) per‑tick logs

---

## Overview

**Goal of the model:** simulate an agent that maintains a predictive self‑model and adapts via **precision‑weighted** integration of external load, internal memory load, affect (tone + volatility), and schema stress. Emotion acts as a **weighting signal** that modulates what is noticed, rehearsed (replayed), stored, and acted upon.

**What’s novel here**
- **Replay mode arbitration** (Explore / Converge / Stabilize) driven by salience, prediction error, volatility, and expected distortion.
- **Precision weighting** across sensory modalities (vision, hearing, touch) using online variance estimates.
- **Two‑timescale stress**: slow allostatic drive blended with a fast surprisal micro‑loop (prediction‑error burst).
- **Attunement equation** (logit → sigmoid) that combines contributors with optional online normalization; can gate actions stochastically.

This aligns with current directions in computational cognitive neuroscience emphasizing **integrative, multiscale, mechanistically interpretable** models.

---

## Research Goals

1. Build a **mechanistically interpretable** agent that links cognitive states to tunable parameters (for phenotyping and hypothesis tests).
2. Implement **predictive coding** loops and **active inference‑style** policy selection to minimize surprise / free energy.
3. Model **emotion–cognition coupling** as a bidirectional regulator of attention, replay selection, and memory consolidation.
4. Support **computational phenotyping** under different parameterizations (e.g., neurotypical, ADHD‑typical, ASD‑typical).
5. Enable **empirical validation** against behavioral/neuroimaging datasets and posterior‑predictive checks.

---

## Techniques Utilized

- **Bayesian / Predictive Coding**: precision weighting; hierarchical prediction‑error blending  
- **Active‑Inference‑style Arbitration**: softmax over replay utilities with distortion penalties  
- **Multiscale Dynamics**: slow drive (allostatic) + fast surprisal micro‑loops  
- **Emotion–Cognition Coupling**: affect tone and volatility modulate attention, gating, and replay priorities  
- **Monte Carlo / Parameter Sweeps**: systematic exploration of sensitivity surfaces  
- **Optional Backends**: NumPy baseline, JAX for very large arrays, and Numba for CPU JIT paths  

> See `simulation.py` for implementation details (attunement terms, stress blending, precision tracking, gating, and arbiter scoring).

---

## How To

### Quick start (single batch)

Run 5 runs at 5000 ticks each:

```bash
python batch_runner.py --runs 5 --total-ticks 5000
```

### Multi‑batch sweeps

Run 5 **batches**, each doing 5 runs at 5000 ticks and a 2×2 grid sweep:

```bash
python batch_runner.py \
  --batches 5 \
  --runs 5 \
  --total-ticks 5000 \
  --grid '{"event_rate":[2,4], "salience_decay":[0.01,0.03]}'
```

### Save per‑tick logs (one JSON per run)

```bash
python batch_runner.py --batches 2 --runs 3 --save-per-tick
```

### Presets and params (optional)

If you have `presets.py` with `PRESETS`, you can set a preset and still override values:

```bash
python batch_runner.py --preset default_theory --runs 3 --params '{"memory_buffer_size":800}'
```

`--params` accepts a JSON string **or** a path to a JSON file.

**Common engine keys:**  
`total_ticks, salience_decay, highly_variable_rate, event_rate, memory_buffer_size, memory_decay, memory_prune_threshold, low_salience_var_rate, bin_size`

---

## Results Structure

After a run, results are grouped under `results/`:

```
results/<base>_<timestamp>/
  batch0/
    run0__event_rate=2_salience_decay=0.01/
      summary.csv
      summary.json
      logs.json          # present if --save-per-tick
    ...
  batch0_summary.csv     # batch‑level summary
  batch0_summary.json
  ...
  <base>_<timestamp>_summary.csv  # global summary across all batches
  <base>_<timestamp>_summary.json
```

`<base>` defaults to `run`, or you can set it with `--summary-name`.

---

## Roadmap

1. **v1.1 Core Integration (current)** – stabilize sensory, salience, replay, attunement, and stress subsystems; document knobs.  
2. **v1.2 Bayesian Predictive Layer** – add explicit free‑energy minimization / uncertainty weighting; expose EFE switch in arbiter.  
3. **v1.3 Multiscale Neural Mapping** – link key variables to oscillatory/region analogs; add export hooks for EEG/fMRI alignment.  
4. **v1.4 Causal Simulation Engine** – integrate structural counterfactual reasoning in replay; support intervention queries.  
5. **v1.5 Empirical Validation** – import open behavioral/neuroimaging datasets; fit and report posterior‑predictive metrics.

---

## Key References

- Breakspear, M., et al. (2024). *System‑level brain modeling.* Frontiers in Neuroscience.  
- Li, H., et al. (2025). *Multiscale brain modeling: bridging microscopic and macroscopic brain dynamics.* Neural Computation.  
- Friston, K., et al. (2024). *Predictive coding and active inference.* Trends in Cognitive Sciences.  
- Pessoa, L. (2024). *Emotion–cognition interactions.* Nature Reviews Neuroscience.  
- Gerstenberg, T., et al. (2024). *Counterfactual simulation in causal cognition.* Cognitive Science.  

---

## Notes

- The engine prints per‑run summaries and overall batch statistics (mean/SD for attunement and stress).  
- Optional backends (JAX/Numba) are used opportunistically; behavior is identical across backends.  
- For exploratory studies, start with shorter runs (e.g., 1000–2000 ticks) and increase as needed.