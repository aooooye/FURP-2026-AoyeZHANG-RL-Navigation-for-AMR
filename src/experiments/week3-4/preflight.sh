#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
# shellcheck source=protocol.env
source "$SCRIPT_DIR/protocol.env"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_DIR="${1:-$REPO_ROOT/src/results/week3-4/preflight_${PROFILE}_${timestamp}}"

if [[ -d "$OUTPUT_DIR" ]] && [[ -n "$(find "$OUTPUT_DIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  printf 'Refusing to overwrite non-empty preflight directory: %s\n' "$OUTPUT_DIR" >&2
  exit 2
fi
mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(realpath "$OUTPUT_DIR")"

exec > >(tee "$OUTPUT_DIR/preflight.txt") 2>&1

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  printf 'status=failed\nutc_end=%s\n' "$(date -u --iso-8601=seconds)" > "$OUTPUT_DIR/run_status.txt"
  exit 1
}

require_file() {
  [[ -f "$1" ]] || fail "missing file: $1"
  printf 'PASS file: %s\n' "$1"
}

require_dir() {
  [[ -d "$1" ]] || fail "missing directory: $1"
  printf 'PASS directory: %s\n' "$1"
}

habitat_path() {
  if [[ "$1" = /* ]]; then
    printf '%s\n' "$1"
  else
    printf '%s/%s\n' "$HABITAT_ROOT" "$1"
  fi
}

printf 'Weeks 3 & 4 PointNav preflight\n'
printf 'utc_start: %s\n' "$(date -u --iso-8601=seconds)"
printf 'hostname: %s\n' "$(hostname)"
printf 'profile: %s\n' "$PROFILE"
printf 'habitat_root: %s\n' "$HABITAT_ROOT"
printf 'python_bin: %s\n' "$PYTHON_BIN"
printf 'expected_habitat_revision: %s\n' "$EXPECTED_HABITAT_REVISION"

require_dir "$HABITAT_ROOT"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || fail "python executable not found: $PYTHON_BIN"
command -v nvidia-smi >/dev/null 2>&1 || fail "nvidia-smi is required for the frozen GPU baseline"
command -v git >/dev/null 2>&1 || fail "git is required to record the Habitat revision"
command -v gzip >/dev/null 2>&1 || fail "gzip is required to validate episode archives"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is required for artifact hashes"

actual_revision="$(git -C "$HABITAT_ROOT" rev-parse HEAD)"
printf 'actual_habitat_revision: %s\n' "$actual_revision"
git -C "$HABITAT_ROOT" status --short > "$OUTPUT_DIR/habitat_git_status.txt"
if [[ "$actual_revision" != "$EXPECTED_HABITAT_REVISION" ]] && [[ "$ALLOW_REVISION_MISMATCH" != "1" ]]; then
  fail "Habitat revision mismatch; set ALLOW_REVISION_MISMATCH=1 only with a documented protocol change"
fi

nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free \
  --format=csv,noheader | tee "$OUTPUT_DIR/nvidia_smi_summary.txt"

"$PYTHON_BIN" - <<'PY' | tee "$OUTPUT_DIR/python_packages.txt"
from importlib import metadata

import habitat
import habitat_sim
import torch

for distribution in ("habitat-lab", "habitat-baselines", "habitat-sim", "torch"):
    try:
        print(f"{distribution}={metadata.version(distribution)}")
    except metadata.PackageNotFoundError:
        print(f"{distribution}=not-found-as-distribution")

print(f"python_torch_cuda={torch.version.cuda}")
print(f"torch_cuda_available={torch.cuda.is_available()}")
if not torch.cuda.is_available():
    raise SystemExit("CUDA is not available in PyTorch")
print(f"torch_gpu={torch.cuda.get_device_name(0)}")
PY

CONFIG_ROOT="$HABITAT_ROOT/habitat-baselines/habitat_baselines/config"
TASK_CONFIG_ROOT="$HABITAT_ROOT/habitat-lab/habitat/config"

case "$PROFILE" in
  gibson)
    CONFIG_NAME="pointnav/ppo_pointnav"
    SOURCE_CONFIG="$CONFIG_ROOT/pointnav/ppo_pointnav.yaml"
    TASK_CONFIG="$TASK_CONFIG_ROOT/benchmark/nav/pointnav/pointnav_gibson.yaml"
    DATA_CONFIG="$TASK_CONFIG_ROOT/habitat/dataset/pointnav/gibson.yaml"
    SCENE_DIR="$HABITAT_ROOT/data/scene_datasets/gibson"
    TRAIN_EPISODES="$HABITAT_ROOT/data/datasets/pointnav/gibson/v1/train/train.json.gz"
    VAL_EPISODES="$HABITAT_ROOT/data/datasets/pointnav/gibson/v1/val/val.json.gz"
    SCENE_CONFIG_ABS="$(habitat_path "$SCENE_DATASET_CONFIG")"
    require_file "$SCENE_CONFIG_ABS"
    minimum_scenes="$MIN_GIBSON_SCENES"
    ;;
  habitat_test)
    CONFIG_NAME="pointnav/ppo_pointnav_example"
    SOURCE_CONFIG="$CONFIG_ROOT/pointnav/ppo_pointnav_example.yaml"
    TASK_CONFIG="$TASK_CONFIG_ROOT/benchmark/nav/pointnav/pointnav_habitat_test.yaml"
    DATA_CONFIG="$TASK_CONFIG_ROOT/habitat/dataset/pointnav/habitat_test.yaml"
    SCENE_DIR="$HABITAT_ROOT/data/scene_datasets/habitat-test-scenes"
    TRAIN_EPISODES="$HABITAT_ROOT/data/datasets/pointnav/habitat-test-scenes/v1/train/train.json.gz"
    VAL_EPISODES="$HABITAT_ROOT/data/datasets/pointnav/habitat-test-scenes/v1/val/val.json.gz"
    SCENE_CONFIG_ABS=""
    minimum_scenes=3
    ;;
  *)
    fail "unknown PROFILE=$PROFILE; expected gibson or habitat_test"
    ;;
esac

printf 'config_name: %s\n' "$CONFIG_NAME"
require_file "$SOURCE_CONFIG"
require_file "$TASK_CONFIG"
require_file "$DATA_CONFIG"
require_dir "$SCENE_DIR"
require_file "$TRAIN_EPISODES"
require_file "$VAL_EPISODES"

gzip -t "$TRAIN_EPISODES" || fail "invalid gzip archive: $TRAIN_EPISODES"
gzip -t "$VAL_EPISODES" || fail "invalid gzip archive: $VAL_EPISODES"
printf 'PASS gzip: %s\n' "$TRAIN_EPISODES"
printf 'PASS gzip: %s\n' "$VAL_EPISODES"

# Habitat's downloader may expose a versioned scene directory through a
# top-level symlink (as it does for habitat-test-scenes). Follow that link when
# inventorying files so the preflight measures the actual installed scenes.
scene_count="$(find -L "$SCENE_DIR" -type f -name '*.glb' | wc -l | tr -d '[:space:]')"
printf 'scene_glb_count: %s\n' "$scene_count"
if (( scene_count < minimum_scenes )); then
  fail "expected at least $minimum_scenes .glb scenes in $SCENE_DIR; found $scene_count"
fi

cp "$SOURCE_CONFIG" "$OUTPUT_DIR/upstream_policy_config.yaml"
cp "$TASK_CONFIG" "$OUTPUT_DIR/upstream_task_config.yaml"
cp "$DATA_CONFIG" "$OUTPUT_DIR/upstream_dataset_config.yaml"
sha256sum "$OUTPUT_DIR"/upstream_*_config.yaml > "$OUTPUT_DIR/config_sha256.txt"

{
  printf 'profile=%s\n' "$PROFILE"
  printf 'config_name=%s\n' "$CONFIG_NAME"
  printf 'habitat_revision=%s\n' "$actual_revision"
  printf 'scene_count=%s\n' "$scene_count"
  printf 'train_episodes=%s\n' "$TRAIN_EPISODES"
  printf 'val_episodes=%s\n' "$VAL_EPISODES"
  printf 'scene_dataset_config=%s\n' "$SCENE_CONFIG_ABS"
} > "$OUTPUT_DIR/profile_manifest.txt"

df -h "$HABITAT_ROOT" | tee "$OUTPUT_DIR/disk_space.txt"
printf 'status=passed\nutc_end=%s\n' "$(date -u --iso-8601=seconds)" | tee "$OUTPUT_DIR/run_status.txt"
