#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HABITAT_ROOT="${HABITAT_ROOT:-$HOME/habitat-lab}"
SEED="${SEED:-100}"
TOTAL_STEPS="${TOTAL_STEPS:-1000}"
RUN_ID="tiny_ppo_seed${SEED}_${TOTAL_STEPS}"
OUTPUT_DIR="${1:-$REPO_ROOT/src/results/week02/$RUN_ID}"
PPO_CONFIG="$HABITAT_ROOT/habitat-baselines/habitat_baselines/config/pointnav/ppo_pointnav_example.yaml"

if [[ ! -f "$PPO_CONFIG" ]]; then
  printf 'Missing official example config: %s\n' "$PPO_CONFIG" >&2
  exit 1
fi

if [[ -e "$OUTPUT_DIR/command.txt" ]]; then
  printf 'Refusing to overwrite an existing run: %s\n' "$OUTPUT_DIR" >&2
  exit 2
fi

mkdir -p "$OUTPUT_DIR/checkpoints" "$OUTPUT_DIR/tb" "$OUTPUT_DIR/video"
cp "$PPO_CONFIG" "$OUTPUT_DIR/ppo_pointnav_example.yaml"

CHECKPOINT_DIR="$(realpath "$OUTPUT_DIR/checkpoints")"
TB_DIR="$(realpath "$OUTPUT_DIR/tb")"
VIDEO_DIR="$(realpath "$OUTPUT_DIR/video")"

cmd=(
  python -u -m habitat_baselines.run
  --config-name=pointnav/ppo_pointnav_example.yaml
  "habitat.seed=$SEED"
  "habitat_baselines.total_num_steps=$TOTAL_STEPS"
  habitat_baselines.num_environments=1
  habitat_baselines.num_checkpoints=1
  "habitat_baselines.checkpoint_folder=$CHECKPOINT_DIR"
  "habitat_baselines.tensorboard_dir=$TB_DIR"
  "habitat_baselines.video_dir=$VIDEO_DIR"
)

{
  printf 'utc_start=%s\n' "$(date -u --iso-8601=seconds)"
  printf 'habitat_root=%s\n' "$HABITAT_ROOT"
  printf 'seed=%s\n' "$SEED"
  printf 'total_steps=%s\n' "$TOTAL_STEPS"
  printf 'command='
  printf '%q ' "${cmd[@]}"
  printf '\n'
} | tee "$OUTPUT_DIR/command.txt"

git -C "$HABITAT_ROOT" rev-parse HEAD > "$OUTPUT_DIR/habitat_lab_revision.txt"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader \
  > "$OUTPUT_DIR/nvidia_smi_summary.txt"

cd "$HABITAT_ROOT"
"${cmd[@]}" 2>&1 | tee "$OUTPUT_DIR/train.log"

find "$CHECKPOINT_DIR" -maxdepth 1 -type f -name '*.pth' -printf '%f\t%s bytes\n' \
  | sort > "$OUTPUT_DIR/checkpoint_files.txt"
find "$TB_DIR" -type f -printf '%P\t%s bytes\n' \
  | sort > "$OUTPUT_DIR/tensorboard_files.txt"

if [[ ! -s "$OUTPUT_DIR/checkpoint_files.txt" ]]; then
  printf 'Tiny PPO run exited but created no checkpoint.\n' >&2
  exit 1
fi
if [[ ! -s "$OUTPUT_DIR/tensorboard_files.txt" ]]; then
  printf 'Tiny PPO run exited but created no TensorBoard output.\n' >&2
  exit 1
fi

printf 'utc_end=%s\nstatus=passed\n' "$(date -u --iso-8601=seconds)" \
  | tee "$OUTPUT_DIR/run_status.txt"
