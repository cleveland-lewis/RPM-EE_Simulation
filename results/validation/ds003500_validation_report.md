# ds003500 Empirical Validation Report

Real trial-level (block-level) behavioral data from OpenNeuro ds003500 compared against clinical preset DDM predictions. See `src/adapters/ds003500.py` for dataset/adapter caveats (block-level granularity, Inh/Sel non-pooling, evidence/load mapping as a modeling choice).

Distributions are compared with a two-sample Kolmogorov-Smirnov test (`scipy.stats.ks_2samp`), not just mean deviation -- KS statistic D is the max gap between the two empirical CDFs; p < 0.05 rejects the null hypothesis that real and simulated values come from the same distribution. Each simulated block averages 18 stochastic DDM trials, matching the real side's 18-trial block average.

| Task family | Group | Preset | n | Real RT (ms) | Sim RT (ms) | RT dev | RT KS D | RT KS p | RT differ? | Real Acc | Sim Acc | Acc dev | Acc KS D | Acc KS p | Acc differ? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Inh | adhd | adhd_typical | 550 | 674.0±200.8 | 654.9±72.1 | -2.8% | 0.255 | 0.0000 | yes | 0.931 | 0.667 | -28.3% | 0.736 | 0.0000 | yes |
| Sel | adhd | adhd_typical | 284 | 815.8±161.6 | 656.7±72.0 | -19.5% | 0.514 | 0.0000 | yes | 0.899 | 0.655 | -27.2% | 0.609 | 0.0000 | yes |
| Inh | control | neurotypical | 1235 | 517.8±181.5 | 535.0±29.4 | +3.3% | 0.513 | 0.0000 | yes | 0.969 | 0.730 | -24.7% | 0.729 | 0.0000 | yes |
| Sel | control | neurotypical | 600 | 649.2±147.6 | 533.6±30.8 | -17.8% | 0.573 | 0.0000 | yes | 0.958 | 0.732 | -23.5% | 0.638 | 0.0000 | yes |
