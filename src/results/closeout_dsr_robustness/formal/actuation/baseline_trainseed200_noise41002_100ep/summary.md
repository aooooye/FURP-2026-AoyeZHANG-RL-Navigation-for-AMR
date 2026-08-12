# Week 3 Fixed Evaluation Summary

- Status: **complete**
- Profile: `habitat_test`
- Config: `pointnav/ppo_pointnav_example`
- Seed: `2026`
- Split: `val`
- Episodes requested: `100`
- Checkpoint: `/home/furp/FURP-2026-AoyeZHANG-RL-Navigation-for-AMR/src/results/closeout_dsr/closeout_baseline_trainseed200_1m_env5/checkpoints/ckpt.9.pth`

| Metric | Mean |
|---|---:|
| `distance_to_goal` | 0.6189 |
| `distance_to_goal_reward` | 0 |
| `non_stop_failure` | 0.07 |
| `premature_stop` | 0.06 |
| `reward` | 6.7675 |
| `spl` | 0.7582 |
| `stop_called` | 0.93 |
| `success` | 0.87 |

Optional metric availability is recorded in `summary.json`. Missing metrics are not estimated.
