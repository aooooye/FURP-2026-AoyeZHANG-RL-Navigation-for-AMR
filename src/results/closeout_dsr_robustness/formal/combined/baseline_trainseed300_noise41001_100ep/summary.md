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
| `distance_to_goal` | 0.4203 |
| `distance_to_goal_reward` | 0.0011 |
| `non_stop_failure` | 0.03 |
| `premature_stop` | 0.08 |
| `reward` | 7.0667 |
| `spl` | 0.7372 |
| `stop_called` | 0.97 |
| `success` | 0.89 |

Optional metric availability is recorded in `summary.json`. Missing metrics are not estimated.
