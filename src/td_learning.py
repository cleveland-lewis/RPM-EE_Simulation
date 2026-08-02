"""
Temporal Difference Learning with Linear Function Approximation

Implements TD(0) with a continuous linear function approximator
V(s) = w^T x(s), replacing the prior tabular implementation that
induced severe state aliasing via coarse discretization of continuous
affective states into 250 rigid bins.

References:
- Sutton, R. S., & Barto, A. G. (2018). Reinforcement Learning: An Introduction.
  MIT Press. (TD(0) with function approximation, Chapter 9)
- Montague, P. R., Dayan, P., & Sejnowski, T. J. (1996). A framework for
  mesencephalic dopamine systems based on predictive Hebbian learning.
  Journal of Neuroscience, 16(5), 1936-1947.
- Maia, T. V., & Frank, M. J. (2011). From reinforcement learning models to
  psychiatric and neurological disorders. Nature Neuroscience, 14(2), 154-162.

Linear Function Approximator:
    V(s) = w^T x(s)
    w ← w + α δ x(s)
    δ = r + γ V(s') − V(s)   (TD error)

Feature vector x(s) ∈ ℝ⁵:
    [emotion_intensity, plausibility, reward_distortion, emotional_prediction, bias]

    emotion_intensity: [0, 1]   — emotional salience of simulation
    plausibility:      [0, 1]   — realism / physical plausibility
    reward_distortion: [0, 1]   — distortion bias (penalty source)
    emotional_pred:    [0, 1]   — normalized emotional prediction (from [-1,1])
    bias:              1.0      — constant offset; its weight encodes initial value

The bias weight is initialized to `initial_value`, so V(s) ≈ initial_value for
any untrained state. All other weights start at zero.

Clinical differentiation:
    MDD:  Low α (blunted learning) + negative initial bias (pessimism).
    ADHD: High α (impulsive) + low γ (delay aversion: devalue future rewards).
    ASD:  Normal α but reward_sensitivity modulates the reward signal.
"""

from typing import Optional

import numpy as np

# Indices for the feature vector
_IDX_EMOTION = 0
_IDX_PLAUSIBILITY = 1
_IDX_DISTORTION = 2
_IDX_EMO_PRED = 3
_IDX_BIAS = 4
_N_FEATURES = 5


class TemporalDifferenceLearner:
    """
    TD(0) learner with a shared linear value function V(s) = w^T x(s).

    Replaces the tabular approach (defaultdict keyed by discrete bins) with a
    continuous weight vector updated by semi-gradient TD(0). This avoids the
    discontinuous value estimates and state-aliasing caused by quantizing
    continuous affective dimensions into 250 rigid bins.

    Clinical modulation:
    - MDD: Low α (blunted learning), negative initial bias (pessimism).
    - ADHD: High α (impulsive updating), low γ (delay aversion).
    - ASD: Normal α; reward_sensitivity scales the reward signal.
    """

    def __init__(
        self,
        alpha: float = 0.1,
        gamma: float = 0.9,
        reward_sensitivity: float = 1.0,
        initial_value: float = 0.0,
    ):
        """
        Initialize TD learner with linear function approximator.

        Args:
            alpha: Learning rate (how fast the value function adapts).
            gamma: Discount factor in [0, 1] (weight of future rewards).
            reward_sensitivity: Multiplicative scaling of the reward signal.
            initial_value: Starting value for all states; encoded as the
                           initial bias weight so V(s) ≈ initial_value before
                           any learning.
        """
        self.alpha = alpha
        self.gamma = gamma
        self.reward_sensitivity = reward_sensitivity
        self.initial_value = initial_value

        # Weight vector for linear approximator V(s) = w^T x(s)
        # Bias weight initialised to initial_value; all others start at zero.
        self.weights = np.zeros(_N_FEATURES, dtype=np.float64)
        self.weights[_IDX_BIAS] = float(initial_value)

        # TD error history (for statistics / diagnostics)
        self.td_errors: list[float] = []

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------

    def _feature_vector(self, sim: dict) -> np.ndarray:
        """
        Extract a normalised feature vector from a simulation dictionary.

        Feature layout (indices defined by _IDX_* constants above):
            [emotion_intensity, plausibility, reward_distortion,
             emotional_prediction (normalised), bias=1]

        emotional_prediction lives in [−1, 1] and is linearly mapped to [0, 1]
        before entering the feature vector.
        """
        emotion = float(sim.get("emotion_intensity", 0.0))
        plausibility = float(sim.get("plausibility", 0.0))
        distortion = float(sim.get("reward_distortion", 0.0))
        # emotional_prediction in [-1, 1] → normalize to [0, 1]
        emo_pred = (float(sim.get("emotional_prediction", 0.0)) + 1.0) / 2.0
        return np.array([emotion, plausibility, distortion, emo_pred, 1.0], dtype=np.float64)

    # ------------------------------------------------------------------
    # Value function
    # ------------------------------------------------------------------

    def compute_value(self, sim: dict) -> float:
        """
        Estimate V(s) = w^T x(s) for a simulation.

        Args:
            sim: Simulation dictionary.

        Returns:
            Scalar value estimate.
        """
        x = self._feature_vector(sim)
        return float(np.dot(self.weights, x))

    # ------------------------------------------------------------------
    # TD update
    # ------------------------------------------------------------------

    def update_value(
        self, current_sim: dict, next_sim: Optional[dict] = None, terminal: bool = False
    ) -> dict[str, float]:
        """
        Semi-gradient TD(0) weight update.

        Update rule:  w ← w + α · δ · x(s)
        where δ = r + γ · V(s') − V(s)  (TD error).

        Args:
            current_sim: Current simulation dictionary.
            next_sim: Next simulation (None or terminal → V(s') = 0).
            terminal: If True, treat as terminal transition (V(s') = 0).

        Returns:
            Dictionary with 'value', 'td_error', 'reward', 'alpha', 'gamma'.
        """
        x = self._feature_vector(current_sim)
        V_current = float(np.dot(self.weights, x))

        reward = self._compute_reward(current_sim)

        if terminal or next_sim is None:
            V_next = 0.0
        else:
            x_next = self._feature_vector(next_sim)
            V_next = float(np.dot(self.weights, x_next))

        # TD error δ
        td_error = reward + self.gamma * V_next - V_current

        # Semi-gradient weight update: w ← w + α δ x
        self.weights += self.alpha * td_error * x

        self.td_errors.append(td_error)

        return {
            "value": float(np.dot(self.weights, x)),
            "td_error": float(td_error),
            "reward": float(reward),
            "alpha": self.alpha,
            "gamma": self.gamma,
        }

    # ------------------------------------------------------------------
    # Reward function
    # ------------------------------------------------------------------

    def _compute_reward(self, sim: dict) -> float:
        """
        Compute immediate reward from simulation features.

        Reward components:
        - Emotional intensity (positive signal)
        - Plausibility (realistic = rewarding)
        - Distortion penalty (distorted = aversive)

        Modulated by reward_sensitivity (clinical parameter):
        - MDD: low sensitivity → blunted reward processing
        - ADHD: high sensitivity → reward-seeking
        """
        emotion_reward = sim.get("emotion_intensity", 0.0)
        plausibility_reward = sim.get("plausibility", 0.0) * 0.3
        distortion_penalty = -sim.get("reward_distortion", 0.0) * 0.5
        raw_reward = emotion_reward + plausibility_reward + distortion_penalty
        return raw_reward * self.reward_sensitivity

    # ------------------------------------------------------------------
    # Affect feedback interface (replaces emotion.py hardcoded thresholds)
    # ------------------------------------------------------------------

    def get_affect_feedback(self, sim: dict) -> float:
        """
        Return learned affect feedback from V(s), scaled to [−0.5, 1.0].

        High value (strongly rewarding simulation) → positive feedback.
        Low value (aversive/neutral simulation) → negative or zero feedback.

        Args:
            sim: Simulation dictionary.

        Returns:
            Affect feedback clipped to [−0.5, 1.0].
        """
        value = self.compute_value(sim)
        feedback = np.tanh(value)  # Squash ℝ → [−1, 1]
        feedback = (feedback + 1.0) / 2.0  # → [0, 1]
        feedback = feedback * 1.5 - 0.5  # → [−0.5, 1.0]
        return float(np.clip(feedback, -0.5, 1.0))

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def reset(self):
        """Reset weights to initial state (bias = initial_value, rest = 0)."""
        self.weights = np.zeros(_N_FEATURES, dtype=np.float64)
        self.weights[_IDX_BIAS] = float(self.initial_value)
        self.td_errors.clear()

    # ------------------------------------------------------------------
    # Statistics / inspection
    # ------------------------------------------------------------------

    def get_statistics(self) -> dict[str, float]:
        """
        Return learning statistics.

        'n_unique_states' is repurposed to count active (non-zero, non-bias)
        feature dimensions, since state generalisation is now continuous.
        """
        if not self.td_errors:
            return {
                "mean_td_error": 0.0,
                "mean_abs_td_error": 0.0,
                "n_updates": 0,
                "n_unique_states": 0,
            }

        n_active = int(np.sum(np.abs(self.weights[:_IDX_BIAS]) > 1e-10))
        return {
            "mean_td_error": float(np.mean(self.td_errors)),
            "mean_abs_td_error": float(np.mean(np.abs(self.td_errors))),
            "std_td_error": float(np.std(self.td_errors)),
            "n_updates": len(self.td_errors),
            "n_unique_states": n_active,  # active feature dimensions after learning
        }

    def get_weights(self) -> dict[str, float]:
        """Return current weight vector as a labelled dictionary."""
        labels = ["w_emotion", "w_plausibility", "w_distortion", "w_emo_pred", "w_bias"]
        return {label: float(w) for label, w in zip(labels, self.weights, strict=False)}
