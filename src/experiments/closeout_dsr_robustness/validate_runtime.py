#!/usr/bin/env python3
"""Read-only runtime/registration gate for the pinned Habitat host."""

from __future__ import annotations

import os
import subprocess
import sys
from importlib import metadata
from pathlib import Path


EXPECTED_DISTRIBUTIONS = {
    "habitat-lab": "0.3.3",
    "habitat-baselines": "0.3.3",
    "habitat-sim": "0.3.3",
    "numpy": "1.26.4",
    "gym": "0.23.0",
}
EXPECTED_REVISION = "cdbb4880519505adf45fba0f0c0c3a3fd18a2a55"


def main() -> int:
    if sys.version_info[:2] != (3, 9):
        raise SystemExit(f"expected Python 3.9, got {sys.version.split()[0]}")
    for distribution, expected in EXPECTED_DISTRIBUTIONS.items():
        actual = metadata.version(distribution)
        if actual != expected:
            raise SystemExit(
                f"expected {distribution}=={expected}, got {actual}"
            )

    habitat_root = Path(os.environ.get("HABITAT_ROOT", "~/habitat-lab")).expanduser()
    revision = subprocess.run(
        ["git", "-C", str(habitat_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if revision != EXPECTED_REVISION:
        raise SystemExit(f"Habitat revision mismatch: {revision}")

    import habitat
    import torch
    from habitat.sims.habitat_simulator.actions import HabitatSimActions

    import robustness_env  # noqa: F401
    from protocol_guard import (
        CHECKPOINT_MANIFEST_PATH,
        PROTOCOL_PATH,
        load_json,
        validate_checkpoint_manifest,
        validate_protocol,
    )

    validate_protocol(load_json(PROTOCOL_PATH))
    validate_checkpoint_manifest(load_json(CHECKPOINT_MANIFEST_PATH))
    registered = habitat.registry.get_env("RobustnessGymHabitatEnv")
    if registered is None:
        raise SystemExit("RobustnessGymHabitatEnv was not registered")
    action_values = {
        int(HabitatSimActions.stop),
        int(HabitatSimActions.move_forward),
        int(HabitatSimActions.turn_left),
        int(HabitatSimActions.turn_right),
    }
    if len(action_values) != 4:
        raise SystemExit(f"navigation action mapping is not four distinct indices: {action_values}")
    if not torch.cuda.is_available():
        raise SystemExit("PyTorch CUDA is unavailable")
    print(f"python={sys.version.split()[0]}")
    for distribution in EXPECTED_DISTRIBUTIONS:
        print(f"{distribution}={metadata.version(distribution)}")
    print(f"habitat_revision={revision}")
    print(f"cuda_device={torch.cuda.get_device_name(0)}")
    print("robustness_registration=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
