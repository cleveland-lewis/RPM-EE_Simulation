"""
Global constants for RPM-EE simulation.

This module defines named constants to replace magic numbers throughout the codebase,
improving readability and maintainability. Constants are grouped by domain.
"""

# ============================================================================
# Memory System Constants
# ============================================================================

# Decay half-life values (in ticks)
HALF_LIFE_LOW_SALIENCE_MIN = 1200
HALF_LIFE_LOW_SALIENCE_MAX = 2400
HALF_LIFE_MID_SALIENCE_MIN = 2400
HALF_LIFE_MID_SALIENCE_MAX = 4800
HALF_LIFE_HIGH_SALIENCE_MIN = 4800
HALF_LIFE_HIGH_SALIENCE_MAX = 7200

# Salience thresholds
DEFAULT_LOW_SALIENCE_THRESHOLD = 0.5
DEFAULT_HIGH_SALIENCE_THRESHOLD = 0.8
DEFAULT_MIN_SALIENCE_FOR_CLEANUP = 0.1

# Similarity and matching
DEFAULT_SIMILARITY_THRESHOLD = 0.8

# Semanticization
MAX_BLEACH_COEFFICIENT = 0.8

# Consolidation
DEFAULT_CONSOLIDATION_THRESHOLD = 0.5
DEFAULT_CONSOLIDATION_BOOST_RATE = 0.1

# Capacity management
DEFAULT_CAPACITY_WEIGHT_SALIENCE = 0.7
DEFAULT_CAPACITY_WEIGHT_RECENCY = 0.3

# Jitter and modulation
DECAY_JITTER_MIN = -0.05
DECAY_JITTER_MAX = 0.05
MODULATION_CLIP_MIN = 0.5
MODULATION_CLIP_MAX = 2.0

# Event field defaults
DEFAULT_EVENT_DURATION = 0.1
DEFAULT_EVENT_INTENSITY = 0.1

# ============================================================================
# Replay and Arbiter Constants
# ============================================================================

# Arbiter weights and temperature
DEFAULT_ARBITER_ALPHA = 1.0
DEFAULT_ARBITER_BETA = 1.0
DEFAULT_ARBITER_GAMMA = 1.0
DEFAULT_SOFTMAX_TEMPERATURE = 1.0

# ============================================================================
# Simulation Constants
# ============================================================================

# Plotting and visualization
MAX_PLOT_POINTS = 10000

# Backend selection thresholds
JAX_TICK_THRESHOLD = 50000

# Sentinel values
NO_ATTUNEMENT_SENTINEL = -999.0

# ============================================================================
# Sensory System Constants
# ============================================================================

# State durations (in ticks)
DEFAULT_AWAKE_DURATION_MIN = 1000
DEFAULT_AWAKE_DURATION_MAX = 2000
DEFAULT_SLEEP_DURATION_MIN = 500
DEFAULT_SLEEP_DURATION_MAX = 1000

# Novelty and salience decay
NOVELTY_REDUCTION_FACTOR = 0.5
SALIENCE_REDUCTION_FACTOR = 0.85

# ============================================================================
# Validation and Metrics Constants
# ============================================================================

# Correlation thresholds
STRONG_CORRELATION_THRESHOLD = 0.7
MODERATE_CORRELATION_THRESHOLD = 0.5

# ICC thresholds
EXCELLENT_ICC_THRESHOLD = 0.9
GOOD_ICC_THRESHOLD = 0.75

# Model fit thresholds
LOW_RMSE_THRESHOLD = 0.1
ACCEPTABLE_RMSE_THRESHOLD = 0.2
