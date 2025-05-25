class SimulationClusterArbiter:
    def __init__(self, alpha=0.5, beta=0.3, gamma=0.2):
        self.alpha = alpha  # weight for physical plausibility
        self.beta = beta  # weight for emotional prediction
        self.gamma = gamma  # weight for reward distortion

    def score_simulations(self, simulations):
        for sim in simulations:
            t1 = sim.get("plausibility", 0.0)
            t2 = sim.get("emotional_prediction", 0.0)
            t3 = sim.get("reward_distortion", 0.0)

            # Inhibit distortion if it consistently fails (flagged previously)
            if sim.get("fatigue_flag") and t3 > 0.5:
                t3 = 0.0  # suppress reward distortion influence

            final_score = (
                    self.alpha * t1 +
                    self.beta * t2 +
                    self.gamma * t3
            )
            sim["final_score"] = round(final_score, 3)
        return simulations

    def sort_simulations(self, simulations):
        return sorted(simulations, key=lambda x: x.get("final_score", 0.0), reverse=True)
