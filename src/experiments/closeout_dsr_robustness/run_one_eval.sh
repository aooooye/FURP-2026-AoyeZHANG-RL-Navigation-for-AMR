#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CLOSEOUT_DIR="$SCRIPT_DIR/../closeout_dsr"
WEEK03_DIR="$SCRIPT_DIR/../week03"
# shellcheck source=../closeout_dsr/protocol.env
source "$CLOSEOUT_DIR/protocol.env"

PHASE="${1:-}"
NOISE_CONDITION="${2:-}"
METHOD="${3:-}"
TRAIN_SEED="${4:-}"
NOISE_SEED="${5:-}"
CHECKPOINT_PATH="${6:-}"
if [[ -z "$PHASE" || -z "$NOISE_CONDITION" || -z "$METHOD" \
  || -z "$TRAIN_SEED" || -z "$NOISE_SEED" || -z "$CHECKPOINT_PATH" ]]; then
  printf 'Usage: %s zero_noise|smoke|formal CONDITION baseline|dsr TRAIN_SEED NOISE_SEED CHECKPOINT\n' "$0" >&2
  exit 2
fi
if [[ ! -f "$CHECKPOINT_PATH" ]]; then
  printf 'Checkpoint not found: %s\n' "$CHECKPOINT_PATH" >&2
  exit 2
fi
CHECKPOINT_PATH="$(realpath "$CHECKPOINT_PATH")"

case "$PHASE" in
  zero_noise)
    EXPECTED_EPISODES=100
    RUN_REL="zero_noise/${METHOD}_trainseed${TRAIN_SEED}_clean_100ep"
    ;;
  smoke)
    EXPECTED_EPISODES=2
    RUN_REL="smoke/${NOISE_CONDITION}/${METHOD}_trainseed${TRAIN_SEED}_noise${NOISE_SEED}_2ep"
    ;;
  formal)
    EXPECTED_EPISODES=100
    RUN_REL="formal/${NOISE_CONDITION}/${METHOD}_trainseed${TRAIN_SEED}_noise${NOISE_SEED}_100ep"
    ;;
  *)
    printf 'Unknown phase: %s\n' "$PHASE" >&2
    exit 2
    ;;
esac

RESULTS_ROOT="$REPO_ROOT/src/results/closeout_dsr_robustness"
RUN_ROOT="$RESULTS_ROOT/$RUN_REL"
if grep -qx 'status=passed' "$RUN_ROOT/run_status.txt" 2>/dev/null; then
  "$PYTHON_BIN" "$SCRIPT_DIR/protocol_guard.py" verify-run \
    --phase "$PHASE" \
    --condition "$NOISE_CONDITION" \
    --method "$METHOD" \
    --train-seed "$TRAIN_SEED" \
    --noise-seed "$NOISE_SEED" \
    --run-root "$RUN_ROOT"
  printf 'Already passed with the frozen identity; preserving: %s\n' "$RUN_ROOT"
  exit 0
fi
if [[ -e "$RUN_ROOT" ]]; then
  printf 'Existing incomplete or failed run requires inspection; refusing overwrite: %s\n' "$RUN_ROOT" >&2
  exit 2
fi

"$PYTHON_BIN" "$SCRIPT_DIR/protocol_guard.py" freeze \
  --results-root "$RESULTS_ROOT"
mkdir -p "$RUN_ROOT/episode_shards"
"$PYTHON_BIN" "$SCRIPT_DIR/protocol_guard.py" validate-run \
  --phase "$PHASE" \
  --condition "$NOISE_CONDITION" \
  --method "$METHOD" \
  --train-seed "$TRAIN_SEED" \
  --noise-seed "$NOISE_SEED" \
  --checkpoint "$CHECKPOINT_PATH" \
  --output "$RUN_ROOT/condition_manifest.json"

manifest_value() {
  "$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))[sys.argv[2]])' \
    "$RUN_ROOT/condition_manifest.json" "$1"
}

export ROBUSTNESS_RUN_PHASE="$PHASE"
export ROBUSTNESS_CONDITION="$NOISE_CONDITION"
export ROBUSTNESS_METHOD="$METHOD"
export ROBUSTNESS_TRAIN_SEED="$TRAIN_SEED"
export ROBUSTNESS_NOISE_SEED="$NOISE_SEED"
export ROBUSTNESS_PROTOCOL_PATH="$SCRIPT_DIR/protocol.json"
export ROBUSTNESS_PROTOCOL_SHA256
ROBUSTNESS_PROTOCOL_SHA256="$(manifest_value protocol_sha256)"
export ROBUSTNESS_CHECKPOINT_SHA256
ROBUSTNESS_CHECKPOINT_SHA256="$(manifest_value checkpoint_sha256)"
export ROBUSTNESS_CHECKPOINT_MANIFEST_SHA256
ROBUSTNESS_CHECKPOINT_MANIFEST_SHA256="$(manifest_value checkpoint_manifest_sha256)"
export ROBUSTNESS_NOISE_MANIFEST_SHA256
ROBUSTNESS_NOISE_MANIFEST_SHA256="$(manifest_value noise_manifest_sha256)"
export ROBUSTNESS_RUN_IDENTITY_SHA256
ROBUSTNESS_RUN_IDENTITY_SHA256="$(manifest_value run_identity_sha256)"
export ROBUSTNESS_EPISODE_SHARD_DIR="$RUN_ROOT/episode_shards"

export PYTHONPATH="$SCRIPT_DIR:$CLOSEOUT_DIR${PYTHONPATH:+:$PYTHONPATH}"
export HABITAT_RUNNER_SCRIPT="$SCRIPT_DIR/run_habitat_with_robustness.py"
export HABITAT_ENV_TASK_OVERRIDE="RobustnessGymHabitatEnv"
export PROFILE EVAL_SEED EVAL_NUM_ENVIRONMENTS EVAL_SPLIT
export EVAL_EPISODES="$EXPECTED_EPISODES"
export SAVE_VIDEO=0
export RUN_ID="robustness_${PHASE}_${NOISE_CONDITION}_${METHOD}_trainseed${TRAIN_SEED}_noise${NOISE_SEED}"
export HABITAT_ROOT PYTHON_BIN EXPECTED_HABITAT_REVISION EGL_VENDOR_JSON
export CHECKPOINT_PATH ALLOW_REVISION_MISMATCH PYTHONNOUSERSITE

set +e
bash "$WEEK03_DIR/run_eval.sh" "$CHECKPOINT_PATH" "$RUN_ROOT"
eval_exit=$?
set -e
if (( eval_exit != 0 )); then
  exit "$eval_exit"
fi

finalize_args=(
  "$PYTHON_BIN" "$SCRIPT_DIR/finalize_run.py"
  --run-root "$RUN_ROOT"
  --expected-episodes "$EXPECTED_EPISODES"
)
if [[ "$PHASE" == "zero_noise" ]]; then
  reference_summary="$REPO_ROOT/src/results/closeout_dsr/closeout_eval_${METHOD}_trainseed${TRAIN_SEED}_evalseed2026_100ep/summary.json"
  finalize_args+=(--reference-summary "$reference_summary")
fi

set +e
"${finalize_args[@]}"
finalize_exit=$?
set -e
if (( finalize_exit != 0 )); then
  printf 'status=failed\nexit_code=%s\nreason=episode_evidence_validation_failed\nutc_end=%s\n' \
    "$finalize_exit" "$(date -u --iso-8601=seconds)" > "$RUN_ROOT/run_status.txt"
  exit "$finalize_exit"
fi

printf 'status=passed\nexit_code=0\nutc_end=%s\n' \
  "$(date -u --iso-8601=seconds)" > "$RUN_ROOT/run_status.txt"
printf 'Robustness evaluation passed: %s\n' "$RUN_ROOT"
