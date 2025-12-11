# Visualization Tooling

This document outlines the plotting and visualization tools available in RPM-EE.

## Available Plots

The following plotting functions are available in `src/visualization.py`:

-   **Time Series**: Plot the evolution of a variable over time.
-   **Histograms**: Visualize the distribution of a variable.
-   **ROC Curves**: Evaluate the performance of a binary classifier.

## Usage

To use these functions, import them from `src.visualization` and call them with your data.

```python
from src.visualization import plot_time_series

# Assuming 'data' is a pandas DataFrame with a 'time' column
plot_time_series(data, 'my_variable')
```

## Metadata

Plots are saved with metadata, including the version of the model and the parameters used to generate the data.
