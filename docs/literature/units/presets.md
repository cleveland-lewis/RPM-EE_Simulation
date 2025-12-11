## Purpose
- Declarative `PRESETS` that configure canonical simulations and trial wrappers.
- Thin runtime wrapper that forwards to `src/simulation.run_simulation`.
- **Teaching-only archive** of the legacy loop now lives at `docs/teaching/learning_core.py`.

## Map from theory → code
- *External load*      
	- precision‑weighted fusion of sensory modalities (vision, hearing, touch)
- *Affect level/vol*   
	- EMA and variance of affect; volatility (stdev) penalizes stability
- *Memory load*
	- capacity‑limited, nonlinear transform of short‑term size
- *Stress (schema)*
	- slow drive (homeostatic/allostatic) + fast surprisal (PE‑driven) micro‑loop
- *Attunement*
	- sigmoid( θ0 + Σ weights × contributors × precisions )

## Notes

• PRESETS only change ***behavioral** flavor*; they do not change the **structure**.
• Backends (JAX/Numba/NumPy) are interchangeable; outputs have the same structure.
• Math: precision weighting (precision ≈ 1/variance), logistic and softmax ideas,
  normalization, and timescales (fast/slow dynamics via EMA and blending).
• Cognitive neuroscience: how *external load*, *working‑memory load*, *affect level*,
  and *affect volatility*, drive a latent **schema stress**, which then influences a
  precision‑weighted **attunement** signal (a logistic of a linear combination).
