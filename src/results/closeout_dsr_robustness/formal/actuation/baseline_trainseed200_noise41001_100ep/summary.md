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
| `distance_to_goal` | 0.3801 |
| `distance_to_goal_reward` | 0.0004 |
| `non_stop_failure` | 0.03 |
| `premature_stop` | 0.03 |
| `reward` | 7.2574 |
| `spl` | 0.8089 |
| `stop_called` | 0.97 |
| `success` | 0.94 |

Optional metric availability is recorded in `summary.json`. Missing metrics are not estimated.
