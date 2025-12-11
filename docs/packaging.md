# Packaging and Distribution

This document outlines the strategy for packaging and distributing RPM-EE as a reusable library and command-line interface (CLI).

## Library

The RPM-EE library will be packaged as a Python wheel and distributed on PyPI.

### Features

-   **Docstrings**: All public functions and classes will have comprehensive docstrings.
-   **Type Hints**: All public functions and classes will have type hints.
-   **Structured Documentation**: The documentation will be generated using Sphinx and hosted on Read the Docs.

## CLI

The CLI will be a wrapper around the `config/batch_runner.py` script, providing a user-friendly interface for running simulations from the command line.

### Installation

The CLI will be installable via pip:

```bash
pip install rpm-ee
```

### Usage

```bash
rpm-ee --preset-name default
```
