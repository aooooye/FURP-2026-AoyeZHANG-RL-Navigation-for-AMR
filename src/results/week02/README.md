# Week 2 PointNav Verification Results

Week 2 advances the project from the verified Week 1 environment smoke test to a reproducible PointNav experiment pipeline. Results are consolidated here, while the detailed metric and case table remains in `metrics_template.md` and the captured runtime artifacts remain under `remote_20260715T130658Z/`.

## Experiment Summary

| Item | Recorded value |
|---|---|
| Task | Habitat PointNav |
| Reproduction target | Official Habitat-Lab v0.3.3 PointNav PPO example |
| Policy / algorithm | `PointNavResNetPolicy` / PPO |
| Policy parameters | Approximately 5.82 million trainable parameters |
| Sensors | RGB `256 x 256`, depth `256 x 256`, and point-goal input from the task config |
| Verification seed | `100` |
| Training environments | `1` |
| Verification budget | `1,000` requested environment steps |
| Run id | `20260715T130658Z` |
| Evidence root | `src/results/week02/remote_20260715T130658Z/` |

PointNav was selected as the first learned-navigation target because the task and data path were already verified in Week 1 and it introduces fewer confounding factors than ObjectNav or language-guided navigation. The intended follow-up experiment is a controlled RGB-D versus depth-only comparison after a learned baseline is reproducible.

## Environment

| Item | Recorded value |
|---|---|
| Hostname | `DESKTOP-FVE9SUP` |
| GPU | NVIDIA GeForce RTX 3060, 12,288 MiB |
| Driver | `595.71.05` |
| PyTorch / CUDA | PyTorch `2.8.0+cu128`; CUDA `12.8`; CUDA available |
| Habitat packages | habitat-lab `0.3.3`; habitat-baselines `0.3.3`; habitat-sim `0.3.3` |
| Habitat-Lab revision | `cdbb4880519505adf45fba0f0c0c3a3fd18a2a55` |

## Preflight

| Check | Result | Status |
|---|---|---|
| CUDA and RTX 3060 discovery | Available | **Passed** |
| Habitat imports and versions | All required packages loaded | **Passed** |
| Official PPO example config | `pointnav/ppo_pointnav_example.yaml` present | **Passed** |
| PointNav task config | `pointnav_habitat_test.yaml` present | **Passed** |
| Habitat test scenes and PointNav episodes | Required paths present | **Passed** |
| Config and environment capture | YAML snapshots, package list, GPU summary, and revision retained | **Passed** |

The upstream Gym deprecation warning and duplicate Magnum plugin warnings did not block imports, CUDA discovery, configuration loading, task execution, or training.

## Deterministic Control Results

| Episode id | Initial geodesic distance | Actions | Final distance to goal | Success | SPL |
|---:|---:|---:|---:|---:|---:|
| 3662 | `11.3938 m` | 77 | `0.1569 m` | 1 | `1.0000` |
| 4171 | `1.9838 m` | 10 | `0.0249 m` | 1 | `0.9889` |
| 1354 | `3.9184 m` | 31 | `0.1335 m` | 1 | `1.0000` |
| **Mean** | **`5.7654 m`** | **39.33** | **`0.1051 m`** | **`1.0000`** | **`0.9963`** |

The acceptance threshold was at least two successes across three recorded episodes. The control achieved `3/3` successes, and all three final RGB frames were retained. This result verifies task navigability, STOP behavior, and metric generation.

## Tiny PPO Verification

| Item | Recorded result |
|---|---|
| UTC start / end | `2026-07-15T13:07:59+00:00` / `2026-07-15T13:08:27+00:00` |
| Process status | Clean exit with `status=passed` |
| Checkpoints | `ckpt.0.pth` and `latest.pth`, each 23,379,245 bytes |
| TensorBoard | One event file, 44,120 bytes |
| Training log | `train.log` retained |
| Exact command and config | `command.txt` and `ppo_pointnav_example.yaml` retained |

The recorded training-window diagnostics are:

| Update / frame | FPS | Distance to goal | Reward | SPL | Success |
|---|---:|---:|---:|---:|---:|
| 10 / 320 | 28.326 | 8.794 | -0.057 | 0.000 | 0.000 |
| 20 / 640 | 47.026 | 8.774 | -0.038 | 0.000 | 0.000 |
| 30 / 960 | 60.387 | 8.610 | -0.039 | 0.000 | 0.000 |

These values show that logging worked. They are rolling training diagnostics, not results from a fixed evaluation set.

## Result Artifacts

- Consolidated metric and case record: `src/results/week02/metrics_template.md`
- Preflight evidence: `src/results/week02/remote_20260715T130658Z/preflight/`
- Deterministic control evidence: `src/results/week02/remote_20260715T130658Z/shortest_path/`
- Tiny PPO evidence: `src/results/week02/remote_20260715T130658Z/tiny_ppo_seed100_1000/`
- Runtime summary: `src/results/week02/remote_20260715T130658Z/orchestration_summary.json`
- Downloaded evidence archive: `src/results/week02/remote_20260715T130658Z.tar.gz`

The archive is `43,222,776` bytes with SHA-256 `0203AF8B75E421188F233BD98BD296CC45FDCE214CE5FBDA2250D276DE99593C`.

## Reproducibility

The captured verification command was:

```bash
python -u -m habitat_baselines.run \
  --config-name=pointnav/ppo_pointnav_example.yaml \
  habitat.seed=100 \
  habitat_baselines.total_num_steps=1000 \
  habitat_baselines.num_environments=1 \
  habitat_baselines.num_checkpoints=1 \
  habitat_baselines.checkpoint_folder=/home/ubuntu/week02_codex_20260715T130658Z/results/tiny_ppo_seed100_1000/checkpoints \
  habitat_baselines.tensorboard_dir=/home/ubuntu/week02_codex_20260715T130658Z/results/tiny_ppo_seed100_1000/tb \
  habitat_baselines.video_dir=/home/ubuntu/week02_codex_20260715T130658Z/results/tiny_ppo_seed100_1000/video
```

Runnable repository scripts and their required order are documented in `src/experiments/week02/README.md`.

## Interpretation Boundary

- The deterministic shortest-path follower is an oracle/control, not a learned-policy result.
- The 1,000-step PPO run verifies execution, logging, checkpointing, TensorBoard output, and evidence packaging; it is not a converged baseline.
- Training-window Success, SPL, reward, and distance values must not be reported as fixed-set evaluation performance.
- Collision rate was not exposed by the recorded configuration and is not estimated.
- A longer baseline must freeze the dataset split, observation set, reward, PPO settings, training budget, seeds, checkpoint policy, and independent evaluation command before performance claims are made.
