# Week 1 Environment Note: Habitat PointNav Baseline

## Project Direction

- Project: End-to-End Navigation for an AMR with Reinforcement Learning.
- Chosen starter path: Habitat RL navigation path.
- Selected baseline direction: Habitat PointNav baseline.
- Week 1 scope: configure one runnable Habitat stack, run minimal Habitat-Sim and PointNav smoke tests, and save evidence. The Week 1 result is execution proof, not a trained baseline score.

## Remote Machine

- SSH target used for evidence: `ubuntu@10.190.20.110`
- Hostname: `DESKTOP-FVE9SUP`
- OS: Ubuntu 26.04 LTS
- Kernel: `7.0.0-22-generic`
- Hardware: Lenovo ThinkStation P350
- GPU: NVIDIA GeForce RTX 3060, 12 GB VRAM
- NVIDIA driver: `595.71.05`
- CUDA reported by `nvidia-smi`: `13.2`

SSH from the Windows workspace required binding to the WLAN source address (`10.176.167.215`) because the default route used a tunnel interface that opened TCP 22 but failed before the SSH banner.

## Python / Habitat Environment

- Environment manager: micromamba
- Micromamba root: `/home/ubuntu/micromamba`
- Conda environment: `habitat`
- Environment Python: `3.9.19`
- Habitat-Lab location: `/home/ubuntu/habitat-lab`
- Habitat-Sim: `0.3.3`
- Habitat-Baselines: `0.3.3`
- PyTorch: `2.8.0+cu128`
- CUDA available in PyTorch: yes
- Dependency check: `pip check` reports no broken requirements.

Activate with:

```bash
source ~/activate_habitat_vlnce.sh
cd ~/habitat-lab
```

## Downloaded Test Data

- Habitat test scenes: `/home/ubuntu/habitat-lab/data/scene_datasets/habitat-test-scenes`
- Habitat test PointNav dataset: `/home/ubuntu/habitat-lab/data/datasets/pointnav/habitat-test-scenes`

The PointNav dataset was downloaded with:

```bash
python -m habitat_sim.utils.datasets_download --uids habitat_test_pointnav_dataset --data-path data/
```

## Smoke Test Evidence

Habitat import / path smoke test:

- Evidence file: `habitat_vlnce_smoke.txt`
- Result: Habitat, Habitat-Baselines, Habitat-Sim, CUDA PyTorch, Habitat-Lab repo path, and test scene path all checked successfully.

Habitat-Sim renderer smoke test:

- Evidence file: `habitat_test_scene_render_smoke.txt`
- Frame: `habitat_test_scene_frame.png`
- Result: loaded `skokloster-castle.glb`, loaded the navmesh, sampled a navigable point, rendered a `256 x 256` frame, and wrote `result: ok`.

PyTorch CUDA smoke test:

- Evidence file: `torch_cuda_smoke.txt`
- Result: CUDA tensor operation ran on `NVIDIA GeForce RTX 3060` with `result: ok`.

Habitat PointNav smoke test:

- Remote script: `/home/ubuntu/habitat-lab/week01_pointnav_smoke.py`
- Repository copy: `../experiments/week01/habitat_pointnav_smoke.py`
- Evidence file: `pointnav_smoke.txt`
- Frame: `pointnav_smoke_frame.png`
- Result: loaded `10000` Habitat test PointNav episodes, reset one episode, executed 5 non-STOP actions, and saved an RGB frame.

Observed PointNav smoke-test metrics:

```text
distance_to_goal: 11.814451217651367
success: 0.0
spl: 0.0
distance_to_goal_reward: -0.0
```

These metrics are expected for a random 5-step smoke test. The goal was to prove that the PointNav environment can execute on the chosen stack.

## Week 2 Direction

- Select the exact Habitat-Baselines PointNav baseline config and command.
- Decide whether to begin with a pretrained/random-policy evaluation or a tiny PPO training run.
- Record fixed seed, config, command, dataset split, output directory, and checkpoint path.
- Track success rate, SPL/path efficiency, episode reward, collision rate, and training stability.
- Begin collecting successful and failed PointNav cases once a real baseline evaluation runs.
