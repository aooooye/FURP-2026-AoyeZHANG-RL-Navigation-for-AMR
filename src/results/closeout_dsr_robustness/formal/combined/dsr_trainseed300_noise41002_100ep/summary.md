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
| `distance_to_goal` | 0.3178 |
| `distance_to_goal_reward` | 0.0004 |
| `non_stop_failure` | 0.02 |
| `premature_stop` | 0.06 |
| `reward` | 7.3978 |
| `spl` | 0.8174 |
| `stop_called` | 0.98 |
| `success` | 0.92 |

Optional metric availability is recorded in `summary.json`. Missing metrics are not estimated.
