# NC-MCM Fitting Workflow

This document outlines the workflow for fitting the NC-MCM model to data.

## 1. Prepare Data

The first step is to prepare the data in the correct format. The data should be a CSV file with columns for the subject ID, the trial number, and the observed data.

## 2. Run Fitting Script

The `fit_nc_mcm.py` script is used to fit the model to the data.

```bash
python3.11 -m src.fit_nc_mcm --data-file path/to/your/data.csv
```

## 3. Inspect Results

The script will output a set of files containing the fitted model, posterior predictive checks, and diagnostic plots. These can be used to assess the quality of the fit.
