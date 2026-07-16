#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HABITAT_ROOT="${HABITAT_ROOT:-$HOME/habitat-lab}"
OUTPUT_DIR="${1:-$REPO_ROOT/src/results/week02/shortest_path}"

mkdir -p "$OUTPUT_DIR"
cd "$HABITAT_ROOT"

export MAGNUM_LOG="${MAGNUM_LOG:-quiet}"
export HABITAT_SIM_LOG="${HABITAT_SIM_LOG:-quiet}"

python "$SCRIPT_DIR/shortest_path_follower.py" \
  --episodes 3 \
  --max-steps 500 \
  --output-dir "$OUTPUT_DIR" \
  2>&1 | tee "$OUTPUT_DIR/shortest_path_stdout.txt"
