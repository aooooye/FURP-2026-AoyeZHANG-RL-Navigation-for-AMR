# Frozen baseline versus DSR results

All policies use standard Habitat 0.3.3 reward and dynamics plus numeric terminal STOP diagnostics during evaluation. Training seed varies; evaluation seed is fixed at 2026 for 100 episodes.

| Condition | Train seed | Success | SPL | Final distance | Premature STOP | Non-STOP failure |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 100 | 94.00% | 82.26% | 0.1202 m | 6.00% | 0.00% |
| baseline | 200 | 88.00% | 77.33% | 0.5469 m | 7.00% | 5.00% |
| baseline | 300 | 84.00% | 70.36% | 0.3644 m | 13.00% | 3.00% |
| dsr | 100 | 92.00% | 75.90% | 0.4863 m | 3.00% | 5.00% |
| dsr | 200 | 99.00% | 87.76% | 0.1038 m | 0.00% | 1.00% |
| dsr | 300 | 96.00% | 86.46% | 0.2372 m | 3.00% | 1.00% |

| Condition | Mean Success | Mean SPL | Mean final distance | Mean premature STOP | Success SD | SPL SD |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 88.67% | 76.65% | 0.3438 m | 8.67% | 5.03% | 5.98% |
| dsr | 95.67% | 83.37% | 0.2758 m | 2.00% | 3.51% | 6.50% |

## Directional differences

- Success: +7.00 percentage points.
- SPL: +6.72 percentage points.
- Final distance: -0.0681 m (negative is better).
- Premature STOP rate: -6.67 percentage points (negative is better).
- Non-STOP failure rate: -0.33 percentage points (negative is better).
- Standard evaluation reward: +0.2236.

These are two-scene fallback results, not a Gibson/HM3D benchmark or a claim of statistical significance. A null or negative result remains the final result; the protocol does not permit switching methods after inspection.
