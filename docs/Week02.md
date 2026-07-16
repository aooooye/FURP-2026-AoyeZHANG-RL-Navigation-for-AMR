# Week 2 - 2026-07-15

**Attended this week's meeting:** Yes

**Progress this week**

- Completed the paper/task comparison and selected Habitat PointNav PPO as the first reproduction target based on the project's Week 1 evidence, available RTX 3060 hardware, and controlled-evaluation requirements.
- Passed the recorded Habitat v0.3.3/CUDA/data/config preflight on the RTX 3060 host.
- Ran a deterministic shortest-path control on three PointNav test episodes: 3/3 successes, mean SPL 0.9963, and mean final distance to goal 0.1051 m.
- Ran the official PointNav PPO example for 1,000 requested steps with seed 100 and one environment. It exited cleanly and produced an exact command record, config snapshot, log, checkpoints, and TensorBoard output.
- Packaged the complete evidence locally under `src/results/week02/remote_20260715T130658Z/` and filled the metric record without presenting the tiny run as a converged model.
- Completed the Week 2 results review: verified the metric/case table, documented unavailable metrics without estimating them, and froze the Week 3 entry criteria.

**Challenges & blockers**

- Upstream Gym deprecation and duplicate Magnum plugin warnings remain, but they did not block CUDA, Habitat imports, task execution, or training.


**Next steps**

- Freeze the Week 3 baseline training budget, seed set, validation split, checkpoint cadence, and evaluation command.
- Train the first learned PointNav baseline, then report Success, SPL, distance to goal, reward, and qualitative success/failure cases on a fixed evaluation set.
- After the baseline is reproducible, compare RGB-D with depth-only observation while keeping all other settings fixed.

**Hours spent (optional):** 30 h
