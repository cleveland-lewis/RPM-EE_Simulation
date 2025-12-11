# RPM-EE Architecture Overview

This document provides a high-level overview of the RPM-EE architecture, including the simulation core, batch runner, and validation framework.

## Core Components

The system is comprised of three main parts:

1.  **Simulation Core (`src/simulation.py`)**: The heart of the model, responsible for executing the cognitive simulation based on the provided configuration.
2.  **Batch Runner (`config/batch_runner.py`)**: A command-line interface for running multiple simulations with different configurations, facilitating experiments and parameter sweeps.
3.  **Validation Framework (`src/validation_metrics.py`)**: Tools for comparing simulation outputs against empirical data to validate the model's predictions.

## Interactions

The `batch_runner.py` script uses the `src/presets.py` to configure and run simulations via the `src/simulation.py` core. The outputs are then evaluated using the `src/validation_metrics.py`.
