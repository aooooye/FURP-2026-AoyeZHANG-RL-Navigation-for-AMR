# Week 6 - 2026-08-07

**Attended this week's meeting:** Yes

**Progress this week**

- Reviewed the Week 3 learned-policy failures. The selected failed episodes stopped at approximately `0.21-0.30 m`, just outside the configured `0.20 m` success radius, indicating that premature STOP was an important failure mechanism.
- Selected the paper-defined Dynamic Success Reward (DSR) as a controlled reward-design intervention. DSR changes only the reward for a successful STOP and does not modify PPO, observations, the action space, the success distance, or the dataset.
- Rejected the previously discussed fixed wrong-STOP penalty because it had not been formally evaluated and would introduce an additional tuning choice.
- Froze a no-tuning comparison protocol: baseline versus DSR, training seeds `100/200/300`, `1,000,000` environment steps per run, five training environments, evaluation seed `2026`, 100 evaluation episodes, two evaluation environments, success distance `0.20 m`, and maximum episode length 500 steps.
- Implemented the DSR reward calculation and dedicated Habitat environment wrapper under `src/experiments/closeout_dsr/`.
- Added protocol guards, preflight checks, fixed training/evaluation commands, aggregation scripts, checkpoint inspection, SHA-256 recording, and unit tests.
- Prepared the pinned runtime constraints, server preflight, and reproducible execution scripts for deployment on the replacement GPU server.

**Challenges & blockers**

- The authorized Gibson dataset remained unavailable, so the experiment retained the documented Habitat `test-scenes` fallback. Results from this profile cannot be presented as Gibson or HM3D benchmark results.
- The original execution host was no longer the correct target for the closeout matrix, so the frozen protocol needed a reproducible migration and server-validation path before formal execution.
- The project needed a single defensible intervention tied to observed failures. Additional PPO tuning, sensor changes, architecture changes, and success-threshold changes were excluded.

**Next steps**

- Complete the environment and data preflight gates.
- Run six fresh training jobs: baseline and DSR across seeds `100/200/300`.
- Evaluate each fresh final checkpoint on the same fixed 100-episode protocol.
- Aggregate only fresh formal evaluations and exclude diagnostic and smoke runs.

**Hours spent (optional):** 40

**Evidence copies in this repository**

- `src/experiments/closeout_dsr/protocol.env`
- `src/experiments/closeout_dsr/dsr_math.py`
- `src/experiments/closeout_dsr/dynamic_success_reward_env.py`
- `src/experiments/closeout_dsr/preflight.sh`
- `src/experiments/closeout_dsr/aggregate_results.py`
- `src/experiments/closeout_dsr/README.md`
