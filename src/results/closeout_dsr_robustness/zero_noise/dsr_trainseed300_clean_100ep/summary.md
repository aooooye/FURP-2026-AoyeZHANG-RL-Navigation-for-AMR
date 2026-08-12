# Week 3 Fixed Evaluation Summary

- Status: **complete**
- Profile: `habitat_test`
- Config: `pointnav/ppo_pointnav_example`
- Seed: `2026`
- Split: `val`
- Episodes requested: `100`
- Checkpoint: `/home/furp/FURP-2026-AoyeZHANG-RL-Navigation-for-AMR/src/results/closeout_dsr/closeout_dsr_trainseed300_1m_env5/checkpoints/ckpt.9.pth`

| Metric | Mean |
|---|---:|
| `distance_to_goal` | 0.2372 |
| `distance_to_goal_reward` | 0 |
| `non_stop_failure` | 0.01 |
| `premature_stop` | 0.03 |
| `reward` | 7.6735 |
| `spl` | 0.8646 |
| `stop_called` | 0.99 |
| `success` | 0.96 |

Optional metric availability is recorded in `summary.json`. Missing metrics are not estimated.
