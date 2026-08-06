class SimulationClusterArbiter:
    """Score and rank candidate simulations by a weighted blend of their signals."""

    def __init__(self, alpha=0.5, beta=0.3, gamma=0.2, fatigue_distortion_suppress_threshold=0.5):
        self.alpha = alpha  # weight for physical plausibility
        self.beta = beta  # weight for emotional prediction
        self.gamma = gamma  # weight for reward distortion
        # Once a simulation has been fatigue-flagged (repeatedly failed/replayed),
        # reward_distortion is suppressed only if it's still above this threshold.
        # Default 0.5 is the midpoint of reward_distortion's [0, 1] scale: a
        # fatigued simulation with sub-midpoint distortion is treated as no
        # longer meaningfully distorted and is left alone, while one still above
        # the midpoint is judged to be a stuck/unreliable distortion signal and
        # zeroed out so it can't dominate final_score.
        self.fatigue_distortion_suppress_threshold = fatigue_distortion_suppress_threshold

    def score_simulations(self, simulations):
        """Compute final_score for each simulation in place and return the list."""
        for sim in simulations:
            t1 = sim.get("plausibility", 0.0)
            t2 = sim.get("emotional_prediction", 0.0)
            t3 = sim.get("reward_distortion", 0.0)

            # Inhibit distortion if it consistently fails (flagged previously)
            if sim.get("fatigue_flag") and t3 > self.fatigue_distortion_suppress_threshold:
                t3 = 0.0  # suppress reward distortion influence

            final_score = self.alpha * t1 + self.beta * t2 + self.gamma * t3
            sim["final_score"] = round(final_score, 3)
        return simulations

    def sort_simulations(self, simulations):
        """Return simulations sorted by final_score, descending.

        Ties on final_score are broken by higher plausibility, then higher
        emotional_prediction, so ordering is deterministic regardless of input
        order -- relying on sort stability alone only preserves *input* order on
        ties, which isn't deterministic if upstream ordering varies.
        """
        return sorted(
            simulations,
            key=lambda x: (
                x.get("final_score", 0.0),
                x.get("plausibility", 0.0),
                x.get("emotional_prediction", 0.0),
            ),
            reverse=True,
        )
