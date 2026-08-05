# RPM-EE Simulation Class (v1.1.0 Integrated with Clinical Presets)

import numpy as np

try:
    # Try relative imports first (when used as package)
    from .arbiter import SimulationClusterArbiter
    from .attunement import SocialAttunementSystem
    from .emotion import EmotionalEncoder
    from .fatigue import ReplayFatigueSuppressor
    from .memory import MemoryStore
    from .memory_vectorized import VectorizedMemoryStore
    from .presets import get_preset
    from .replay import ReplayModeArbitrator
    from .rpm import RecursivePredictiveModeler
    from .salience import SalienceTagger
    from .selfmodel import SelfModel
    from .sensory import SensoryInputSystem
except ImportError:
    # Fall back to absolute imports (when run directly)
    from arbiter import SimulationClusterArbiter
    from attunement import SocialAttunementSystem
    from emotion import EmotionalEncoder
    from fatigue import ReplayFatigueSuppressor
    from memory import MemoryStore
    from memory_vectorized import VectorizedMemoryStore
    from presets import get_preset
    from replay import ReplayModeArbitrator
    from rpm import RecursivePredictiveModeler
    from salience import SalienceTagger
    from selfmodel import SelfModel
    from sensory import SensoryInputSystem

# Prediction-error magnitude above which stress reactivity kicks in
_STRESS_REACTIVITY_PE_THRESHOLD = 0.5


class RPMEESimulation:
    """Orchestrates one clinically-parameterized RPM-EE simulation run."""

    def __init__(self, preset="neurotypical", use_vectorized_memory=False):
        """
        Initialize simulation with clinical preset.

        Args
        ----
        preset: Clinical preset name (default: 'neurotypical')
               Options: 'neurotypical', 'asd_typical', 'adhd_typical', 'mdd_typical'
        use_vectorized_memory: Use NumPy+Numba VectorizedMemoryStore instead of
                               MemoryStore (default: False). Produces identical
                               results with better performance for large memory sizes.
        """
        self.clock = 0
        self.logs = []

        # Load clinical preset parameters
        self.preset_name = preset
        self.params = get_preset(preset)

        # Subsystems (initialized with preset parameters)
        self.sensory = SensoryInputSystem()
        self.tagger = SalienceTagger()
        self.memory = VectorizedMemoryStore() if use_vectorized_memory else MemoryStore()
        self.rpm = RecursivePredictiveModeler()
        self.encoder = EmotionalEncoder()
        self.replay_mode = ReplayModeArbitrator()
        self.fatigue = ReplayFatigueSuppressor()
        self.arbiter = SimulationClusterArbiter()
        self.self_model = SelfModel()
        self.attuner = SocialAttunementSystem()

        # Apply clinical preset to subsystems
        self._configure_from_preset()

    def _configure_from_preset(self):
        """Apply clinical preset parameters to subsystems."""
        # Configure self model with stress parameters
        self.self_model.schema_stress = self.params["stress_baseline"]
        self.stress_reactivity = self.params["stress_reactivity"]
        self.stress_recovery = self.params["stress_recovery"]

        # Configure memory with WM capacity
        self.memory.capacity = int(self.params["wm_capacity"])
        self.memory.decay_rate = self.params["wm_decay_rate"]

        # Configure emotional baseline
        self.self_model.emotion_baseline = (
            self.params["positive_affect"] - self.params["negative_affect"]
        )

        # Store attention/executive parameters
        self.attention_stability = self.params["attention_stability"]
        self.switch_cost = self.params["switch_cost"]
        self.vigilance_decrement = self.params["vigilance_decrement"]

        # Store prediction/learning parameters
        self.prediction_error_gain = self.params["prediction_error_gain"]
        self.exploration_rate = self.params["exploration_rate"]

        # Configure RPM with DDM parameters (NEW - Phase 1)
        self.rpm.configure_ddm(
            {
                "base_rt": self.params["base_rt"],
                "rt_variability": self.params["rt_variability"],
                "rt_slowing": self.params["rt_slowing"],
                "base_accuracy": self.params["base_accuracy"],
                "accuracy_decline": self.params["accuracy_decline"],
            }
        )

        # Configure Bayesian PE in self model (NEW - Phase 3)
        self.self_model.configure_bayesian_pe(
            {
                "sensory_precision": self.params["sensory_precision"],
                "prior_precision": self.params["prior_precision"],
                "volatile_precision": self.params["volatile_precision"],
                "precision_learning_rate": self.params["precision_learning_rate"],
            }
        )

        # Configure TD learning in emotional encoder (NEW - Phase 4)
        self.encoder.configure_td_learning(
            {
                "td_alpha": self.params["td_alpha"],
                "td_gamma": self.params["td_gamma"],
                "td_initial_value": self.params["td_initial_value"],
                "reward_sensitivity": self.params["reward_sensitivity"],
            }
        )

    def step(self):
        """Advance the simulation by one clock tick and log resulting metrics."""
        self.clock += 1
        self.sensory.update_clock()
        input_packet = self.sensory.generate_input()
        tagged_events = self.tagger.tag_input(input_packet)
        self.memory.store_events(tagged_events)

        # Pass WM load to events for DDM (NEW - Phase 1)
        wm_load = self.memory.get_working_memory_load()
        for event in tagged_events:
            event["wm_load"] = wm_load

        matched, unmatched = self.memory.match_patterns(tagged_events)
        simulations = self.rpm.generate_simulations(matched)
        encoded = self.encoder.encode_simulations(simulations)
        fatigued = self.fatigue.apply_fatigue(encoded)
        scored = self.arbiter.score_simulations(fatigued)
        ranked = self.arbiter.sort_simulations(scored)
        evaluated = self.self_model.evaluate_simulations(ranked)
        relative_negative_bias = max(0.0, self.params.get("negative_affect", 0.20) - 0.20)
        attunement_score = self.attuner.evaluate_predictions(
            evaluated,
            reward_sensitivity=self.params.get("reward_sensitivity", 1.0),
            negative_bias=relative_negative_bias,
        )

        # Use precision-weighted PE if Bayesian PE available (NEW - Phase 3)
        if self.self_model.bayesian_pe:
            prediction_error = self.self_model.bayesian_pe.get_weighted_prediction_error(evaluated)
        else:
            # Fallback to simple mean
            prediction_error = sum(sim.get("schema_mismatch", 0.0) for sim in evaluated) / max(
                1, len(evaluated)
            )

        # Example system state for mode selection (with clinical parameters)
        system_state = {
            "clock": self.clock,
            "stress": self.self_model.schema_stress,
            "prediction_error": prediction_error,
            "emotion_volatility": sum(abs(sim["emotional_prediction"]) for sim in evaluated)
            / max(1, len(evaluated)),
            "attention_stability": self.attention_stability,
            "vigilance_level": max(
                0.0, self.attention_stability - self.vigilance_decrement * self.clock / 100
            ),
        }

        mode = self.replay_mode.select_mode(system_state)

        # Apply stress dynamics based on clinical preset
        self._update_stress(system_state)

        # Calculate RT/accuracy statistics for logging (NEW - Phase 1)
        rt_values = [s["rt"] for s in simulations if s.get("rt") is not None]
        accuracy_values = [s["accurate"] for s in simulations if s.get("accurate") is not None]

        if rt_values:
            rt_mean = np.mean(rt_values)
            rt_std = np.std(rt_values)
        else:
            rt_mean = None
            rt_std = None

        accuracy = np.mean(accuracy_values) if accuracy_values else None

        # Calculate precision metrics (NEW - Phase 3)
        if evaluated and any("precision_ratio" in s for s in evaluated):
            precision_ratios = [
                s.get("precision_ratio", 1.0) for s in evaluated if "precision_ratio" in s
            ]
            volatilities = [s.get("volatility", 0.5) for s in evaluated if "volatility" in s]
            avg_precision_ratio = np.mean(precision_ratios) if precision_ratios else 1.0
            avg_volatility = np.mean(volatilities) if volatilities else 0.5
        else:
            avg_precision_ratio = 1.0
            avg_volatility = 0.5

        # Log basic metrics with clinical parameters
        self.logs.append(
            {
                "clock": self.clock,
                "state": input_packet["state"],
                "replay_mode": mode,
                "num_tagged": len(tagged_events),
                "num_simulations": len(simulations),
                "attunement_score": attunement_score,
                "schema_stress": round(self.self_model.schema_stress, 3),
                "preset": self.preset_name,
                "vigilance": round(system_state["vigilance_level"], 3),
                # NEW: Phase 1 DDM metrics
                "rt_mean": round(rt_mean, 2) if rt_mean is not None else None,
                "rt_std": round(rt_std, 2) if rt_std is not None else None,
                "accuracy": round(accuracy, 3) if accuracy is not None else None,
                # NEW: Phase 3 Bayesian PE metrics
                "precision_ratio": round(avg_precision_ratio, 3),  # ASD marker
                "volatility": round(avg_volatility, 3),  # Environmental uncertainty
            }
        )

    def _update_stress(self, system_state):
        """Update stress based on clinical preset parameters."""
        # 1. Baseline Reversion: Pull stress towards the clinical baseline, not zero
        baseline = self.params["stress_baseline"]
        current = self.self_model.schema_stress
        self.self_model.schema_stress = current + (baseline - current) * self.stress_recovery

        # 2. Reactivity Spikes: Increase stress based on prediction errors
        pe = system_state["prediction_error"]
        if pe > _STRESS_REACTIVITY_PE_THRESHOLD:
            self.self_model.schema_stress += self.stress_reactivity * pe * 0.1

        # 3. Boundary Clamp: Keep stress within [0, 1]
        self.self_model.schema_stress = max(0.0, min(1.0, self.self_model.schema_stress))

    def run(self, episodes=100):
        """Run the simulation for the given number of episodes, calling step() each time."""
        for episode in range(episodes):
            self.step()
            if episode % 10 == 0:
                print(f"Episode {episode} complete")
        print("Simulation complete.")

    def step_trial(self, trial):
        """Run one externally-supplied trial through the DDM only.

        Unlike step(), this does not touch sensory/salience/memory/arbiter/
        self_model -- those subsystems operate on synthetic multimodal event
        streams with no defined semantics for a single two-alternative
        decision trial from an external dataset. Empirical validation
        compares real behavioral data against the one subsystem that has a
        directly comparable output: the DDM's (rt, accuracy) prediction from
        (evidence, load).

        Args
        ----
        trial: an object with .evidence (float, [-1, 1]), .load
            (float, [0, 1]), and .difficulty (float, [0, 1]) attributes
            -- e.g. adapters.base.Trial. load and difficulty are
            distinct axes (see ddm.py's predict_action docstring and
            README.md "DDM load vs. difficulty") -- do not conflate them.

        Returns
        -------
        The DDM's predict_action() dict: action, rt, accurate,
        confidence, evidence, load, difficulty. Compare 'rt'/'accurate'
        against trial.observed_rt_ms/observed_correct in the calling
        harness.
        """
        if self.rpm.ddm is None:
            msg = (
                "RPM has no configured DDM -- call sim with a clinical "
                "preset (configure_ddm runs automatically in __init__)."
            )
            raise RuntimeError(msg)
        return self.rpm.ddm.predict_action(trial.evidence, trial.load, trial.difficulty)
