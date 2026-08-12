# Week 3 Fixed Evaluation Summary

- Status: **complete**
- Profile: `habitat_test`
- Config: `pointnav/ppo_pointnav_example`
- Seed: `2026`
- Split: `val`
- Episodes requested: `100`
- Checkpoint: `/home/furp/FURP-2026-AoyeZHANG-RL-Navigation-for-AMR/src/results/closeout_dsr/closeout_dsr_trainseed100_1m_env5/checkpoints/ckpt.9.pth`

| Metric | Mean |
|---|---:|
| `distance_to_goal` | 0.4026 |
| `distance_to_goal_reward` | -0.0001 |
| `non_stop_failure` | 0.04 |
| `premature_stop` | 0.02 |
| `reward` | 7.0894 |
| `spl` | 0.7734 |
| `stop_called` | 0.96 |
| `success` | 0.94 |

Optional metric availability is recorded in `summary.json`. Missing metrics are not estimated.
