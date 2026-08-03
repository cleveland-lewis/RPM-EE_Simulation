# ds003500 Empirical Validation Report

Real trial-level (block-level) behavioral data from OpenNeuro ds003500 compared against clinical preset DDM predictions. See `src/adapters/ds003500.py` for dataset/adapter caveats (block-level granularity, Inh/Sel non-pooling, evidence/load mapping as a modeling choice).

Distributions are compared with a two-sample Kolmogorov-Smirnov test (`scipy.stats.ks_2samp`), not just mean deviation -- KS statistic D is the max gap between the two empirical CDFs; p < 0.05 rejects the null hypothesis that real and simulated values come from the same distribution. Each simulated block averages 18 stochastic DDM trials, matching the real side's 18-trial block average.

| Task family | Group | Preset | n | Real RT (ms) | Sim RT (ms) | RT dev | RT KS D | RT KS p | RT differ? | Real Acc | Sim Acc | Acc dev | Acc KS D | Acc KS p | Acc differ? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Inh | adhd | adhd_typical | 550 | 674.0±200.8 | 637.1±60.5 | -5.5% | 0.326 | 0.0000 | yes | 0.931 | 0.773 | -17.0% | 0.630 | 0.0000 | yes |
| Sel | adhd | adhd_typical | 284 | 815.8±161.6 | 641.5±65.3 | -21.4% | 0.599 | 0.0000 | yes | 0.899 | 0.773 | -14.0% | 0.535 | 0.0000 | yes |
| Inh | control | neurotypical | 1235 | 517.8±181.5 | 516.2±21.6 | -0.3% | 0.481 | 0.0000 | yes | 0.969 | 0.873 | -9.9% | 0.547 | 0.0000 | yes |
| Sel | control | neurotypical | 600 | 649.2±147.6 | 516.0±20.2 | -20.5% | 0.693 | 0.0000 | yes | 0.958 | 0.871 | -9.0% | 0.465 | 0.0000 | yes |
