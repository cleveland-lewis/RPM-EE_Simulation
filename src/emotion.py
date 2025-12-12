# RPM-EE Emotional Encoder (v1.1.0)

import random

class EmotionalEncoder:
    def __init__(self):
        self.replay_fatigue_threshold = 3
        self.simulation_replay_count = {}

    def encode_simulations(self, simulations):
        for sim in simulations:
            sim_id = sim["id"]
            self.simulation_replay_count.setdefault(sim_id, 0)
            self.simulation_replay_count[sim_id] += 1

            # Emotion feedback loop
            sim["emotion_intensity"] = abs(sim.get("emotional_prediction", 0))
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
        # Reinforce high-emotion, low-plausibility simulations as distorted favorites
        reward_distortion = sim.get("reward_distortion", 0)
        emotion_intensity = sim.get("emotion_intensity", 0)
        
        if reward_distortion > 0.4 and emotion_intensity > 0.6:
            return 0.6  # biasing replay upwards
        elif emotion_intensity > 0.5:
            return 0.3
        elif emotion_intensity > 0.2:
            return 0.1
        else:
            return -0.1  # suppress weak/no emotion