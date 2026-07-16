#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
# shellcheck source=protocol.env
source "$SCRIPT_DIR/protocol.env"

CHECKPOINT_PATH="${CHECKPOINT_PATH:-${1:-}}"
if [[ -z "$CHECKPOINT_PATH" ]] || [[ ! -f "$CHECKPOINT_PATH" ]]; then
  printf 'Set CHECKPOINT_PATH or pass an exact trusted checkpoint file as argument 1.\n' >&2
  exit 2
fi
CHECKPOINT_PATH="$(realpath "$CHECKPOINT_PATH")"
EVAL_SEED="${EVAL_SEED:-2026}"

case "$PROFILE" in
  gibson)
    CONFIG_NAME="pointnav/ppo_pointnav"
    SOURCE_CONFIG="$HABITAT_ROOT/habitat-baselines/habitat_baselines/config/pointnav/ppo_pointnav.yaml"
    EVAL_NUM_ENVIRONMENTS="${EVAL_NUM_ENVIRONMENTS:-$GIBSON_EVAL_NUM_ENVIRONMENTS}"
    ;;
  habitat_test)
    CONFIG_NAME="pointnav/ppo_pointnav_example"
    SOURCE_CONFIG="$HABITAT_ROOT/habitat-baselines/habitat_baselines/config/pointnav/ppo_pointnav_example.yaml"
    EVAL_NUM_ENVIRONMENTS="${EVAL_NUM_ENVIRONMENTS:-$HABITAT_TEST_EVAL_NUM_ENVIRONMENTS}"
    ;;
  *)
    printf 'Unknown PROFILE=%s; expected gibson or habitat_test.\n' "$PROFILE" >&2
    exit 2
    ;;
esac

checkpoint_stem="$(basename "$CHECKPOINT_PATH" .pth)"
RUN_ID="${RUN_ID:-week3-4_eval_${PROFILE}_evalseed${EVAL_SEED}_${checkpoint_stem}_$(date -u +%Y%m%dT%H%M%SZ)}"
if [[ ! "$RUN_ID" =~ ^[A-Za-z0-9._-]+$ ]]; then
  printf 'RUN_ID may contain only letters, digits, dot, underscore, and hyphen: %s\n' "$RUN_ID" >&2
  exit 2
fi

RUN_ROOT="${2:-$REPO_ROOT/src/results/week3-4/$RUN_ID}"
if [[ -e "$RUN_ROOT/command.txt" ]] || [[ -e "$RUN_ROOT/run_status.txt" ]]; then
  printf 'Refusing to overwrite an existing evaluation: %s\n' "$RUN_ROOT" >&2
  exit 2
fi
mkdir -p "$RUN_ROOT/tb" "$RUN_ROOT/video" "$RUN_ROOT/eval_state"
RUN_ROOT="$(realpath "$RUN_ROOT")"

PROFILE="$PROFILE" HABITAT_ROOT="$HABITAT_ROOT" PYTHON_BIN="$PYTHON_BIN" \
EXPECTED_HABITAT_REVISION="$EXPECTED_HABITAT_REVISION" \
ALLOW_REVISION_MISMATCH="$ALLOW_REVISION_MISMATCH" \
SCENE_DATASET_CONFIG="$SCENE_DATASET_CONFIG" \
MIN_GIBSON_SCENES="$MIN_GIBSON_SCENES" \
bash "$SCRIPT_DIR/preflight.sh" "$RUN_ROOT/preflight"

cp "$SOURCE_CONFIG" "$RUN_ROOT/upstream_policy_config.yaml"
sha256sum "$CHECKPOINT_PATH" > "$RUN_ROOT/checkpoint_sha256.txt"
printf '%s\n' "$CHECKPOINT_PATH" > "$RUN_ROOT/checkpoint_path.txt"

"$PYTHON_BIN" "$SCRIPT_DIR/inspect_checkpoint.py" \
  --checkpoint "$CHECKPOINT_PATH" \
  --expected-min-steps 0 \
  --expected-profile "$PROFILE" \
  --output "$RUN_ROOT/input_checkpoint.json"

if [[ "$SAVE_VIDEO" == "1" ]]; then
  video_option='["disk"]'
else
  video_option='[]'
fi

cmd=(
  "$PYTHON_BIN" -u -m habitat_baselines.run
  "--config-name=$CONFIG_NAME"
  "habitat.seed=$EVAL_SEED"
  "habitat_baselines.evaluate=True"
  "habitat_baselines.load_resume_state_config=False"
  "habitat_baselines.eval_ckpt_path_dir=$CHECKPOINT_PATH"
  "habitat_baselines.checkpoint_folder=$RUN_ROOT/eval_state"
  "habitat_baselines.tensorboard_dir=$RUN_ROOT/tb"
  "habitat_baselines.video_dir=$RUN_ROOT/video"
  "habitat_baselines.test_episode_count=$EVAL_EPISODES"
  "habitat_baselines.num_environments=$EVAL_NUM_ENVIRONMENTS"
  "habitat_baselines.eval.split=$EVAL_SPLIT"
  "habitat_baselines.eval.video_option=$video_option"
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
  printf 'evaluation_seed=%s\n' "$EVAL_SEED"
  printf 'eval_split=%s\n' "$EVAL_SPLIT"
  printf 'eval_episodes=%s\n' "$EVAL_EPISODES"
  printf 'save_video=%s\n' "$SAVE_VIDEO"
  printf 'checkpoint=%s\n' "$CHECKPOINT_PATH"
  printf 'command='
  printf '%q ' "${cmd[@]}"
  printf '\n'
} | tee "$RUN_ROOT/command.txt"

if [[ -f "$EGL_VENDOR_JSON" ]]; then
  export __EGL_VENDOR_LIBRARY_FILENAMES="$EGL_VENDOR_JSON"
fi
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"

# Habitat 0.3.3 checkpoints contain more than a plain state_dict. PyTorch 2.6+
# defaults to a restricted loader. This compatibility setting is safe only for
# checkpoints generated and controlled by this project.
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD="${TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD:-1}"

cd "$HABITAT_ROOT"
set +e
"${cmd[@]}" 2>&1 | tee "$RUN_ROOT/eval.log"
eval_exit=${PIPESTATUS[0]}
set -e

if (( eval_exit != 0 )); then
  printf 'status=failed\nexit_code=%s\nutc_end=%s\n' \
    "$eval_exit" "$(date -u --iso-8601=seconds)" | tee "$RUN_ROOT/run_status.txt"
  exit "$eval_exit"
fi

"$PYTHON_BIN" "$SCRIPT_DIR/summarize_eval.py" \
  --log "$RUN_ROOT/eval.log" \
  --output "$RUN_ROOT/summary.json" \
  --markdown-output "$RUN_ROOT/summary.md" \
  --profile "$PROFILE" \
  --config "$CONFIG_NAME" \
  --seed "$EVAL_SEED" \
  --split "$EVAL_SPLIT" \
  --episodes "$EVAL_EPISODES" \
  --checkpoint "$CHECKPOINT_PATH"

find "$RUN_ROOT/video" -type f -printf '%P\t%s bytes\n' | sort > "$RUN_ROOT/video_files.txt"
find "$RUN_ROOT/video" -type f -print0 | sort -z | xargs -0 -r sha256sum \
  > "$RUN_ROOT/video_sha256.txt"

printf 'status=passed\nexit_code=0\nutc_end=%s\n' \
  "$(date -u --iso-8601=seconds)" | tee "$RUN_ROOT/run_status.txt"
