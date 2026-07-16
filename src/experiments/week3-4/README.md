# Weeks 3 & 4 PointNav Baseline Reproduction

This directory implements the workflow documented in `docs/Week3-4.md` as a parameterized, evidence-preserving pipeline. A completed Habitat test-scenes fallback result is stored under `src/results/week3-4/remote_20260716T074249Z/`.

## Execution status

The 2026-07-16 Gibson gate failed because the authorized Gibson data was absent. The documented fallback then completed with seed 100, 1M total steps, five training environments, a final fixed-budget checkpoint, a separate 100-episode evaluation, and a separate video case run. See `docs/Week3-4.md` and `src/results/week3-4/README.md`.

## Core route

- primary dataset/profile: Gibson PointNav v1;
- policy: official Habitat RGB-D PPO config;
- primary training seed: 100;
- fixed evaluation seed: 2026 for every training-seed comparison;
- core training budget: 5M steps;
- quantitative evaluation: final checkpoint, fixed `val` split, 100 episodes;
- later extension: seeds 200/300, then RGB-D versus depth-only only after the core baseline passes.

The official config is pinned as `configs/ppo_pointnav_upstream_cdbb488.yaml`. The scripts run the matching config from the installed Habitat-Lab checkout and copy that live file into each run directory.

## Data gate

The Gibson scene archive cannot be fetched blindly: Habitat's documentation requires agreement to the Gibson terms of use. Prepare these paths on the training host:

```text
$HABITAT_ROOT/data/scene_datasets/gibson/
  gibson.scene_dataset_config.json
  *.glb                         # at least 88 scenes, recursively

$HABITAT_ROOT/data/datasets/pointnav/gibson/v1/
  train/train.json.gz
  val/val.json.gz
```

The PointNav episode archive is listed by Habitat as `pointnav_gibson_v1.zip`. The scene files must come from the Gibson-authorized download. Do not store dataset credentials in this repository.

## Commands

Run from the project repository on the Ubuntu training host with the Habitat environment activated.

### 1. Preflight

```bash
bash src/experiments/week3-4/preflight.sh
```

### 2. Same-protocol calibration

```bash
PROFILE=gibson TOTAL_STEPS=10000 NUM_CHECKPOINTS=1 \
RUN_ID=week3-4_calibration_seed100 \
bash src/experiments/week3-4/run_train.sh
```

This must create a checkpoint and TensorBoard event, but its metrics are not a learned-baseline result.

For later repeats, set `TRAIN_SEED=200` or `TRAIN_SEED=300`. Do not change `EVAL_SEED=2026` when comparing those policies.

### 3. Core 5M-step training

```bash
RUN_ID=week3-4_gibson_seed100_5m \
bash src/experiments/week3-4/run_train.sh
```

For a long SSH session, launch the same run under `nohup` and monitor the files instead of relying on the terminal connection:

```bash
RUN_ID=week3-4_gibson_seed100_5m \
bash src/experiments/week3-4/launch_detached.sh train

cat src/results/week3-4/week3-4_gibson_seed100_5m/launcher.pid
tail -f src/results/week3-4/week3-4_gibson_seed100_5m/launcher.log
```

### 4. Fixed validation evaluation

Pass one exact checkpoint file, normally the final fixed-budget checkpoint:

```bash
CHECKPOINT_PATH=src/results/week3-4/week3-4_gibson_seed100_5m/checkpoints/ckpt.9.pth \
EVAL_EPISODES=100 SAVE_VIDEO=0 \
bash src/experiments/week3-4/run_eval.sh
```

The evaluation can also be detached by setting the exact checkpoint and using `launch_detached.sh eval`.

Use `final_checkpoint_path.txt` and `final_checkpoint.json` from the training run to confirm the selected file and its completed step count. The runner uses an explicit update-based checkpoint interval because Habitat 0.3.3's percentage schedule can save an initial checkpoint and miss the final fixed-budget state.

### 5. Separate qualitative cases

```bash
CHECKPOINT_PATH=/absolute/path/to/the/final/checkpoint.pth \
EVAL_EPISODES=20 SAVE_VIDEO=1 \
bash src/experiments/week3-4/run_eval.sh
```

Continue case collection if those 20 episodes do not include at least 3 successes and 3 failures. The case run does not replace the 100-episode quantitative evaluation.

## Documented fallback

If Gibson fails the initial preflight because the authorized scene data is unavailable, use the already verified test-scene route and state the downgrade explicitly:

```bash
PROFILE=habitat_test RUN_ID=week3-4_habitat_test_seed100_1m \
bash src/experiments/week3-4/run_train.sh
```

This profile defaults to 1M steps and one environment. It may satisfy the execution/evaluation workflow, but it must not be described as a Gibson baseline or a full Habitat-paper reproduction.

To reproduce the completed fallback settings with the combined-week naming, use:

```bash
PROFILE=habitat_test TOTAL_STEPS=1000000 NUM_ENVIRONMENTS=5 \
NUM_CHECKPOINTS=10 TRAIN_SEED=100 \
RUN_ID=week3-4_habitat_test_seed100_1m_env5 \
bash src/experiments/week3-4/run_train.sh
```

Its validation split contains two scenes, so the completed evaluation used:

```bash
PROFILE=habitat_test EVAL_NUM_ENVIRONMENTS=2 EVAL_EPISODES=100 \
EVAL_SEED=2026 SAVE_VIDEO=0 \
CHECKPOINT_PATH=/absolute/path/to/ckpt.9.pth \
bash src/experiments/week3-4/run_eval.sh
```

## PyTorch 2.8 checkpoint compatibility

The evaluation script sets `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` so unmodified Habitat 0.3.3 call sites can load the project's own checkpoints under newer PyTorch versions. This disables the restricted weights-only loader for those call sites. Evaluate only checkpoints generated by this trusted project; never use the setting for an untrusted `.pth` file.

## Expected evidence

Each run refuses to overwrite an existing output and records:

- preflight output and pinned revision;
- exact shell-safe command;
- live upstream config snapshot;
- console log;
- GPU/package/data inventory;
- checkpoint and TensorBoard file inventories;
- checkpoint hashes;
- final-checkpoint step inspection against the frozen budget;
- evaluation JSON/Markdown summary;
- optional local videos plus a hash inventory.

Large checkpoints, TensorBoard events, and videos remain inside the project working tree but are ignored by `src/results/week3-4/.gitignore`. Their text inventories remain reviewable.
