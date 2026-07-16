# Week 2 Metrics and Case Record

## Run record

| Run id | Policy/control | Config | Seed | Dataset/split | Steps | Episodes | Success | SPL | Reward | Distance to goal | Collision rate | Evidence status |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| `20260715T130658Z/shortest_path` | Habitat shortest-path follower | `pointnav_habitat_test.yaml` | N/A | Habitat test scenes, train split | mean 39.33 actions | 3 | `1.0000` | mean `0.9963` | N/A | mean `0.1051 m` | Not exposed by this config | Complete oracle/control run |
| `20260715T130658Z/tiny_ppo_seed100_1000` | PPO execution verification | `ppo_pointnav_example.yaml` plus recorded overrides | 100 | Habitat test scenes, train split | 1,000 requested | No separate evaluation | last training window `0.000` | last training window `0.000` | last training window `-0.039` | last training window `8.610 m` | Not recorded | Complete execution gate; not an evaluation |
| `baseline_eval_001` | Learned PPO checkpoint | TBD | 100 | Future validation split | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Week 3 work |

The tiny PPO diagnostics above are the final reported training window at update 30 / frame 960. They are recorded only to show that metric logging worked; they do not support a learned-policy performance claim.

## Deterministic episode record

| Episode | Episode id | Initial geodesic distance | Actions | Final distance to goal | Success | SPL | Final frame |
|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 3662 | `11.3938 m` | 77 | `0.1569 m` | 1 | `1.0000` | `remote_20260715T130658Z/shortest_path/episode_01_final.png` |
| 2 | 4171 | `1.9838 m` | 10 | `0.0249 m` | 1 | `0.9889` | `remote_20260715T130658Z/shortest_path/episode_02_final.png` |
| 3 | 1354 | `3.9184 m` | 31 | `0.1335 m` | 1 | `1.0000` | `remote_20260715T130658Z/shortest_path/episode_03_final.png` |
| **Mean** | - | **`5.7654 m`** | **39.33** | **`0.1051 m`** | **`1.0000`** | **`0.9963`** | - |

## Reproducibility record

| Field | Value |
|---|---|
| Run id | `20260715T130658Z` |
| UTC preflight | `2026-07-15T13:06:56+00:00` |
| Tiny PPO UTC start/end | `2026-07-15T13:07:59+00:00` / `2026-07-15T13:08:27+00:00` |
| Hostname | `DESKTOP-FVE9SUP` |
| GPU and driver | NVIDIA GeForce RTX 3060, driver 595.71.05, 12,288 MiB |
| PyTorch/CUDA | PyTorch 2.8.0+cu128; CUDA 12.8; CUDA available |
| Habitat-Lab revision | `cdbb4880519505adf45fba0f0c0c3a3fd18a2a55` |
| Habitat packages | habitat-lab 0.3.3; habitat-baselines 0.3.3; habitat-sim 0.3.3 |
| Exact command | `remote_20260715T130658Z/tiny_ppo_seed100_1000/command.txt` |
| Config snapshots | `remote_20260715T130658Z/preflight/*.yaml` and `remote_20260715T130658Z/tiny_ppo_seed100_1000/ppo_pointnav_example.yaml` |
| Checkpoints | `ckpt.0.pth` and `latest.pth`, each 23,379,245 bytes |
| Checkpoint SHA-256 | `ckpt.0.pth`: `5D44279DABEC2E13D5B0A30A9C00C4196FB6A809279814DABC735D8E4E718A9A`; `latest.pth`: `F9B8EE0F531A3FB34F7AF7C35EC2ABCA4B4B6DF41A2C1F8FF81AA834DA8D156A` |
| TensorBoard/log | `remote_20260715T130658Z/tiny_ppo_seed100_1000/tb/` and `train.log` |

## Qualitative cases

| Case | Evidence-backed observation | Interpretation |
|---|---|---|
| Episode 3662 | Longest control case: 77 actions from `11.3938 m`, ending at `0.1569 m` with success `1` and SPL `1.0000` | The task, STOP behavior, and metric pipeline work on the longest sampled path |
| Episode 4171 | Shortest control case: 10 actions from `1.9838 m`, ending at `0.0249 m` with success `1` and SPL `0.9889` | A successful stop can have SPL below 1 when the executed path is slightly longer than the shortest path |
| Episode 1354 | Medium control case: 31 actions from `3.9184 m`, ending at `0.1335 m` with success `1` and SPL `1.0000` | The control completed a second efficient path at a different initial distance |
