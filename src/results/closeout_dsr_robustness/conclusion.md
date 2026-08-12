# DSR controlled test-time robustness result

**Primary interpretation:** 未观察到DSR鲁棒优势。

| Noise condition | Success robustness advantage | Seed-direction consistency | SPL robustness advantage |
|---|---:|---:|---:|
| localization | +0.0011 | 1/3 | +0.0011 |
| actuation | -0.0211 | 1/3 | -0.0156 |
| combined | -0.0256 | 1/3 | -0.0204 |

Robustness advantage is `(DSR noisy - DSR clean) - (Baseline noisy - Baseline clean)`; positive values are favorable for Success and SPL.

This is descriptive evidence from two Habitat test scenes. No statistical-significance, Gibson/HM3D, real-robot, or Sim2Real claim is made.
