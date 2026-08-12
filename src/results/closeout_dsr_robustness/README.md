# Completed controlled test-time robustness results

This directory contains the second-stage formal evidence for baseline versus DSR under frozen synthetic test-time errors.

## Formal matrix

| Phase | Runs | Episodes | Aggregate use |
|---|---:|---:|---|
| Zero-noise reference | 6 | 600 | Included |
| Formal noisy evaluation | 54 | 5,400 | Included |
| Smoke | 6 | 12 | Excluded |

The strict formal aggregate contains 60 runs, 6,000 episodes, and 27 paired cells. All formal leaf statuses are `passed` with `exit_code=0`.

## Primary files

- [`comparison.json`](comparison.json): authoritative machine-readable aggregate.
- [`comparison.csv`](comparison.csv): paired cells and summary table.
- [`conclusion.md`](conclusion.md): concise interpretation.
- [`run_status.csv`](run_status.csv): exact 6 clean plus 54 noisy run inventory.
- [`protocol_snapshot.json`](protocol_snapshot.json): protocol copied with the result.
- [`checkpoint_manifest_snapshot.json`](checkpoint_manifest_snapshot.json): checkpoint whitelist copied with the result.
- [`noise_manifest.json`](noise_manifest.json): frozen noise realization metadata.
- [`frozen_hashes.json`](frozen_hashes.json): evidence hashes.

## Result

| Condition | Success robustness advantage | Positive training seeds | SPL robustness advantage |
|---|---:|---:|---:|
| Localization | `+0.11 pp` | `1/3` | `+0.11 pp` |
| Actuation | `-2.11 pp` | `1/3` | `-1.56 pp` |
| Combined | `-2.56 pp` | `1/3` | `-2.04 pp` |

Robustness advantage is `(DSR noisy - DSR clean) - (baseline noisy - baseline clean)`; positive values favor DSR for Success and SPL. The preregistered combined result is negative, so the formal interpretation is: **No DSR robustness advantage was observed.**

The clean improvement and the robustness result must be reported together. This result must not be rewritten as “DSR is more robust under noise.”

## Evidence boundary and archive

This is descriptive evidence from two Habitat test scenes using synthetic localization and actuation perturbations. It is not a statistical-significance claim, Gibson/HM3D benchmark, real-robot result, or Sim2Real validation.

The verified local archive is `artifacts/archives/closeout_dsr_robustness_20260812.tar`, with SHA-256 `8319275aa62145f4977c2cd6588c1c760705af23bb637fb43a4fac06edf55cf1`.
