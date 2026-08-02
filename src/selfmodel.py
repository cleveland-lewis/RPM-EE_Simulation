try:
    from .bayesian_pe import BayesianPredictiveModeler, PrecisionWeights
except ImportError:
    from bayesian_pe import BayesianPredictiveModeler, PrecisionWeights

# Schema-mismatch magnitude above which stress ramps up rather than decays
_STRESS_TRIGGER_MISMATCH = 0.5


class SelfModel:
    """Tracks traits, emotion baseline, and schema stress across simulations."""

    def __init__(self):
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

    def configure_bayesian_pe(self, params: dict):
        """Initialize Bayesian PE from preset parameters."""
        precision = PrecisionWeights(
            sensory_precision=params["sensory_precision"],
            prior_precision=params["prior_precision"],
            volatile_precision=params["volatile_precision"],
            learning_rate=params["precision_learning_rate"],
        )
        self.bayesian_pe = BayesianPredictiveModeler(precision)

    def evaluate_simulations(self, simulations):
        """Score prediction-error/schema mismatch and update stress for each simulation."""
        for sim in simulations:
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
            if mismatch > _STRESS_TRIGGER_MISMATCH:
                self.schema_stress += 0.1
            else:
                self.schema_stress *= 0.95  # decay

            # Apply schema filtering penalty
            realism = sim.get("plausibility", 0.0)
            realism_bias = self.traits["realism_bias"]
            penalty = (1.0 - realism) * realism_bias
            sim["schema_filtered_score"] = max(0.0, sim.get("final_score", 0.0) - penalty)

        return simulations

    def update_emotion_baseline(self, new_valence):
        """Update the running emotion baseline with an exponential moving average."""
        self.emotion_baseline = 0.8 * self.emotion_baseline + 0.2 * new_valence
