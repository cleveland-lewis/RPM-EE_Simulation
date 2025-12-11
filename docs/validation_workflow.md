# Validation Workflow

This document outlines the workflow for validating the RPM-EE model.

## 1. Run Simulation

Run a simulation using the desired configuration.

```bash
python3.11 -m src.presets --preset-name default
```

## 2. Generate Validation Metrics

Use the `validation_metrics.py` script to generate validation metrics from the simulation output.

```bash
python3.11 -m src.validation_metrics --simulation-output results/.../simulation_data.csv
```

## 3. Create Report

The validation metrics script will generate a report in markdown format, which can be used for preregistration.
