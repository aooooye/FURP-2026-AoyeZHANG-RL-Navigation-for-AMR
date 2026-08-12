# Week 8 - 2026-08-12

**Attended this week's meeting:** yes

**Progress this week**

- Froze an evaluation-only robustness protocol using the same six final baseline/DSR checkpoints. No policy was retrained or fine-tuned.
- Defined three controlled test-time conditions:
  - `localization`: perturb only the policy-visible PointGoal distance and bearing.
  - `actuation`: perturb only the executed forward distance and turn angle.
  - `combined`: apply the paired localization and actuation perturbations together.
- Preserved simulation ground truth for reward, success determination, final distance, and SPL. The success distance remained fixed at `0.20 m`.
- Implemented stateless SHA-256/Box-Muller noise generation, paired episode/noise sequences, protocol guards, per-episode telemetry, strict finalization, and an aggregate gate.
- Passed all 19 unit tests locally and in the pinned remote Habitat environment.
- Completed six zero-noise evaluations and confirmed that all seven saved aggregate metrics matched the first-stage clean results with maximum absolute error `0.0`.
- Completed six two-episode smoke runs. These 12 episodes were stored separately and excluded from formal results.
- Completed all 54 formal noisy evaluations. Together with the six clean references, the strict aggregate contains 60 runs and 6,000 formal episodes.
- Obtained the following Success robustness advantages:
  - Localization noise: `+0.11` percentage points, but only `1/3` training seeds were positive.
  - Actuation noise: `-2.11` percentage points, with `1/3` positive seeds.
  - Combined noise: `-2.56` percentage points, with `1/3` positive seeds.
- The preregistered primary interpretation is therefore: **No DSR robustness advantage was observed.**
- Found a descriptive mechanism signal: under combined noise, DSR's noise-induced premature-STOP increase was 3.33 percentage points larger than baseline. This is not treated as a causal or statistically significant result.
- Created and fully verified a standalone second-stage evidence archive. The extracted archive matched the source directory across all 1,859 files.

**Challenges & blockers**

- One completed actuation run initially triggered a validation warning because the evaluator log rounded reward to four decimal places. The same 100 saved episode shards were re-finalized with a reward-specific rounding tolerance; the GPU evaluation was not rerun.
- Historical first-stage evaluation stored aggregate metrics but not historical per-episode records. Therefore, zero-noise validation proves exact aggregate agreement, not historical episode-by-episode identity.
- The robustness study uses synthetic controlled perturbations on two Habitat test scenes. It is not sensor calibration, real chassis modelling, Sim2Real validation, or real-AMR evidence.
- The negative/mixed robustness result must be retained. Noise amplitudes, seeds, thresholds, checkpoints, and aggregation rules cannot be changed after inspecting the result.

**Hours spent (optional):** 40

**Evidence copies in this repository**

- `src/experiments/closeout_dsr_robustness/protocol.json`
- `src/experiments/closeout_dsr_robustness/checkpoint_manifest.json`
- `src/results/closeout_dsr_robustness/comparison.json`
- `src/results/closeout_dsr_robustness/comparison.csv`
- `src/results/closeout_dsr_robustness/conclusion.md`
- `src/results/closeout_dsr_robustness/run_status.csv`

**Local evidence archive**

- `artifacts/archives/closeout_dsr_robustness_20260812.tar`
- SHA-256: `8319275aa62145f4977c2cd6588c1c760705af23bb637fb43a4fac06edf55cf1`
