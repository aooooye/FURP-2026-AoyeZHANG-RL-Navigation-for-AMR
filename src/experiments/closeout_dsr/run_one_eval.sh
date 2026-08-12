#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
# shellcheck source=protocol.env
source "$SCRIPT_DIR/protocol.env"

CONDITION="${1:-}"
TRAIN_SEED="${2:-}"
CHECKPOINT_PATH="${3:-}"
if [[ "$CONDITION" != "baseline" && "$CONDITION" != "dsr" ]]; then
  printf 'Usage: %s baseline|dsr TRAIN_SEED CHECKPOINT_PATH [SAVE_VIDEO] [main|diagnostic]\n' "$0" >&2
  exit 2
fi
if [[ ! " $TRAIN_SEEDS " =~ " $TRAIN_SEED " ]]; then
  printf 'TRAIN_SEED must be one of the frozen seeds: %s\n' "$TRAIN_SEEDS" >&2
  exit 2
fi
if [[ ! -f "$CHECKPOINT_PATH" ]]; then
  printf 'Checkpoint not found: %s\n' "$CHECKPOINT_PATH" >&2
  exit 2
fi
CHECKPOINT_PATH="$(realpath "$CHECKPOINT_PATH")"
SAVE_VIDEO="${4:-0}"
if [[ "$SAVE_VIDEO" != "0" && "$SAVE_VIDEO" != "1" ]]; then
  printf 'SAVE_VIDEO must be 0 or 1.\n' >&2
  exit 2
fi
EVAL_ROLE="${5:-main}"
if [[ "$EVAL_ROLE" != "main" && "$EVAL_ROLE" != "diagnostic" ]]; then
  printf 'EVAL_ROLE must be main or diagnostic.\n' >&2
  exit 2
fi
if [[ "$EVAL_ROLE" == "diagnostic" ]] \
  && [[ "$CONDITION" != "baseline" || "$TRAIN_SEED" != "100" ]]; then
  printf 'The migration diagnostic is frozen to baseline seed 100.\n' >&2
  exit 2
fi

if [[ "$EVAL_ROLE" == "diagnostic" ]]; then
  RUN_ID="closeout_diagnostic_oldbaseline_trainseed100_evalseed${EVAL_SEED}_100ep"
else
  RUN_ID="closeout_eval_${CONDITION}_trainseed${TRAIN_SEED}_evalseed${EVAL_SEED}_100ep"
fi
RUN_ROOT="$REPO_ROOT/src/results/closeout_dsr/$RUN_ID"
if grep -qx 'status=passed' "$RUN_ROOT/run_status.txt" 2>/dev/null; then
  expected_checkpoint_hash="$(sha256sum "$CHECKPOINT_PATH" | awk '{print $1}')"
  recorded_checkpoint_hash="$(awk 'NR==1 {print $1}' "$RUN_ROOT/checkpoint_sha256.txt" 2>/dev/null || true)"
  video_artifacts_ok=1
  if [[ "$SAVE_VIDEO" == "1" && ! -s "$RUN_ROOT/video_files.txt" ]]; then
    video_artifacts_ok=0
  fi
  if [[ "$recorded_checkpoint_hash" == "$expected_checkpoint_hash" ]] \
    && grep -Fxq "training_condition=$CONDITION" "$RUN_ROOT/condition_manifest.txt" \
    && grep -Fxq "training_seed=$TRAIN_SEED" "$RUN_ROOT/condition_manifest.txt" \
    && grep -Fxq "evaluation_role=$EVAL_ROLE" "$RUN_ROOT/condition_manifest.txt" \
    && grep -Fxq "save_video=$SAVE_VIDEO" "$RUN_ROOT/condition_manifest.txt" \
    && (( video_artifacts_ok == 1 )); then
    printf 'Already passed with the same checkpoint and role; preserving evaluation: %s\n' "$RUN_ROOT"
    exit 0
  fi
  printf 'Passed evaluation exists but checkpoint, role, or video request differs: %s\n' "$RUN_ROOT" >&2
  exit 2
fi
if [[ -e "$RUN_ROOT" ]]; then
  printf 'Existing incomplete evaluation requires inspection; refusing overwrite: %s\n' "$RUN_ROOT" >&2
  exit 2
fi
mkdir -p "$RUN_ROOT"

{
  printf 'training_condition=%s\n' "$CONDITION"
  printf 'training_seed=%s\n' "$TRAIN_SEED"
  printf 'evaluation_role=%s\n' "$EVAL_ROLE"
  printf 'evaluation_seed=%s\n' "$EVAL_SEED"
  printf 'evaluation_environment=standard Habitat 0.3.3 reward/dynamics plus STOP diagnostics\n'
  printf 'evaluation_reward=standard Habitat 0.3.3 reward\n'
  printf 'diagnostics=stop_called,premature_stop,non_stop_failure\n'
  printf 'save_video=%s\n' "$SAVE_VIDEO"
} > "$RUN_ROOT/condition_manifest.txt"

# All policies use standard Habitat reward and dynamics. The diagnostic wrapper
# adds terminal numeric info only, so metrics and reported reward stay comparable.
export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"
export HABITAT_RUNNER_SCRIPT="$SCRIPT_DIR/run_habitat_with_dsr.py"
export HABITAT_ENV_TASK_OVERRIDE="$DIAGNOSTIC_ENV_TASK"
export PROFILE EVAL_SEED EVAL_EPISODES EVAL_NUM_ENVIRONMENTS EVAL_SPLIT
export SAVE_VIDEO RUN_ID HABITAT_ROOT PYTHON_BIN EXPECTED_HABITAT_REVISION
export EGL_VENDOR_JSON CHECKPOINT_PATH ALLOW_REVISION_MISMATCH PYTHONNOUSERSITE

set +e
bash "$SCRIPT_DIR/../week03/run_eval.sh" "$CHECKPOINT_PATH" "$RUN_ROOT"
run_exit=$?
set -e
if (( run_exit != 0 )); then
  if [[ ! -f "$RUN_ROOT/run_status.txt" ]]; then
    printf 'status=failed\nexit_code=%s\nreason=wrapper_or_preflight_failure\n' "$run_exit" \
      > "$RUN_ROOT/run_status.txt"
  fi
  exit "$run_exit"
fi
