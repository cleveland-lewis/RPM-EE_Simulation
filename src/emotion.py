try:
    from .td_learning import TemporalDifferenceLearner
except ImportError:
    from td_learning import TemporalDifferenceLearner


class EmotionalEncoder:
    def __init__(self):
        self.replay_fatigue_threshold = 3
        self.simulation_replay_count = {}

        # TD learning for affect feedback (NEW - Phase 4)
        self.td_learner = None

    def configure_td_learning(self, params: dict):
        """Initialize TD learner from preset parameters."""
        self.td_learner = TemporalDifferenceLearner(
            alpha=params["td_alpha"],
            gamma=params["td_gamma"],
            reward_sensitivity=params.get("reward_sensitivity", 1.0),
            initial_value=params["td_initial_value"],
        )

    def encode_simulations(self, simulations):
        for sim in simulations:
            sim_id = sim["id"]
            self.simulation_replay_count.setdefault(sim_id, 0)
            self.simulation_replay_count[sim_id] += 1

            # Emotion feedback loop
            sim["emotion_intensity"] = abs(sim["emotional_prediction"])
            sim["affect_feedback"] = self._calculate_affect_feedback(sim)
            sim["replay_weight"] += sim["affect_feedback"]

            # Emotional fatigue suppression
            if self.simulation_replay_count[sim_id] > self.replay_fatigue_threshold:
                sim["replay_weight"] *= 0.5
                sim["fatigue_flag"] = True
            else:
                sim["fatigue_flag"] = False

        return simulations

    def _calculate_affect_feedback(self, sim):
        # Use TD learning if available (NEW - Phase 4)
        if self.td_learner:
            return self.td_learner.get_affect_feedback(sim)

        # Fallback to hardcoded thresholds (DEPRECATED - v1.1 behavior)
        # Reinforce high-emotion, low-plausibility simulations as distorted favorites
        if sim["reward_distortion"] > 0.4 and sim["emotion_intensity"] > 0.6:
            return 0.6  # biasing replay upwards
        elif sim["emotion_intensity"] > 0.5:
            return 0.3
        elif sim["emotion_intensity"] > 0.2:
            return 0.1
        else:
            return -0.1  # suppress weak/no emotion
