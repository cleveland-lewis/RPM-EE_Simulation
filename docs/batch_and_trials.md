# Batch Runner and Trial Simulators

This document provides an overview of the batch runner and trial simulators in RPM-EE.

## Batch Runner

The batch runner (`config/batch_runner.py`) allows you to run multiple simulations with different configurations.

### Features

-   **Grid Search**: Automatically run simulations for all combinations of a set of parameters.
-   **Reproducibility**: Each run is executed with a specific seed to ensure reproducibility.
-   **Logging**: All results are logged to a specified output directory.

## Trial Simulators

The trial simulators (`src/trial_wrapper.py`) provide a framework for running trial-based experiments.

### `TrialSimulator`

The `TrialSimulator` runs a single trial and returns the results.

### `DualTaskSimulator`

The `DualTaskSimulator` runs a dual-task experiment, where the participant performs two tasks simultaneously.

## Configuration

Both the batch runner and the trial simulators are configured using a `SimulationConfig` object.
