# Week 2 PointNav Preparation

These scripts move the project from a Week 1 random-action smoke test to a reproducible learned-policy pipeline without starting an uncontrolled full training run.

## Assumptions

- Ubuntu host with NVIDIA RTX 3060;
- Habitat-Lab checkout at `~/habitat-lab`;
- activated `habitat` micromamba/conda environment;
- Habitat-Lab, Habitat-Sim, and Habitat-Baselines v0.3.3-compatible installation;
- Habitat test scenes and PointNav test episodes already downloaded.

## Run order

From the repository root on the Ubuntu host:

```bash
export MAMBA_ROOT_PREFIX="$HOME/micromamba"
eval "$("$HOME/.local/bin/micromamba" shell hook -s bash)"
micromamba activate habitat

export HABITAT_ROOT="$HOME/habitat-lab"
bash src/experiments/week02/preflight.sh
bash src/experiments/week02/run_shortest_path.sh
SEED=100 TOTAL_STEPS=1000 bash src/experiments/week02/run_tiny_ppo.sh
```

Do not run the third command if either earlier command fails.

## Outputs

The scripts write under `src/results/week02/` by default:

- `preflight/`: versions, GPU, exact revision, path checks, and copied configs;
- `shortest_path/`: stdout, summary JSON, per-episode JSONL, and final frames;
- `tiny_ppo_seed100_1000/`: exact command, training log, config snapshot, checkpoint inventory, and TensorBoard inventory.

Model checkpoint files are ignored by the repository. Record their filenames, sizes, and hashes; do not commit large `.pth` files.

## Interpretation

- The shortest-path follower is an oracle/control, not an RL result.
- The 1,000-step PPO run is an execution/evidence test, not a converged baseline.
- Full Gibson training starts only after the recorded preflight, deterministic control, and tiny PPO verification complete successfully. Their consolidated outcome is in `src/results/week02/README.md`.
