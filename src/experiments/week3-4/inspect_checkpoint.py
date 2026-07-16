#!/usr/bin/env python3
"""Verify the final trusted Habitat checkpoint reached the frozen step budget."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def get_nested(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if isinstance(current, Mapping):
            current = current[key]
        else:
            current = getattr(current, key)
    return current


def integer_value(value: Any) -> int:
    if hasattr(value, "item"):
        value = value.item()
    return int(value)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--expected-min-steps", type=int, required=True)
    parser.add_argument("--expected-profile", choices=("gibson", "habitat_test"))
    parser.add_argument("--expected-training-seed", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not args.checkpoint.is_file():
        raise SystemExit(f"Checkpoint does not exist: {args.checkpoint}")

    # Import only in the executable path so the pure helpers remain testable on
    # a documentation workstation without PyTorch. This must only inspect a
    # checkpoint produced by this trusted project.
    import torch

    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    try:
        step = integer_value(get_nested(checkpoint, "extra_state", "step"))
    except (KeyError, AttributeError, TypeError, ValueError) as exc:
        raise SystemExit(f"Checkpoint has no readable extra_state.step: {exc}") from exc

    try:
        configured_total_steps = integer_value(
            get_nested(checkpoint, "config", "habitat_baselines", "total_num_steps")
        )
    except (KeyError, AttributeError, TypeError, ValueError):
        configured_total_steps = None

    try:
        training_seed = integer_value(get_nested(checkpoint, "config", "habitat", "seed"))
    except (KeyError, AttributeError, TypeError, ValueError):
        training_seed = None

    try:
        dataset_path = str(
            get_nested(checkpoint, "config", "habitat", "dataset", "data_path")
        )
    except (KeyError, AttributeError, TypeError, ValueError):
        dataset_path = ""

    if "/gibson/" in dataset_path.replace("\\", "/"):
        observed_profile = "gibson"
    elif "habitat-test-scenes" in dataset_path:
        observed_profile = "habitat_test"
    else:
        observed_profile = "unknown"

    complete = step >= args.expected_min_steps
    profile_matches = (
        args.expected_profile is None or observed_profile == args.expected_profile
    )
    training_seed_matches = (
        args.expected_training_seed is None
        or training_seed == args.expected_training_seed
    )
    payload = {
        "checkpoint": str(args.checkpoint.resolve()),
        "checkpoint_sha256": file_sha256(args.checkpoint),
        "step": step,
        "expected_min_steps": args.expected_min_steps,
        "configured_total_num_steps": configured_total_steps,
        "training_seed": training_seed,
        "dataset_path": dataset_path,
        "observed_profile": observed_profile,
        "expected_profile": args.expected_profile,
        "profile_matches": profile_matches,
        "expected_training_seed": args.expected_training_seed,
        "training_seed_matches": training_seed_matches,
        "status": "complete"
        if complete and profile_matches and training_seed_matches
        else "incomplete_or_mismatched",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if not complete:
        raise SystemExit(
            f"Final checkpoint step {step} is below frozen budget {args.expected_min_steps}"
        )
    if not profile_matches:
        raise SystemExit(
            f"Checkpoint profile {observed_profile} does not match {args.expected_profile}"
        )
    if not training_seed_matches:
        raise SystemExit(
            f"Checkpoint training seed {training_seed} does not match "
            f"{args.expected_training_seed}"
        )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
