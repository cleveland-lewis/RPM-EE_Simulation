# ds003500 Empirical Validation Report

Real trial-level (block-level) behavioral data from OpenNeuro ds003500 compared against clinical preset DDM predictions. See `src/adapters/ds003500.py` for dataset/adapter caveats (block-level granularity, Inh/Sel non-pooling, evidence/load mapping as a modeling choice).

| Task family | Group | Preset | n | Real RT (ms) | Sim RT (ms) | RT dev | Real Acc | Sim Acc | Acc dev |
|---|---|---|---|---|---|---|---|---|---|
| Inh | adhd | adhd_typical | 550 | 674.0±200.8 | 666.5±295.0 | -1.1% | 0.931 | 0.673 | -27.7% |
| Sel | adhd | adhd_typical | 284 | 815.8±161.6 | 627.9±266.7 | -23.0% | 0.899 | 0.616 | -31.4% |
| Inh | control | neurotypical | 1235 | 517.8±181.5 | 531.8±110.1 | +2.7% | 0.969 | 0.734 | -24.2% |
| Sel | control | neurotypical | 600 | 649.2±147.6 | 534.3±106.2 | -17.7% | 0.958 | 0.718 | -25.0% |
