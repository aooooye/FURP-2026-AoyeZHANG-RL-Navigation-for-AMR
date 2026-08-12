#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LAUNCH_DIR="${1:?launcher directory is required}"

export PATH="${ROBUSTNESS_ENV_BIN:-/home/furp/micromamba/envs/habitat/bin}:$PATH"
export PYTHON_BIN="${PYTHON_BIN:-/home/furp/micromamba/envs/habitat/bin/python}"
export HABITAT_ROOT="${HABITAT_ROOT:-/home/furp/habitat-lab}"

set +e
"$PYTHON_BIN" "$SCRIPT_DIR/run_robustness.py" --phase formal
matrix_exit=$?
set -e
if (( matrix_exit == 0 )); then
  status=passed
else
  status=failed
fi
printf 'status=%s\nexit_code=%s\nutc_end=%s\n' \
  "$status" "$matrix_exit" "$(date -u --iso-8601=seconds)" \
  > "$LAUNCH_DIR/run_status.txt"
exit "$matrix_exit"
