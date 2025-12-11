"""
RPM-EE public API surface.

Only the names in `__all__` are considered stable for consumers of the library.
Everything else (including helper functions within modules) is internal and may
change without notice.
"""

__version__ = '1.1.0'

# Core simulation
from .simulation import parameter_sweep, fit_nc_mcm, run_simulation

# Presets and configuration helpers
from .presets import PRESETS, get_preset_params, list_presets

# Trial-based wrappers
from .trial_wrapper import DualTaskSimulator, TrialSimulator, quick_trial

# Components exposed for advanced use
from .arbiter import SimulationClusterArbiter
from .sensory import SensoryInputSystem

_VALIDATION_EXPORTS = [
    'compute_convergent_validity',
    'compute_hrv_stress_convergence',
    'compute_memory_load_prediction',
    'compute_action_execution_auc',
    'compute_confidence_correlation',
    'compute_discriminant_validity',
    'compute_icc',
    'compute_lapse_prediction',
    'compute_lagged_omission_prediction',
    'compute_all_endpoints',
    'generate_calibration_plot',
]

def __getattr__(name):
    """Lazily import validation metrics so optional deps (e.g., scikit-learn) are only required by consumers who use them."""
    if name in _VALIDATION_EXPORTS:
        from importlib import import_module
        return getattr(import_module('src.validation_metrics'), name)
    raise AttributeError(f"module 'src' has no attribute '{name}'")

__all__ = [
    # Core simulation
    'run_simulation',
    'parameter_sweep',
    'fit_nc_mcm',

    # Presets
    'PRESETS',
    'get_preset_params',
    'list_presets',

    # Trial wrappers
    'TrialSimulator',
    'DualTaskSimulator',
    'quick_trial',

    # Validation metrics
    *_VALIDATION_EXPORTS,

    # Components
    'SensoryInputSystem',
    'SimulationClusterArbiter',
]
