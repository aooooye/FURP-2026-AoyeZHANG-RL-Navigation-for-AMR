#!/usr/bin/env python3
"""Unified, resumable launcher for the frozen robustness matrix."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from protocol_guard import (
    CHECKPOINT_MANIFEST_PATH,
    FORMAL_NOISE_SEEDS,
    METHODS,
    NOISY_CONDITIONS,
    PROTOCOL_PATH,
    RESULTS_ROOT,
    TRAINING_SEEDS,
    build_run_manifest,
    checkpoint_entry,
    freeze_artifacts,
    load_json,
    run_relative_path,
    validate_checkpoint_manifest,
    validate_protocol,
    verify_passed_run,
)


SCRIPT_DIR = Path(__file__).resolve().parent
RUN_ONE = SCRIPT_DIR / "run_one_eval.sh"


@dataclass(frozen=True)
class RunSpec:
    phase: str
    condition: str
    method: str
    training_seed: int
    noise_seed: int


def matrix(phase: str) -> list[RunSpec]:
    if phase == "zero_noise":
        return [
            RunSpec(phase, "clean", method, seed, 0)
            for method in METHODS
            for seed in TRAINING_SEEDS
        ]
    if phase == "smoke":
        return [
            RunSpec(phase, condition, method, 100, 41001)
            for condition in NOISY_CONDITIONS
            for method in METHODS
        ]
    if phase == "formal":
        return [
            RunSpec(phase, condition, method, seed, noise_seed)
            for condition in NOISY_CONDITIONS
            for method in METHODS
            for seed in TRAINING_SEEDS
            for noise_seed in FORMAL_NOISE_SEEDS
        ]
    raise ValueError(f"unknown matrix phase: {phase}")


def checkpoint_path(spec: RunSpec, checkpoint_manifest: dict) -> Path:
    entry = checkpoint_entry(
        checkpoint_manifest, spec.method, spec.training_seed
    )
    return (SCRIPT_DIR.parents[2] / entry["path"]).resolve()


def run_root(spec: RunSpec) -> Path:
    return RESULTS_ROOT / run_relative_path(
        spec.phase,
        spec.condition,
        spec.method,
        spec.training_seed,
        spec.noise_seed,
    )


def require_gate(phase: str) -> None:
    prerequisites: list[str] = []
    if phase in ("smoke", "formal"):
        prerequisites.append("zero_noise")
    if phase == "formal":
        prerequisites.append("smoke")
    for prerequisite in prerequisites:
        for spec in matrix(prerequisite):
            expected = build_run_manifest(
                phase=spec.phase,
                condition=spec.condition,
                method=spec.method,
                training_seed=spec.training_seed,
                noise_seed=spec.noise_seed,
            )
            verify_passed_run(run_root(spec), expected)


def command_for(spec: RunSpec, checkpoint_manifest: dict) -> list[str]:
    return [
        "bash",
        str(RUN_ONE),
        spec.phase,
        spec.condition,
        spec.method,
        str(spec.training_seed),
        str(spec.noise_seed),
        str(checkpoint_path(spec, checkpoint_manifest)),
    ]


def execute_phase(phase: str, *, dry_run: bool) -> int:
    protocol = load_json(PROTOCOL_PATH)
    checkpoint_manifest = load_json(CHECKPOINT_MANIFEST_PATH)
    validate_protocol(protocol)
    validate_checkpoint_manifest(checkpoint_manifest)
    specs = matrix(phase)
    if dry_run:
        for spec in specs:
            print(json.dumps(command_for(spec, checkpoint_manifest)))
        print(f"dry_run_count={len(specs)}")
        return 0
    if os.name != "posix":
        raise SystemExit(
            "Habitat evaluation requires the pinned Linux/EGL environment; "
            "use --dry-run on this host."
        )
    freeze_artifacts()
    require_gate(phase)
    for index, spec in enumerate(specs, start=1):
        expected = build_run_manifest(
            phase=spec.phase,
            condition=spec.condition,
            method=spec.method,
            training_seed=spec.training_seed,
            noise_seed=spec.noise_seed,
        )
        root = run_root(spec)
        try:
            verify_passed_run(root, expected)
        except (FileNotFoundError, ValueError):
            pass
        else:
            print(f"[{index}/{len(specs)}] preserving passed run: {root}")
            continue
        print(f"[{index}/{len(specs)}] running: {spec}", flush=True)
        subprocess.run(command_for(spec, checkpoint_manifest), check=True)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=("zero_noise", "smoke", "formal", "aggregate"),
        required=True,
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.phase == "aggregate":
        if args.dry_run:
            print(json.dumps([sys.executable, str(SCRIPT_DIR / "aggregate_results.py")]))
            return 0
        subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "aggregate_results.py")],
            check=True,
        )
        return 0
    return execute_phase(args.phase, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
