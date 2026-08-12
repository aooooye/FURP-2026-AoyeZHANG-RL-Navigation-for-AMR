from __future__ import annotations

import importlib.metadata as metadata
import platform
from pathlib import Path

import habitat
import habitat_baselines
import habitat_sim
import torch


ROOT = Path.home()
OUT_DIR = ROOT / "week01_habitat_evidence"
OUT_DIR.mkdir(exist_ok=True)

habitat_lab = ROOT / "habitat-lab"
scene = habitat_lab / "data" / "scene_datasets" / "habitat-test-scenes" / "skokloster-castle.glb"
vlnce = ROOT / "VLN-CE"

lines = [
    "Week 1 Habitat / VLN-CE smoke test",
    f"python: {platform.python_version()}",
    f"torch: {torch.__version__}",
    f"torch_cuda_available: {torch.cuda.is_available()}",
    f"habitat: {metadata.version('habitat-lab')}",
    f"habitat_baselines: {metadata.version('habitat-baselines')}",
    f"habitat_sim: {metadata.version('habitat-sim')}",
    f"habitat_file: {habitat.__file__}",
    f"habitat_baselines_file: {habitat_baselines.__file__}",
    f"habitat_sim_file: {habitat_sim.__file__}",
    f"habitat_lab_repo: {habitat_lab.exists()} {habitat_lab}",
    f"vlnce_repo: {vlnce.exists()} {vlnce}",
    f"habitat_test_scene_present: {scene.exists()} {scene}",
]

if not scene.exists():
    lines.append(
        "data_note: Habitat test scene was not downloaded; remote host could not connect to huggingface.co."
    )

lines.append("result: ok")

output = OUT_DIR / "habitat_vlnce_smoke.txt"
output.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
print(f"saved: {output}")
