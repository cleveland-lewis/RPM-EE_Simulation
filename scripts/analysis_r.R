#!/usr/bin/env Rscript
# Analysis workflow for RPM-EE simulation results, companion to the Python
# pipeline (GitHub issue #24, "Option A": separate Python + R analysis
# tracks, joined only by the CSV/JSON export in src/analysis/export_results_for_r.py).
#
# Usage:
#   Rscript scripts/analysis_r.R [path/to/rpm_ee_results.csv] [output_dir]
#
# Defaults:
#   input      results/export/rpm_ee_results.csv
#   output_dir results/r_analysis
#
# Expected input schema (produced by
# `python -m analysis.export_results_for_r`, see docs/analysis_r.md):
#   preset, rt_mean, rt_std, accuracy, plus other per-episode log fields.
# Rows with NA rt_mean/accuracy (neutral-evidence episodes -- see
# src/ddm.py's predict_action docstring) are dropped before summarizing.

suppressMessages({
  library(tidyverse)
})

args <- commandArgs(trailingOnly = TRUE)
input_path <- if (length(args) >= 1) args[[1]] else "results/export/rpm_ee_results.csv"
output_dir <- if (length(args) >= 2) args[[2]] else "results/r_analysis"

if (!file.exists(input_path)) {
  stop(sprintf(
    "Input file not found: %s\nExport it first with:\n  python -m analysis.export_results_for_r --input <run.json> --output_csv %s",
    input_path, input_path
  ))
}

dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)

data <- read_csv(input_path, show_col_types = FALSE) %>%
  filter(!is.na(rt_mean), !is.na(accuracy))

if (nrow(data) == 0) {
  stop("No rows with non-NA rt_mean/accuracy in the input -- nothing to analyze.")
}

# ---------------------------------------------------------------------------
# 1. Summary statistics by preset
# ---------------------------------------------------------------------------
summary_by_preset <- data %>%
  group_by(preset) %>%
  summarise(
    n = n(),
    rt_mean_avg = mean(rt_mean),
    rt_mean_sd = sd(rt_mean),
    accuracy_avg = mean(accuracy),
    accuracy_sd = sd(accuracy),
    .groups = "drop"
  )

print(summary_by_preset)
write_csv(summary_by_preset, file.path(output_dir, "summary_by_preset.csv"))

# ---------------------------------------------------------------------------
# 2. RT and accuracy distributions by preset
# ---------------------------------------------------------------------------
rt_plot <- ggplot(data, aes(x = rt_mean, fill = preset)) +
  geom_histogram(alpha = 0.6, position = "identity", bins = 30) +
  labs(
    title = "RT distribution by clinical preset",
    x = "Mean RT per episode (ms)", y = "Count"
  ) +
  theme_minimal()
ggsave(file.path(output_dir, "rt_distribution_by_preset.png"), rt_plot, width = 8, height = 5)

accuracy_plot <- ggplot(data, aes(x = preset, y = accuracy, fill = preset)) +
  geom_boxplot(alpha = 0.7) +
  labs(
    title = "Accuracy distribution by clinical preset",
    x = "Preset", y = "Accuracy"
  ) +
  theme_minimal() +
  theme(legend.position = "none")
ggsave(file.path(output_dir, "accuracy_distribution_by_preset.png"), accuracy_plot, width = 8, height = 5)

# ---------------------------------------------------------------------------
# 3. Effect-size / calibration plot
#
# Cohen's d for each non-baseline preset's rt_mean and accuracy relative to
# the neurotypical baseline -- summarizes clinical differentiation at a
# glance rather than requiring a reader to compare raw distributions.
# ---------------------------------------------------------------------------
BASELINE_PRESET <- "neurotypical"

cohens_d <- function(x, y) {
  nx <- length(x)
  ny <- length(y)
  pooled_sd <- sqrt(((nx - 1) * var(x) + (ny - 1) * var(y)) / (nx + ny - 2))
  if (pooled_sd == 0 || is.na(pooled_sd)) {
    return(NA_real_)
  }
  (mean(x) - mean(y)) / pooled_sd
}

if (BASELINE_PRESET %in% unique(data$preset)) {
  baseline_rows <- data %>% filter(preset == BASELINE_PRESET)

  effect_sizes <- data %>%
    filter(preset != BASELINE_PRESET) %>%
    group_by(preset) %>%
    summarise(
      rt_mean_d = cohens_d(rt_mean, baseline_rows$rt_mean),
      accuracy_d = cohens_d(accuracy, baseline_rows$accuracy),
      .groups = "drop"
    ) %>%
    pivot_longer(cols = c(rt_mean_d, accuracy_d), names_to = "metric", values_to = "cohens_d")

  write_csv(effect_sizes, file.path(output_dir, "effect_sizes_vs_neurotypical.csv"))

  calibration_plot <- ggplot(effect_sizes, aes(x = preset, y = cohens_d, fill = metric)) +
    geom_col(position = "dodge") +
    geom_hline(yintercept = 0, linetype = "dashed") +
    labs(
      title = sprintf("Effect size vs. %s baseline (Cohen's d)", BASELINE_PRESET),
      x = "Preset", y = "Cohen's d", fill = "Metric"
    ) +
    theme_minimal()
  ggsave(file.path(output_dir, "effect_size_calibration.png"), calibration_plot, width = 8, height = 5)
} else {
  message(sprintf(
    "Baseline preset '%s' not present in data -- skipping effect-size/calibration plot.",
    BASELINE_PRESET
  ))
}

message(sprintf("Done. Outputs written to: %s", output_dir))
