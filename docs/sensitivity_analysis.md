# NC-MCM Sensitivity Analysis

This document outlines the process for conducting a sensitivity analysis of the NC-MCM model.

## Objective

The goal of this analysis is to understand how the model's output is affected by changes in its input parameters, particularly the priors and hyperparameters.

## Methodology

1.  **Identify Parameters**: Select the key parameters to be analyzed.
2.  **Define Ranges**: Specify the range of values to be tested for each parameter.
3.  **Run Simulations**: Execute a series of simulations, varying one parameter at a time while keeping the others constant.
4.  **Analyze Results**: Compare the simulation outputs to assess the impact of each parameter.
5.  **Document Findings**: Summarize the results and provide guidance on parameter tuning.

## Tools

The `config/batch_runner.py` script can be used to automate the execution of multiple simulations.
