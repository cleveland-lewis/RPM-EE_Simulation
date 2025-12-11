# Testing Strategy

This document outlines the testing strategy for RPM-EE.

## Test Suite

The test suite is divided into three parts:

-   **Unit Tests**: These test individual components in isolation.
-   **Integration Tests**: These test the interaction between multiple components.
-   **Regression Tests**: These test for regressions in the model's output.

## Continuous Integration

A CI pipeline is set up to run the test suite on every push to the main branch.

## Coverage

The test suite aims to cover the following areas:

-   Core simulation invariants (e.g., no NaNs, bounded variables).
-   Batch/grid behavior (e.g., reproducibility, pooling logic).
-   Validation metrics (e.g., regression tests on example datasets).
