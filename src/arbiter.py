
class SimulationClusterArbiter:
    """
    Cluster arbiter with optional state-aware weighting and softmax selection.
    Backward-compatible defaults preserve prior behavior:
      • reward_distortion is ADDITIVE by default (penalty mode is opt-in)
      • binary fatigue flag still works; graded fatigue uses optional 'fatigue_level'
      • weights alpha/beta/gamma are constant unless 'adaptive' is enabled
    """
    def __init__(self, alpha=0.5, beta=0.3, gamma=0.2,
                 *,
                 adaptive: bool = False,
                 penalize_distortion: bool = True,
                 k_fatigue: float = 0.7,
                 use_softmax: bool = False,
                 base_temp: float = 1.0,
                 inertia_bonus: float = 0.03):
        # Base weights (kept for backward compatibility)
        self.alpha = float(alpha)
        self.beta = float(beta)
        self.gamma = float(gamma)
        # New optional behaviors
        self.adaptive = bool(adaptive)
        self.penalize_distortion = bool(penalize_distortion)
        self.k_fatigue = float(k_fatigue)
        self.use_softmax = bool(use_softmax)
        self.base_temp = float(base_temp)
        self.inertia_bonus = float(inertia_bonus)

    @staticmethod
    def _clip01(x):
        try:
            x = float(x)
        except (ValueError, TypeError):
            x = 0.0
        return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

    def _adaptive_weights(self, *, stress=0.0, volatility=0.0, salience=0.0, confidence=0.5):
        """Compute state-aware weights; renormalize to sum to 1.
        If self.adaptive is False, return the base weights normalized.
        """
        a0, b0, g0 = self.alpha, self.beta, self.gamma
        if not self.adaptive:
            s = (a0 + b0 + g0) or 1.0
            return a0/s, b0/s, g0/s
        # Simple linear modulation; conservative gains to avoid large swings
        a_eff = a0 * (1.0 + 0.5 * self._clip01(stress) + 0.3 * self._clip01(volatility))
        g_eff = g0 * (1.0 - 0.6 * self._clip01(stress) - 0.4 * self._clip01(volatility))
        b_eff = b0 * (1.0 + 0.4 * self._clip01(salience) * self._clip01(confidence))
        s = (a_eff + b_eff + g_eff) or 1.0
        return a_eff/s, b_eff/s, g_eff/s

    def score_simulations(self, simulations, **state):
        """
        Score a list of simulation dicts in-place and return it.
        Each dict may include keys:
          plausibility, emotional_prediction, reward_distortion (floats in [0,1])
          fatigue_flag (bool), fatigue_level (float in [0,1])
        Optional state (kwargs) for adaptive weighting / softmax temperature:
          stress, volatility, salience, confidence (floats in [0,1])
        """
        stress = self._clip01(state.get('stress', 0.0))
        volatility = self._clip01(state.get('volatility', 0.0))
        salience = self._clip01(state.get('salience', 0.0))
        confidence = self._clip01(state.get('confidence', 0.5))

        a, b, g = self._adaptive_weights(stress=stress, volatility=volatility,
                                         salience=salience, confidence=confidence)
        utils = []
        for sim in simulations:
            t1 = self._clip01(sim.get("plausibility", 0.0))
            t2 = self._clip01(sim.get("emotional_prediction", 0.0))
            rd_raw = self._clip01(sim.get("reward_distortion", 0.0))

            # Fatigue handling: binary flag still supported; graded if 'fatigue_level' provided
            fatigue_level = sim.get("fatigue_level")
            if fatigue_level is None:
                fatigue_level = 1.0 if sim.get("fatigue_flag") else 0.0
            fatigue_level = self._clip01(fatigue_level)

            # Graded suppression of reward distortion contribution under fatigue
            rd_eff = rd_raw * (1.0 - self.k_fatigue * fatigue_level)

            # Backward-compatible default: distortion is additive unless penalize_distortion=True
            if self.penalize_distortion:
                u = a * t1 + b * t2 - g * rd_eff
            else:
                # Maintain additive behavior from original code
                u = a * t1 + b * t2 + g * rd_eff

            # Add inertia bonus to every score
            u += self.inertia_bonus

            sim["final_score"] = round(float(u), 6)
            # Add transparent attribution for analysis (non-breaking extra fields)
            sim.setdefault("_terms", {})
            sim.setdefault("_weights", {})
            sim["_terms"].update({
                "plausibility": t1,
                "emotion": t2,
                "reward_distortion": rd_eff,
                "fatigue_level": fatigue_level,
            })
            sim["_weights"].update({
                "alpha_eff": a,
                "beta_eff": b,
                "gamma_eff": g,
            })
            utils.append(u)

        # Optional softmax selection probabilities for downstream stochastic choice
        if self.use_softmax and simulations:
            import math
            T = max(1e-6, self.base_temp * (1.0 - 0.7 * confidence + 0.6 * volatility))
            m = max(utils)
            exps = [math.exp((u - m) / T) for u in utils]
            Z = sum(exps) or 1.0
            for sim, e in zip(simulations, exps):
                sim["select_prob"] = float(e / Z)

        return simulations

    @staticmethod
    def sort_simulations(simulations):
        return sorted(simulations, key=lambda x: x.get("final_score", 0.0), reverse=True)
