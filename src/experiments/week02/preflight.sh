#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HABITAT_ROOT="${HABITAT_ROOT:-$HOME/habitat-lab}"
OUTPUT_DIR="${1:-$REPO_ROOT/src/results/week02/preflight}"

mkdir -p "$OUTPUT_DIR"
exec > >(tee "$OUTPUT_DIR/preflight.txt") 2>&1

PPO_CONFIG="$HABITAT_ROOT/habitat-baselines/habitat_baselines/config/pointnav/ppo_pointnav_example.yaml"
TASK_CONFIG="$HABITAT_ROOT/habitat-lab/habitat/config/benchmark/nav/pointnav/pointnav_habitat_test.yaml"
SCENE_DIR="$HABITAT_ROOT/data/scene_datasets/habitat-test-scenes"
EPISODE_DIR="$HABITAT_ROOT/data/datasets/pointnav/habitat-test-scenes"

failures=0

check_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    printf 'PASS file: %s\n' "$path"
  else
    printf 'FAIL missing file: %s\n' "$path"
    failures=$((failures + 1))
  fi
}

check_dir() {
  local path="$1"
  if [[ -d "$path" ]]; then
    printf 'PASS directory: %s\n' "$path"
  else
    printf 'FAIL missing directory: %s\n' "$path"
    failures=$((failures + 1))
  fi
}

printf 'Week 2 Habitat PointNav preflight\n'
printf 'utc_time: %s\n' "$(date -u --iso-8601=seconds)"
printf 'hostname: %s\n' "$(hostname)"
printf 'habitat_root: %s\n' "$HABITAT_ROOT"
printf 'repo_root: %s\n' "$REPO_ROOT"
printf 'python: %s\n' "$(command -v python)"

if [[ -d "$HABITAT_ROOT/.git" ]]; then
  git -C "$HABITAT_ROOT" rev-parse HEAD | tee "$OUTPUT_DIR/habitat_lab_revision.txt"
  git -C "$HABITAT_ROOT" status --short > "$OUTPUT_DIR/habitat_lab_status.txt"
else
  printf 'FAIL Habitat-Lab git checkout missing at %s\n' "$HABITAT_ROOT"
  failures=$((failures + 1))
fi

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader \
    | tee "$OUTPUT_DIR/nvidia_smi_summary.txt"
else
  printf 'FAIL nvidia-smi is not available\n'
  failures=$((failures + 1))
fi

python - <<'PY' | tee "$OUTPUT_DIR/python_packages.txt"
from importlib import metadata

import habitat
import habitat_baselines
import habitat_sim
import torch

print(f"torch={torch.__version__}")
print(f"torch_cuda_available={torch.cuda.is_available()}")
print(f"torch_cuda_version={torch.version.cuda}")
print(f"torch_gpu={torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE'}")
for package in ("habitat-lab", "habitat-baselines", "habitat-sim"):
    try:
        print(f"{package}={metadata.version(package)}")
    except metadata.PackageNotFoundError:
        print(f"{package}=editable-or-version-unavailable")
PY

if ! python - <<'PY'
import torch
raise SystemExit(0 if torch.cuda.is_available() else 1)
PY
then
  printf 'FAIL PyTorch cannot use CUDA\n'
  failures=$((failures + 1))
else
  printf 'PASS PyTorch CUDA is available\n'
fi

check_file "$PPO_CONFIG"
check_file "$TASK_CONFIG"
check_dir "$SCENE_DIR"
check_dir "$EPISODE_DIR"

if [[ -f "$PPO_CONFIG" ]]; then
  cp "$PPO_CONFIG" "$OUTPUT_DIR/ppo_pointnav_example.yaml"
fi
if [[ -f "$TASK_CONFIG" ]]; then
  cp "$TASK_CONFIG" "$OUTPUT_DIR/pointnav_habitat_test.yaml"
fi

if [[ "$failures" -ne 0 ]]; then
  printf 'PREFLIGHT FAILED: %d required checks failed\n' "$failures"
  exit 1
fi

printf 'PREFLIGHT PASSED\n' | tee "$OUTPUT_DIR/preflight_passed.txt"
