# Simulation API

This document details the API for the RPM-EE simulation core.

## `run_simulation`

The main entry point for running a simulation.

### Parameters

-   `config`: A `SimulationConfig` object containing the simulation parameters.
-   `preset_name`: The name of a preset to use.
-   `seed`: The random seed for the simulation.

### Returns

A dictionary containing the simulation results, including logs, stats, and diagnostics.

## `parameter_sweep`

Runs a parameter sweep over a given set of parameters.

### Parameters

-   `parameters`: A dictionary of parameters to sweep.
-   `config`: A base `SimulationConfig` object.

### Returns

A list of simulation results.

## `fit_nc_mcm`

Fits the NC-MCM model to the simulation data.

### Parameters

-   `data`: The simulation data to fit the model to.

### Returns

The fitted model.
