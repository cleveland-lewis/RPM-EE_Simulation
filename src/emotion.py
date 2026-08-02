try:
    from .td_learning import TemporalDifferenceLearner
except ImportError:
    from td_learning import TemporalDifferenceLearner

# Fatigue: halve replay weight once a simulation has been replayed this often
_FATIGUE_WEIGHT_PENALTY = 0.5

# Legacy (non-TD-learning) affect feedback thresholds/values -- see
# _calculate_affect_feedback's fallback branch.
_DISTORTION_BIAS_THRESHOLD = 0.4
_HIGH_EMOTION_THRESHOLD = 0.6
_MEDIUM_EMOTION_THRESHOLD = 0.5
_LOW_EMOTION_THRESHOLD = 0.2
_DISTORTED_FAVORITE_FEEDBACK = 0.6
_HIGH_EMOTION_FEEDBACK = 0.3
_LOW_EMOTION_FEEDBACK = 0.1
_WEAK_EMOTION_FEEDBACK = -0.1


class EmotionalEncoder:
    """Encodes affect feedback and fatigue for generated simulations."""

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
        """Attach emotion intensity, affect feedback, and fatigue flags to each simulation."""
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
                sim["replay_weight"] *= _FATIGUE_WEIGHT_PENALTY
                sim["fatigue_flag"] = True
            else:
                sim["fatigue_flag"] = False

        return simulations

    def _calculate_affect_feedback(self, sim):
        # Use TD learning if available (NEW - Phase 4)
        if self.td_learner:
            return self.td_learner.get_affect_feedback(sim)

        # Fallback to hardcoded thresholds (legacy v1.1 behavior, used only
        # when no TD learner has been configured)
        # Reinforce high-emotion, low-plausibility simulations as distorted favorites
        if (
            sim["reward_distortion"] > _DISTORTION_BIAS_THRESHOLD
            and sim["emotion_intensity"] > _HIGH_EMOTION_THRESHOLD
        ):
            return _DISTORTED_FAVORITE_FEEDBACK  # biasing replay upwards
        if sim["emotion_intensity"] > _MEDIUM_EMOTION_THRESHOLD:
            return _HIGH_EMOTION_FEEDBACK
        if sim["emotion_intensity"] > _LOW_EMOTION_THRESHOLD:
            return _LOW_EMOTION_FEEDBACK
        return _WEAK_EMOTION_FEEDBACK  # suppress weak/no emotion
