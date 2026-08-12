#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$REPO_ROOT"
sha256sum -c "$SCRIPT_DIR/baseline_seed100.sha256"

bash "$SCRIPT_DIR/preflight.sh"

baseline_seed100_checkpoint="$REPO_ROOT/src/results/week03/remote_20260716T074249Z/week03_habitat_test_seed100_1m_env5/checkpoints/ckpt.9.pth"
bash "$SCRIPT_DIR/run_one_eval.sh" \
  baseline 100 "$baseline_seed100_checkpoint" 0 diagnostic
"${PYTHON_BIN:-python}" "$SCRIPT_DIR/validate_baseline_diagnostic.py"

bash "$SCRIPT_DIR/run_smoke.sh" baseline
bash "$SCRIPT_DIR/run_smoke.sh" dsr

for seed in 100 200 300; do
  for condition in baseline dsr; do
    bash "$SCRIPT_DIR/run_one_train.sh" "$condition" "$seed"
    train_root="$REPO_ROOT/src/results/closeout_dsr/closeout_${condition}_trainseed${seed}_1m_env5"
    checkpoint_path="$(<"$train_root/final_checkpoint_path.txt")"

    save_video=0
    if [[ "$condition" == "dsr" && "$seed" == "100" ]]; then
      save_video=1
    fi
    bash "$SCRIPT_DIR/run_one_eval.sh" \
      "$condition" "$seed" "$checkpoint_path" "$save_video"
  done
done

"${PYTHON_BIN:-python}" "$SCRIPT_DIR/aggregate_results.py"
