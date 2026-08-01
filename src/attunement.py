import random


class SocialAttunementSystem:
    def __init__(self):
        self.current_truth = self._generate_truth()
        self.history = []

    def _generate_truth(self):
        # Simulates a dynamic external 'social norm' value between 0 and 1
        return round(random.uniform(0.0, 1.0), 2)

    def evaluate_predictions(self, simulations, reward_sensitivity=1.0, negative_bias=0.0):
        # Pick one simulation or average multiple, applying clinical biases
        predicted_value = self._infer_from_simulations(
            simulations, reward_sensitivity, negative_bias
        )
        score = self._score_prediction(predicted_value, self.current_truth)

        # Log and update
        self.history.append(
            {"truth": self.current_truth, "predicted": predicted_value, "score": score}
        )

        # Update to a new truth next cycle
        self.current_truth = self._generate_truth()
        return score

    def _infer_from_simulations(self, simulations, reward_sensitivity, negative_bias):
        if not simulations:
            return 0.5  # neutral guess

        avg_valence = sum(sim.get("emotional_prediction", 0.0) for sim in simulations) / len(
            simulations
        )

        # Apply clinical modifiers to the raw valence
        # Dampen positive valence based on reward sensitivity (Anhedonia marker)
        if avg_valence > 0:
            avg_valence *= reward_sensitivity

        # Apply negative bias (Rumination/Negative Affect marker)
        avg_valence -= negative_bias

        # Clamp to [-1, 1] before normalizing
        avg_valence = max(-1.0, min(1.0, avg_valence))

        return round((avg_valence + 1.0) / 2.0, 2)  # normalize from [-1,1] to [0,1]

    def _score_prediction(self, predicted, truth):
        diff = abs(predicted - truth)
        if diff < 0.05:
            return 5
        elif diff < 0.1:
            return 4
        elif diff < 0.2:
            return 3
        elif diff < 0.3:
            return 2
        elif diff < 0.4:
            return 1
        else:
            return 0
