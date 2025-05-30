import uuid


class RecursivePredictiveModeler:
    def __init__(self):
        self.simulation_history = []
        self.slot_structure = ["agent", "emotion", "action", "result"]
        self.simulations = []

    def generate_simulations(self, matched_events):
        simulations = []
        for event in matched_events:
            sim = self._create_simulation(event)
            self.simulation_history.append(sim)
            simulations.append(sim)
        self.simulations = simulations
        return simulations

    def _create_simulation(self, event):
        # Slot-filling with biased selections based on the input
        simulation = {
            "id": str(uuid.uuid4()),
            "source_event_id": event["id"],
            "agent": "self",  # default assumption
            "emotion": event["emotion"],
            "action": self._predict_action(event),
            "result": self._predict_result(event),
            "plausibility": self._compute_physical_plausibility(event),
            "emotional_prediction": self._estimate_emotional_outcome(event),
            "reward_distortion": self._distortion_bias(event),
            "replay_weight": 1.0  # default before feedback
        }
        return simulation

    @staticmethod
    def _predict_action(event):
        # Placeholder logic — replace with real mapping from emotion or modality
        if event["modality"] == "vision":
            return "approach" if event["emotion"]["valence"] > 0 else "withdraw"
        elif event["modality"] == "touch":
            return "recoil" if event["emotion"]["valence"] < 0 else "explore"
        return "observe"

    @staticmethod
    def _predict_result(event):
        # Result is simplified as binary — success/failure or positive/negative
        if event["emotion"]["valence"] > 0.5:
            return "positive outcome"
        elif event["emotion"]["valence"] < -0.5:
            return "negative outcome"
        return "neutral outcome"

    @staticmethod
    def _compute_physical_plausibility(event):
        # Modality and intensity influence realism
        realism = 1.0 - abs(event["intensity"] - 0.5)
        return round(realism, 3)

    @staticmethod
    def _estimate_emotional_outcome(event):
        # Use emotion valence as expected emotion prediction
        return round(event["emotion"]["valence"], 3)

    def _distortion_bias(self, event):
        # Higher valence + low plausibility → more likely distorted
        distortion = max(0.0, event["emotion"]["valence"] - self._compute_physical_plausibility(event))
        return round(distortion, 3)

    def get_simulations(self):
        return self.simulations
