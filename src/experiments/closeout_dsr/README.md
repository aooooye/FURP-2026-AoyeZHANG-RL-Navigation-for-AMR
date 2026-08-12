# Frozen clean comparison: Dynamic Success Reward

This directory contains the completed first-stage clean baseline-versus-DSR experiment. It ports the paper-defined Dynamic Success Reward (DSR) to the pinned Habitat 0.3.3 environment without modifying the installed Habitat source.

**Status:** complete. The six fresh training runs and six fixed evaluations passed. The authoritative aggregate is [`../../results/closeout_dsr/comparison.json`](../../results/closeout_dsr/comparison.json), with a readable summary in [`../../results/closeout_dsr/comparison.md`](../../results/closeout_dsr/comparison.md). Do not rerun or alter the frozen protocol merely to change the observed result.

## Frozen comparison

| Item | Baseline | DSR |
|---|---|---|
| Policy/config | `pointnav/ppo_pointnav_example` | same |
| Dataset | Habitat test-scenes fallback | same |
| Training steps | 1,000,000 | same |
| Training environments | 5 | same |
| Training seeds | 100, 200, 300 | 100, 200, 300 |
| Evaluation | seed 2026, val, 100 episodes, 2 environments | same |
| Success threshold | 0.20 m | same |
| Reward change | none | successful STOP bonus uses DSR |
| Failed STOP penalty | none | none |

DSR is applied only on a successful STOP:

```text
success_reward * exp((success_distance - final_distance) / success_distance)
```

Habitat's constant success reward is 2.5 and the frozen success distance is 0.20 m. No coefficient, threshold, sensor, PPO setting, or training budget may be tuned after results are observed.

The source is Grande, Batra, and Wijmans, [Realistic PointGoal Navigation via Auxiliary Losses and Information Bottleneck](https://arxiv.org/abs/2109.08677), with the authors' [reference implementation](https://github.com/NicoGrande/habitat-pointnav-via-ib/blob/master/habitat_baselines/common/environments.py).

## Why this implementation is low-risk

- `dynamic_success_reward_env.py` subclasses the public Habitat 0.3.3 `RLTaskEnv` API and registers a new Gym environment.
- Standard slack and geodesic-progress rewards are inherited unchanged.
- Habitat's existing constant success bonus is replaced by adding only `DSR - constant_bonus`.
- The installed Habitat checkout remains unmodified and must stay at commit `cdbb4880519505adf45fba0f0c0c3a3fd18a2a55`.
- Every policy is evaluated with standard reward and dynamics plus a diagnostic-only wrapper that reports `stop_called`, `premature_stop`, and `non_stop_failure`; policy behavior and evaluation reward remain comparable.

## Ignored checkpoint required for full reproduction

The existing seed-100 baseline checkpoint is local and ignored by Git. It must be transferred with the working tree for the environment/mechanism gate; it is not used as one of the final same-server comparison runs:

```text
src/results/week03/remote_20260716T074249Z/
  week03_habitat_test_seed100_1m_env5/checkpoints/ckpt.9.pth
  week03_eval_habitat_test_seed2026_100ep_ckpt9_env2/summary.json
```

Their expected hashes are stored in `baseline_seed100.sha256`. A remote Git clone alone is not sufficient unless the ignored checkpoint is transferred separately.

## Reproduction sequence

Run these commands on the allocated Ubuntu server.

### 1. Allocation gate

```bash
bash src/experiments/closeout_dsr/server_preflight.sh
```

This verifies GPU memory, driver, CPU, RAM, persistent disk, EGL, system tools, and access to the required package sources.

### 2. Environment bootstrap

Ask the administrator to install the listed system packages and `micromamba`. Then, only if an image of the proven old environment cannot be restored:

```bash
bash src/experiments/closeout_dsr/bootstrap_server.sh
```

The script refuses to overwrite an existing `habitat` environment or `~/habitat-lab` checkout. It installs the proven core versions, checks out the exact Habitat commit, downloads only official Habitat test data, and runs a headless EGL/CUDA smoke check.

If this script is interrupted by a network or quota failure, it preserves a script-owned state marker. Fix the infrastructure cause and resume the same installation without changing versions:

```bash
BOOTSTRAP_RESUME=1 bash src/experiments/closeout_dsr/bootstrap_server.sh
```

Resume is accepted only when the environment name, Habitat path, revision, and state marker match the original attempt.

Do not use `tools/setup_habitat_rl_vm.sh` for this closeout: that older helper checks out the moving `stable` branch and does not pin the exact Habitat-Sim build.

Activate the resulting environment and set the same root for every command:

```bash
export MAMBA_ROOT_PREFIX="$HOME/micromamba"
eval "$(micromamba shell hook -s bash)"
micromamba activate habitat
export HABITAT_ROOT="$HOME/habitat-lab"
```

### 3. Transfer and verify the project

Transfer the local working tree plus the ignored final checkpoint. From the project root on the server:

```bash
sha256sum -c src/experiments/closeout_dsr/baseline_seed100.sha256
```

Do not proceed if either hash differs.

### 4. Run the complete frozen matrix

For a persistent SSH-safe run:

```bash
bash src/experiments/closeout_dsr/launch_matrix_detached.sh
tail -f src/results/closeout_dsr/matrix_launcher/launcher.log
```

The matrix performs, in order:

1. full environment/data/revision/plugin preflight;
2. a diagnostic re-evaluation of the transferred old baseline seed-100 checkpoint and a mechanism/reproduction gate;
3. 10,000-step baseline and DSR integrity smokes, ignored for performance decisions;
4. fresh same-server training in paired order `baseline-100, DSR-100, baseline-200, DSR-200, baseline-300, DSR-300`;
5. fixed 100-episode diagnostic evaluation immediately after each new training run;
6. disk videos for the DSR seed-100 evaluation for failure-mechanism review;
7. final three-seed aggregation.

There are six new 1M-step training runs. Re-running baseline seed 100 on the new server avoids mixing old- and new-host training artifacts in the main comparison; the transferred old checkpoint remains a compatibility and mechanism gate only.

## Failure handling

- A failed allocation or Habitat preflight stops all training. Fix infrastructure only; do not alter the protocol.
- A smoke run validates execution only. Its performance must not be used to choose or reject DSR.
- If a run fails for an infrastructure reason, first fix that cause. Preserve the failed canonical run and failed `matrix_launcher` with `archive_failed_attempt.sh`, then relaunch the unchanged matrix; completed runs are reused only after their hashes and manifests match. Do not change seed, reward, steps, or PPO settings.
- A null or negative final comparison is still the project result. Do not switch to wrong-STOP penalties, threshold changes, sensor ablations, PPO tuning, HM3D/Gibson migration, ROS, or Gazebo after inspection.

## Claim boundary

The final result is a controlled, failure-driven reward ablation on the two-scene Habitat test-scenes fallback. The diagnostic wrapper changes only numeric terminal info, not reward or dynamics. The result is not a Gibson/HM3D benchmark, a proof of statistical significance, a new navigation algorithm, or real-robot validation.
