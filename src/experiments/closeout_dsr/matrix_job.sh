#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCH_DIR="${1:?launcher directory is required}"

set +e
bash "$SCRIPT_DIR/run_matrix.sh"
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
