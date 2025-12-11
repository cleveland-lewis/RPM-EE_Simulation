
import random
from typing import Optional, List, Dict



class SocialAttunementSystem:
    """
    Simple evaluator that scores how well our simulation-predicted social value
    matches a hidden "truth" in [0,1].

    Now optionally incorporates an external attunement signal A \in [0,1] by
    blending it with the simulation-derived estimate. The blend is gated by A
    so that when attunement is higher we trust it more, but it never exceeds 40%
    of the mixture (keeps predictions anchored in task context).
    """
    def __init__(self):
        self.current_truth = self._generate_truth()
        self.history: List[Dict] = []

    @staticmethod
    def _generate_truth() -> float:
        # Simulates a dynamic external 'social norm' value between 0 and 1
        return round(random.uniform(0.0, 1.0), 2)

    def evaluate_predictions(self, simulations: List[Dict], attunement: Optional[float] = None) -> int:
        """Evaluate a batch of candidate simulations against current truth.

        Args:
            simulations: list of dicts with optional key 'emotional_prediction' in [-1,1] or [0,1].
            attunement: optional scalar A in [0,1] representing alignment/engagement.
        Returns:
            Integer score in {0..5} where higher is better.
        """
        predicted_value, blend_info = self._infer_from_simulations(simulations, attunement)
        score = self._score_prediction(predicted_value, self.current_truth)

        # Log and update
        self.history.append({
            "truth": self.current_truth,
            "predicted": predicted_value,
            "score": score,
            "attunement": None if attunement is None else float(max(0.0, min(1.0, attunement))),
            "blend": blend_info,
        })

        # Update to a new truth next cycle
        self.current_truth = self._generate_truth()
        return score

    @staticmethod
    def _infer_from_simulations(simulations: List[Dict], attunement: Optional[float] = None):
        # 1) Derive a [0,1] estimate from simulations
        if not simulations:
            sim_est = 0.5
        else:
            vals = []
            for sim in simulations:
                v = sim.get("emotional_prediction", 0.0)
                # Accept either [-1,1] or [0,1]
                if -1.0 <= float(v) <= 1.0:
                    if float(v) < 0.0 or sim.get("range", "auto") == "[-1,1]":
                        # map [-1,1] -> [0,1]
                        vals.append(0.5 * (float(v) + 1.0))
                    else:
                        vals.append(float(v))
                else:
                    # If out of range, clamp and map conservatively
                    vals.append(max(0.0, min(1.0, float(v))))
            sim_est = round(sum(vals) / len(vals), 2) if vals else 0.5

        # 2) Blend with attunement if provided: pred = (1-g)*sim_est + g*A
        if attunement is None:
            g = 0.0
            pred = sim_est
        else:
            A = float(max(0.0, min(1.0, attunement)))
            # Gate: allow attunement to contribute up to 40% of the prediction
            g = 0.40 * A  # g in [0, 0.40]
            pred = (1.0 - g) * sim_est + g * A
        return round(pred, 2), {"g": round(g, 3), "sim_est": sim_est}

    @staticmethod
    def _score_prediction(predicted: float, truth: float) -> int:
        diff = abs(predicted - truth)
        if diff < 0.05:
            return 5
        elif diff < 0.1:
            return 4
        elif diff < 0.2:
            return 3
        elif diff < 0.3:
            return 2
        elif diff < 0.4:
            return 1
        else:
            return 0
