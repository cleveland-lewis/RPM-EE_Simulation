# Getting Started with RPM-EE

This guide provides a walkthrough of the essential steps to get the RPM-EE model up and running.

## 1. Installation

First, ensure you have Python 3.11 or higher installed. Then, clone the repository and install the required dependencies.

```bash
git clone https://github.com/your-repo/RPM-EE.git
cd RPM-EE
pip install -r requirements.txt
```

## 2. Running a Basic Simulation

You can run a simulation using the presets.

```bash
python3.11 -m src.presets --preset-name default
```

## 3. Inspecting the Output

Simulation results are saved in the `results/` directory. Each run will have a unique timestamped folder containing the simulation data and configuration.
