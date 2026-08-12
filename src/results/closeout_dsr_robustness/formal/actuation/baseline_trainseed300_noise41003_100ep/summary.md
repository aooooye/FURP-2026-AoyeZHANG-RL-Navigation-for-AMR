# Week 3 Fixed Evaluation Summary

- Status: **complete**
- Profile: `habitat_test`
- Config: `pointnav/ppo_pointnav_example`
- Seed: `2026`
- Split: `val`
- Episodes requested: `100`
- Checkpoint: `/home/furp/FURP-2026-AoyeZHANG-RL-Navigation-for-AMR/src/results/closeout_dsr/closeout_baseline_trainseed300_1m_env5/checkpoints/ckpt.9.pth`

| Metric | Mean |
|---|---:|
| `distance_to_goal` | 0.4779 |
| `distance_to_goal_reward` | 0 |
| `non_stop_failure` | 0.04 |
| `premature_stop` | 0.06 |
| `reward` | 6.9938 |
| `spl` | 0.758 |
| `stop_called` | 0.96 |
| `success` | 0.9 |

Optional metric availability is recorded in `summary.json`. Missing metrics are not estimated.
