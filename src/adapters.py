# =============================================================================
# adapters.py - Real-Data Adapters for RPM-EE Validation
# =============================================================================
"""
This module provides data adapters that allow RPM-EE simulation to run in
"observation-conditioned mode" using real empirical data instead of synthetic
inputs. This is essential for model validation against behavioral, physiological,
and self-report measurements.

Key Components:
    1. DataAdapter protocol: Interface for custom data loaders
    2. EmpiricalDataAdapter: Main adapter for lab/EMA data
    3. Helper functions for time alignment and interpolation
    4. Observers for learned prediction error (Kalman, EMA)

References:
    - validation_protocol.md: Study 1 (Lab) and Study 2 (Ambulatory) specs
    - empirical_mapping.md: Variable measurement definitions
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Callable, Protocol
from pathlib import Path
import warnings


# =============================================================================
# Constants & Schema
# =============================================================================

ADAPTER_SCHEMA_VERSION = "1.0.0"

# Required columns for empirical data (minimum viable)
REQUIRED_COLUMNS = {
    'timestamp',  # Unix milliseconds or relative time from session start
}

# Optional columns (model will use defaults if missing)
OPTIONAL_COLUMNS = {
    'affect_valence',      # [-3, +3] or [-1, 1] (will normalize)
    'stress_rating',       # [0, 10] (will normalize to [0, 1])
    'arousal',             # [1, 7] (will normalize)
    'hrv_rmssd',           # ms (will inverse-normalize for stress proxy)
    'scl',                 # µS (will normalize for arousal proxy)
    'vision_load',         # [0, 1] stimulus intensity
    'auditory_load',       # [0, 1] stimulus intensity
    'touch_load',          # [0, 1] stimulus intensity
    'nback_accuracy',      # [0, 1] for memory load inference
    'nback_rt',            # ms for memory load inference
    'action_executed',     # Binary: 1=response, 0=omission
    'confidence_rating',   # [0, 100] (will normalize to [0, 1])
    'task_block',          # Integer block ID for segmentation
    'trial_number',        # Integer trial ID within block
}


# =============================================================================
# Data Adapter Protocol
# =============================================================================

class DataAdapter(Protocol):
    """
    Protocol (interface) for data adapters that supply observed time-series
    to RPM-EE simulation in observation-conditioned mode.

    Any custom adapter must implement these methods to be compatible with
    run_simulation(..., data_adapter=MyAdapter()).
    """

    def get_total_ticks(self) -> int:
        """Return total number of ticks (timepoints) in the dataset."""
        ...

    def get_affect_feedback(self, tick: int) -> float:
        """
        Return affect feedback (valence) at given tick.
        Range: [-1, 1] where -1=very negative, 0=neutral, +1=very positive.
        """
        ...

    def get_stress_rating(self, tick: int) -> Optional[float]:
        """
        Return self-reported stress at given tick (if available).
        Range: [0, 1] where 0=no stress, 1=extreme stress.
        Returns None if missing (model will impute).
        """
        ...

    def get_external_load(self, tick: int) -> Dict[str, float]:
        """
        Return modality-specific external loads at given tick.
        Returns dict with keys: 'vision', 'hearing', 'touch'.
        Each value in [0, 1] (normalized stimulus intensity).
        """
        ...

    def get_memory_load(self, tick: int) -> Optional[float]:
        """
        Return working memory load estimate at given tick (if available).
        Range: [0, 1] where 0=empty buffer, 1=at capacity.
        Returns None to use model's internal calculation.
        """
        ...

    def get_action_executed(self, tick: int) -> Optional[bool]:
        """
        Return observed action execution (response present) at given tick.
        Returns True if action executed, False if omission, None if N/A.
        This is used for validation (not to constrain the model).
        """
        ...

    def get_observation(self, tick: int) -> Dict[str, Any]:
        """Return a unified observation dict for the simulation loop."""
        ...


# =============================================================================
# Empirical Data Adapter (Main Implementation)
# =============================================================================

class EmpiricalDataAdapter:
    """
    Main data adapter for loading empirical data from CSV files (lab or EMA).

    Handles:
        - Time alignment (timestamp matching)
        - Missing data interpolation
        - Unit normalization (e.g., stress 0-10 → 0-1)
        - Downsampling/upsampling to match simulation tick rate

    Usage:
        adapter = EmpiricalDataAdapter.from_csv("participant_001.csv", tick_rate='1s')
        result = run_simulation(data_adapter=adapter, observed_mode=1)
    """

    def __init__(
        self,
        df: pd.DataFrame,
        tick_rate: str = '1s',
        interpolate_missing: bool = True,
        time_column: str = 'timestamp',
    ):
        """
        Initialize adapter from a pandas DataFrame.

        Parameters:
            df: DataFrame with time-stamped empirical data
            tick_rate: Tick interval (pandas freq string: '1s', '100ms', etc.)
            interpolate_missing: If True, linearly interpolate missing values
            time_column: Name of column containing timestamps
        """
        self.df_raw = df.copy()
        self.tick_rate = tick_rate
        self.time_column = time_column

        # Convert time column to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
            self.df_raw[time_column] = pd.to_datetime(df[time_column], unit='ms')

        # Resample to uniform tick rate
        self.df = self._resample_to_tick_rate(df, tick_rate, interpolate_missing)

        # Normalize units to model's expected ranges
        self._normalize_columns()

        # Precompute series for fast lookup
        self.total_ticks = len(self.df)
        self._precompute_series()

    def _resample_to_tick_rate(
        self,
        df: pd.DataFrame,
        tick_rate: str,
        interpolate: bool
    ) -> pd.DataFrame:
        """Resample data to uniform tick rate with optional interpolation."""
        df = df.set_index(self.time_column)
        df_resampled = df.resample(tick_rate).mean()  # Average within bins

        if interpolate:
            # Linear interpolation for missing values (max gap = 5 ticks)
            df_resampled = df_resampled.interpolate(
                method='linear',
                limit=5,
                limit_direction='both'
            )

        return df_resampled.reset_index()

    def _normalize_columns(self):
        """Normalize all columns to expected ranges."""
        # Affect: [-3, +3] or [-1, 1] → [-1, 1]
        if 'affect_valence' in self.df.columns:
            max_val = self.df['affect_valence'].abs().max()
            if max_val > 1.5:  # Likely [-3, +3] scale
                self.df['affect_valence'] = self.df['affect_valence'] / 3.0

        # Stress: [0, 10] → [0, 1]
        if 'stress_rating' in self.df.columns:
            max_stress = self.df['stress_rating'].max()
            if max_stress > 2.0:  # Likely [0, 10] scale
                self.df['stress_rating'] = self.df['stress_rating'] / 10.0

        # Arousal: [1, 7] → [0, 1]
        if 'arousal' in self.df.columns:
            if self.df['arousal'].min() >= 1.0:  # Likely [1, 7] scale
                self.df['arousal'] = (self.df['arousal'] - 1.0) / 6.0

        # Confidence: [0, 100] → [0, 1]
        if 'confidence_rating' in self.df.columns:
            max_conf = self.df['confidence_rating'].max()
            if max_conf > 2.0:  # Likely [0, 100] scale
                self.df['confidence_rating'] = self.df['confidence_rating'] / 100.0

        # HRV: ms → inverse-normalized stress proxy
        if 'hrv_rmssd' in self.df.columns:
            # Higher HRV → lower stress; use robust normalization
            median_hrv = self.df['hrv_rmssd'].median()
            mad_hrv = (self.df['hrv_rmssd'] - median_hrv).abs().median()
            self.df['hrv_stress_proxy'] = np.clip(
                1.0 - (self.df['hrv_rmssd'] - median_hrv) / (3 * mad_hrv + 1e-6),
                0.0, 1.0
            )

    def _precompute_series(self):
        """Precompute numpy arrays for fast tick-level access."""
        n = self.total_ticks

        # Affect
        self.affect_series = self.df['affect_valence'].fillna(0.0).values if 'affect_valence' in self.df else np.zeros(n)

        # Stress (use HRV proxy if rating missing)
        if 'stress_rating' in self.df.columns:
            self.stress_series = self.df['stress_rating'].fillna(0.5).values
        elif 'hrv_stress_proxy' in self.df.columns:
            self.stress_series = self.df['hrv_stress_proxy'].fillna(0.5).values
        else:
            self.stress_series = np.full(n, 0.5)  # Neutral default

        # External loads (modalities)
        self.vision_series = self.df['vision_load'].fillna(0.2).values if 'vision_load' in self.df else np.full(n, 0.2)
        self.auditory_series = self.df['auditory_load'].fillna(0.2).values if 'auditory_load' in self.df else np.full(n, 0.2)
        self.touch_series = self.df['touch_load'].fillna(0.1).values if 'touch_load' in self.df else np.full(n, 0.1)

        # Memory load (from N-back performance if available)
        if 'nback_accuracy' in self.df.columns and 'nback_rt' in self.df.columns:
            # Heuristic: load = (1 - accuracy) * normalized_RT
            acc = self.df['nback_accuracy'].fillna(0.7)
            rt_norm = (self.df['nback_rt'] - 400) / 1000  # Assume 400-1400ms range
            self.memory_load_series = ((1 - acc) * np.clip(rt_norm, 0, 1)).values
        else:
            self.memory_load_series = None  # Use model's internal calc

        # Action executed (observed)
        self.action_executed_series = self.df['action_executed'].values if 'action_executed' in self.df else None

    @classmethod
    def from_csv(
        cls,
        file_path: str | Path,
        tick_rate: str = '1s',
        interpolate_missing: bool = True,
        time_column: str = 'timestamp',
    ) -> 'EmpiricalDataAdapter':
        """
        Load empirical data from CSV file.

        Example CSV format:
            timestamp,affect_valence,stress_rating,vision_load,action_executed
            0,0.5,3,0.3,1
            1000,0.2,4,0.5,1
            2000,-0.1,5,0.4,0

        Parameters:
            file_path: Path to CSV file
            tick_rate: Tick interval ('1s', '100ms', etc.)
            interpolate_missing: Interpolate missing values
            time_column: Name of timestamp column

        Returns:
            EmpiricalDataAdapter instance
        """
        df = pd.read_csv(file_path)

        # Validate required columns
        if time_column not in df.columns:
            raise ValueError(f"Required column '{time_column}' not found in CSV")

        return cls(df, tick_rate, interpolate_missing, time_column)

    # Protocol implementation
    def get_total_ticks(self) -> int:
        return self.total_ticks

    def get_affect_feedback(self, tick: int) -> float:
        if 0 <= tick < self.total_ticks:
            return float(self.affect_series[tick])
        return 0.0

    def get_stress_rating(self, tick: int) -> Optional[float]:
        if 0 <= tick < self.total_ticks:
            return float(self.stress_series[tick])
        return None

    def get_external_load(self, tick: int) -> Dict[str, float]:
        if 0 <= tick < self.total_ticks:
            return {
                'vision': float(self.vision_series[tick]),
                'hearing': float(self.auditory_series[tick]),
                'touch': float(self.touch_series[tick]),
            }
        return {'vision': 0.2, 'hearing': 0.2, 'touch': 0.1}

    def get_memory_load(self, tick: int) -> Optional[float]:
        if self.memory_load_series is not None and 0 <= tick < self.total_ticks:
            return float(self.memory_load_series[tick])
        return None

    def get_action_executed(self, tick: int) -> Optional[bool]:
        if self.action_executed_series is not None and 0 <= tick < self.total_ticks:
            val = self.action_executed_series[tick]
            if pd.notna(val):
                return bool(val)
        return None

    def get_observation(self, tick: int) -> Dict[str, Any]:
        return {
            "avg_affect_feedback": self.get_affect_feedback(tick),
            "modality_loads": self.get_external_load(tick),
            "memory_load": self.get_memory_load(tick),
            "action_executed": self.get_action_executed(tick),
            "stress_rating": self.get_stress_rating(tick),
        }


# =============================================================================
# Prediction Error Observers (Learnable Models)
# =============================================================================

class PredictionErrorObserver:
    """
    Base class for prediction error observers that learn expectations
    from observed external load and compute trial-level surprise.

    This is essential for validation: we need PE computed from real stimuli,
    not synthetic inputs.
    """

    def update(self, observation: float) -> float:
        """
        Update observer with new observation and return prediction error.

        Parameters:
            observation: Observed external load at current tick [0, 1]

        Returns:
            Absolute prediction error: |observation - expectation|
        """
        raise NotImplementedError


class EMAObserver(PredictionErrorObserver):
    """
    Exponential Moving Average observer (simple delta-rule learner).

    PE_t = |x_t - μ_{t-1}|
    μ_t = μ_{t-1} + α * (x_t - μ_{t-1})

    This is the simplest learnable observer and aligns with the fast surprisal
    micro-loop in the RPM-EE model.
    """

    def __init__(self, learning_rate: float = 0.1, initial_estimate: float = 0.5):
        """
        Initialize EMA observer.

        Parameters:
            learning_rate: Step size α for EMA update (default 0.1)
            initial_estimate: Initial expectation μ_0 (default 0.5)
        """
        self.alpha = learning_rate
        self.mu = initial_estimate

    def update(self, observation: float) -> float:
        # Compute PE before updating
        pe = abs(observation - self.mu)
        # Update expectation
        self.mu += self.alpha * (observation - self.mu)
        return pe

    def reset(self):
        """Reset observer to initial state (for new block/session)."""
        self.mu = 0.5


class KalmanObserver(PredictionErrorObserver):
    """
    Kalman filter observer for external load prediction.

    Maintains Gaussian belief over external load with observation noise and
    process noise. More principled than EMA but requires tuning R and Q.

    Model:
        x_t = x_{t-1} + w_t        (process: random walk, w ~ N(0, Q))
        z_t = x_t + v_t            (observation: noisy measurement, v ~ N(0, R))
    """

    def __init__(
        self,
        process_noise: float = 0.01,
        observation_noise: float = 0.05,
        initial_estimate: float = 0.5,
        initial_uncertainty: float = 0.1,
    ):
        """
        Initialize Kalman observer.

        Parameters:
            process_noise: Process variance Q (how much true load drifts)
            observation_noise: Observation variance R (measurement noise)
            initial_estimate: Initial mean μ_0
            initial_uncertainty: Initial variance σ²_0
        """
        self.Q = process_noise
        self.R = observation_noise
        self.mu = initial_estimate
        self.sigma2 = initial_uncertainty

    def update(self, observation: float) -> float:
        # Predict step
        mu_pred = self.mu  # Random walk: x_t|t-1 = x_{t-1|t-1}
        sigma2_pred = self.sigma2 + self.Q

        # Compute PE (innovation) before update
        pe = abs(observation - mu_pred)

        # Update step
        K = sigma2_pred / (sigma2_pred + self.R)  # Kalman gain
        self.mu = mu_pred + K * (observation - mu_pred)
        self.sigma2 = (1 - K) * sigma2_pred

        return pe

    def reset(self):
        """Reset observer to initial state."""
        self.mu = 0.5
        self.sigma2 = 0.1


# =============================================================================
# Helper Functions
# =============================================================================

def align_model_to_empirical(
    model_logs: List[Dict],
    empirical_df: pd.DataFrame,
    time_column: str = 'timestamp',
    tolerance_ms: int = 500,
) -> pd.DataFrame:
    """
    Align model outputs to empirical timestamps for validation analyses.

    Returns merged DataFrame with both model and empirical columns,
    aligned by nearest timestamp (within tolerance).

    Parameters:
        model_logs: Output from run_simulation(...)['logs']
        empirical_df: DataFrame with empirical measurements
        time_column: Name of timestamp column in empirical_df
        tolerance_ms: Maximum time difference (ms) for matching

    Returns:
        Merged DataFrame with columns: timestamp, model_*, empirical_*
    """
    # Convert model logs to DataFrame
    model_df = pd.DataFrame(model_logs)

    # Add timestamps if not present (assume tick = millisecond or second)
    if 'timestamp' not in model_df.columns:
        if 'clock' in model_df.columns:
            model_df['timestamp'] = model_df['clock'] * 1000  # Assume ticks = ms
        else:
            raise ValueError("Model logs must have 'clock' or 'timestamp' column")

    # Ensure both have datetime timestamps
    model_df['timestamp'] = pd.to_datetime(model_df['timestamp'], unit='ms')
    if not pd.api.types.is_datetime64_any_dtype(empirical_df[time_column]):
        empirical_df = empirical_df.copy()
        empirical_df[time_column] = pd.to_datetime(empirical_df[time_column], unit='ms')

    # Merge on nearest timestamp (within tolerance)
    merged = pd.merge_asof(
        empirical_df.sort_values(time_column),
        model_df.sort_values('timestamp'),
        left_on=time_column,
        right_on='timestamp',
        direction='nearest',
        tolerance=pd.Timedelta(milliseconds=tolerance_ms),
        suffixes=('_empirical', '_model')
    )

    return merged


def compute_memory_load_from_nback(
    accuracy: float,
    rt: float,
    baseline_rt: float = 600.0,
    capacity: float = 1.0,
) -> float:
    """
    Infer working memory load from N-back trial performance.

    Heuristic: Load increases with errors and RT slowing.

    Parameters:
        accuracy: Trial accuracy (0 or 1 for binary; 0-1 for graded)
        rt: Response time (ms)
        baseline_rt: Expected RT for low-load trials (ms)
        capacity: Maximum load (default 1.0)

    Returns:
        Estimated memory load [0, 1]
    """
    # Error component
    error_load = 1.0 - accuracy

    # RT slowing component (normalized)
    rt_slowing = max(0.0, (rt - baseline_rt) / baseline_rt)
    rt_load = min(1.0, rt_slowing)

    # Weighted combination
    load = 0.6 * error_load + 0.4 * rt_load

    return float(np.clip(load, 0.0, capacity))


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    """
    Example: Load empirical data and prepare for observation-conditioned simulation.
    """
    import sys

    # Create synthetic example data
    n_ticks = 100
    example_df = pd.DataFrame({
        'timestamp': np.arange(n_ticks) * 1000,  # Milliseconds
        'affect_valence': np.sin(np.linspace(0, 4*np.pi, n_ticks)),  # Oscillating affect
        'stress_rating': np.clip(np.random.randn(n_ticks) * 2 + 5, 0, 10),  # Mean=5, SD=2
        'vision_load': np.random.rand(n_ticks) * 0.5 + 0.2,  # [0.2, 0.7]
        'action_executed': (np.random.rand(n_ticks) > 0.3).astype(int),  # 70% action rate
    })

    # Save example
    example_path = Path(__file__).parent.parent / 'docs' / 'example_empirical_data.csv'
    example_df.to_csv(example_path, index=False)
    print(f"Created example empirical data: {example_path}")

    # Load via adapter
    adapter = EmpiricalDataAdapter.from_csv(example_path, tick_rate='1s')
    print(f"\nAdapter initialized with {adapter.get_total_ticks()} ticks")

    # Test protocol methods
    print(f"Affect at tick 10: {adapter.get_affect_feedback(10):.3f}")
    print(f"Stress at tick 10: {adapter.get_stress_rating(10):.3f}")
    print(f"External load at tick 10: {adapter.get_external_load(10)}")

    # Test observers
    print("\n--- Testing Prediction Error Observers ---")
    ema_obs = EMAObserver(learning_rate=0.1)
    kalman_obs = KalmanObserver(process_noise=0.01, observation_noise=0.05)

    observations = [0.3, 0.5, 0.7, 0.5, 0.4, 0.6]
    print("Observation | EMA PE | Kalman PE")
    for obs in observations:
        pe_ema = ema_obs.update(obs)
        pe_kalman = kalman_obs.update(obs)
        print(f"{obs:.2f}        | {pe_ema:.3f}  | {pe_kalman:.3f}")

    print("\n✓ Adapters module working correctly")
