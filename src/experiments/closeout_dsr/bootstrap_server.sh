#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_REVISION="cdbb4880519505adf45fba0f0c0c3a3fd18a2a55"
ENV_NAME="${ENV_NAME:-habitat}"
HABITAT_ROOT="${HABITAT_ROOT:-$HOME/habitat-lab}"
MAMBA_BIN="${MAMBA_BIN:-$(command -v micromamba || true)}"
MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-$HOME/micromamba}"
EGL_VENDOR_JSON="${EGL_VENDOR_JSON:-/usr/share/glvnd/egl_vendor.d/10_nvidia.json}"
BOOTSTRAP_RESUME="${BOOTSTRAP_RESUME:-0}"
BOOTSTRAP_STATE="${BOOTSTRAP_STATE:-${HABITAT_ROOT}.closeout_bootstrap_state}"
export MAMBA_ROOT_PREFIX
export PYTHONNOUSERSITE=1
CONSTRAINTS_FILE="$SCRIPT_DIR/runtime_constraints.txt"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

[[ -n "$MAMBA_BIN" && -x "$MAMBA_BIN" ]] \
  || fail "micromamba must be installed by the server administrator"
[[ "$BOOTSTRAP_RESUME" == "0" || "$BOOTSTRAP_RESUME" == "1" ]] \
  || fail "BOOTSTRAP_RESUME must be 0 or 1"

env_exists=0
if "$MAMBA_BIN" env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  env_exists=1
fi

if [[ "$BOOTSTRAP_RESUME" == "0" ]]; then
  [[ ! -e "$HABITAT_ROOT" ]] \
    || fail "refusing to overwrite existing Habitat path: $HABITAT_ROOT"
  (( env_exists == 0 )) \
    || fail "refusing to modify existing micromamba environment: $ENV_NAME"
  [[ ! -e "$BOOTSTRAP_STATE" ]] \
    || fail "bootstrap state already exists; inspect it before continuing: $BOOTSTRAP_STATE"
  {
    printf 'env_name=%s\n' "$ENV_NAME"
    printf 'habitat_root=%s\n' "$HABITAT_ROOT"
    printf 'expected_revision=%s\n' "$EXPECTED_REVISION"
    printf 'status=in_progress\n'
  } > "$BOOTSTRAP_STATE"
else
  [[ -f "$BOOTSTRAP_STATE" ]] \
    || fail "resume requires the state file created by this script: $BOOTSTRAP_STATE"
  grep -Fxq "env_name=$ENV_NAME" "$BOOTSTRAP_STATE" \
    || fail "resume environment does not match bootstrap state"
  grep -Fxq "habitat_root=$HABITAT_ROOT" "$BOOTSTRAP_STATE" \
    || fail "resume Habitat path does not match bootstrap state"
  grep -Fxq "expected_revision=$EXPECTED_REVISION" "$BOOTSTRAP_STATE" \
    || fail "resume revision does not match bootstrap state"
  if grep -Fxq 'status=complete' "$BOOTSTRAP_STATE"; then
    fail "bootstrap is already complete; run the closeout preflight instead"
  fi
fi

bootstrap_complete=0
on_exit() {
  exit_code=$?
  if (( exit_code != 0 && bootstrap_complete == 0 )); then
    printf 'Bootstrap stopped with partial state preserved. After fixing infrastructure, resume with:\n' >&2
    printf '  BOOTSTRAP_RESUME=1 bash %q\n' "$0" >&2
  fi
  return "$exit_code"
}
trap on_exit EXIT

if (( env_exists == 0 )); then
  "$MAMBA_BIN" create -y -n "$ENV_NAME" \
    -c conda-forge -c aihabitat \
    python=3.9.19 pip cmake=3.14.0 git-lfs=3.7.1 \
    "habitat-sim=0.3.3=py3.9_headless_bullet_linux_acbe6f4922e68145e401e55c30f9dfea460a3f24" \
    withbullet headless
else
  printf 'Resuming existing script-owned environment: %s\n' "$ENV_NAME"
fi

eval "$("$MAMBA_BIN" shell hook -s bash)"
micromamba activate "$ENV_NAME"
git lfs install --skip-repo

python -m pip install --upgrade \
  -c "$CONSTRAINTS_FILE" \
  pip==26.0.1 setuptools==82.0.1 wheel==0.47.0 \
  pillow==10.4.0 packaging==26.2
python -m pip install \
  -c "$CONSTRAINTS_FILE" \
  torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 \
  --index-url https://download.pytorch.org/whl/cu128
python -m pip install \
  -c "$CONSTRAINTS_FILE" \
  numpy==1.26.4 gym==0.23.0 hydra-core==1.3.3 omegaconf==2.3.1

if [[ ! -e "$HABITAT_ROOT" ]]; then
  git clone https://github.com/facebookresearch/habitat-lab.git "$HABITAT_ROOT"
else
  [[ -d "$HABITAT_ROOT/.git" ]] \
    || fail "resume Habitat path is not a Git checkout: $HABITAT_ROOT"
  git -C "$HABITAT_ROOT" diff --quiet \
    || fail "resume Habitat checkout has tracked modifications"
fi
if ! git -C "$HABITAT_ROOT" cat-file -e "$EXPECTED_REVISION^{commit}" 2>/dev/null; then
  git -C "$HABITAT_ROOT" fetch origin "$EXPECTED_REVISION"
fi
git -C "$HABITAT_ROOT" checkout --detach "$EXPECTED_REVISION"

python -m pip install -c "$CONSTRAINTS_FILE" -e "$HABITAT_ROOT/habitat-lab"
python -m pip install -c "$CONSTRAINTS_FILE" -e "$HABITAT_ROOT/habitat-baselines"
python -m pip check

mkdir -p "$HABITAT_ROOT/data"
(
  cd "$HABITAT_ROOT"
  python -m habitat_sim.utils.datasets_download \
    --uids habitat_test_scenes \
    --data-path data/ \
    --no-replace
  python -m habitat_sim.utils.datasets_download \
    --uids habitat_test_pointnav_dataset \
    --data-path data/ \
    --no-replace
)

export __EGL_VENDOR_LIBRARY_FILENAMES="$EGL_VENDOR_JSON"
unset DISPLAY || true
(
  cd "$HABITAT_ROOT"
  python - <<'PY'
from pathlib import Path

import habitat
import habitat_baselines
import habitat_sim
import torch
from habitat_sim.agent import ActionSpec, ActuationSpec, AgentConfiguration

scene = Path("data/scene_datasets/habitat-test-scenes/skokloster-castle.glb")
if not scene.is_file():
    raise FileNotFoundError(scene)

sim_cfg = habitat_sim.SimulatorConfiguration()
sim_cfg.scene_id = str(scene)
sensor = habitat_sim.CameraSensorSpec()
sensor.uuid = "rgb"
sensor.sensor_type = habitat_sim.SensorType.COLOR
sensor.resolution = [64, 64]
agent_cfg = AgentConfiguration()
agent_cfg.sensor_specifications = [sensor]
agent_cfg.action_space = {
    "move_forward": ActionSpec(
        "move_forward", ActuationSpec(amount=0.25)
    )
}

sim = habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [agent_cfg]))
try:
    sim.initialize_agent(0)
    observation = sim.step("move_forward")
    print(f"rgb_shape={observation['rgb'].shape}")
finally:
    sim.close()

print(f"habitat={habitat.__file__}")
print(f"habitat_baselines={habitat_baselines.__file__}")
print(f"habitat_sim={habitat_sim.__version__}")
print(f"torch={torch.__version__}")
print(f"torch_cuda={torch.version.cuda}")
print(f"torch_cuda_available={torch.cuda.is_available()}")
if not torch.cuda.is_available():
    raise SystemExit("PyTorch CUDA unavailable")
PY
)

git -C "$HABITAT_ROOT" rev-parse HEAD
"$MAMBA_BIN" list -n "$ENV_NAME" --explicit \
  > "$HOME/habitat_closeout_conda_explicit.txt"
python -m pip freeze > "$HOME/habitat_closeout_pip_freeze.txt"
printf 'status=complete\n' >> "$BOOTSTRAP_STATE"
bootstrap_complete=1

printf 'Bootstrap passed. Activate with:\n'
printf '  export MAMBA_ROOT_PREFIX=%q\n' "$MAMBA_ROOT_PREFIX"
printf '  eval "$(%q shell hook -s bash)"\n' "$MAMBA_BIN"
printf '  micromamba activate %q\n' "$ENV_NAME"
