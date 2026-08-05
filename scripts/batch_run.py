#!/usr/bin/env python3
"""
Run src/main.py's simulation repeatedly and stop once the batch-level
distribution of run outcomes is plausibly normal (Shapiro-Wilk), so
downstream analyses that assume normality (e.g. parametric CIs) have a
justified sample rather than an arbitrary fixed batch count.

Each batch is one full RPMEESimulation run (same as `python src/main.py`);
the per-batch summary statistic is that run's mean episode accuracy
(unseeded, so batches vary run to run). Stops early once Shapiro-Wilk
p > ALPHA on the accumulated batch means, subject to MIN_BATCHES (the
user-requested floor) and MAX_BATCHES (standard large-sample cutoff,
beyond which the Central Limit Theorem makes the sampling distribution
of the mean normal regardless of Shapiro's verdict on the raw batches).
"""

import csv
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy.stats import shapiro

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from simulation import RPMEESimulation  # noqa: E402

EPISODES_PER_BATCH = 1000
MIN_BATCHES = 20
MAX_BATCHES = 30
ALPHA = 0.05

REPO_ROOT = Path(__file__).parent.parent
TERMINAL_PLOTS_SCRIPT = REPO_ROOT / "scripts" / "terminal_plots.R"


def run_batch(episodes: int, batch_num: int, episode_rows: list[dict]) -> float:
    sim = RPMEESimulation()
    for episode in range(episodes):
        sim.step()
        if episode % 100 == 0:
            print(f"    episode {episode}/{episodes}")
    for log in sim.logs:
        if log["accuracy"] is not None and log["rt_mean"] is not None:
            episode_rows.append(
                {
                    "batch": batch_num,
                    "episode": log.get("clock"),
                    "accuracy": log["accuracy"],
                    "rt_mean": log["rt_mean"],
                }
            )
    accuracies = [log["accuracy"] for log in sim.logs if log["accuracy"] is not None]
    return float(np.mean(accuracies)) if accuracies else float("nan")


def render_terminal_plots(episode_rows: list[dict]) -> None:
    """Export episode-level results to CSV and render ASCII plots via R."""
    rscript = shutil.which("Rscript")
    if rscript is None:
        print("\n(Rscript not found on PATH -- skipping terminal plots. Install R to enable them.)")
        return
    if not episode_rows:
        print("\n(no episode data collected -- skipping terminal plots.)")
        return

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["batch", "episode", "accuracy", "rt_mean"])
        writer.writeheader()
        writer.writerows(episode_rows)
        csv_path = f.name

    try:
        subprocess.run([rscript, str(TERMINAL_PLOTS_SCRIPT), csv_path], check=False)
    finally:
        Path(csv_path).unlink(missing_ok=True)


def main() -> int:
    batch_means = []
    episode_rows: list[dict] = []
    for i in range(1, MAX_BATCHES + 1):
        print(f"[batch {i}] running {EPISODES_PER_BATCH} episodes...")
        batch_means.append(run_batch(EPISODES_PER_BATCH, i, episode_rows))

        if i < MIN_BATCHES:
            continue

        stat, p = shapiro(batch_means)
        print(f"[batch {i}] Shapiro-Wilk on {i} batch means: W={stat:.3f} p={p:.3f}")
        if p > ALPHA:
            print(f"Stopping at {i} batches -- batch means not distinguishable from normal.")
            break
    else:
        print(
            f"Reached MAX_BATCHES={MAX_BATCHES} without a clean normality verdict; "
            f"stopping anyway (n={MAX_BATCHES} is large enough for CLT to apply)."
        )

    print(f"\n{len(batch_means)} batch means: {[round(m, 3) for m in batch_means]}")
    print(f"mean={np.mean(batch_means):.3f}  std={np.std(batch_means):.3f}")

    render_terminal_plots(episode_rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
