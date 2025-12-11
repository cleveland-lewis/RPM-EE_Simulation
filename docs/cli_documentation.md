# CLI Documentation

This document details the command-line interface for the RPM-EE model, focusing on the `batch_runner.py` script.

## `batch_runner.py`

The `batch_runner.py` script is the primary entry point for running simulations from the command line.

### Usage

```bash
python3.11 -m config.batch_runner [OPTIONS]
```

### Options

-   `--preset-name TEXT`: The name of the preset to use for the simulation.
-   `--num-runs INTEGER`: The number of simulation runs.
-   `--output-root TEXT`: The root directory for the simulation results.
-   `--help`: Show the help message and exit.

### Wizard

The batch runner includes an interactive wizard to guide you through the configuration process. To use it, run the script without any options.
