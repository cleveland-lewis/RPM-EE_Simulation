#!/usr/bin/env Rscript
# Terminal (ASCII) plots for scripts/batch_run.py, rendered directly in the
# shell via the txtplot package -- no image viewer needed. Reads the
# per-episode CSV that batch_run.py exports (columns: preset, batch,
# episode, accuracy, rt_mean) and prints:
#   0. Diagnosis (preset) breakdown -- how many episodes each preset
#      contributed before its own Shapiro-Wilk stopping rule fired
#   Per preset:
#     1. Distribution of batch means (density + skewness/kurtosis)
#     2. Boxplot of batch means (outliers, spread)
#     3. Batch-mean convergence trend (does the mean stabilize over batches?)
#     4. Autocorrelation of batch means (checks the independence assumption
#        behind treating batch means as a random sample for Shapiro-Wilk)
#   Finally:
#     5. A 2D heatmap of accuracy vs. RT across all episodes, all presets
#        pooled -- distinct clusters correspond to distinct diagnoses, and
#        off-center density within a cluster indicates skew
#
# Usage:
#   Rscript scripts/terminal_plots.R <path/to/episodes.csv>

suppressMessages({
  if (!requireNamespace("txtplot", quietly = TRUE)) {
    message("txtplot not installed -- attempting install.packages(\"txtplot\")...")
    tryCatch(
      install.packages("txtplot", repos = "https://cloud.r-project.org", quiet = TRUE),
      error = function(e) NULL
    )
  }
  if (!requireNamespace("txtplot", quietly = TRUE)) {
    message("Could not install txtplot (no internet access?) -- skipping terminal plots.")
    quit(status = 0)
  }
  library(txtplot)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1) {
  stop("Usage: Rscript scripts/terminal_plots.R <path/to/episodes.csv>")
}
csv_path <- args[[1]]
if (!file.exists(csv_path)) {
  stop(sprintf("Input file not found: %s", csv_path))
}

data <- read.csv(csv_path, stringsAsFactors = FALSE)
data <- data[!is.na(data$accuracy) & !is.na(data$rt_mean), ]
if (nrow(data) == 0) {
  stop("No rows with non-NA accuracy/rt_mean in the input -- nothing to plot.")
}
if (!"preset" %in% names(data)) {
  data$preset <- "unspecified"
}

banner <- function(title) {
  cat("\n", strrep("=", 70), "\n", title, "\n", strrep("=", 70), "\n", sep = "")
}

skewness <- function(x) {
  n <- length(x)
  m <- mean(x)
  s <- sd(x)
  (sum((x - m)^3) / n) / s^3
}

kurtosis_excess <- function(x) {
  n <- length(x)
  m <- mean(x)
  s <- sd(x)
  (sum((x - m)^4) / n) / s^4 - 3
}

presets <- sort(unique(data$preset))

# -----------------------------------------------------------------------
# 0. Diagnosis breakdown
# -----------------------------------------------------------------------
banner("0. Diagnosis breakdown (episodes run per preset)")
counts <- table(data$preset)
for (p in names(counts)) {
  cat(sprintf("  %-15s %6d episodes  (%.1f%%)\n", p, counts[[p]], 100 * counts[[p]] / nrow(data)))
}
cat("\n")
if (length(presets) >= 2) {
  txtbarchart(factor(data$preset))
} else {
  cat("(only one preset present -- nothing to compare)\n")
}

# -----------------------------------------------------------------------
# Per-preset: distribution, boxplot, convergence trend, autocorrelation
# -----------------------------------------------------------------------
for (p in presets) {
  pdata <- data[data$preset == p, ]
  batch_means <- aggregate(accuracy ~ batch, data = pdata, FUN = mean)
  batch_means <- batch_means[order(batch_means$batch), ]
  bm <- batch_means$accuracy

  banner(sprintf("1. [%s] Distribution of batch means (accuracy)", p))
  cat(sprintf(
    "n=%d  mean=%.4f  sd=%.4f  min=%.4f  max=%.4f\n",
    length(bm), mean(bm), sd(bm), min(bm), max(bm)
  ))
  if (length(bm) >= 3 && sd(bm) > 0) {
    cat(sprintf(
      "skewness=%.3f  excess kurtosis=%.3f  (0 = symmetric/normal-tailed)\n",
      skewness(bm), kurtosis_excess(bm)
    ))
  }
  if (length(bm) >= 4 && sd(bm) > 0) {
    txtdensity(bm, xlab = sprintf("[%s] batch mean accuracy", p))
  } else {
    cat("(too few batches or zero variance for a density plot)\n")
  }

  banner(sprintf("2. [%s] Boxplot of batch means", p))
  if (length(bm) >= 2) {
    txtboxplot(bm, xlab = sprintf("[%s] batch mean accuracy", p))
  } else {
    cat("(need at least 2 batches for a boxplot)\n")
  }

  banner(sprintf("3. [%s] Batch-mean convergence trend", p))
  if (nrow(batch_means) >= 2) {
    txtplot(batch_means$batch, batch_means$accuracy,
      xlab = "batch #", ylab = "mean accuracy"
    )
  } else {
    cat("(need at least 2 batches for a trend plot)\n")
  }

  banner(sprintf("4. [%s] Autocorrelation of batch means", p))
  if (nrow(batch_means) >= 4) {
    txtacf(bm, lag.max = min(10, nrow(batch_means) - 1))
    cat("Bars decaying to ~0 quickly support treating batches as independent\n")
    cat("(a load-bearing assumption behind the Shapiro-Wilk stopping rule).\n")
  } else {
    cat("(need at least 4 batches for an autocorrelation plot)\n")
  }
}

# -----------------------------------------------------------------------
# 5. Heatmap: accuracy vs. RT across all episodes, all presets pooled
# -----------------------------------------------------------------------
banner("5. Accuracy vs. RT heatmap (all episodes, all presets pooled)")
bins <- 60
x <- data$rt_mean
y <- data$accuracy
if (length(unique(x)) > 1 && length(unique(y)) > 1) {
  xb <- cut(x, breaks = bins, labels = FALSE, include.lowest = TRUE)
  yb <- cut(y, breaks = bins, labels = FALSE, include.lowest = TRUE)
  m <- matrix(0, nrow = bins, ncol = bins)
  for (i in seq_along(x)) {
    m[yb[i], xb[i]] <- m[yb[i], xb[i]] + 1
  }
  cat(sprintf(
    "x-axis: rt_mean [%.1f, %.1f]ms   y-axis: accuracy [%.3f, %.3f] (bottom-up)\n",
    min(x), max(x), min(y), max(y)
  ))
  cat("Separate clusters correspond to separate diagnoses; off-center density\n")
  cat("within a cluster indicates skew.\n\n")
  txtimage(m, width = 50, height = 18)
} else {
  cat("(not enough distinct RT/accuracy values for a heatmap)\n")
}

cat("\n")
