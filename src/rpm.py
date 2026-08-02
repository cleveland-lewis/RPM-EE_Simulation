import uuid
from typing import Optional

try:
    from .ddm import DriftDiffusionModel
except ImportError:
    from ddm import DriftDiffusionModel


class RecursivePredictiveModeler:
    def __init__(self, ddm_params: Optional[dict] = None):
        self.simulation_history = []
        self.slot_structure = ["agent", "emotion", "action", "result"]
        self.simulations = []

        # Initialize DDM (if params provided)
        self.ddm = None
        if ddm_params:
            self.ddm = DriftDiffusionModel(**ddm_params)

    def configure_ddm(self, params: dict):
        """Configure DDM from clinical preset parameters."""
        self.ddm = DriftDiffusionModel(
            base_rt=params["base_rt"],
            rt_variability=params["rt_variability"],
            rt_slowing=params["rt_slowing"],
            base_accuracy=params["base_accuracy"],
            accuracy_decline=params["accuracy_decline"],
        )

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
        }

        # Use DDM for action prediction (if available)
        if self.ddm:
            evidence = event["emotion"]["valence"]
            load = event.get("wm_load", 0.0)  # From memory system
            decision = self.ddm.predict_action(evidence, load)

            simulation["action"] = decision["action"]
            simulation["rt"] = decision["rt"]
            simulation["accurate"] = decision["accurate"]
            simulation["confidence"] = decision["confidence"]
        else:
            # Fallback to old logic (deprecated)
            simulation["action"] = self._predict_action(event)
            simulation["rt"] = None
            simulation["accurate"] = None
            simulation["confidence"] = 0.5

        simulation["result"] = self._predict_result(event)
        simulation["plausibility"] = self._compute_physical_plausibility(event)
        simulation["emotional_prediction"] = self._estimate_emotional_outcome(event)
        simulation["reward_distortion"] = self._distortion_bias(event)
        simulation["replay_weight"] = 1.0  # default before feedback
        return simulation

    def _predict_action(self, event):
        """Legacy fallback used only when no DDM is configured; prefer the DDM path."""
        # Placeholder logic — replace with real mapping from emotion or modality
        if event["modality"] == "vision":
            return "approach" if event["emotion"]["valence"] > 0 else "withdraw"
        elif event["modality"] == "touch":
            return "recoil" if event["emotion"]["valence"] < 0 else "explore"
        return "observe"

    def _predict_result(self, event):
        # Result is simplified as binary — success/failure or positive/negative
        if event["emotion"]["valence"] > 0.5:
            return "positive outcome"
        elif event["emotion"]["valence"] < -0.5:
            return "negative outcome"
        return "neutral outcome"

    def _compute_physical_plausibility(self, event):
        # Modality and intensity influence realism
        realism = 1.0 - abs(event["intensity"] - 0.5)
        return round(realism, 3)

    def _estimate_emotional_outcome(self, event):
        # Use emotion valence as expected emotion prediction
        return round(event["emotion"]["valence"], 3)

    def _distortion_bias(self, event):
        # Higher valence + low plausibility → more likely distorted
        distortion = max(
            0.0, event["emotion"]["valence"] - self._compute_physical_plausibility(event)
        )
        return round(distortion, 3)

    def get_simulations(self):
        return self.simulations
