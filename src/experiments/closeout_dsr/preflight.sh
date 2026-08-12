#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
# shellcheck source=protocol.env
source "$SCRIPT_DIR/protocol.env"
export PYTHONNOUSERSITE

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_DIR="${1:-$REPO_ROOT/src/results/closeout_dsr/preflight_${timestamp}}"

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

printf 'Closeout DSR preflight\n'
printf 'utc_start: %s\n' "$(date -u --iso-8601=seconds)"

PROFILE="$PROFILE" \
HABITAT_ROOT="$HABITAT_ROOT" \
PYTHON_BIN="$PYTHON_BIN" \
EXPECTED_HABITAT_REVISION="$EXPECTED_HABITAT_REVISION" \
EGL_VENDOR_JSON="$EGL_VENDOR_JSON" \
ALLOW_REVISION_MISMATCH=0 \
bash "$SCRIPT_DIR/../week03/preflight.sh" "$OUTPUT_DIR/habitat" \
  || fail "base Habitat preflight failed"

"$PYTHON_BIN" - <<'PY' | tee "$OUTPUT_DIR/frozen_runtime_versions.txt"
from importlib import metadata
from pathlib import Path
import sys

expected = {
    "habitat-lab": "0.3.3",
    "habitat-baselines": "0.3.3",
    "habitat-sim": "0.3.3",
    "numpy": "1.26.4",
    "gym": "0.23.0",
    "hydra-core": "1.3.3",
    "omegaconf": "2.3.1",
    "pillow": "10.4.0",
    "packaging": "26.2",
    "pip": "26.0.1",
    "setuptools": "82.0.1",
    "wheel": "0.47.0",
}
if sys.version_info[:3] != (3, 9, 19):
    raise SystemExit(f"python mismatch: {sys.version.split()[0]} != 3.9.19")
print(f"python={sys.version.split()[0]}")
for distribution, expected_version in expected.items():
    actual_version = metadata.version(distribution)
    print(f"{distribution}={actual_version}")
    if actual_version != expected_version:
        raise SystemExit(
            f"{distribution} mismatch: {actual_version} != {expected_version}"
        )

torch_version = metadata.version("torch")
print(f"torch={torch_version}")
if not torch_version.startswith("2.8.0"):
    raise SystemExit(f"torch mismatch: {torch_version} does not start with 2.8.0")
for distribution, expected_prefix in {
    "torchvision": "0.23.0",
    "torchaudio": "2.8.0",
}.items():
    actual_version = metadata.version(distribution)
    print(f"{distribution}={actual_version}")
    if not actual_version.startswith(expected_prefix):
        raise SystemExit(
            f"{distribution} mismatch: {actual_version} does not start with {expected_prefix}"
        )

expected_build = (
    "py3.9_headless_bullet_linux_"
    "acbe6f4922e68145e401e55c30f9dfea460a3f24"
)
metadata_dir = Path(sys.prefix) / "conda-meta"
records = list(metadata_dir.glob("habitat-sim-0.3.3-*.json"))
if len(records) != 1 or expected_build not in records[0].name:
    raise SystemExit(
        "Habitat-Sim conda build mismatch: "
        + ", ".join(record.name for record in records)
    )
print(f"habitat_sim_conda_record={records[0].name}")
PY

(
  cd "$SCRIPT_DIR"
  "$PYTHON_BIN" -m unittest -v test_dsr_math.py
) | tee "$OUTPUT_DIR/dsr_unit_tests.txt" \
  || fail "DSR math unit tests failed"

PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" \
"$PYTHON_BIN" - <<'PY' | tee "$OUTPUT_DIR/dsr_registration.txt"
import habitat
import dynamic_success_reward_env  # noqa: F401

for name in (
    "DynamicSuccessRewardGymHabitatEnv",
    "StopDiagnosticGymHabitatEnv",
):
    env_class = habitat.registry.get_env(name)
    if env_class is None:
        raise SystemExit(f"environment registration missing: {name}")
    print(f"registered_env={name}")
    print(f"registered_class={env_class.__module__}.{env_class.__name__}")
PY

PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" \
"$PYTHON_BIN" "$SCRIPT_DIR/run_habitat_with_dsr.py" \
  --config-name=pointnav/ppo_pointnav_example \
  --cfg job \
  "habitat.env_task=$DSR_ENV_TASK" \
  > "$OUTPUT_DIR/dsr_resolved_config.yaml" \
  || fail "Hydra could not compose the DSR environment override"
grep -q "env_task: $DSR_ENV_TASK" "$OUTPUT_DIR/dsr_resolved_config.yaml" \
  || fail "resolved Hydra config does not contain the frozen DSR environment"

PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" \
"$PYTHON_BIN" "$SCRIPT_DIR/run_habitat_with_dsr.py" \
  --config-name=pointnav/ppo_pointnav_example \
  --cfg job \
  "habitat.env_task=$DIAGNOSTIC_ENV_TASK" \
  > "$OUTPUT_DIR/diagnostic_resolved_config.yaml" \
  || fail "Hydra could not compose the diagnostic environment override"
grep -q "env_task: $DIAGNOSTIC_ENV_TASK" "$OUTPUT_DIR/diagnostic_resolved_config.yaml" \
  || fail "resolved Hydra config does not contain the diagnostic environment"

sha256sum \
  "$SCRIPT_DIR/dsr_math.py" \
  "$SCRIPT_DIR/dynamic_success_reward_env.py" \
  "$SCRIPT_DIR/run_habitat_with_dsr.py" \
  "$SCRIPT_DIR/protocol.env" \
  "$SCRIPT_DIR/runtime_constraints.txt" \
  > "$OUTPUT_DIR/implementation_sha256.txt"

{
  printf 'profile=%s\n' "$PROFILE"
  printf 'training_seeds=%s\n' "$TRAIN_SEEDS"
  printf 'evaluation_seed=%s\n' "$EVAL_SEED"
  printf 'total_steps=%s\n' "$TOTAL_STEPS"
  printf 'evaluation_episodes=%s\n' "$EVAL_EPISODES"
  printf 'dsr_env_task=%s\n' "$DSR_ENV_TASK"
  printf 'diagnostic_env_task=%s\n' "$DIAGNOSTIC_ENV_TASK"
  printf 'dsr_formula=%s\n' "$DSR_FORMULA"
} > "$OUTPUT_DIR/frozen_protocol.txt"

printf 'status=passed\nutc_end=%s\n' \
  "$(date -u --iso-8601=seconds)" | tee "$OUTPUT_DIR/run_status.txt"
