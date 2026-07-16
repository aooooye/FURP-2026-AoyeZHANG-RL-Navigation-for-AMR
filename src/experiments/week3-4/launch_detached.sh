#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Export the frozen defaults and any caller overrides to the detached child.
set -a
# shellcheck source=protocol.env
source "$SCRIPT_DIR/protocol.env"
set +a

MODE="${1:-}"
if [[ "$MODE" != "train" ]] && [[ "$MODE" != "eval" ]]; then
  printf 'Usage: %s train|eval\n' "$0" >&2
  printf 'For eval, also set CHECKPOINT_PATH to one trusted checkpoint file.\n' >&2
  exit 2
fi

if [[ "$MODE" == "train" ]]; then
  effective_seed="$TRAIN_SEED"
  seed_label="trainseed"
else
  effective_seed="$EVAL_SEED"
  seed_label="evalseed"
fi
RUN_ID="${RUN_ID:-week3-4_${MODE}_${PROFILE}_${seed_label}${effective_seed}_$(date -u +%Y%m%dT%H%M%SZ)}"
if [[ ! "$RUN_ID" =~ ^[A-Za-z0-9._-]+$ ]]; then
  printf 'RUN_ID may contain only letters, digits, dot, underscore, and hyphen: %s\n' "$RUN_ID" >&2
  exit 2
fi
export RUN_ID TRAIN_SEED EVAL_SEED

RUN_ROOT="${RUN_ROOT:-$REPO_ROOT/src/results/week3-4/$RUN_ID}"
if [[ -e "$RUN_ROOT/launcher.pid" ]] || [[ -e "$RUN_ROOT/command.txt" ]] || [[ -e "$RUN_ROOT/run_status.txt" ]]; then
  printf 'Refusing to overwrite an existing detached run: %s\n' "$RUN_ROOT" >&2
  exit 2
fi
mkdir -p "$RUN_ROOT"
RUN_ROOT="$(realpath "$RUN_ROOT")"

if [[ "$MODE" == "train" ]]; then
  child=(bash "$SCRIPT_DIR/run_train.sh" "$RUN_ROOT")
else
  if [[ -z "${CHECKPOINT_PATH:-}" ]] || [[ ! -f "$CHECKPOINT_PATH" ]]; then
    printf 'Detached evaluation requires CHECKPOINT_PATH to be an existing trusted file.\n' >&2
    exit 2
  fi
  export CHECKPOINT_PATH
  child=(bash "$SCRIPT_DIR/run_eval.sh" "$CHECKPOINT_PATH" "$RUN_ROOT")
fi

nohup "${child[@]}" > "$RUN_ROOT/launcher.log" 2>&1 < /dev/null &
launcher_pid=$!
printf '%s\n' "$launcher_pid" > "$RUN_ROOT/launcher.pid"
{
  printf 'mode=%s\n' "$MODE"
  printf 'run_id=%s\n' "$RUN_ID"
  printf 'pid=%s\n' "$launcher_pid"
  printf 'utc_start=%s\n' "$(date -u --iso-8601=seconds)"
} > "$RUN_ROOT/launcher_status.txt"

printf 'Detached %s started.\n' "$MODE"
printf 'run_root=%s\n' "$RUN_ROOT"
printf 'pid=%s\n' "$launcher_pid"
printf 'status: ps -p %s -o pid,etime,stat,cmd\n' "$launcher_pid"
printf 'log: tail -f %q\n' "$RUN_ROOT/launcher.log"
