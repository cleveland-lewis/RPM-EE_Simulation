"""
Drift-Diffusion Model with EZ-Diffusion Parameter Recovery

Maps observable clinical statistics (mean RT, RT variance, accuracy)
to theoretically grounded DDM parameters (v, a, Ter) via the EZ-diffusion
equations (Wagenmakers et al., 2007). This replaces the prior ad-hoc
mappings (fixed v = 0.35; a = 0.2 + arbitrary heuristic).

References:
- Ratcliff, R., & McKoon, G. (2008). The diffusion decision model: Theory and
  data for two-choice decision tasks. Neural Computation, 20(4), 873-922.
- Wagenmakers, E.-J., van der Maas, H. L. J., & Grasman, R. P. P. P. (2007).
  An EZ-diffusion model for response time and accuracy.
  Psychonomic Bulletin & Review, 14(1), 3-22.
  (Closed-form algebraic recovery of v, a, Ter from MRT, VRT, Pc.)
- Bogacz et al. (2006). The physics of optimal decision making.
  Psychological Review, 113(4), 700-765.

EZ-diffusion parameter recovery (s = 0.1 fixed, Ratcliff convention):
    L   = logit(Pc)
    v   = sign(Pc − 0.5) · s · [L · (Pc²L − PcL + Pc − 0.5) / VRT]^(1/4)
    a   = s² · L / v
    MDT = (a/2v) · tanh(va / (2s²))        [mean decision time]
    Ter = MRT − MDT                         [non-decision time]

where:
    Pc  = base_accuracy (proportion correct)
    MRT = base_rt · rt_slowing / 1000       (seconds)
    VRT = (MRT · rt_variability)²           (seconds²)

Clinical differentiation emerges from parameter recovery, not from
ad-hoc constants:
    NT   → moderate v, moderate a (balanced speed-accuracy)
    MDD  → lower v (psychomotor slowing → weaker evidence accumulation)
    ADHD → lower v (noise-dominated) + smaller a (impulsive boundary)
    ASD  → moderate v, slight reduction from rt_slowing
"""

import numpy as np
from typing import Dict, Optional


class DriftDiffusionModel:
    """
    DDM with EZ-diffusion algebraic parameter recovery.

    Internal DDM parameters (v, a, Ter) are derived from observable clinical
    statistics using Wagenmakers et al. (2007). The within-trial noise s is
    fixed at 0.1 (Ratcliff's scaling convention) for identifiability.

    The simulation loop uses 1 ms time steps with parameters scaled to ms:
        drift per step  = v · dt_s          (dt_s = 0.001 s)
        noise per step  = s · √dt_s         (Euler-Maruyama)
        boundary        = a / 2             (symmetric ±a/2 around zero)

    Parameters:
        base_rt (float): Target mean RT in milliseconds.
        rt_variability (float): Target coefficient of variation (CV) of RT.
        rt_slowing (float): Multiplicative RT slowing factor (≥ 1.0).
        base_accuracy (float): Baseline proportion correct (Pc).
        accuracy_decline (float): Reduction in Pc per unit of cognitive load.
        random_seed (int, optional): Seed for reproducibility.
    """

    # EZ-diffusion noise parameter (Ratcliff scaling convention)
    _S = 0.1
    # Time step for Euler-Maruyama simulation (seconds)
    _DT_S = 0.001
    # Maximum decision time before timeout (ms)
    _MAX_TIME_MS = 5000.0
    # Physiological RT floor (ms)
    _RT_FLOOR_MS = 100.0
    # Minimum non-decision time (encoding + motor response), seconds.
    # Standard EZ-diffusion (Wagenmakers et al., 2007) attributes *all*
    # trial-to-trial RT variance to decision-time noise, since it assumes
    # no across-trial variability in drift rate or non-decision time. For
    # presets with high target rt_variability (e.g. adhd_typical, CV=0.45,
    # per Klein et al. 2006 / Kofler et al. 2013), the only way the
    # closed-form solution can generate that much variance is by shrinking
    # Ter toward zero -- a mathematical artifact of the recovery equations,
    # not a real claim about non-decision time. 300 ms reflects typical
    # encoding+motor estimates in two-choice RT tasks (Ratcliff & McKoon,
    # 2008) and is applied uniformly across presets, since no preset's
    # evidence base makes a specific claim about non-decision time itself
    # (see GitHub issue #6). v and a are derived from Pc/VRT only and are
    # unaffected by this floor; when it binds, simulated mean RT will run
    # above the preset's literal base_rt target rather than silently
    # producing an implausibly fast (or cross-preset-inverted) Ter.
    _TER_FLOOR_S = 0.30

    def __init__(
        self,
        base_rt: float = 500.0,
        rt_variability: float = 0.15,
        rt_slowing: float = 1.0,
        base_accuracy: float = 0.90,
        accuracy_decline: float = 0.05,
        random_seed: Optional[int] = None
    ):
        self.rng = np.random.default_rng(random_seed)

        # Clinical parameters (stored for inspection / drift correction)
        self.base_rt = base_rt
        self.rt_variability = rt_variability
        self.rt_slowing = rt_slowing
        self.base_accuracy = base_accuracy
        self.accuracy_decline = accuracy_decline

        # Recover DDM parameters via EZ-diffusion
        self._configure_ddm()

    # ------------------------------------------------------------------
    # EZ-diffusion parameter recovery
    # ------------------------------------------------------------------

    def _configure_ddm(self):
        """
        Algebraically recover v, a, Ter from target behavioral statistics.

        Equations from Wagenmakers et al. (2007), Appendix:
            L   = logit(Pc)
            v   = sign(Pc − 0.5) · s · [L(Pc²L − PcL + Pc − 0.5) / VRT]^(1/4)
            a   = s² · L / v
            Ter = MRT − (a/2v) · tanh(va/(2s²))

        After recovery, parameters are converted to 1 ms time-step scale for
        the simulation loop (drift and noise per step; boundary = a/2).
        """
        s = self._S

        # Target statistics
        MRT = self.base_rt * self.rt_slowing / 1000.0   # seconds
        VRT = (MRT * self.rt_variability) ** 2           # seconds²
        # Clip Pc away from singularities at 0 and 1
        Pc = float(np.clip(self.base_accuracy, 0.501, 0.999))

        # Logit of proportion correct
        L = np.log(Pc / (1.0 - Pc))

        # Drift rate recovery
        # Argument under the 4th-root must be non-negative.
        inner = L * (Pc**2 * L - Pc * L + Pc - 0.5) / VRT
        inner = max(inner, 1e-12)
        self.v = float(np.sign(Pc - 0.5) * s * (inner ** 0.25))

        # Boundary separation (full width in Wagenmakers' notation)
        # Guard against v ≈ 0 to prevent division by zero.
        if abs(self.v) < 1e-6:
            # v → 0 limit: a² = 2 · s² · VRT  (from L'Hôpital on variance formula)
            self.a = float(s * np.sqrt(2.0 * VRT))
        else:
            self.a = float(s**2 * L / self.v)
        self.a = max(self.a, 0.01)  # physical minimum boundary

        # Mean decision time and non-decision time
        MDT = self._mean_decision_time(self.v, self.a, s)
        self.Ter = float(max(self._TER_FLOOR_S, MRT - MDT))  # see _TER_FLOOR_S docstring

        # Derived simulation-loop parameters (1 ms = 0.001 s time steps)
        dt_s = self._DT_S
        self.v_per_step = self.v * dt_s             # drift per 1 ms step
        self.s_per_step = s * np.sqrt(dt_s)         # noise std per 1 ms step
        self.boundary = self.a / 2.0                # symmetric ±boundary

        # Store fixed noise for get_parameters() compatibility
        self.s = s

    @staticmethod
    def _mean_decision_time(v: float, a: float, s: float) -> float:
        """
        Compute mean decision time for a symmetric DDM.

        MDT = (a / 2v) · tanh(va / (2s²))

        Uses tanh for numerical stability (avoids exp overflow).
        Handles v → 0 limit via the small-angle approximation.
        """
        if abs(v) < 1e-6:
            # Limit: tanh(x)/x → 1 as x → 0  ⟹  MDT → a² / (2 s²)
            return float(a**2 / (2.0 * s**2))
        arg = v * a / (2.0 * s**2)
        return float((a / (2.0 * v)) * np.tanh(arg))

    # ------------------------------------------------------------------
    # Trial simulation
    # ------------------------------------------------------------------

    # Fraction by which drift is attenuated at difficulty=1.0. Kept < 1 so
    # accumulation never fully stalls (avoids pathological RT at the
    # timeout ceiling for maximally-difficult trials).
    _MAX_DIFFICULTY_DRIFT_ATTENUATION = 0.7

    def predict_action(
        self,
        evidence: float,
        load: float = 0.0,
        difficulty: float = 0.0
    ) -> Dict:
        """
        Run a single DDM trial.

        `load` and `difficulty` are deliberately separate axes -- they were
        conflated in earlier versions (see GitHub issue #6), which inverted
        the RT ordering for harder task conditions. See README.md, section
        "DDM load vs. difficulty", for the full rationale.

            load:       reduces the effective accuracy target -> shrinks the
                         decision boundary -> FASTER, less accurate responses.
                         A speed-under-pressure / WM-interference account.
                         Use for genuine working-memory or time-pressure load.
            difficulty: attenuates the drift rate directly -> weaker/noisier
                         momentary evidence -> SLOWER, less accurate
                         responses. A stimulus/task-difficulty account. Use
                         for harder discriminations, more distractors, more
                         complex search -- anything where a real participant
                         takes longer, not less time, to resolve.

        Args:
            evidence: Evidence strength and direction in [−1, 1].
                      Positive → 'approach', negative → 'withdraw'.
            load: Cognitive/WM load in [0, 1] (reduces effective boundary).
            difficulty: Task/stimulus difficulty in [0, 1] (reduces drift).

        Returns:
            Dict with keys:
                'action'    : 'approach' or 'withdraw'
                'rt'        : reaction time (ms), ≥ RT_FLOOR_MS
                'accurate'  : bool | None (None for neutral evidence)
                'confidence': float in [0, 1]
                'evidence'  : original evidence
                'load'      : original load
                'difficulty': original difficulty
        """
        # Load reduces the effective accuracy target → smaller boundary
        effective_Pc = float(np.clip(
            self.base_accuracy - load * self.accuracy_decline, 0.501, 0.999
        ))
        # Recompute boundary for effective accuracy
        if abs(self.v) > 1e-6:
            L_eff = np.log(effective_Pc / (1.0 - effective_Pc))
            a_eff = float(max(0.01, self._S**2 * L_eff / self.v)) / 2.0
        else:
            a_eff = self.boundary  # fallback

        # Evidence scales the drift rate (direction + magnitude)
        if abs(evidence) <= 0.01:
            evidence_scaled = 0.01 * np.sign(evidence) if evidence != 0 else 0.01
        else:
            evidence_scaled = evidence

        # Difficulty attenuates drift directly (weaker/noisier evidence
        # accumulation), independent of the boundary/load mechanism above.
        difficulty_clamped = float(np.clip(difficulty, 0.0, 1.0))
        drift_attenuation = 1.0 - self._MAX_DIFFICULTY_DRIFT_ATTENUATION * difficulty_clamped

        effective_v_step = self.v_per_step * evidence_scaled * drift_attenuation

        # Euler-Maruyama accumulation until boundary or timeout
        x = 0.0
        t = 0.0
        while abs(x) < a_eff and t < self._MAX_TIME_MS:
            x += effective_v_step + self.rng.normal(0.0, self.s_per_step)
            t += 1.0  # 1 ms per step

        # Decision
        if t >= self._MAX_TIME_MS:
            choice_upper = bool(self.rng.random() > 0.5)
            rt_decision = t
            confidence = 0.5
        else:
            choice_upper = x >= a_eff
            rt_decision = t
            # Confidence: fractional overshoot (small for weak signal, ~1 for strong)
            confidence = float(min(1.0, abs(x) / a_eff))

        action = 'approach' if choice_upper else 'withdraw'

        # Accuracy: None for neutral evidence (no correct answer defined)
        if abs(evidence) <= 0.01:
            correct = None
        else:
            correct = (evidence > 0 and choice_upper) or (evidence < 0 and not choice_upper)

        # Total RT = decision time (ms) + non-decision time (ms)
        rt = rt_decision + self.Ter * 1000.0
        rt = max(self._RT_FLOOR_MS, rt)

        return {
            'action': action,
            'rt': round(rt, 2),
            'accurate': correct,
            'confidence': round(confidence, 3),
            'evidence': round(evidence, 3),
            'load': round(load, 3),
            'difficulty': round(difficulty_clamped, 3)
        }

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def get_parameters(self) -> Dict[str, float]:
        """Return clinical inputs and EZ-recovered DDM parameters."""
        return {
            # Clinical inputs
            'base_rt': self.base_rt,
            'rt_variability': self.rt_variability,
            'rt_slowing': self.rt_slowing,
            'base_accuracy': self.base_accuracy,
            'accuracy_decline': self.accuracy_decline,
            # EZ-recovered DDM parameters
            'v': round(self.v, 4),
            'a': round(self.a, 4),
            'Ter': round(self.Ter * 1000.0, 2),  # display in ms
            's': round(self.s, 4),
            'boundary': round(self.boundary, 4),
        }
