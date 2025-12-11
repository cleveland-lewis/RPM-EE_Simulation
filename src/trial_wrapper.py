"""
Trial-based wrapper for RPM-EE simulation.

Converts continuous tick-based simulation into discrete trial units
for comparison with experimental cognitive tasks.
"""

import numpy as np
import math
import subprocess
from typing import Dict, List, Any, Optional, TypedDict, Tuple, Literal
import logging

__all__ = ['TrialSimulator', 'DualTaskSimulator', 'quick_trial']

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

class TrialResult(TypedDict, total=False):
    RT: float
    accuracy: float
    p_correct: float
    correct: bool
    action_executed: bool
    action_rate: float
    attunement_mean: float
    attunement_std: float
    attunement_final: float
    attunement_min: float
    attunement_max: float
    stress_mean: float
    stress_std: float
    ext_load_mean: float
    mem_load_mean: float
    aff_vol_mean: float
    replay_mode_counts: Dict[str, int]
    dominant_mode: str
    PE_mean: float
    PE_max: float
    confidence_mean: float
    trial_number: int
    duration: int
    stimulus: Dict[str, float]
    preset: str
    seed: Optional[int]
    git_commit: Optional[str]
try:
    from src.simulation import run_simulation
except ImportError:
    from simulation import run_simulation


class TrialSimulator:
    """
    Wrapper that runs RPM-EE simulation in discrete trials.

    Each trial:
    1. Runs simulation for fixed duration (default 200 ticks)
    2. Extracts aggregate metrics (mean attunement, action rate, etc.)
    3. Returns trial-level summary

    Usage:
        sim = TrialSimulator(preset='default')
        result = sim.run_trial(
            stimulus={'ext_load': 0.8, 'mem_load': 0.6},
            duration=200
        )
        print(result['RT'], result['accuracy'])
    """

    def __init__(
        self,
        preset: str = 'default',
        base_RT: float = 400.0,
        RT_scale: float = 600.0,
        RT_shape: float = 2.0,
        RT_scale_ex_gaussian: float = 50.0,
        seed: Optional[int] = None,
        enable_learning: bool = False,
        learning_rate: float = 0.1,
        **kwargs
    ):
        """
        Initialize trial simulator.

        Args:
            preset: Which preset to use ('default', 'asd_typical', etc.)
            base_RT: Baseline response time in ms (calibrated to ~400ms for simple tasks)
            RT_scale: RT range (base_RT to base_RT + RT_scale) (calibrated to ~1000ms max)
            RT_shape: Shape parameter for ex-Gaussian RT distribution (tau component)
            RT_scale_ex_gaussian: Scale parameter for exponential tail of RT distribution
            seed: Random seed for reproducibility
            enable_learning: Enable cross-trial learning and adaptation
            learning_rate: Rate of learning adaptation (0-1)
            **kwargs: Additional parameters passed to run_simulation
        """
        self.preset = preset
        self.base_RT = base_RT
        self.RT_scale = RT_scale
        self.RT_shape = RT_shape
        self.RT_scale_ex_gaussian = RT_scale_ex_gaussian
        self.base_seed = seed
        self.trial_count = 0
        self.base_kwargs = kwargs
        self.trial_history = []
        self._rng = np.random.default_rng(seed)

        # Learning and adaptation parameters
        self.enable_learning = enable_learning
        self.learning_rate = learning_rate
        self._accumulated_experience = 0.0
        self._recent_accuracy = 0.5  # Running estimate
        self._recent_RT = 700.0  # Running estimate

    def run_trial(
        self,
        stimulus: Dict[str, float],
        duration: int = 200,
        trial_seed: Optional[int] = None,
        **override_kwargs
    ) -> TrialResult:
        """Run a single trial and return aggregated results."""
        self.trial_count += 1
        self._validate_trial_inputs(stimulus, duration)

        use_seed = self._derive_seed(trial_seed)
        git_commit = self._git_commit()
        rng = self._local_rng(use_seed)

        sim_kwargs = self._build_sim_kwargs(stimulus, override_kwargs)
        result = run_simulation(
            total_ticks=duration,
            preset=self.preset,
            seed=use_seed,
            **sim_kwargs
        )

        logs = self._extract_logs(result)
        series = self._extract_series(logs, stimulus)
        trial_result = self._assemble_trial_result(
            series, stimulus, duration, use_seed, git_commit, rng
        )

        self.trial_history.append(trial_result)
        return trial_result

    def _validate_trial_inputs(self, stimulus: Dict[str, float], duration: int) -> None:
        if duration <= 0:
            raise ValueError("duration must be > 0")
        for k in ('ext_load_target','mem_load_target','volatility','schema_stress_bias'):
            if k in stimulus and not (0.0 <= float(stimulus[k]) <= 1.0):
                raise ValueError(f"{k} must be in [0,1], got {stimulus[k]}")
        if 'affect' in stimulus and not (-1.0 <= float(stimulus['affect']) <= 1.0):
            raise ValueError(f"affect must be in [-1,1], got {stimulus['affect']}")

    def _derive_seed(self, trial_seed: Optional[int]) -> Optional[int]:
        if trial_seed is not None:
            return trial_seed
        if self.base_seed is not None:
            return self.base_seed + self.trial_count
        return None

    def _build_sim_kwargs(self, stimulus: Dict[str, Any], override_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        sim_kwargs = {**self.base_kwargs, **override_kwargs}
        sim_kwargs.update(self._map_stimulus(stimulus, sim_kwargs))
        return sim_kwargs

    def _extract_logs(self, result: Any) -> List[Dict[str, Any]]:
        if isinstance(result, dict) and 'logs' in result:
            logs = result['logs']
        elif isinstance(result, list):
            logs = result
        else:
            raise ValueError(f"Unexpected result type: {type(result)}")
        if not logs:
            raise ValueError("Simulation returned empty logs")
        return logs

    def _extract_series(self, logs: List[Dict[str, Any]], stimulus: Dict[str, float]) -> Dict[str, np.ndarray]:
        attunement = np.array([log.get('attunement_score', 0.0) for log in logs])
        stress = np.array([log.get('schema_stress', 0.0) for log in logs])
        ext_load = np.array([log.get('ext_load', 0.0) for log in logs])
        mem_load = np.array([log.get('mem_load', 0.0) for log in logs])
        aff_vol = np.array([log.get('affect_volatility', 0.0) for log in logs])

        if 'difficulty' in stimulus:
            diff = float(np.clip(stimulus['difficulty'], 0.0, 1.0))
            ext_load = np.full_like(ext_load, diff, dtype=float)
            mem_load = np.full_like(mem_load, diff, dtype=float)

        return {
            'attunement': attunement,
            'stress': stress,
            'ext_load': ext_load,
            'mem_load': mem_load,
            'aff_vol': aff_vol,
            'actions': np.array([log.get('action_executed', False) for log in logs]),
            'prediction_error': np.array([log.get('prediction_error', 0.0) for log in logs]),
            'selection_conf': np.array([log.get('selection_confidence', 0.0) for log in logs]),
            'replay_modes': self._normalize_modes([log.get('replay_mode', 'unknown') for log in logs]),
        }

    def _assemble_trial_result(
        self,
        series: Dict[str, np.ndarray],
        stimulus: Dict[str, float],
        duration: int,
        seed: Optional[int],
        git_commit: Optional[str],
        rng: np.random.Generator,
    ) -> TrialResult:
        attunement = series['attunement']
        stress = series['stress']
        ext_load = series['ext_load']
        mem_load = series['mem_load']
        aff_vol = series['aff_vol']
        actions = series['actions']
        prediction_error = series['prediction_error']
        selection_conf = series['selection_conf']
        replay_modes = series['replay_modes']

        acc_value, p_correct, correct = self._compute_accuracy(attunement, stress, ext_load, mem_load, aff_vol, rng)
        return {
            'RT': self._compute_RT(attunement, stress, ext_load, mem_load, rng),
            'accuracy': acc_value,
            'p_correct': p_correct,
            'correct': bool(correct),
            'action_executed': bool(np.any(actions)),
            'action_rate': float(np.mean(actions)),
            'attunement_mean': float(np.mean(attunement)),
            'attunement_std': float(np.std(attunement)),
            'attunement_final': float(attunement[-1]),
            'attunement_min': float(np.min(attunement)),
            'attunement_max': float(np.max(attunement)),
            'stress_mean': float(np.mean(stress)),
            'stress_std': float(np.std(stress)),
            'ext_load_mean': float(np.mean(ext_load)),
            'mem_load_mean': float(np.mean(mem_load)),
            'aff_vol_mean': float(np.mean(aff_vol)),
            'replay_mode_counts': self._count_modes(replay_modes),
            'dominant_mode': self._dominant_mode(replay_modes),
            'PE_mean': float(np.mean(prediction_error)),
            'PE_max': float(np.max(prediction_error)),
            'confidence_mean': float(np.mean(selection_conf)),
            'trial_number': self.trial_count,
            'duration': duration,
            'stimulus': stimulus.copy(),
            'preset': self.preset,
            'seed': seed,
            'git_commit': git_commit,
        }

    def _git_commit(self) -> Optional[str]:
        """
        Return the current short git commit hash, or None if unavailable.
        """
        try:
            commit = subprocess.check_output(
                ['git', 'rev-parse', '--short', 'HEAD'],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            return commit or None
        except subprocess.CalledProcessError as e:
            logger.debug(f"Git command failed: {e}")
            return None
        except FileNotFoundError:
            logger.debug("Git executable not found.")
            return None
        except Exception as e:
            logger.debug(f"An unexpected error occurred while getting git commit: {e}")
            return None

    def _compute_RT(
        self,
        attunement: np.ndarray,
        stress: np.ndarray,
        ext_load: np.ndarray,
        mem_load: np.ndarray,
        rng: np.random.Generator
    ) -> float:
        """
        Compute response time from internal states using ex-Gaussian distribution.

        Core principle: RT inversely related to attunement
        - High attunement → fast RT
        - High load/stress → slow RT

        Uses ex-Gaussian distribution (convolution of Gaussian and exponential)
        which is empirically validated for RT data in cognitive psychology.

        Formula:
        - mu (Gaussian mean) = base + scale * (1 - attunement_eff)
        - sigma (Gaussian SD) = RT_shape
        - tau (exponential tail) = RT_scale_ex_gaussian

        Returns RT from ex-Gaussian(mu, sigma, tau) with learning adaptation.
        """
        mean_att = np.mean(attunement)
        mean_stress = np.mean(stress)
        mean_load = 0.5 * np.mean(ext_load) + 0.5 * np.mean(mem_load)

        # Load penalty reduces effective attunement
        load_penalty = 0.3 * mean_load + 0.2 * mean_stress
        attunement_eff = mean_att * (1.0 - load_penalty)
        attunement_eff = np.clip(attunement_eff, 0.01, 1.0)

        # Learning adaptation: reduce base RT with experience
        learning_bonus = 0.0
        if self.enable_learning and self.trial_count > 1:
            # Logarithmic learning curve (diminishing returns)
            learning_bonus = self.learning_rate * 50.0 * np.log(self.trial_count)

        # Ex-Gaussian parameters
        mu = self.base_RT + self.RT_scale * (1.0 - attunement_eff) - learning_bonus
        sigma = self.RT_shape
        tau = self.RT_scale_ex_gaussian

        # Sample from ex-Gaussian: Gaussian + Exponential
        gaussian_component = rng.normal(mu, sigma)
        exponential_component = rng.exponential(tau)
        RT = gaussian_component + exponential_component

        # Biologically plausible bounds [200, 3000]ms
        RT = np.clip(RT, 200, 3000)

        # Update running estimate for learning
        if self.enable_learning:
            self._recent_RT = (1 - self.learning_rate) * self._recent_RT + self.learning_rate * RT

        return float(RT)

    def _compute_accuracy(
        self,
        attunement: np.ndarray,
        stress: np.ndarray,
        ext_load: np.ndarray,
        mem_load: np.ndarray,
        aff_vol: np.ndarray,
        rng: np.random.Generator
    ) -> Tuple[float, float, bool]:
        """
        Compute accuracy from internal states using refined empirically-based formula.

        Core principle: Accuracy relates to sustained attunement
        - High stable attunement → high accuracy
        - High load/stress/volatility → low accuracy
        - Learning improves performance over trials

        Returns continuous probability p_correct based on attunement dynamics,
        calibrated to typical cognitive task performance (50-95% accuracy range).

        Returns:
            (accuracy_value, p_correct, correct)
            - accuracy_value: float, continuous probability of correct response [0,1]
            - p_correct: float, probability of correct response [0,1] (same as accuracy_value)
            - correct: bool, whether response was correct (stochastic outcome)
        """
        mean_att = np.mean(attunement)
        std_att = np.std(attunement)
        mean_stress = np.mean(stress)
        mean_load = 0.5 * np.mean(ext_load) + 0.5 * np.mean(mem_load)
        mean_vol = np.mean(aff_vol)

        # Base accuracy from mean attunement (scaled and shifted for typical performance)
        # Empirical calibration: even low attunement should allow ~50% chance performance
        base_acc = 0.5 + 0.45 * mean_att

        # Refined penalties based on cognitive psychology literature
        # Stress impairs performance more than load (Arnsten, 2009)
        stress_penalty = 0.35 * mean_stress
        load_penalty = 0.25 * mean_load
        volatility_penalty = 0.15 * mean_vol
        # Instability penalty: high variance in attunement indicates poor task engagement
        instability_penalty = 0.20 * std_att

        # Learning bonus: improved performance with practice
        learning_bonus = 0.0
        if self.enable_learning and self.trial_count > 1:
            # Logarithmic learning curve (diminishing returns, max +10%)
            learning_bonus = min(0.10, self.learning_rate * 0.15 * np.log(self.trial_count))

        # Compute continuous probability (return this as accuracy)
        accuracy = base_acc - stress_penalty - load_penalty - volatility_penalty - instability_penalty + learning_bonus
        p_correct = float(np.clip(accuracy, 0.0, 1.0))

        # Stochastic element (Bernoulli-like variability for binary outcome)
        correct = (rng.random() < p_correct)

        # Update running estimate for learning
        if self.enable_learning:
            self._recent_accuracy = (1 - self.learning_rate) * self._recent_accuracy + self.learning_rate * p_correct

        # Return continuous probability as accuracy (not binary)
        accuracy_value = float(p_correct)
        return accuracy_value, p_correct, correct

    def _local_rng(self, use_seed: Optional[int]) -> np.random.Generator:
        """
        Return a numpy random Generator for this trial.
        If use_seed is not None, returns a generator with that seed,
        else returns the simulator's base generator.
        """
        if use_seed is not None:
            return np.random.default_rng(use_seed)
        return self._rng

    def _map_stimulus(self, stimulus: Dict[str, float], sim_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate experimental stimulus into engine overrides *only if* the engine
        is configured to accept those keys. We avoid injecting unknown kwargs by
        intersecting with keys already present in sim_kwargs.

        Accepted conceptual inputs
        --------------------------
        ext_load_target, mem_load_target in [0,1]
        affect in [-1,1]
        volatility in [0,1]
        schema_stress_bias in [0,1]
        difficulty in [0,1]
        """
        def clip01(x: float) -> float:
            return float(np.clip(x, 0.0, 1.0))

        mapped: Dict[str, Any] = {}
        # Only map to keys the engine already expects (present in sim_kwargs)
        # This prevents TypeError from unknown **kwargs to run_simulation.
        if 'ext_load' in sim_kwargs and 'ext_load_target' in stimulus:
            mapped['ext_load'] = clip01(stimulus['ext_load_target'])
        if 'mem_load' in sim_kwargs and 'mem_load_target' in stimulus:
            mapped['mem_load'] = clip01(stimulus['mem_load_target'])
        if 'affect_tone' in sim_kwargs and 'affect' in stimulus:
            mapped['affect_tone'] = float(np.clip(stimulus['affect'], -1.0, 1.0))
        if 'affect_volatility' in sim_kwargs and 'volatility' in stimulus:
            mapped['affect_volatility'] = clip01(stimulus['volatility'])
        if 'schema_stress_bias' in sim_kwargs and 'schema_stress_bias' in stimulus:
            mapped['schema_stress_bias'] = clip01(stimulus['schema_stress_bias'])
        return mapped

    def _normalize_modes(self, modes: List[str]) -> List[str]:
        """Normalize replay mode labels to a canonical set."""
        canon = {
            'explore': 'explore', 'Explore': 'explore', 'EXPLORE': 'explore',
            'converge': 'converge', 'Converge': 'converge', 'CONVERGE': 'converge',
            'stabilize': 'stabilize', 'Stabilize': 'stabilize', 'STABILIZE': 'stabilize',
        }
        return [canon.get(str(m), 'unknown') for m in modes]

    def _count_modes(self, modes: List[str]) -> Dict[str, int]:
        """Count occurrences of each replay mode."""
        from collections import Counter
        counts = Counter(modes)
        return dict(counts)

    def _dominant_mode(self, modes: List[str]) -> str:
        """Find most frequent replay mode."""
        counts = self._count_modes(modes)
        if not counts:
            return 'unknown'
        return max(counts.items(), key=lambda x: x[1])[0]

    def run_experiment(
        self,
        trial_list: List[Dict[str, Any]],
        progress: bool = True
    ) -> List[TrialResult]:
        """
        Run multiple trials (full experiment).

        Args:
            trial_list: List of trial specifications, each with:
                        {'stimulus': {...}, 'duration': 200, ...}
            progress: Show progress bar (requires tqdm)

        Returns:
            List of TrialResult dicts, each including 'seed' and 'git_commit' for reproducibility.
        """
        results: List[TrialResult] = []

        iterator = trial_list
        if progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(trial_list, desc="Running trials")
            except ImportError:
                logger.warning("tqdm not installed. Install with 'pip install tqdm' to see progress bar.")
                pass

        for trial_spec in iterator:
            stimulus = trial_spec.get('stimulus', {})
            duration = trial_spec.get('duration', 200)
            kwargs = {k: v for k, v in trial_spec.items()
                     if k not in ['stimulus', 'duration']}

            result = self.run_trial(stimulus, duration, **kwargs)
            results.append(result)

        return results

    def reset(self):
        """Reset trial counter and history."""
        self.trial_count = 0
        self.trial_history = []

    def get_history(self) -> List[TrialResult]:
        """Get all trial results from history. Each TrialResult includes 'seed' and 'git_commit' for reproducibility."""
        return self.trial_history.copy()

    def summary_statistics(self) -> Dict[str, float]:
        """Compute summary statistics across all trials."""
        if not self.trial_history:
            return {}

        RTs = [t['RT'] for t in self.trial_history]
        accs = [t['accuracy'] for t in self.trial_history]
        atts = [t['attunement_mean'] for t in self.trial_history]

        return {
            'n_trials': len(self.trial_history),
            'mean_RT': float(np.mean(RTs)),
            'std_RT': float(np.std(RTs)),
            'mean_accuracy': float(np.mean(accs)),
            'std_accuracy': float(np.std(accs)),
            'mean_attunement': float(np.mean(atts)),
            'std_attunement': float(np.std(atts)),
        }


class DualTaskSimulator(TrialSimulator):
    """
    Specialized simulator for dual-task paradigms.

    Manipulates both external load (perceptual task) and
    memory load (cognitive task) simultaneously.
    """

    def create_trial_design(
        self,
        ext_load_levels: List[float] = [0.2, 0.5, 0.8],
        mem_load_levels: List[float] = [0.2, 0.5, 0.8],
        n_reps: int = 10,
        shuffle: bool = True,
        balanced_order: str = 'full'
    ) -> List[Dict]:
        """
        Create factorial design for dual-task experiment.

        Args:
            ext_load_levels: Levels of external load [0,1]
            mem_load_levels: Levels of memory load [0,1]
            n_reps: Number of repetitions per condition
            shuffle: Whether to shuffle the order of trials (deterministic using simulator seed)
            balanced_order: Placeholder for future block-wise balancing ('full', 'block', etc.)
                Currently only 'full' is supported.

        Returns:
            List of trial specifications for all combinations.
        """
        trials = []
        for ext in ext_load_levels:
            for mem in mem_load_levels:
                for rep in range(n_reps):
                    trials.append({
                        'stimulus': {
                            'ext_load_target': ext,
                            'mem_load_target': mem,
                            'condition': f'ext{ext:.1f}_mem{mem:.1f}'
                        },
                        'duration': 200
                    })
        # Deterministic shuffle using simulator seed
        if shuffle:
            rng = np.random.default_rng(self.base_seed or 0)
            rng.shuffle(trials)
        # balanced_order is a placeholder for future block-wise balancing
        return trials


# Convenience function
def quick_trial(
    preset: str = 'default',
    difficulty: float = 0.5,
    duration: int = 200,
    seed: Optional[int] = None
) -> TrialResult:
    """
    Quick single-trial simulation.

    Args:
        preset: Preset name
        difficulty: Overall difficulty [0,1]
        duration: Trial duration in ticks
        seed: Random seed

    Returns:
        TrialResult dict, including 'seed' and 'git_commit' for reproducibility.
    """
    sim = TrialSimulator(preset=preset, seed=seed)
    stimulus = {
        'ext_load_target': difficulty,
        'mem_load_target': difficulty,
    }
    return sim.run_trial(stimulus, duration)


# --- Analysis and export utilities ---

def results_to_dataframe(results: List[TrialResult]):
    """Return a pandas DataFrame from a list of trial results.
    Requires pandas.
    """
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("results_to_dataframe requires pandas. `pip install pandas`. ") from e
    # Normalize nested dicts like replay_mode_counts
    return pd.json_normalize(results, sep='.')


def save_results(results: List[TrialResult], path: str, fmt: Literal['csv', 'jsonl'] = 'csv') -> str:
    """Save trial results to CSV or JSONL. Returns the path written.
    - csv: tabular columns via pandas (requires pandas)
    - jsonl: one JSON object per line, no dependencies
    """
    if fmt == 'csv':
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError("CSV export requires pandas. `pip install pandas`. ") from e
        df = pd.json_normalize(results, sep='.')
        df.to_csv(path, index=False)
        return path
    elif fmt == 'jsonl':
        import json
        with open(path, 'w', encoding='utf-8') as f:
            for row in results:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
        return path
    else:
        raise ValueError("fmt must be 'csv' or 'jsonl'")


# --- RT Distribution Validation Utilities ---

def fit_exgaussian(RTs: np.ndarray) -> Dict[str, float]:
    """
    Fit ex-Gaussian distribution to RT data using method of moments.

    The ex-Gaussian is the convolution of a Gaussian(mu, sigma) and
    Exponential(tau). This function estimates the three parameters:
    - mu: Gaussian mean
    - sigma: Gaussian SD
    - tau: Exponential scale (controls right tail)

    Args:
        RTs: Array of response times (in ms)

    Returns:
        Dict with keys: mu, sigma, tau, mean_RT, sd_RT, skew_RT

    References:
        Heathcote et al. (1991). Analysis of response time distributions:
        An example using the Stroop task. Psychological Bulletin, 109(2), 340.
    """
    RTs = np.asarray(RTs)
    if len(RTs) < 3:
        raise ValueError("Need at least 3 RTs for fitting")

    # Compute empirical moments
    mean_RT = float(np.mean(RTs))
    var_RT = float(np.var(RTs, ddof=1))
    sd_RT = float(np.std(RTs, ddof=1))

    # Skewness (use scipy if available, else compute manually)
    try:
        from scipy.stats import skew
        skew_RT = float(skew(RTs, bias=False))
    except ImportError:
        # Manual skewness calculation (unbiased)
        n = len(RTs)
        m3 = np.mean((RTs - mean_RT)**3)
        skew_RT = (n / ((n-1) * (n-2))) * (m3 / sd_RT**3) if n > 2 else 0.0

    # Method of moments estimation
    # For ex-Gaussian: mean = mu + tau, var = sigma^2 + tau^2, skew = 2*tau^3 / (sigma^2 + tau^2)^(3/2)

    # Estimate tau from skewness (if skew > 0)
    if skew_RT > 0.01:
        # Solve: skew = 2*tau^3 / var^(3/2)
        tau = np.cbrt((skew_RT * var_RT**(3/2)) / 2.0)
    else:
        tau = 0.0  # No tail

    # Estimate sigma^2 from variance
    sigma_sq = max(0.0, var_RT - tau**2)
    sigma = np.sqrt(sigma_sq)

    # Estimate mu from mean
    mu = mean_RT - tau

    return {
        'mu': float(mu),
        'sigma': float(sigma),
        'tau': float(tau),
        'mean_RT': mean_RT,
        'sd_RT': sd_RT,
        'skew_RT': float(skew_RT)
    }


def validate_rt_distribution(
    results: List[TrialResult],
    show_plot: bool = False,
    save_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate RT distribution against ex-Gaussian model.

    Args:
        results: List of trial results
        show_plot: Whether to display diagnostic plots
        save_path: Path to save plot (if None, no save)

    Returns:
        Dict with fit parameters and goodness-of-fit metrics
    """
    RTs = np.array([r['RT'] for r in results])

    if len(RTs) < 10:
        raise ValueError("Need at least 10 trials for meaningful validation")

    # Fit ex-Gaussian
    fit_params = fit_exgaussian(RTs)

    # Generate diagnostic plot if requested
    if show_plot or save_path:
        try:
            import matplotlib
            matplotlib.use('Agg')  # Headless backend
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(1, 3, figsize=(15, 4))

            # Histogram with density
            axes[0].hist(RTs, bins=30, density=True, alpha=0.6, edgecolor='black', label='Observed')
            axes[0].set_xlabel('Response Time (ms)')
            axes[0].set_ylabel('Density')
            axes[0].set_title('RT Distribution')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)

            # Q-Q plot (quantile-quantile)
            axes[1].scatter(np.arange(len(RTs)) / len(RTs), np.sort(RTs), alpha=0.5)
            axes[1].set_xlabel('Theoretical Quantiles')
            axes[1].set_ylabel('Sample Quantiles (RT ms)')
            axes[1].set_title('Q-Q Plot')
            axes[1].grid(True, alpha=0.3)

            # Summary statistics
            info_text = f"""Ex-Gaussian Fit:

μ = {fit_params['mu']:.1f} ms
σ = {fit_params['sigma']:.1f} ms
τ = {fit_params['tau']:.1f} ms

Empirical:
Mean = {fit_params['mean_RT']:.1f} ms
SD = {fit_params['sd_RT']:.1f} ms
Skew = {fit_params['skew_RT']:.2f}"""

            axes[2].text(0.1, 0.5, info_text, fontsize=10, family='monospace',
                        verticalalignment='center')
            axes[2].axis('off')
            axes[2].set_title('Fit Parameters')

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')

            if not show_plot:
                plt.close(fig)

        except ImportError:
            logger.warning("Matplotlib not installed. Skipping RT distribution plot.")
            pass  # Skip plotting if matplotlib unavailable

    return {
        'fit_params': fit_params,
        'n_trials': len(RTs),
        'RT_range': (float(np.min(RTs)), float(np.max(RTs))),
        'RT_median': float(np.median(RTs))
    }
