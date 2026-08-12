#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
OUTPUT_FILE="${1:-$REPO_ROOT/src/results/closeout_dsr/server_preflight_$(date -u +%Y%m%dT%H%M%SZ).txt}"
mkdir -p "$(dirname "$OUTPUT_FILE")"
exec > >(tee "$OUTPUT_FILE") 2>&1

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

printf 'Closeout server allocation preflight\n'
printf 'utc_start: %s\n' "$(date -u --iso-8601=seconds)"
printf 'hostname: %s\n' "$(hostname)"

[[ "$(uname -s)" == "Linux" ]] || fail "Linux is required"
[[ "$(uname -m)" == "x86_64" ]] || fail "x86_64 is required"
[[ -f /etc/os-release ]] || fail "/etc/os-release is missing"
# shellcheck disable=SC1091
source /etc/os-release
[[ "${ID:-}" == "ubuntu" ]] || fail "Ubuntu is required; found ${ID:-unknown}"
printf 'os: %s %s\n' "${NAME:-Ubuntu}" "${VERSION_ID:-unknown}"

for command_name in git curl gzip sha256sum nvidia-smi ffmpeg micromamba ldconfig; do
  command -v "$command_name" >/dev/null 2>&1 \
    || fail "missing system command: $command_name"
done

gpu_line="$(nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv,noheader | head -n 1)"
printf 'gpu: %s\n' "$gpu_line"
vram_mib="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n 1 | tr -d '[:space:]')"
(( vram_mib >= 11000 )) || fail "at least 11,000 MiB GPU memory is required"
vram_free_mib="$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -n 1 | tr -d '[:space:]')"
(( vram_free_mib >= 10000 )) || fail "at least 10,000 MiB free GPU memory is required"
compute_processes="$(nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader 2>/dev/null || true)"
[[ -z "$compute_processes" ]] \
  || fail "GPU has active compute processes and is not ready for the frozen run: $compute_processes"
compute_capability="$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -n 1 | tr -d '[:space:]')"
printf 'compute_capability: %s\n' "$compute_capability"
awk -v capability="$compute_capability" 'BEGIN { exit !(capability + 0 >= 8.0) }' \
  || fail "Ampere-class compute capability 8.0 or newer is required"

driver_version="$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -n 1 | tr -d '[:space:]')"
if [[ "$(printf '%s\n%s\n' "570.26" "$driver_version" | sort -V | head -n 1)" != "570.26" ]]; then
  fail "NVIDIA driver $driver_version is below the conservative CUDA 12.8 floor 570.26"
fi

cpu_count="$(nproc)"
memory_kib="$(awk '/MemTotal/ {print $2}' /proc/meminfo)"
disk_free_kib="$(df -Pk "$HOME" | awk 'NR==2 {print $4}')"
printf 'cpu_count: %s\n' "$cpu_count"
printf 'memory_kib: %s\n' "$memory_kib"
printf 'home_disk_free_kib: %s\n' "$disk_free_kib"
(( cpu_count >= 8 )) || fail "at least 8 CPU threads are required"
(( memory_kib >= 30000000 )) || fail "at least 30,000,000 KiB RAM is required"
(( disk_free_kib >= 100000000 )) || fail "at least 100,000,000 KiB free persistent storage is required"
if command -v quota >/dev/null 2>&1; then
  printf 'user_quota:\n'
  quota -s 2>&1 || true
fi

[[ -f /usr/share/glvnd/egl_vendor.d/10_nvidia.json ]] \
  || fail "NVIDIA EGL vendor JSON is missing"
ldconfig_output="$(ldconfig -p 2>/dev/null)"
grep -q 'libEGL\.so' <<< "$ldconfig_output" || fail "libEGL is missing"
grep -q 'libOpenGL\.so' <<< "$ldconfig_output" || fail "libOpenGL is missing"

git ls-remote https://github.com/facebookresearch/habitat-lab.git HEAD >/dev/null \
  || fail "cannot reach GitHub"
git ls-remote https://huggingface.co/datasets/ai-habitat/habitat_test_scenes.git HEAD >/dev/null \
  || fail "cannot reach the official Habitat test-scenes repository"
for url in \
  https://pypi.org/simple/pip/ \
  https://conda.anaconda.org/conda-forge/linux-64/repodata.json.zst \
  https://conda.anaconda.org/aihabitat/linux-64/repodata.json.zst \
  https://download.pytorch.org/whl/cu128/; do
  curl -fsSIL --max-time 30 "$url" >/dev/null \
    || fail "cannot reach package source: $url"
done
curl -fsSL --range 0-0 --max-time 30 \
  http://dl.fbaipublicfiles.com/habitat/habitat-test-pointnav-dataset_v1.0.zip \
  -o /dev/null \
  || fail "cannot reach the official Habitat PointNav test dataset"

printf 'status=passed\n'
printf 'utc_end: %s\n' "$(date -u --iso-8601=seconds)"
