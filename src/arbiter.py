import warnings

_REQUIRED_SIM_KEYS = ("plausibility", "emotional_prediction", "reward_distortion")


class SimulationClusterArbiter:
    """Score and rank candidate simulations by a weighted blend of their signals."""

    def __init__(  # noqa: PLR0913 -- each param is an independently meaningful tunable
        self,
        alpha=0.5,
        beta=0.3,
        gamma=0.2,
        fatigue_distortion_suppress_threshold=0.5,
        normalize_inputs=False,
        validate_keys=False,
        on_missing_keys="warn",
    ):
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
        # plausibility, emotional_prediction, and reward_distortion aren't on a
        # common scale upstream: plausibility is ~[0.5, 1.0], emotional_prediction
        # is [-1, 1] (see td_learning.py), and reward_distortion is unbounded above
        # 0. Weighting them directly can let one component dominate final_score
        # purely because of its native range, not its actual signal strength.
        # Off by default to preserve existing behavior for current callers; when
        # enabled, each component is min-max scaled to [0, 1] across the batch
        # passed to score_simulations before weights are applied.
        self.normalize_inputs = normalize_inputs
        # Missing plausibility/emotional_prediction/reward_distortion silently
        # default to 0.0 (see below), which can mask upstream data issues.
        # validate_keys=False preserves that silent-default behavior for
        # existing callers; when True, score_simulations checks every sim for
        # the required keys before scoring and either warns (on_missing_keys=
        # "warn", the default) or raises ValueError (on_missing_keys="raise").
        # fatigue_flag is intentionally not required here: its absence is a
        # legitimate "not fatigued" state, not a data-quality problem.
        self.validate_keys = validate_keys
        self.on_missing_keys = on_missing_keys

    @staticmethod
    def _minmax_normalize(values):
        """Scale values to [0, 1]; an all-equal batch maps to a neutral 0.5."""
        lo, hi = min(values), max(values)
        if hi == lo:
            return [0.5] * len(values)
        return [(v - lo) / (hi - lo) for v in values]

    def _check_required_keys(self, simulations):
        for i, sim in enumerate(simulations):
            missing = [key for key in _REQUIRED_SIM_KEYS if key not in sim]
            if not missing:
                continue
            message = (
                f"Simulation at index {i} is missing required key(s) {missing}; "
                f"will default to 0.0 for scoring."
            )
            if self.on_missing_keys == "raise":
                raise ValueError(message)
            warnings.warn(message, stacklevel=3)

    def score_simulations(self, simulations):
        """Compute final_score for each simulation in place and return the list."""
        if self.validate_keys:
            self._check_required_keys(simulations)

        if self.normalize_inputs and simulations:
            t1_norm = self._minmax_normalize([sim.get("plausibility", 0.0) for sim in simulations])
            t2_norm = self._minmax_normalize(
                [sim.get("emotional_prediction", 0.0) for sim in simulations]
            )
            t3_norm = self._minmax_normalize(
                [sim.get("reward_distortion", 0.0) for sim in simulations]
            )

        for i, sim in enumerate(simulations):
            if self.normalize_inputs:
                t1, t2, t3 = t1_norm[i], t2_norm[i], t3_norm[i]
            else:
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
