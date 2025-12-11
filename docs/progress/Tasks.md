# Engine
## Algorithm Calibration
- [ ] **Fix attunement distribution** - Increase theta0 to ~1.2, reduce penalty multipliers
## Memory
- [ ] Need to make the memory feature more robust and aligned with validated research. 
# Modeling
- [ ] **Add accuracy model** - Compute accuracy from attunement and load.
- [ ] **Accurate language** - Ensure that the language and terms throughout the model are consistent and precise in alignment with validated research. 
- [ ] **Model recovery test** - Generate synthetic data, recover parameters
- [ ] **Add baseline comparison models**: linear-only, stress-only, and null model.
- [ ] **Artificial Intelligence** - Utilize an artificial intelligence to assist in the analysis of vast amounts of data.
	- [ ] Will only perform basic duties.
	- [ ] Will not alter or access testing or the algorithm
	- [ ] Will run local **only**.
	- [ ] Will offer analyses of data that are not obvious. 
- [ ] **Fit to public dataset** - Download Flanker/Stroop data and test the model. 
	- [ ] If no or insufficient data is available, conduct research, if possible. 
- [ ] **Add parameter learning** - Trial-by-trial adaptation (Δθ updates)
# Testing
## Debugging
- [ ] **Log each trial** - Every time a trial is run, log a debugging file, showcasing a synopsis of what went on during this trial. 
## Batch
- [ ] **Create trial wrapper class** - `src/trial_wrapper.py` with TrialSimulator.
- [ ] **Add RT generation** - Map attunement → RT in trial wrapper.
- [ ] **Create a validation test suite** to ensure test distributions are reasonable.
# Experiments
- [ ] **Implement full precision tracking** - Update pi_aff, pi_str, pi_mem, pi_vol (not just pi_ext)
- [ ] **Document testable predictions** - What does RPM-EE predict uniquely?
- [ ]  **Create trial examples** - Common experimental paradigms.
- [ ] **Increase Computing** - increase computing power.
	- [ ] Either ask parents and explain the stakes or go to the professor. 
- [ ] **Collect pilot data** - N=20-30, test specific predictions
# Literature
- [ ]  **Write operational definitions**: map attunement/stress to observables.
- [ ] **README** - Complete the `README.md`
- [ ] **Peer Review** - Submit papers to peer review
- [ ] **Add THEORY.md** - Core assumptions, boundary conditions.
- [ ] **Add Bibliography.md** - Key citations for all claims.
- [ ] **Document design decisions** - Justify architectural choices
- [ ] **Write a methods paper** - Submit to Behavior Research Methods.
- [ ] **Design-focused experiment** - Dual-task interference study

# Expansion
- [ ] **Create an interactive demo**: a web interface for parameter exploration.
- [ ] **Validate clinical presets** - Compare ASD/ADHD to real clinical data.
- [ ] **Extended validation** - Multiple datasets, multiple tasks


---


---

# Priority Order

- **Day 1-2:** Item 1 (trial wrapper) 
- **Day 3:** Item 2 (RT), Item 3 (distribution)  
- **Day 4-5:** Item 4 (validation tests) 
- **Day 6-7:** Item 7 (model recovery)