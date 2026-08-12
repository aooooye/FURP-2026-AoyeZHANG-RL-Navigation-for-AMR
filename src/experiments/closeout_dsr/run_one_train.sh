#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
# shellcheck source=protocol.env
source "$SCRIPT_DIR/protocol.env"

CONDITION="${1:-}"
TRAIN_SEED="${2:-}"
if [[ "$CONDITION" != "baseline" && "$CONDITION" != "dsr" ]]; then
  printf 'Usage: %s baseline|dsr TRAIN_SEED\n' "$0" >&2
  exit 2
fi
if [[ ! " $TRAIN_SEEDS " =~ " $TRAIN_SEED " ]]; then
  printf 'TRAIN_SEED must be one of the frozen seeds: %s\n' "$TRAIN_SEEDS" >&2
  exit 2
fi

RUN_ID="closeout_${CONDITION}_trainseed${TRAIN_SEED}_1m_env5"
RUN_ROOT="$REPO_ROOT/src/results/closeout_dsr/$RUN_ID"
if grep -qx 'status=passed' "$RUN_ROOT/run_status.txt" 2>/dev/null; then
  if grep -Fxq "condition=$CONDITION" "$RUN_ROOT/condition_manifest.txt" \
    && grep -Fxq "training_seed=$TRAIN_SEED" "$RUN_ROOT/condition_manifest.txt" \
    && [[ -s "$RUN_ROOT/final_checkpoint_path.txt" ]] \
    && [[ -f "$(<"$RUN_ROOT/final_checkpoint_path.txt")" ]] \
    && sha256sum -c "$RUN_ROOT/closeout_implementation_sha256.txt" >/dev/null 2>&1; then
    printf 'Already passed with the same frozen inputs; preserving run: %s\n' "$RUN_ROOT"
    exit 0
  fi
  printf 'Passed run exists but its frozen inputs or artifacts differ: %s\n' "$RUN_ROOT" >&2
  exit 2
fi
if [[ -e "$RUN_ROOT" ]]; then
  printf 'Existing incomplete run requires inspection; refusing overwrite: %s\n' "$RUN_ROOT" >&2
  exit 2
fi
mkdir -p "$RUN_ROOT"

{
  printf 'condition=%s\n' "$CONDITION"
  printf 'training_seed=%s\n' "$TRAIN_SEED"
  printf 'formula=%s\n' "$([[ "$CONDITION" == "dsr" ]] && printf '%s' "$DSR_FORMULA" || printf 'standard Habitat 0.3.3 reward')"
  printf 'failed_stop_penalty=none\n'
  printf 'protocol_change_allowed=false\n'
} > "$RUN_ROOT/condition_manifest.txt"

sha256sum \
  "$SCRIPT_DIR/dsr_math.py" \
  "$SCRIPT_DIR/dynamic_success_reward_env.py" \
  "$SCRIPT_DIR/run_habitat_with_dsr.py" \
  "$SCRIPT_DIR/protocol.env" \
  "$SCRIPT_DIR/runtime_constraints.txt" \
  > "$RUN_ROOT/closeout_implementation_sha256.txt"

export PROFILE TOTAL_STEPS NUM_ENVIRONMENTS NUM_CHECKPOINTS
export TRAIN_SEED RUN_ID HABITAT_ROOT PYTHON_BIN EXPECTED_HABITAT_REVISION
export EGL_VENDOR_JSON ALLOW_REVISION_MISMATCH PYTHONNOUSERSITE

if [[ "$CONDITION" == "dsr" ]]; then
  export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"
  export HABITAT_RUNNER_SCRIPT="$SCRIPT_DIR/run_habitat_with_dsr.py"
  export HABITAT_ENV_TASK_OVERRIDE="$DSR_ENV_TASK"
else
  unset HABITAT_RUNNER_SCRIPT HABITAT_ENV_TASK_OVERRIDE || true
fi

set +e
bash "$SCRIPT_DIR/../week03/run_train.sh" "$RUN_ROOT"
run_exit=$?
set -e
if (( run_exit != 0 )); then
  if [[ ! -f "$RUN_ROOT/run_status.txt" ]]; then
    printf 'status=failed\nexit_code=%s\nreason=wrapper_or_preflight_failure\n' "$run_exit" \
      > "$RUN_ROOT/run_status.txt"
  fi
  exit "$run_exit"
fi
