import warnings
from typing import Any

try:
    from .bayesian_pe import BayesianPredictiveModeler, PrecisionWeights
except ImportError:
    from bayesian_pe import BayesianPredictiveModeler, PrecisionWeights

# Schema-mismatch magnitude above which stress ramps up rather than decays
_STRESS_TRIGGER_MISMATCH = 0.5

# Keys evaluate_simulations() relies on; missing values silently default to
# 0.0 unless on_missing_keys is "warn" or "error" (issue #57).
_REQUIRED_SIM_KEYS = ("emotional_prediction", "plausibility")
_VALID_MISSING_KEY_MODES = ("ignore", "warn", "error")


class SelfModel:
    """Tracks traits, emotion baseline, and schema stress across simulations."""

    def __init__(self, verbose: bool = False, on_missing_keys: str = "warn") -> None:
        if on_missing_keys not in _VALID_MISSING_KEY_MODES:
            message = (
                f"on_missing_keys must be one of {_VALID_MISSING_KEY_MODES}, "
                f"got {on_missing_keys!r}"
            )
            raise ValueError(message)

        self.traits = {
            "adaptive": 0.6,
            "avoidant": 0.4,
            "social": 0.5,
            "realism_bias": 0.7,  # tendency to prefer realistic simulations
        }
        self.emotion_baseline = 0.0  # running average of expected emotion
        self.schema_stress = 0.0

        # Bayesian precision-weighted PE system (NEW - Phase 3)
        self.bayesian_pe = None

        # When True, evaluate_simulations() attaches an "arbiter_debug" dict
        # to each simulation (issue #58) -- off by default to keep sim dicts
        # lean in the normal run loop.
        self.verbose = verbose

        # How to react when a sim dict is missing a required key: "ignore"
        # keeps the old silent-0.0-default behavior, "warn" logs and
        # defaults, "error" raises (issue #57).
        self.on_missing_keys = on_missing_keys

    def configure_bayesian_pe(self, params: dict[str, float]) -> None:
        """Initialize Bayesian PE from preset parameters."""
        precision = PrecisionWeights(
            sensory_precision=params["sensory_precision"],
            prior_precision=params["prior_precision"],
            volatile_precision=params["volatile_precision"],
            learning_rate=params["precision_learning_rate"],
        )
        self.bayesian_pe = BayesianPredictiveModeler(precision)

    def _validate_sim_keys(self, sim: dict[str, Any]) -> None:
        """Warn or raise when a sim dict is missing required keys."""
        if self.on_missing_keys == "ignore":
            return

        missing = [key for key in _REQUIRED_SIM_KEYS if key not in sim]
        if not missing:
            return

        message = f"Simulation missing required keys {missing}; defaulting to 0.0"
        if self.on_missing_keys == "error":
            raise KeyError(message)
        warnings.warn(message, stacklevel=3)

    def _update_stress_from_mismatch(self, mismatch: float) -> None:
        """Ramp schema_stress on large mismatch, otherwise decay it."""
        if mismatch > _STRESS_TRIGGER_MISMATCH:
            self.schema_stress += 0.1
        else:
            self.schema_stress *= 0.95  # decay

    def evaluate_simulations(self, simulations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Score prediction-error/schema mismatch and update stress for each simulation."""
        for sim in simulations:
            self._validate_sim_keys(sim)

            expected_valence = self.emotion_baseline
            actual_valence = sim.get("emotional_prediction", 0.0)

            # Use Bayesian PE if available (NEW - Phase 3)
            if self.bayesian_pe:
                # Update beliefs with observation (use DDM confidence as observation precision)
                observation_precision = sim.get("confidence", 0.5)
                pe_result = self.bayesian_pe.update_beliefs(
                    observation=actual_valence, observation_precision=observation_precision
                )

                # Store weighted PE components
                sim["schema_mismatch"] = abs(pe_result["pe_total"])
                sim["pe_sensory"] = pe_result["pe_sensory"]
                sim["pe_state"] = pe_result["pe_state"]
                sim["volatility"] = pe_result["volatility"]
                sim["precision_ratio"] = pe_result["precision_ratio"]

                mismatch = abs(pe_result["pe_total"])
            else:
                # Fallback to old logic (DEPRECATED)
                mismatch = abs(actual_valence - expected_valence)
                sim["schema_mismatch"] = mismatch

            # Update schema stress (with precision weighting)
            self._update_stress_from_mismatch(mismatch)

            # Apply schema filtering penalty
            realism = sim.get("plausibility", 0.0)
            realism_bias = self.traits["realism_bias"]
            penalty = (1.0 - realism) * realism_bias
            sim["schema_filtered_score"] = max(0.0, sim.get("final_score", 0.0) - penalty)

            if self.verbose:
                sim["arbiter_debug"] = {
                    "final_score": sim.get("final_score", 0.0),
                    "mismatch": mismatch,
                    "pe_sensory": sim.get("pe_sensory"),
                    "pe_state": sim.get("pe_state"),
                    "volatility": sim.get("volatility"),
                    "suppressed": bool(sim.get("fatigue_flag", False)),
                }

        return simulations

    def update_emotion_baseline(self, new_valence: float) -> None:
        """Update the running emotion baseline with an exponential moving average."""
        self.emotion_baseline = 0.8 * self.emotion_baseline + 0.2 * new_valence
