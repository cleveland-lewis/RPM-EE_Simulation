class SelfModel:
    def __init__(self):
        self.traits = {
            "adaptive": 0.6,
            "avoidant": 0.4,
            "social": 0.5,
            "realism_bias": 0.7  # tendency to prefer realistic simulations
        }
        self.emotion_baseline = 0.0  # running average of expected emotion
        self.schema_stress = 0.0

    def evaluate_simulations(self, simulations):
        for sim in simulations:
            expected_valence = self.emotion_baseline
            actual_valence = sim.get("emotional_prediction", 0.0)
            mismatch = abs(actual_valence - expected_valence)

            # Store mismatch magnitude
            sim["schema_mismatch"] = mismatch

            # Update schema stress
            if mismatch > 0.5:
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
        self.emotion_baseline = 0.8 * self.emotion_baseline + 0.2 * new_valence
