# Completed clean baseline-versus-DSR results

This directory contains the completed first-stage three-seed comparison between the standard Habitat PointNav PPO baseline and the paper-defined Dynamic Success Reward (DSR).

## Formal aggregate

- Status: complete; all six fresh training runs and all six fixed evaluations passed.
- Training seeds: `100`, `200`, `300`.
- Evaluation: seed `2026`, 100 episodes per policy, two evaluation environments.
- Baseline mean Success/SPL: `88.67% / 76.65%`.
- DSR mean Success/SPL: `95.67% / 83.37%`.
- DSR minus baseline: Success `+7.00` percentage points; SPL `+6.72` percentage points; final distance `-0.0681 m`; premature STOP `-6.67` percentage points.

Primary files:

- [`comparison.json`](comparison.json): authoritative machine-readable aggregate.
- [`comparison.md`](comparison.md): readable result tables and claim boundary.
- [`wp5_evidence_audit_20260811.md`](wp5_evidence_audit_20260811.md): run, checkpoint, hash, and archive audit.

The aggregate includes only the six fresh formal evaluations. Diagnostic runs, integrity smokes, training rolling-window metrics, and the transferred old seed-100 checkpoint are excluded from the performance comparison.

## Claim boundary

This is a controlled reward ablation on two Habitat `test-scenes` and three training seeds. It is not a Gibson/HM3D benchmark, a claim of statistical significance, a new RL algorithm, or real-robot/Sim2Real evidence.

Large checkpoints, TensorBoard events, and videos may be excluded by repository-wide ignore rules. The complete local archive is `artifacts/archives/closeout_dsr_remote_20260811.tar`, with SHA-256 `0ea7645ce5ff97498932f68fb57af3777b5417de00302e94e6e8abed3c6af40e`.
