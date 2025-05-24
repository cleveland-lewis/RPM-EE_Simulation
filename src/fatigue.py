class ReplayFatigueSuppressor:
    def __init__(self, fatigue_threshold=5, suppression_factor=0.5):
        self.replay_counts = {}
        self.fatigue_threshold = fatigue_threshold
        self.suppression_factor = suppression_factor

    def apply_fatigue(self, simulations):
        for sim in simulations:
            sim_id = sim["id"]
            self.replay_counts.setdefault(sim_id, 0)
            self.replay_counts[sim_id] += 1

            if self.replay_counts[sim_id] > self.fatigue_threshold:
                sim["replay_weight"] *= self.suppression_factor
                sim["fatigue_flag"] = True
            else:
                sim["fatigue_flag"] = False

        return simulations

    def reset_fatigue(self, sim_id):
        self.replay_counts[sim_id] = 0
