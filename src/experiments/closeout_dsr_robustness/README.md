# Controlled test-time robustness experiment

This directory contains the completed second-stage evaluation-only robustness study. It reuses the six final checkpoints from the clean baseline-versus-DSR matrix and tests whether the clean DSR advantage is retained under frozen synthetic localization and actuation errors.

**Status:** complete. Do not retrain policies or rerun the 60-run formal matrix unless evidence corruption is confirmed and a rerun is explicitly authorized.

## Frozen design

- Methods: baseline and DSR.
- Training seeds: `100`, `200`, `300`.
- Formal noise seeds: `41001`, `41002`, `41003`.
- Conditions: `clean`, `localization`, `actuation`, `combined`.
- Evaluation: seed `2026`, 100 episodes, two environments, success distance `0.20 m`.
- Matrix: 6 zero-noise references plus 54 formal noisy evaluations, totaling 60 runs and 6,000 formal episodes.
- Smoke: six two-episode runs stored separately and excluded from the aggregate.

Localization noise changes only the policy-visible PointGoal distance/bearing. Actuation noise changes only executed forward distance/turn angle. Reward, success, final distance, and SPL continue to use simulator ground truth.

## Entry points

- [`protocol.json`](protocol.json): frozen machine-readable protocol and noise model.
- [`checkpoint_manifest.json`](checkpoint_manifest.json): six-checkpoint whitelist and hashes.
- [`run_robustness.py`](run_robustness.py): `zero_noise`, `smoke`, `formal`, and `aggregate` orchestration.
- [`robustness_core.py`](robustness_core.py): stateless SHA-256/Box-Muller noise generation.
- [`robustness_env.py`](robustness_env.py): observation/action perturbation and telemetry.
- [`protocol_guard.py`](protocol_guard.py): protocol, checkpoint, identity, and hash guards.
- [`finalize_run.py`](finalize_run.py): per-run shard merge and validation.
- [`aggregate_results.py`](aggregate_results.py): strict 60-run aggregate gate.

The four `test_*.py` files contain 19 unit tests. The implementation passed all 19 locally and in the pinned Habitat environment.

## Result

The authoritative result is [`../../results/closeout_dsr_robustness/comparison.json`](../../results/closeout_dsr_robustness/comparison.json). The primary combined Success robustness advantage was `-2.56` percentage points, with only `1/3` training seeds favorable. Therefore: **No DSR robustness advantage was observed.**

This is a controlled synthetic sensitivity study on two Habitat test scenes. It is not sensor calibration, chassis identification, Gibson/HM3D evaluation, real-robot testing, or Sim2Real validation.
