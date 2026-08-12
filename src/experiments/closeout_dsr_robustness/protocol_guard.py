#!/usr/bin/env python3
"""Validate and freeze every input used by the robustness evaluation."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

from robustness_core import (
    RNG_ALGORITHM,
    canonical_json_sha256,
    sha256_file,
    stateless_standard_normal,
)


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
PROTOCOL_PATH = SCRIPT_DIR / "protocol.json"
CHECKPOINT_MANIFEST_PATH = SCRIPT_DIR / "checkpoint_manifest.json"
RESULTS_ROOT = REPO_ROOT / "src" / "results" / "closeout_dsr_robustness"

METHODS = ("baseline", "dsr")
TRAINING_SEEDS = (100, 200, 300)
NOISY_CONDITIONS = ("localization", "actuation", "combined")
FORMAL_NOISE_SEEDS = (41001, 41002, 41003)
METRICS = (
    "success",
    "spl",
    "distance_to_goal",
    "reward",
    "stop_called",
    "premature_stop",
    "non_stop_failure",
)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return payload


def noise_manifest_payload(protocol: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "formal_noise_seeds": protocol["formal_noise_seeds"],
        "noise_models": protocol["noise_models"],
        "pointgoal_sensor_uuid": protocol["pointgoal_sensor_uuid"],
        "rng": protocol["rng"],
    }


def noise_manifest_sha256(protocol: Mapping[str, Any]) -> str:
    return canonical_json_sha256(noise_manifest_payload(protocol))


def _require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"frozen protocol mismatch for {label}: {actual!r} != {expected!r}")


def validate_protocol(protocol: Mapping[str, Any]) -> None:
    _require_equal(protocol.get("schema_version"), 1, "schema_version")
    _require_equal(protocol.get("profile"), "habitat_test", "profile")
    _require_equal(tuple(protocol.get("training_methods", [])), METHODS, "training_methods")
    _require_equal(tuple(protocol.get("training_seeds", [])), TRAINING_SEEDS, "training_seeds")
    _require_equal(
        tuple(protocol.get("formal_noise_seeds", [])),
        FORMAL_NOISE_SEEDS,
        "formal_noise_seeds",
    )
    _require_equal(
        tuple(protocol.get("conditions", [])),
        ("clean", *NOISY_CONDITIONS),
        "conditions",
    )
    _require_equal(tuple(protocol.get("metrics", [])), METRICS, "metrics")
    evaluation = protocol["evaluation"]
    for key, expected in {
        "seed": 2026,
        "split": "val",
        "episodes": 100,
        "num_environments": 2,
        "max_episode_steps": 500,
        "success_distance_m": 0.2,
    }.items():
        _require_equal(evaluation.get(key), expected, f"evaluation.{key}")
    localization = protocol["noise_models"]["localization"]
    _require_equal(
        localization,
        {
            "sampling_scope": "episode_constant",
            "distance_bias_m": {"std": 0.05, "clip": [-0.15, 0.15]},
            "bearing_bias_deg": {"std": 2.0, "clip": [-6.0, 6.0]},
            "ground_truth_metrics_unchanged": True,
        },
        "noise_models.localization",
    )
    actuation = protocol["noise_models"]["actuation"]
    _require_equal(
        actuation,
        {
            "sampling_scope": "per_action_step",
            "forward_distance_m": {
                "nominal": 0.25,
                "std": 0.005,
                "clip": [0.235, 0.265],
            },
            "turn_angle_deg": {
                "nominal": 10.0,
                "std": 1.0 / 6.0,
                "clip": [9.5, 10.5],
            },
            "stop_noise": False,
            "lateral_slip": False,
            "translation_during_turn": False,
        },
        "noise_models.actuation",
    )
    rng = protocol["rng"]
    _require_equal(rng.get("algorithm"), RNG_ALGORITHM, "rng.algorithm")
    _require_equal(rng.get("step_index_origin"), 0, "rng.step_index_origin")
    _require_equal(
        rng.get("method_and_training_seed_excluded"),
        True,
        "rng.method_and_training_seed_excluded",
    )
    golden_vectors = rng.get("golden_vectors", [])
    if len(golden_vectors) < 4:
        raise ValueError("the protocol must contain at least four RNG golden vectors")
    for vector in golden_vectors:
        key = vector["key"]
        actual = stateless_standard_normal(*key)
        if not math.isclose(
            actual, float(vector["standard_normal"]), rel_tol=0.0, abs_tol=1e-15
        ):
            raise ValueError(f"RNG golden vector mismatch for {key}: {actual}")


def validate_checkpoint_manifest(
    manifest: Mapping[str, Any], *, verify_files: bool = True
) -> None:
    _require_equal(manifest.get("schema_version"), 1, "checkpoint schema_version")
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("checkpoint manifest entries must be a list")
    expected = {(method, seed) for method in METHODS for seed in TRAINING_SEEDS}
    seen: set[tuple[str, int]] = set()
    for entry in entries:
        key = (str(entry.get("method")), int(entry.get("training_seed")))
        if key in seen:
            raise ValueError(f"duplicate checkpoint entry: {key}")
        seen.add(key)
        relative = Path(str(entry.get("path")))
        if relative.is_absolute():
            raise ValueError(f"checkpoint path must be repository-relative: {relative}")
        resolved = (REPO_ROOT / relative).resolve()
        try:
            resolved.relative_to(REPO_ROOT.resolve())
        except ValueError as exc:
            raise ValueError(f"checkpoint escapes repository: {relative}") from exc
        expected_hash = str(entry.get("sha256", ""))
        if len(expected_hash) != 64:
            raise ValueError(f"invalid checkpoint SHA-256 for {key}")
        if verify_files:
            if not resolved.is_file():
                raise FileNotFoundError(f"missing frozen checkpoint: {resolved}")
            actual_hash = sha256_file(resolved)
            if actual_hash != expected_hash:
                raise ValueError(
                    f"checkpoint SHA-256 mismatch for {key}: {actual_hash} != {expected_hash}"
                )
    if seen != expected:
        raise ValueError(f"checkpoint matrix mismatch: {seen} != {expected}")


def checkpoint_entry(
    manifest: Mapping[str, Any], method: str, training_seed: int
) -> Mapping[str, Any]:
    matches = [
        entry
        for entry in manifest["entries"]
        if entry["method"] == method
        and int(entry["training_seed"]) == int(training_seed)
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one checkpoint for {(method, training_seed)}")
    return matches[0]


def expected_episodes(protocol: Mapping[str, Any], phase: str) -> int:
    if phase == "smoke":
        return int(protocol["smoke"]["episodes"])
    return int(protocol["evaluation"]["episodes"])


def validate_run_selection(
    protocol: Mapping[str, Any],
    *,
    phase: str,
    condition: str,
    method: str,
    training_seed: int,
    noise_seed: int,
) -> None:
    if method not in METHODS or training_seed not in TRAINING_SEEDS:
        raise ValueError("method or training seed is outside the frozen matrix")
    if phase == "zero_noise":
        if condition != "clean" or noise_seed != 0:
            raise ValueError("zero_noise is frozen to condition=clean and noise_seed=0")
    elif phase == "smoke":
        if condition not in NOISY_CONDITIONS:
            raise ValueError("smoke requires one of the three noisy conditions")
        if training_seed != int(protocol["smoke"]["training_seed"]):
            raise ValueError("smoke is frozen to training seed 100")
        if noise_seed != int(protocol["smoke"]["noise_seed"]):
            raise ValueError("smoke is frozen to noise seed 41001")
    elif phase == "formal":
        if condition not in NOISY_CONDITIONS:
            raise ValueError("formal runs require one of the three noisy conditions")
        if noise_seed not in FORMAL_NOISE_SEEDS:
            raise ValueError("formal noise seed is outside the frozen matrix")
    else:
        raise ValueError(f"unknown evaluation phase: {phase}")


def condition_flags(condition: str) -> tuple[bool, bool]:
    if condition == "clean":
        return False, False
    if condition == "localization":
        return True, False
    if condition == "actuation":
        return False, True
    if condition == "combined":
        return True, True
    raise ValueError(f"unknown condition: {condition}")


def run_relative_path(
    phase: str,
    condition: str,
    method: str,
    training_seed: int,
    noise_seed: int,
) -> Path:
    if phase == "zero_noise":
        return Path("zero_noise") / f"{method}_trainseed{training_seed}_clean_100ep"
    episodes = 2 if phase == "smoke" else 100
    return Path(phase) / condition / (
        f"{method}_trainseed{training_seed}_noise{noise_seed}_{episodes}ep"
    )


def build_run_manifest(
    *,
    phase: str,
    condition: str,
    method: str,
    training_seed: int,
    noise_seed: int,
) -> dict[str, Any]:
    protocol = load_json(PROTOCOL_PATH)
    checkpoint_manifest = load_json(CHECKPOINT_MANIFEST_PATH)
    validate_protocol(protocol)
    validate_checkpoint_manifest(checkpoint_manifest, verify_files=False)
    validate_run_selection(
        protocol,
        phase=phase,
        condition=condition,
        method=method,
        training_seed=training_seed,
        noise_seed=noise_seed,
    )
    entry = checkpoint_entry(checkpoint_manifest, method, training_seed)
    selected_checkpoint = (REPO_ROOT / entry["path"]).resolve()
    if not selected_checkpoint.is_file():
        raise FileNotFoundError(f"missing frozen checkpoint: {selected_checkpoint}")
    selected_hash = sha256_file(selected_checkpoint)
    if selected_hash != entry["sha256"]:
        raise ValueError(
            f"checkpoint SHA-256 mismatch for {(method, training_seed)}: "
            f"{selected_hash} != {entry['sha256']}"
        )
    localization_enabled, actuation_enabled = condition_flags(condition)
    identity = {
        "phase": phase,
        "condition": condition,
        "training_method": method,
        "training_seed": training_seed,
        "noise_seed": noise_seed,
        "episodes": expected_episodes(protocol, phase),
        "evaluation_seed": int(protocol["evaluation"]["seed"]),
        "evaluation_split": protocol["evaluation"]["split"],
        "evaluation_num_environments": int(protocol["evaluation"]["num_environments"]),
        "checkpoint_relative_path": entry["path"],
        "checkpoint_sha256": entry["sha256"],
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "checkpoint_manifest_sha256": sha256_file(CHECKPOINT_MANIFEST_PATH),
        "noise_manifest_sha256": noise_manifest_sha256(protocol),
        "localization_enabled": localization_enabled,
        "actuation_enabled": actuation_enabled,
    }
    identity["run_identity_sha256"] = canonical_json_sha256(identity)
    identity["checkpoint"] = str(selected_checkpoint)
    return identity


def freeze_artifacts(results_root: Path = RESULTS_ROOT) -> dict[str, str]:
    protocol = load_json(PROTOCOL_PATH)
    checkpoint_manifest = load_json(CHECKPOINT_MANIFEST_PATH)
    validate_protocol(protocol)
    validate_checkpoint_manifest(checkpoint_manifest)
    results_root.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "protocol_snapshot.json": PROTOCOL_PATH.read_bytes(),
        "checkpoint_manifest_snapshot.json": CHECKPOINT_MANIFEST_PATH.read_bytes(),
        "noise_manifest.json": (
            json.dumps(
                noise_manifest_payload(protocol),
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8"),
    }
    for name, content in artifacts.items():
        destination = results_root / name
        if destination.exists() and destination.read_bytes() != content:
            raise ValueError(f"refusing to replace a different frozen artifact: {destination}")
        if not destination.exists():
            destination.write_bytes(content)
    hashes = {
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "checkpoint_manifest_sha256": sha256_file(CHECKPOINT_MANIFEST_PATH),
        "noise_manifest_sha256": noise_manifest_sha256(protocol),
    }
    hash_path = results_root / "frozen_hashes.json"
    encoded = json.dumps(hashes, indent=2, sort_keys=True) + "\n"
    if hash_path.exists() and hash_path.read_text(encoding="utf-8") != encoded:
        raise ValueError(f"refusing to replace different frozen hashes: {hash_path}")
    if not hash_path.exists():
        hash_path.write_text(encoded, encoding="utf-8")
    return hashes


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify_passed_run(run_root: Path, expected: Mapping[str, Any]) -> None:
    status_path = run_root / "run_status.txt"
    if not status_path.is_file() or "status=passed" not in status_path.read_text(
        encoding="utf-8"
    ).splitlines():
        raise ValueError(f"run is not passed: {run_root}")
    actual = load_json(run_root / "condition_manifest.json")
    for key, value in expected.items():
        if key == "checkpoint":
            # Absolute paths legitimately differ after a result bundle is
            # transferred between the pinned Linux host and the review host.
            # The repository-relative path and SHA-256 are checked separately.
            continue
        elif actual.get(key) != value:
            raise ValueError(f"passed run manifest mismatch for {key}: {run_root}")
    summary = load_json(run_root / "robustness_summary.json")
    if summary.get("status") != "complete":
        raise ValueError(f"passed run has incomplete robustness summary: {run_root}")
    if summary.get("run", {}).get("run_identity_sha256") != expected[
        "run_identity_sha256"
    ]:
        raise ValueError(f"passed run identity mismatch: {run_root}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate-run")
    validate.add_argument("--phase", choices=("zero_noise", "smoke", "formal"), required=True)
    validate.add_argument("--condition", required=True)
    validate.add_argument("--method", choices=METHODS, required=True)
    validate.add_argument("--train-seed", type=int, required=True)
    validate.add_argument("--noise-seed", type=int, required=True)
    validate.add_argument("--checkpoint", type=Path, required=True)
    validate.add_argument("--output", type=Path, required=True)
    verify = subparsers.add_parser("verify-run")
    verify.add_argument("--phase", choices=("zero_noise", "smoke", "formal"), required=True)
    verify.add_argument("--condition", required=True)
    verify.add_argument("--method", choices=METHODS, required=True)
    verify.add_argument("--train-seed", type=int, required=True)
    verify.add_argument("--noise-seed", type=int, required=True)
    verify.add_argument("--run-root", type=Path, required=True)
    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--results-root", type=Path, default=RESULTS_ROOT)
    subparsers.add_parser("validate-all")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate-all":
        validate_protocol(load_json(PROTOCOL_PATH))
        validate_checkpoint_manifest(load_json(CHECKPOINT_MANIFEST_PATH))
        print("protocol_and_checkpoints=passed")
        return 0
    if args.command == "freeze":
        print(json.dumps(freeze_artifacts(args.results_root), sort_keys=True))
        return 0
    if args.command == "verify-run":
        manifest = build_run_manifest(
            phase=args.phase,
            condition=args.condition,
            method=args.method,
            training_seed=args.train_seed,
            noise_seed=args.noise_seed,
        )
        verify_passed_run(args.run_root, manifest)
        print("passed_run_verified=1")
        return 0
    manifest = build_run_manifest(
        phase=args.phase,
        condition=args.condition,
        method=args.method,
        training_seed=args.train_seed,
        noise_seed=args.noise_seed,
    )
    supplied = args.checkpoint.resolve()
    expected = Path(manifest["checkpoint"]).resolve()
    if supplied != expected:
        raise SystemExit(f"checkpoint path mismatch: {supplied} != {expected}")
    write_json(args.output, manifest)
    print(manifest["run_identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
