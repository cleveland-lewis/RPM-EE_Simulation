## Open  [Q#]
- **[Q1] Canonical engine vs teaching core**
  - Decide whether `src/simulation.py` or `src/presets.py` (or a new shared module) is the canonical engine and how teaching narratives should be surfaced separately.
- **[Q2] FastAPI / web usage scope**
  - Clarify whether the FastAPI `/config` endpoint is for local use only or intended for a broader UI service, which would affect security and deployment choices.
- **[Q3] NC-MCM’s role**
  - How central is the Bayesian fitting pipeline to RPM-EE’s mission: core functionality or optional extension?
- **[Q4] Multi-agent/interactive scope**
  - Should the architecture evolve toward multi-agent or interactive tasks? Answering this guides future state structure and replay logic.