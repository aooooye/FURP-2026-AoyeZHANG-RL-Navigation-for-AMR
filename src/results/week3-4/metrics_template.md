# Weeks 3 & 4 Learned PointNav Metrics

Values below come only from the final fixed-budget checkpoint's separate validation evaluation.

| Run id | Profile | Config/revision | Train seed | Eval seed | Train steps | Eval split | Eval episodes | Success | SPL | Reward/return | Final distance | Collision/path stats | Evidence status |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| `week03_habitat_test_seed100_1m_env5` + `week03_eval_habitat_test_seed2026_100ep_ckpt9_env2` | Habitat test-scenes RGB-D fallback | `pointnav/ppo_pointnav_example` / `cdbb4880519505adf45fba0f0c0c3a3fd18a2a55` | 100 | 2026 | 1,000,000 | val | 100 | 0.9200 | 0.8389 | 7.7472 | 0.1062 m | unavailable; not exposed by resolved evaluator | Complete fallback result |

## Artifact record

| Item | In-repository path or value |
|---|---|
| Primary Gibson gate | `src/results/week3-4/remote_20260716T074249Z/gibson_gate/` |
| Passed fallback preflight | `src/results/week3-4/remote_20260716T074249Z/habitat_test_gate/` |
| Passed five-environment calibration | `src/results/week3-4/remote_20260716T074249Z/week03_habitat_test_calibration_seed100_10k_env5/` |
| Exact training command | `src/results/week3-4/remote_20260716T074249Z/week03_habitat_test_seed100_1m_env5/command.txt` |
| Training log | `src/results/week3-4/remote_20260716T074249Z/week03_habitat_test_seed100_1m_env5/train.log` |
| Config snapshot | `src/results/week3-4/remote_20260716T074249Z/week03_habitat_test_seed100_1m_env5/upstream_policy_config.yaml` |
| Final checkpoint | `ckpt.9.pth`, SHA-256 `e662c5e2f5546266ebcf8765ef61a743fd9416969c3bd6755561ad0d6133bed0` |
| Final checkpoint inspection | `src/results/week3-4/remote_20260716T074249Z/week03_habitat_test_seed100_1m_env5/final_checkpoint.json` |
| Checkpoint hash inventory | `src/results/week3-4/remote_20260716T074249Z/week03_habitat_test_seed100_1m_env5/checkpoint_primary_sha256.txt` |
| TensorBoard inventory | `src/results/week3-4/remote_20260716T074249Z/week03_habitat_test_seed100_1m_env5/tensorboard_files.txt` |
| Exact evaluation command | `src/results/week3-4/remote_20260716T074249Z/week03_eval_habitat_test_seed2026_100ep_ckpt9_env2/command.txt` |
| Evaluation log | `src/results/week3-4/remote_20260716T074249Z/week03_eval_habitat_test_seed2026_100ep_ckpt9_env2/eval.log` |
| Parsed JSON summary | `src/results/week3-4/remote_20260716T074249Z/week03_eval_habitat_test_seed2026_100ep_ckpt9_env2/summary.json` |
| Qualitative cases | `src/results/week3-4/cases_template.md` and `src/results/week3-4/selected_cases/` |

## Protocol boundary

- The Gibson data gate failed because authorized scenes and episode archives were absent.
- This row is the documented Habitat test-scenes fallback and must not be described as a Gibson baseline.
- The calibration and formal fallback run used five environments after a five-environment calibration passed on the RTX 3060.
- The fixed evaluation used two environments because the validation split contains two scenes.

## Claim check

- [x] Values come from the fixed `val` evaluation, not a training window.
- [x] The evaluated checkpoint is the final fixed-budget checkpoint selected before validation.
- [x] Dataset/profile, seed, steps, episode count, and Habitat revision are explicit.
- [x] Missing collision/path statistics are labelled unavailable rather than inferred.
- [x] The stopped single-environment attempt is retained as partial/failed and is not described as the completed run.

## Baseline decision

- Engineering baseline gate: **pass** for the Habitat test-scenes fallback.
- Formal RGB-D versus depth-only ablation gate: **hold**.
- Reason: the fixed validation profile contains only two scenes and only seed `100` has completed training.
- Required before formal ablation: a documented multi-scene train/validation profile and at least one repeat baseline seed under the same fixed evaluation.
