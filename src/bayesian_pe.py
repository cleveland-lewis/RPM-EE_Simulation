"""
Bayesian Precision-Weighted Prediction Error Framework.

Implements hierarchical Bayesian updating with precision parameters
to model predictive coding and enable ASD aberrant precision account.

References
----------
- Friston, K. (2010). The free-energy principle: a unified brain theory?
  Nature Reviews Neuroscience, 11(2), 127-138.
- Mathys, C., Daunizeau, J., Friston, K. J., & Stephan, K. E. (2011).
  A Bayesian foundation for individual learning under uncertainty.
  Frontiers in Human Neuroscience, 5, 39.
  (Hierarchical Gaussian Filter — HGF — formal derivation)
- Pellicano, E., & Burr, D. (2012). When the world becomes 'too real':
  a Bayesian explanation of autistic perception. Trends in Cognitive Sciences, 16(10), 504-510.
- Lawson, R. P., Rees, G., & Friston, K. J. (2014). An aberrant precision
  account of autism. Frontiers in Human Neuroscience, 8, 302.

Core concepts:
- Precision (π): Inverse variance (1/σ²), representing confidence/certainty
- Higher precision → more influential in belief updating
- ASD: High sensory precision + low prior precision = over-reliance on sensory input
- Prediction error weighted by precision: PE_weighted = π * (observation - prediction)

Volatility update (HGF Level 3):
  Volatility is tracked in LOG-VARIANCE space (log_v), updated via a
  dimensionless variance prediction error (VOPE):

      σ²_hat = BASE_VAR * exp(log_v)     # predictive variance
      VOPE   = pe² / σ²_hat - 1           # dimensionless chi-sq-like residual
      log_v ← log_v + (κ/2) * VOPE       # log-variance update
      μ_vol  = sigmoid(log_v)             # display: maps log_v to [0, 1]

  This is dimensionally consistent: both pe² and σ²_hat are variance-scale
  quantities; their ratio is dimensionless. Contrast with the invalid
  'pe² - μ_vol' subtraction (mixed units) used in prior versions.
"""

from dataclasses import dataclass

import numpy as np

# Reference variance scale for the volatility level.
# Observations are in approximately [-1, 1]; typical squared PEs are O(0.01-0.1).
# This sets the neutral operating point of the log-volatility tracker.
_BASE_VAR = 0.01


@dataclass
class PrecisionWeights:
    """Precision parameters for different information sources."""

    sensory_precision: float = 1.0  # π_sensory (weight for sensory PE)
    prior_precision: float = 1.0  # π_prior (weight for prior predictions)
    volatile_precision: float = 0.5  # π_volatile (uncertainty about volatility)
    learning_rate: float = 0.1  # Meta-learning rate for precision (κ)


class BayesianPredictiveModeler:
    """
    Hierarchical Bayesian system with precision-weighted prediction errors.

    Implements 3-level hierarchy following the HGF formalism (Mathys et al., 2011):
    1. Sensory level: Observations vs. predictions
    2. Hidden state level: State estimates vs. transitions
    3. Volatility level (log-variance): Estimate environmental change rate

    Volatility update is performed in LOG-VARIANCE space to preserve
    dimensional consistency. The predictive variance at level 3 is
    σ²_hat = BASE_VAR * exp(log_v), and the volatility prediction error
    is VOPE = pe² / σ²_hat - 1 (dimensionless). This avoids the invalid
    arithmetic subtraction of a raw squared error from a scalar [0,1] estimate.

    This enables modeling of aberrant precision in ASD:
    - High sensory_precision → over-weight sensory prediction errors
    - Low prior_precision → under-weight top-down predictions
    - Result: Difficulty filtering sensory noise, poor generalization
    """

    def __init__(self, precision_weights: PrecisionWeights):
        """
        Initialize Bayesian PE system with precision parameters.

        Args
        ----
        precision_weights: PrecisionWeights object with clinical parameters
        """
        self.precision = precision_weights

        # State estimates (beliefs)
        self.mu_sensory = 0.0  # Expected sensory input
        self.mu_state = 0.0  # Expected hidden state

        # Log-volatility (HGF Level 3 state, operates in log-variance space)
        self.log_v = 0.0  # log-volatility; sigmoid(0) = 0.5 = initial μ_vol
        self.mu_volatility = 0.5  # Display value: sigmoid(log_v), clamped to [0, 1]

        # State precisions (confidence)
        self.pi_sensory = self.precision.sensory_precision
        self.pi_state = self.precision.prior_precision
        self.pi_volatility = self.precision.volatile_precision

        # Prediction error history
        self.pe_history: list[dict] = []

    def update_beliefs(
        self, observation: float, observation_precision: float = 1.0
    ) -> dict[str, float]:
        """
        Bayesian update with precision-weighted prediction error.

        Volatility is updated via the HGF log-variance update rule:
            VOPE = pe_state² / (BASE_VAR * exp(log_v)) - 1
            log_v ← log_v + (κ/2) * VOPE
        ensuring dimensional consistency (pe² and σ²_hat share units).

        Args
        ----
        observation: Actual sensory value (e.g., emotional valence)
        observation_precision: Confidence in observation (from DDM confidence)

        Returns
        -------
        Dictionary with:
                'pe_sensory': Precision-weighted sensory PE
                'pe_state': State-level PE
                'mu_sensory': Updated sensory belief
                'mu_state': Updated state belief
                'volatility': Current volatility estimate (sigmoid of log_v)
                'precision_ratio': π_sensory / π_prior (ASD marker)
        """
        # Level 1: Sensory prediction error
        pe_sensory_raw = observation - self.mu_sensory
        pe_sensory_weighted = self.pi_sensory * pe_sensory_raw

        # Bayesian update of sensory belief
        # μ_posterior = (π_prior * μ_prior + π_likelihood * observation) / (π_prior + π_likelihood)
        total_precision = self.pi_sensory + observation_precision
        if total_precision > 0:
            self.mu_sensory = (
                self.pi_sensory * self.mu_sensory + observation_precision * observation
            ) / total_precision

        # Level 2: State prediction error (belief vs. sensory evidence)
        pe_state_raw = self.mu_sensory - self.mu_state
        pe_state_weighted = self.pi_state * pe_state_raw

        # Update state belief with adaptive learning rate
        learning_rate = self._adaptive_learning_rate()
        self.mu_state += learning_rate * pe_state_weighted

        # Level 3: Volatility estimation in log-variance space (HGF formalism)
        #
        # Predictive variance at this level, scaled by BASE_VAR:
        sigma2_hat = _BASE_VAR * np.exp(self.log_v)
        #
        # Dimensionless variance prediction error (VOPE):
        #   pe_state_raw² is empirical variance; σ²_hat is predicted variance.
        #   VOPE = (empirical - predicted) / predicted, analogous to a chi-sq residual.
        vope = (pe_state_raw**2) / sigma2_hat - 1.0
        #
        # Log-variance update (κ = learning_rate, halved for chi-sq scaling):
        self.log_v += (self.precision.learning_rate / 2.0) * vope
        self.log_v = float(np.clip(self.log_v, -5.0, 5.0))  # prevent overflow
        #
        # Display value in [0, 1] via sigmoid:
        self.mu_volatility = float(1.0 / (1.0 + np.exp(-self.log_v)))

        # Adjust precisions based on volatility
        self._update_precisions()

        # Log PE
        self.pe_history.append(
            {
                "pe_sensory": pe_sensory_weighted,
                "pe_state": pe_state_weighted,
                "observation": observation,
                "mu_sensory": self.mu_sensory,
                "mu_state": self.mu_state,
                "volatility": self.mu_volatility,
            }
        )

        return {
            "pe_sensory": float(pe_sensory_weighted),
            "pe_state": float(pe_state_weighted),
            "pe_total": float(pe_sensory_weighted + pe_state_weighted),
            "mu_sensory": float(self.mu_sensory),
            "mu_state": float(self.mu_state),
            "volatility": float(self.mu_volatility),
            "precision_ratio": float(self.pi_sensory / self.pi_state)
            if self.pi_state > 0
            else np.inf,
        }

    def _adaptive_learning_rate(self) -> float:
        """
        Adjust learning rate based on volatility estimate.

        High volatility → higher learning rate (faster adaptation to changes)
        Low volatility → lower learning rate (trust stable predictions)
        """
        return self.precision.learning_rate * (1.0 + self.mu_volatility)

    def _update_precisions(self):
        """
        Update precision parameters based on volatility.

        High volatility → reduce prior precision (predictions less reliable)
        Sensory precision stays closer to baseline (small volatility adjustment)
        """
        volatility_factor = 1.0 - 0.5 * self.mu_volatility
        self.pi_state = self.precision.prior_precision * volatility_factor
        self.pi_sensory = self.precision.sensory_precision * (1.0 - 0.2 * self.mu_volatility)

    def get_weighted_prediction_error(self, simulations: list[dict]) -> float:
        """
        Calculate precision-weighted PE across multiple simulations.

        Args
        ----
        simulations: List of simulation dicts with 'emotional_prediction' and 'confidence'

        Returns
        -------
        Precision-weighted mean PE
        """
        if not simulations:
            return 0.0

        total_weighted_pe = 0.0
        total_precision = 0.0

        for sim in simulations:
            sim_precision = sim.get("confidence", 0.5)
            sim_pe = abs(sim.get("schema_mismatch", 0.0))

            total_weighted_pe += sim_precision * sim_pe
            total_precision += sim_precision

        return total_weighted_pe / total_precision if total_precision > 0 else 0.0

    def reset(self):
        """Reset beliefs to initial state (e.g., for new episode)."""
        self.mu_sensory = 0.0
        self.mu_state = 0.0
        self.log_v = 0.0
        self.mu_volatility = 0.5
        self.pi_sensory = self.precision.sensory_precision
        self.pi_state = self.precision.prior_precision
        self.pi_volatility = self.precision.volatile_precision
        self.pe_history = []

    def get_state(self) -> dict[str, float]:
        """Get current state of the Bayesian PE system."""
        return {
            "mu_sensory": float(self.mu_sensory),
            "mu_state": float(self.mu_state),
            "log_v": float(self.log_v),
            "mu_volatility": float(self.mu_volatility),
            "pi_sensory": float(self.pi_sensory),
            "pi_state": float(self.pi_state),
            "pi_volatility": float(self.pi_volatility),
            "precision_ratio": float(self.pi_sensory / self.pi_state)
            if self.pi_state > 0
            else np.inf,
            "n_updates": len(self.pe_history),
        }
