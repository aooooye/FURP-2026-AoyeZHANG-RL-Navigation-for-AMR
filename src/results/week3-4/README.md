# PointNav PPO Fallback Baseline

## Model Summary

| Item | Value |
|---|---|
| Architecture | ResNet18 visual encoder + GRU policy |
| Parameters | 5,821,797 |
| Algorithm | PPO |
| Sensors | RGB 256×256 + Depth 256×256 + GPS+Compass |
| Actions | Stop, move forward, turn left, turn right |
| Dataset | Habitat test-scenes PointNav v1 fallback |
| Base config | `pointnav/ppo_pointnav_example` |
| Habitat revision | `cdbb4880519505adf45fba0f0c0c3a3fd18a2a55` |
| Training seed | `100` |
| Evaluation seed | `2026` |

## Final Checkpoint

| File | Step | Size | SHA-256 |
|---|---:|---:|---|
| `ckpt.9.pth` | 1,000,000 | 23,379,309 bytes | `e662c5e2f5546266ebcf8765ef61a743fd9416969c3bd6755561ad0d6133bed0` |

- Ten main checkpoints were saved across the frozen budget.
- Final-checkpoint inspection status: `complete`.
- Training artifacts: `remote_20260716T074249Z/week03_habitat_test_seed100_1m_env5/`

## Final Metrics

Metrics come from the separately launched final-checkpoint evaluation, not from a rolling training window.

| Split | Episodes | Success | SPL | Reward | Distance to goal |
|---|---:|---:|---:|---:|---:|
| `val` | 100 | 92.00% | 83.89% | 7.7472 | 0.1062 m |

Collision and additional path statistics were not exposed by the resolved evaluator and remain unavailable.

Evaluation artifacts:

- `remote_20260716T074249Z/week03_eval_habitat_test_seed2026_100ep_ckpt9_env2/summary.json`
- `remote_20260716T074249Z/week03_eval_habitat_test_seed2026_100ep_ckpt9_env2/summary.md`
- `remote_20260716T074249Z/week03_eval_habitat_test_seed2026_100ep_ckpt9_env2/eval.log`

## Evaluation Videos

- 99 videos were saved from a separate 100-episode video run.
- Saved outcomes: 91 successes and 8 failures.
- Three success and three failure cases were selected for review under `selected_cases/`.
- The reviewed failures stopped at `0.21-0.30 m`, just outside the configured `0.20 m` success radius, and are classified as premature STOP / threshold misses.

Detailed case records are stored in `cases_template.md`.

## Environment

| Item | Value |
|---|---|
| GPU | NVIDIA GeForce RTX 3060, 12 GB |
| Habitat-Sim | 0.3.3 |
| Habitat-Lab | 0.3.3 |
| Habitat-Baselines | 0.3.3 |
| PyTorch | 2.8.0+cu128 |
| Python | 3.9.19 |
| Training environments | 5 |
| Evaluation environments | 2 |

The validation split contains two scenes, so evaluation used two environments. A five-environment attempt exited before episode 1 because the active scene batch was reduced to two.

## Reproducibility

Calibration:

```bash
PROFILE=habitat_test TOTAL_STEPS=10000 NUM_ENVIRONMENTS=5 \
NUM_CHECKPOINTS=1 TRAIN_SEED=100 \
RUN_ID=week3-4_habitat_test_calibration_seed100_10k_env5 \
bash src/experiments/week3-4/run_train.sh
```

Training:

```bash
PROFILE=habitat_test TOTAL_STEPS=1000000 NUM_ENVIRONMENTS=5 \
NUM_CHECKPOINTS=10 TRAIN_SEED=100 \
RUN_ID=week3-4_habitat_test_seed100_1m_env5 \
bash src/experiments/week3-4/run_train.sh
```

Fixed evaluation:

```bash
PROFILE=habitat_test EVAL_NUM_ENVIRONMENTS=2 EVAL_EPISODES=100 \
EVAL_SEED=2026 SAVE_VIDEO=0 \
CHECKPOINT_PATH=/absolute/path/to/ckpt.9.pth \
bash src/experiments/week3-4/run_eval.sh
```

## Baseline Decision

- Engineering baseline gate: **pass** for the documented fallback.
- Formal RGB-D versus depth-only ablation gate: **hold**.
- Reason: the validation profile contains only two scenes and only seed `100` has completed training.
- Before formal ablation, use a documented multi-scene train/validation profile and complete at least one repeat RGB-D baseline seed under the same fixed evaluation.

## Evidence

- `orchestration_summary.json`
- `metrics_template.md`
- `cases_template.md`
- `selected_cases/`
- `remote_20260716T074249Z/`

Large checkpoints, TensorBoard events, and MP4 files remain local and are ignored. Credentials and dataset archives are not stored.
