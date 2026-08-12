#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LAUNCH_DIR="$REPO_ROOT/src/results/closeout_dsr/matrix_launcher"

if [[ -e "$LAUNCH_DIR/launcher.pid" || -e "$LAUNCH_DIR/run_status.txt" ]]; then
  printf 'Existing launcher state requires inspection; refusing overwrite: %s\n' "$LAUNCH_DIR" >&2
  exit 2
fi
mkdir -p "$LAUNCH_DIR"

nohup bash "$SCRIPT_DIR/matrix_job.sh" "$LAUNCH_DIR" \
  > "$LAUNCH_DIR/launcher.log" 2>&1 &
launcher_pid=$!
printf '%s\n' "$launcher_pid" > "$LAUNCH_DIR/launcher.pid"
printf 'pid=%s\nutc_start=%s\n' \
  "$launcher_pid" "$(date -u --iso-8601=seconds)" \
  > "$LAUNCH_DIR/launcher_state.txt"

printf 'Launched frozen matrix as PID %s\n' "$launcher_pid"
printf 'Monitor: tail -f %q\n' "$LAUNCH_DIR/launcher.log"
