# Weeks 3 & 4 - 2026-07-16

**Attended this week's meeting:** Yes

**Progress during Weeks 3 & 4**

- Ran the Gibson gate on the RTX 3060 host. The pinned Habitat revision, packages, CUDA, and GPU passed, but the authorized Gibson scenes and PointNav Gibson train/validation files were absent.
- Followed the documented fallback instead of claiming a Gibson result. The Habitat test-scenes profile passed preflight with three `.glb` scenes, valid train/validation archives, Habitat packages `0.3.3`, PyTorch `2.8.0+cu128`, and revision `cdbb4880519505adf45fba0f0c0c3a3fd18a2a55`.
- Completed the same-profile calibration with seed `100`, five environments, and a requested 10,000-step budget. Its final checkpoint records `10,080` steps and is treated only as an execution gate.
- Completed the fallback training run with seed `100`, five environments, 1,000,000 environment steps, ten checkpoints, a TensorBoard event, exact commands, config snapshots, logs, inventories, and hashes.
- Selected the final fixed-budget checkpoint `ckpt.9.pth` before validation. It records exactly `1,000,000` steps and has SHA-256 `e662c5e2f5546266ebcf8765ef61a743fd9416969c3bd6755561ad0d6133bed0`.
- Completed the separate evaluation on `100` fixed-seed `val` episodes: Success `0.9200`, SPL `0.8389`, mean reward `7.7472`, and mean final distance to goal `0.1062 m`.
- Completed the separate video evaluation. It reproduced the quantitative aggregate, saved `99` videos, and provided at least three real learned-policy successes and three failures for case review.
- Reviewed the selected failures. All three stopped at `0.21-0.30 m`, just outside the configured `0.20 m` success radius, so they are recorded as premature-STOP / threshold-miss cases.
- Completed the results review and verified that calibration, learned training, fixed validation, and qualitative cases are reported as separate evidence classes.
- Passed the engineering baseline gate for the documented fallback, but placed the formal RGB-D versus depth-only ablation on hold because the validation profile has only two scenes and the completed policy has only one training seed.

**Challenges & blockers**

- Habitat 0.3.3's percentage-based checkpoint schedule can save an initial checkpoint and miss the final state. The runner now uses an explicit update interval and verifies the final checkpoint step.
- The validation split has two scenes. A first five-environment evaluation exited before episode 1 because the evaluator reduced the active batch to two scenes; rerunning with two evaluation environments completed all 100 episodes.

**Next steps**

- Reproduce the RGB-D baseline on that profile and complete at least one repeat training seed under the same fixed evaluation.
- Start the formal RGB-D versus depth-only ablation only after those entry conditions pass, changing only the observation input.

**Evidence copies in this repository**

- `src/experiments/week3-4/`
- `src/results/week3-4/orchestration_summary.json`
- `src/results/week3-4/README.md`
- `src/results/week3-4/metrics_template.md`
- `src/results/week3-4/cases_template.md`
- `src/results/week3-4/selected_cases/`
- `src/results/week3-4/remote_20260716T074249Z/`
