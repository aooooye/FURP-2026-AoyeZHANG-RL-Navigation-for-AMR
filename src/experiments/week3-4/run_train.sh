#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
# shellcheck source=protocol.env
source "$SCRIPT_DIR/protocol.env"

TRAIN_SEED="${TRAIN_SEED:-$PRIMARY_SEED}"
PPO_ROLLOUT_STEPS="${PPO_ROLLOUT_STEPS:-32}"
case "$PROFILE" in
  gibson)
    CONFIG_NAME="pointnav/ppo_pointnav"
    SOURCE_CONFIG="$HABITAT_ROOT/habitat-baselines/habitat_baselines/config/pointnav/ppo_pointnav.yaml"
    TOTAL_STEPS="${TOTAL_STEPS:-$GIBSON_TOTAL_STEPS}"
    NUM_ENVIRONMENTS="${NUM_ENVIRONMENTS:-$GIBSON_NUM_ENVIRONMENTS}"
    ;;
  habitat_test)
    CONFIG_NAME="pointnav/ppo_pointnav_example"
    SOURCE_CONFIG="$HABITAT_ROOT/habitat-baselines/habitat_baselines/config/pointnav/ppo_pointnav_example.yaml"
    TOTAL_STEPS="${TOTAL_STEPS:-$HABITAT_TEST_TOTAL_STEPS}"
    NUM_ENVIRONMENTS="${NUM_ENVIRONMENTS:-$HABITAT_TEST_NUM_ENVIRONMENTS}"
    ;;
  *)
    printf 'Unknown PROFILE=%s; expected gibson or habitat_test.\n' "$PROFILE" >&2
    exit 2
    ;;
esac

if (( NUM_CHECKPOINTS < 1 )); then
  printf 'NUM_CHECKPOINTS must be at least 1: %s\n' "$NUM_CHECKPOINTS" >&2
  exit 2
fi

# Habitat 0.3.3's num_checkpoints mode saves once immediately because its
# internal checkpoint percentage starts at -1, and it can therefore miss the
# final fixed-budget state. Use an explicit update interval instead. With the
# pinned PPO configs, each update collects PPO_ROLLOUT_STEPS per environment.
steps_per_update=$((PPO_ROLLOUT_STEPS * NUM_ENVIRONMENTS))
checkpoint_interval_updates=$(( \
  (TOTAL_STEPS + steps_per_update * NUM_CHECKPOINTS - 1) \
    / (steps_per_update * NUM_CHECKPOINTS) \
))

RUN_ID="${RUN_ID:-week3-4_${PROFILE}_trainseed${TRAIN_SEED}_${TOTAL_STEPS}_$(date -u +%Y%m%dT%H%M%SZ)}"
if [[ ! "$RUN_ID" =~ ^[A-Za-z0-9._-]+$ ]]; then
  printf 'RUN_ID may contain only letters, digits, dot, underscore, and hyphen: %s\n' "$RUN_ID" >&2
  exit 2
fi

RUN_ROOT="${1:-$REPO_ROOT/src/results/week3-4/$RUN_ID}"
if [[ -e "$RUN_ROOT/command.txt" ]] || [[ -e "$RUN_ROOT/run_status.txt" ]]; then
  printf 'Refusing to overwrite an existing run: %s\n' "$RUN_ROOT" >&2
  exit 2
fi
mkdir -p "$RUN_ROOT/checkpoints" "$RUN_ROOT/tb" "$RUN_ROOT/video"
RUN_ROOT="$(realpath "$RUN_ROOT")"
CHECKPOINT_DIR="$RUN_ROOT/checkpoints"
TB_DIR="$RUN_ROOT/tb"
VIDEO_DIR="$RUN_ROOT/video"

PROFILE="$PROFILE" HABITAT_ROOT="$HABITAT_ROOT" PYTHON_BIN="$PYTHON_BIN" \
EXPECTED_HABITAT_REVISION="$EXPECTED_HABITAT_REVISION" \
ALLOW_REVISION_MISMATCH="$ALLOW_REVISION_MISMATCH" \
SCENE_DATASET_CONFIG="$SCENE_DATASET_CONFIG" \
MIN_GIBSON_SCENES="$MIN_GIBSON_SCENES" \
bash "$SCRIPT_DIR/preflight.sh" "$RUN_ROOT/preflight"

cp "$SOURCE_CONFIG" "$RUN_ROOT/upstream_policy_config.yaml"

cmd=(
  "$PYTHON_BIN" -u -m habitat_baselines.run
  "--config-name=$CONFIG_NAME"
  "habitat.seed=$TRAIN_SEED"
  "habitat_baselines.evaluate=False"
  "habitat_baselines.total_num_steps=$TOTAL_STEPS"
  "habitat_baselines.num_updates=-1"
  "habitat_baselines.num_environments=$NUM_ENVIRONMENTS"
  "habitat_baselines.num_checkpoints=-1"
  "habitat_baselines.checkpoint_interval=$checkpoint_interval_updates"
  "habitat_baselines.checkpoint_folder=$CHECKPOINT_DIR"
  "habitat_baselines.tensorboard_dir=$TB_DIR"
  "habitat_baselines.video_dir=$VIDEO_DIR"
)

if [[ "$PROFILE" == "gibson" ]]; then
  if [[ "$SCENE_DATASET_CONFIG" = /* ]]; then
    scene_config_abs="$SCENE_DATASET_CONFIG"
  else
    scene_config_abs="$HABITAT_ROOT/$SCENE_DATASET_CONFIG"
  fi
  cmd+=("habitat.simulator.scene_dataset=$scene_config_abs")
fi

{
  printf 'utc_start=%s\n' "$(date -u --iso-8601=seconds)"
  printf 'run_id=%s\n' "$RUN_ID"
  printf 'profile=%s\n' "$PROFILE"
  printf 'training_seed=%s\n' "$TRAIN_SEED"
  printf 'total_steps=%s\n' "$TOTAL_STEPS"
  printf 'num_environments=%s\n' "$NUM_ENVIRONMENTS"
  printf 'num_checkpoints=%s\n' "$NUM_CHECKPOINTS"
  printf 'ppo_rollout_steps=%s\n' "$PPO_ROLLOUT_STEPS"
  printf 'checkpoint_interval_updates=%s\n' "$checkpoint_interval_updates"
  printf 'habitat_root=%s\n' "$HABITAT_ROOT"
  printf 'command='
  printf '%q ' "${cmd[@]}"
  printf '\n'
} | tee "$RUN_ROOT/command.txt"

git -C "$HABITAT_ROOT" rev-parse HEAD > "$RUN_ROOT/habitat_lab_revision.txt"
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free \
  --format=csv,noheader > "$RUN_ROOT/nvidia_smi_summary.txt"

if [[ -f "$EGL_VENDOR_JSON" ]]; then
  export __EGL_VENDOR_LIBRARY_FILENAMES="$EGL_VENDOR_JSON"
fi
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"

cd "$HABITAT_ROOT"
set +e
"${cmd[@]}" 2>&1 | tee "$RUN_ROOT/train.log"
train_exit=${PIPESTATUS[0]}
set -e

if (( train_exit != 0 )); then
  printf 'status=failed\nexit_code=%s\nutc_end=%s\n' \
    "$train_exit" "$(date -u --iso-8601=seconds)" | tee "$RUN_ROOT/run_status.txt"
  exit "$train_exit"
fi

find "$CHECKPOINT_DIR" -maxdepth 1 -type f -name '*.pth' -printf '%f\t%s bytes\n' \
  | sort > "$RUN_ROOT/checkpoint_files.txt"
find "$CHECKPOINT_DIR" -maxdepth 1 -type f -name '*.pth' -print0 \
  | sort -z | xargs -0 -r sha256sum > "$RUN_ROOT/checkpoint_sha256.txt"
find "$TB_DIR" -type f -printf '%P\t%s bytes\n' | sort > "$RUN_ROOT/tensorboard_files.txt"

if [[ ! -s "$RUN_ROOT/checkpoint_files.txt" ]]; then
  printf 'Training exited without a checkpoint inventory.\n' >&2
  printf 'status=failed\nexit_code=1\nreason=no_checkpoints\nutc_end=%s\n' \
    "$(date -u --iso-8601=seconds)" | tee "$RUN_ROOT/run_status.txt"
  exit 1
fi
if [[ ! -s "$RUN_ROOT/tensorboard_files.txt" ]]; then
  printf 'Training exited without TensorBoard output.\n' >&2
  printf 'status=failed\nexit_code=1\nreason=no_tensorboard_output\nutc_end=%s\n' \
    "$(date -u --iso-8601=seconds)" | tee "$RUN_ROOT/run_status.txt"
  exit 1
fi

FINAL_CHECKPOINT="$(find "$CHECKPOINT_DIR" -maxdepth 1 -type f -name 'ckpt.*.pth' \
  | sort -V | tail -n 1)"
if [[ -z "$FINAL_CHECKPOINT" ]] || [[ ! -f "$FINAL_CHECKPOINT" ]]; then
  FINAL_CHECKPOINT="$CHECKPOINT_DIR/latest.pth"
fi
if [[ -z "$FINAL_CHECKPOINT" ]] || [[ ! -f "$FINAL_CHECKPOINT" ]]; then
  printf 'status=failed\nexit_code=1\nreason=no_final_checkpoint\nutc_end=%s\n' \
    "$(date -u --iso-8601=seconds)" | tee "$RUN_ROOT/run_status.txt"
  exit 1
fi
printf '%s\n' "$FINAL_CHECKPOINT" > "$RUN_ROOT/final_checkpoint_path.txt"

set +e
"$PYTHON_BIN" "$SCRIPT_DIR/inspect_checkpoint.py" \
  --checkpoint "$FINAL_CHECKPOINT" \
  --expected-min-steps "$TOTAL_STEPS" \
  --expected-profile "$PROFILE" \
  --expected-training-seed "$TRAIN_SEED" \
  --output "$RUN_ROOT/final_checkpoint.json" \
  2>&1 | tee "$RUN_ROOT/final_checkpoint_inspection.txt"
inspection_exit=${PIPESTATUS[0]}
set -e
if (( inspection_exit != 0 )); then
  printf 'status=failed\nexit_code=%s\nreason=checkpoint_below_frozen_budget\nutc_end=%s\n' \
    "$inspection_exit" "$(date -u --iso-8601=seconds)" | tee "$RUN_ROOT/run_status.txt"
  exit "$inspection_exit"
fi

printf 'status=passed\nexit_code=0\nutc_end=%s\n' \
  "$(date -u --iso-8601=seconds)" | tee "$RUN_ROOT/run_status.txt"
