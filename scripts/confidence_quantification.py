"""
Confidence Quantification for RPM-EE Clinical Presets (Phase 3.3)

Closes the "Confidence Quantification" milestone from PHASE3_PROGRESS.md:

1. Bayesian credible intervals for parameters where the literature gives
   distributional data (a mean/SD or an explicit 95% CI), built as a
   normal-normal conjugate update of a confidence-derived prior.
2. Confidence-weighted sensitivity analysis: combine each parameter's
   sensitivity index (from scripts/sensitivity_analysis.py output) with its
   qualitative evidence confidence (PARAMETER_CONFIDENCE in src/presets.py).
3. A risk matrix flagging parameters that are both high-sensitivity and
   low-confidence.

METHOD NOTES (read before trusting a number):
- The "prior" for every parameter is Normal(mean=preset value, sd=f(confidence)),
  where f() maps HIGH/MODERATE/LOW confidence to a fraction of the parameter's
  documented valid range (docs/PARAMETER_SCALES.md). This is a stand-in for
  "how much would we expect an expert's belief to move" -- it is NOT itself
  derived from data.
- Where a cited meta-analysis reports a mean+SD or an explicit 95% CI
  (see LITERATURE_EVIDENCE below), that is treated as a likelihood and
  combined with the prior via standard conjugate normal-normal updating to
  produce a genuine data-informed posterior credible interval.
- All other parameters get a prior-only interval, explicitly labeled as such.
  This is intentional: the issue asks for credible intervals only "where
  literature gives distributional data" -- fabricating precision for
  parameters with no such data would be worse than not reporting an interval.

Author: Cleveland Lewis
Date: 2026-08-03
Version: 1.0
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from presets import CLINICAL_PRESETS, PARAMETER_CONFIDENCE  # noqa: E402

SENSITIVITY_DIR = Path("results/sensitivity_analysis")
OUTPUT_DIR = Path("results/confidence_quantification")

PRESET_NAMES = ["neurotypical", "asd_typical", "adhd_typical", "mdd_typical"]

# =============================================================================
# Parameter valid ranges (docs/PARAMETER_SCALES.md) -- used to scale the
# confidence-derived prior SD. Parameters not listed here use a 0-1 default.
# =============================================================================
PARAM_RANGES: dict[str, tuple[float, float]] = {
    "base_rt": (300.0, 800.0),
    "rt_variability": (0.05, 0.80),
    # NOTE: docs/PARAMETER_SCALES.md documents rt_slowing as a 0.00-0.25
    # proportional-slowing rate, but src/presets.py actually stores it as a
    # multiplier (1.0 = no slowing, up to ~1.2). Range below matches the
    # code's actual usage, not the (stale) doc. See PHASE3_VALIDATION_FINDINGS.md
    # for the analogous switch_cost scale-ambiguity issue.
    "rt_slowing": (1.0, 1.30),
    "base_accuracy": (0.40, 1.00),
    "accuracy_decline": (0.00, 0.05),
    "wm_capacity": (2.0, 6.0),
    "wm_decay_rate": (0.005, 0.030),
    "attention_stability": (0.40, 0.95),
    "switch_cost": (0.05, 0.35),
    "vigilance_decrement": (0.005, 0.035),
    "stress_baseline": (0.10, 0.80),
    "stress_reactivity": (0.05, 0.80),
    "stress_recovery": (0.02, 0.20),
    "positive_affect": (0.10, 0.80),
    "negative_affect": (0.10, 0.70),
    "reward_sensitivity": (0.05, 0.60),
    "prediction_error_gain": (0.05, 0.50),
    "exploration_rate": (0.05, 0.50),
}

# Confidence category -> prior SD as a fraction of the parameter's range width.
CONFIDENCE_PRIOR_FRACTION = {
    "HIGH": 0.05,
    "MODERATE": 0.15,
    "LOW": 0.30,
    "UNKNOWN": 0.35,
}

# Confidence category -> weight (0-1) used for confidence-weighted sensitivity.
CONFIDENCE_WEIGHT = {
    "HIGH": 1.0,
    "MODERATE": 0.6,
    "LOW": 0.25,
    "UNKNOWN": 0.1,
}

Z_95 = 1.959964

# Sensitivity-index thresholds used by classify_risk().
SI_HIGH_IMPACT = 1.0
SI_MODERATE_IMPACT = 0.3


def _widen_ranges_to_observed_values() -> None:
    """
    docs/PARAMETER_SCALES.md ranges and src/presets.py values have drifted for
    several parameters (e.g. accuracy_decline, reward_sensitivity,
    prediction_error_gain exceed their documented max in some presets -- a
    known class of issue, see the switch_cost scale ambiguity in
    docs/PHASE3_VALIDATION_FINDINGS.md). Widen PARAM_RANGES in place so a
    preset's own value is never clipped out of its own credible interval;
    this affects prior width and CI clipping, not the reported point values.
    """
    for preset_params in CLINICAL_PRESETS.values():
        for param, value in preset_params.items():
            if param not in PARAM_RANGES:
                continue
            lo, hi = PARAM_RANGES[param]
            PARAM_RANGES[param] = (min(lo, value), max(hi, value))


_widen_ranges_to_observed_values()


# =============================================================================
# Literature evidence with distributional data (mean+SD or explicit 95% CI).
# Everything else falls back to a prior-only interval.
# =============================================================================
@dataclass
class LiteratureEvidence:
    citation: str
    metric: str
    # Value + CI already expressed directly on the parameter's own scale.
    mapped_mean: float
    mapped_ci95: tuple[float, float]
    n_note: str


LITERATURE_EVIDENCE: dict[tuple[str, str], LiteratureEvidence] = {
    ("adhd_typical", "rt_variability"): LiteratureEvidence(
        citation="Kofler et al. (2013)",
        metric="RT coefficient of variation, ADHD vs. control (meta-analysis)",
        # ADHD CV = 0.45 (SD=0.12); reported effect Hedges' g=0.76 [0.63, 0.88].
        # CI derived by propagating the reported g-CI through the same
        # value/effect-size ratio (0.45/0.76) implicit in the current mapping.
        mapped_mean=0.45,
        mapped_ci95=(0.63 * (0.45 / 0.76), 0.88 * (0.45 / 0.76)),
        n_note="319 studies, N=13,233 ADHD / 11,842 control",
    ),
    ("mdd_typical", "stress_baseline"): LiteratureEvidence(
        citation="Burke et al. (2005)",
        metric="Basal cortisol, MDD vs. control (meta-analysis; μg/dL, mapped via /50.0)",
        mapped_mean=32.5 / 50.0,
        mapped_ci95=(28.0 / 50.0, 37.0 / 50.0),
        n_note="361 studies",
    ),
}


def prior_sd(param: str, confidence: str) -> float:
    lo, hi = PARAM_RANGES.get(param, (0.0, 1.0))
    width = hi - lo
    fraction = CONFIDENCE_PRIOR_FRACTION.get(confidence, CONFIDENCE_PRIOR_FRACTION["UNKNOWN"])
    return max(width * fraction, 1e-6)


def normal_normal_update(
    prior_mean: float, prior_sd_: float, lik_mean: float, lik_sd: float
) -> tuple[float, float]:
    """Conjugate Bayesian update for two independent Normal estimates."""
    prior_prec = 1.0 / (prior_sd_**2)
    lik_prec = 1.0 / (lik_sd**2)
    post_prec = prior_prec + lik_prec
    post_mean = (prior_mean * prior_prec + lik_mean * lik_prec) / post_prec
    post_sd = post_prec**-0.5
    return post_mean, post_sd


@dataclass
class CredibleInterval:
    parameter: str
    preset_value: float
    confidence: str
    prior_mean: float
    prior_sd: float
    has_literature_data: bool
    posterior_mean: float
    posterior_sd: float
    ci_low: float
    ci_high: float
    source: str


def compute_credible_interval(
    preset: str, param: str, value: float, confidence: str
) -> CredibleInterval:
    p_mean = value
    p_sd = prior_sd(param, confidence)

    evidence = LITERATURE_EVIDENCE.get((preset, param))
    if evidence is None:
        ci_low, ci_high = clip_to_range(param, p_mean - Z_95 * p_sd, p_mean + Z_95 * p_sd)
        return CredibleInterval(
            parameter=param,
            preset_value=value,
            confidence=confidence,
            prior_mean=p_mean,
            prior_sd=p_sd,
            has_literature_data=False,
            posterior_mean=p_mean,
            posterior_sd=p_sd,
            ci_low=ci_low,
            ci_high=ci_high,
            source="Prior only (no distributional literature data)",
        )

    lik_mean = evidence.mapped_mean
    lik_sd = (evidence.mapped_ci95[1] - evidence.mapped_ci95[0]) / (2 * Z_95)
    post_mean, post_sd = normal_normal_update(p_mean, p_sd, lik_mean, lik_sd)
    ci_low, ci_high = clip_to_range(param, post_mean - Z_95 * post_sd, post_mean + Z_95 * post_sd)

    return CredibleInterval(
        parameter=param,
        preset_value=value,
        confidence=confidence,
        prior_mean=p_mean,
        prior_sd=p_sd,
        has_literature_data=True,
        posterior_mean=post_mean,
        posterior_sd=post_sd,
        ci_low=ci_low,
        ci_high=ci_high,
        source=f"{evidence.citation} -- {evidence.metric} ({evidence.n_note})",
    )


def clip_to_range(param: str, lo: float, hi: float) -> tuple[float, float]:
    """Clip a normal-approximation CI to the parameter's physically valid range."""
    range_lo, range_hi = PARAM_RANGES.get(param, (float("-inf"), float("inf")))
    return max(lo, range_lo), min(hi, range_hi)


@dataclass
class RiskEntry:
    parameter: str
    max_sensitivity: float
    confidence: str
    confidence_weight: float
    confidence_weighted_sensitivity: float
    risk_score: float
    risk_category: str


def classify_risk(max_sensitivity: float, confidence: str) -> str:
    if max_sensitivity > SI_HIGH_IMPACT and confidence == "LOW":
        return "CRITICAL"
    if max_sensitivity > SI_HIGH_IMPACT and confidence == "MODERATE":
        return "WATCH"
    if max_sensitivity > SI_HIGH_IMPACT and confidence == "HIGH":
        return "WELL-SUPPORTED"
    if SI_MODERATE_IMPACT <= max_sensitivity <= SI_HIGH_IMPACT and confidence == "LOW":
        return "MONITOR"
    return "LOW-RISK"


def load_sensitivity_summary(preset: str) -> dict[str, float]:
    """Return {parameter: max_sensitivity} for a preset, or {} if unavailable."""
    path = SENSITIVITY_DIR / f"sensitivity_data_{preset}.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {param: info["max_sensitivity"] for param, info in data.get("summary", {}).items()}


def analyze_preset(preset: str) -> dict[str, Any]:
    params = CLINICAL_PRESETS[preset]
    confidence_map = PARAMETER_CONFIDENCE.get(preset, {})
    sensitivity = load_sensitivity_summary(preset)

    credible_intervals = [
        compute_credible_interval(preset, param, value, confidence_map.get(param, "UNKNOWN"))
        for param, value in params.items()
        if param in PARAM_RANGES
    ]

    risk_entries = []
    for param, max_sens in sensitivity.items():
        # Older sensitivity-analysis runs used a hardcoded fallback parameter
        # set with different names (e.g. task_switch_cost, rt_slowing_rate)
        # that no longer match CLINICAL_PRESETS; skip those as stale.
        if param not in params:
            continue
        confidence = confidence_map.get(param, "UNKNOWN")
        weight = CONFIDENCE_WEIGHT.get(confidence, CONFIDENCE_WEIGHT["UNKNOWN"])
        risk_entries.append(
            RiskEntry(
                parameter=param,
                max_sensitivity=max_sens,
                confidence=confidence,
                confidence_weight=weight,
                confidence_weighted_sensitivity=max_sens * weight,
                risk_score=max_sens * (1 - weight),
                risk_category=classify_risk(max_sens, confidence),
            )
        )
    risk_entries.sort(key=lambda r: r.risk_score, reverse=True)

    return {
        "preset": preset,
        "credible_intervals": credible_intervals,
        "risk_entries": risk_entries,
    }


def generate_report(preset: str, result: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(exist_ok=True, parents=True)

    md_path = output_dir / f"confidence_quantification_{preset}.md"
    with md_path.open("w") as f:
        f.write(f"# Confidence Quantification: {preset}\n\n")
        f.write("**Date:** 2026-08-03\n")
        f.write(
            "**Method:** Normal-normal conjugate Bayesian update of a "
            "confidence-derived prior against literature-reported distributional "
            "data (mean/SD or 95% CI), where available.\n\n"
        )
        f.write("---\n\n")

        f.write("## Bayesian Credible Intervals\n\n")
        f.write("| Parameter | Value | Confidence | 95% CI | Data-informed? | Source |\n")
        f.write("|---|---|---|---|---|---|\n")
        for ci in result["credible_intervals"]:
            f.write(
                f"| {ci.parameter} | {ci.preset_value:.3g} | {ci.confidence} | "
                f"[{ci.ci_low:.3g}, {ci.ci_high:.3g}] | "
                f"{'Yes' if ci.has_literature_data else 'No (prior only)'} | {ci.source} |\n"
            )
        f.write("\n")

        f.write("---\n\n")
        f.write("## Confidence-Weighted Sensitivity & Risk Matrix\n\n")
        f.write(
            "`risk_score = max_sensitivity_index * (1 - confidence_weight)`. "
            "High risk_score means a parameter both moves outcomes a lot "
            "*and* rests on weak evidence.\n\n"
        )
        f.write(
            "| Parameter | Max SI | Confidence | Weight | Weighted SI | Risk Score | Category |\n"
        )
        f.write("|---|---|---|---|---|---|---|\n")
        for r in result["risk_entries"]:
            f.write(
                f"| {r.parameter} | {r.max_sensitivity:.3f} | {r.confidence} | "
                f"{r.confidence_weight:.2f} | {r.confidence_weighted_sensitivity:.3f} | "
                f"{r.risk_score:.3f} | **{r.risk_category}** |\n"
            )
        f.write("\n")

        critical = [r for r in result["risk_entries"] if r.risk_category in ("CRITICAL", "WATCH")]
        f.write("### Flagged Parameters (CRITICAL / WATCH)\n\n")
        if critical:
            for r in critical:
                f.write(
                    f"- **{r.parameter}** ({r.risk_category}): SI={r.max_sensitivity:.2f}, "
                    f"confidence={r.confidence} -- prioritize evidence strengthening.\n"
                )
        else:
            f.write("None.\n")
        f.write("\n")

    json_path = output_dir / f"confidence_quantification_{preset}.json"
    json_data = {
        "preset": preset,
        "credible_intervals": [asdict(ci) for ci in result["credible_intervals"]],
        "risk_entries": [asdict(r) for r in result["risk_entries"]],
    }
    json_path.write_text(json.dumps(json_data, indent=2))

    return md_path


def generate_aggregate_summary(all_results: dict[str, dict[str, Any]], output_dir: Path) -> Path:
    """Cross-preset summary, focused on the risk matrix (issue #19's ask)."""
    path = output_dir / "confidence_quantification_summary.md"

    all_risk: list[tuple[str, RiskEntry]] = [
        (preset, r) for preset, result in all_results.items() for r in result["risk_entries"]
    ]
    all_risk.sort(key=lambda pr: pr[1].risk_score, reverse=True)

    with path.open("w") as f:
        f.write("# Confidence Quantification Summary (All Presets)\n\n")
        f.write("**Date:** 2026-08-03\n")
        f.write(
            '**Related:** Issue #19, PHASE3_PROGRESS.md "Confidence Quantification" milestone\n\n'
        )
        f.write("---\n\n")

        f.write("## Global Risk Matrix (High Sensitivity + Low Confidence)\n\n")
        f.write("Top 15 parameter/preset combinations by risk score:\n\n")
        f.write("| Preset | Parameter | Max SI | Confidence | Risk Score | Category |\n")
        f.write("|---|---|---|---|---|---|\n")
        for preset, r in all_risk[:15]:
            f.write(
                f"| {preset} | {r.parameter} | {r.max_sensitivity:.3f} | {r.confidence} | "
                f"{r.risk_score:.3f} | **{r.risk_category}** |\n"
            )
        f.write("\n")

        critical_or_watch = [
            (p, r) for p, r in all_risk if r.risk_category in ("CRITICAL", "WATCH")
        ]
        f.write("### CRITICAL / WATCH Parameters Across All Presets\n\n")
        if critical_or_watch:
            for preset, r in critical_or_watch:
                f.write(f"- **{r.parameter}** ({preset}): {r.risk_category}\n")
        else:
            f.write("None.\n")
        f.write("\n")

        f.write("### Comparison to PHASE3_VALIDATION_FINDINGS.md\n\n")
        f.write(
            "The findings document previously named `reward_sensitivity` and "
            "`prediction_error_gain` as the highest-priority high-sensitivity / "
            "low-confidence parameters (based on manual review). The table above "
            "recomputes this from the actual sensitivity-analysis + confidence data "
            "and should be treated as the current source of truth.\n\n"
        )

        f.write("---\n\n")
        f.write("## Methodology\n\n")
        f.write(
            "See module docstring in `scripts/confidence_quantification.py` for full "
            "detail. In short:\n\n"
            "1. Every parameter gets a prior Normal(preset value, sd) where sd scales "
            "with (LOW/MODERATE/HIGH) evidence confidence as a fraction of the "
            "parameter's documented range (docs/PARAMETER_SCALES.md).\n"
            "2. Where a cited meta-analysis reports a mean/SD or explicit 95% CI on "
            "the same (or a linearly mappable) scale, that is combined with the prior "
            "via conjugate normal-normal Bayesian updating to get a genuine posterior "
            "credible interval. Currently: `rt_variability` (ADHD, Kofler et al. 2013) "
            "and `stress_baseline` (MDD, Burke et al. 2005).\n"
            "3. All other parameters report a prior-only interval, explicitly labeled "
            "as not data-informed.\n"
            "4. Confidence-weighted sensitivity multiplies each parameter's max "
            "sensitivity index (from `scripts/sensitivity_analysis.py`) by a "
            "confidence weight (HIGH=1.0, MODERATE=0.6, LOW=0.25); `risk_score` uses "
            "the complement, so it is highest for parameters that matter a lot but are "
            "weakly supported.\n"
        )

    return path


def main() -> None:
    print("=" * 70)
    print("CLINICAL PRESETS: CONFIDENCE QUANTIFICATION")
    print("=" * 70)

    all_results = {}
    for preset in PRESET_NAMES:
        print(f"\nAnalyzing: {preset}")
        result = analyze_preset(preset)
        all_results[preset] = result
        report_path = generate_report(preset, result, OUTPUT_DIR)
        print(f"  Report: {report_path}")

        flagged = [r for r in result["risk_entries"] if r.risk_category in ("CRITICAL", "WATCH")]
        if flagged:
            print(f"  Flagged (CRITICAL/WATCH): {', '.join(r.parameter for r in flagged)}")

    summary_path = generate_aggregate_summary(all_results, OUTPUT_DIR)
    print(f"\nAggregate summary: {summary_path}")
    print("\nDone.")


if __name__ == "__main__":
    main()
