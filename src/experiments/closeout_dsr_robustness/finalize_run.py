#!/usr/bin/env python3
"""Merge vector-worker telemetry and validate one robustness evaluation."""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from protocol_guard import METRICS, load_json
from robustness_core import canonical_json_sha256, sha256_file


EPISODE_BOOLEAN_METRICS = (
    "success",
    "stop_called",
    "premature_stop",
    "non_stop_failure",
)
EVALUATOR_LOG_TOLERANCES = {
    # Habitat prints four decimals. Episode reward is accumulated once by the
    # evaluator and independently by the telemetry wrapper, so float32/float64
    # accumulation can add a few micro-units beyond the 0.5e-4 print bound.
    "reward": 1.1e-4,
}
DEFAULT_EVALUATOR_LOG_TOLERANCE = 5.1e-5


def load_episode_shards(shard_directory: Path) -> list[dict[str, Any]]:
    if not shard_directory.is_dir():
        raise FileNotFoundError(f"episode shard directory is absent: {shard_directory}")
    shard_paths = sorted(shard_directory.glob("episodes-*.jsonl"))
    if not shard_paths:
        raise FileNotFoundError(f"no episode shards found in {shard_directory}")
    records: list[dict[str, Any]] = []
    for path in shard_paths:
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"non-object record in {path}:{line_number}")
            records.append(payload)
    return records


def validate_episode_records(
    records: list[dict[str, Any]],
    manifest: Mapping[str, Any],
    expected_episodes: int,
) -> list[dict[str, Any]]:
    if len(records) != expected_episodes:
        raise ValueError(
            f"episode count mismatch: {len(records)} != {expected_episodes}"
        )
    expected_fields = {
        "phase": manifest["phase"],
        "condition": manifest["condition"],
        "training_method": manifest["training_method"],
        "training_seed": manifest["training_seed"],
        "noise_seed": manifest["noise_seed"],
        "checkpoint_sha256": manifest["checkpoint_sha256"],
        "protocol_sha256": manifest["protocol_sha256"],
        "checkpoint_manifest_sha256": manifest["checkpoint_manifest_sha256"],
        "noise_manifest_sha256": manifest["noise_manifest_sha256"],
        "run_identity_sha256": manifest["run_identity_sha256"],
    }
    identities: set[tuple[str, str]] = set()
    for record in records:
        for key, expected in expected_fields.items():
            if record.get(key) != expected:
                raise ValueError(
                    f"episode metadata mismatch for {key}: {record.get(key)!r} != {expected!r}"
                )
        identity = (str(record.get("scene_id")), str(record.get("episode_id")))
        if identity in identities:
            raise ValueError(f"duplicate episode identity: {identity}")
        identities.add(identity)
        steps = int(record.get("steps", -1))
        if not 1 <= steps <= 500:
            raise ValueError(f"invalid episode step count for {identity}: {steps}")
        for metric in METRICS:
            if metric not in record:
                raise ValueError(f"episode {identity} is missing metric {metric}")
        success = bool(record["success"])
        stop_called = bool(record["stop_called"])
        premature = bool(record["premature_stop"])
        non_stop = bool(record["non_stop_failure"])
        if premature != (stop_called and not success):
            raise ValueError(f"premature STOP partition mismatch for {identity}")
        if non_stop != ((not stop_called) and not success):
            raise ValueError(f"non-STOP failure partition mismatch for {identity}")
    return sorted(records, key=lambda item: (str(item["scene_id"]), str(item["episode_id"])))


def aggregate_episode_metrics(records: Iterable[Mapping[str, Any]]) -> dict[str, float]:
    rows = list(records)
    return {
        metric: statistics.fmean(float(row[metric]) for row in rows)
        for metric in METRICS
    }


def compare_evaluator_summary(
    evaluator_summary: Mapping[str, Any],
    manifest: Mapping[str, Any],
    metrics: Mapping[str, float],
) -> dict[str, float]:
    if evaluator_summary.get("status") != "complete":
        raise ValueError("Habitat evaluator summary is incomplete")
    if evaluator_summary.get("seed") != manifest["evaluation_seed"]:
        raise ValueError("Habitat evaluator seed mismatch")
    if evaluator_summary.get("episodes_requested") != manifest["episodes"]:
        raise ValueError("Habitat evaluator episode count mismatch")
    if evaluator_summary.get("checkpoint_sha256") != manifest["checkpoint_sha256"]:
        raise ValueError("Habitat evaluator checkpoint SHA-256 mismatch")
    logged = evaluator_summary.get("metrics", {})
    differences: dict[str, float] = {}
    for metric in METRICS:
        if metric not in logged:
            raise ValueError(f"Habitat evaluator summary is missing metric {metric}")
        difference = abs(float(metrics[metric]) - float(logged[metric]))
        differences[metric] = difference
        tolerance = EVALUATOR_LOG_TOLERANCES.get(
            metric, DEFAULT_EVALUATOR_LOG_TOLERANCE
        )
        if difference > tolerance:
            raise ValueError(
                f"episode telemetry disagrees with evaluator for {metric}: "
                f"{metrics[metric]} vs {logged[metric]} (tolerance={tolerance})"
            )
    return differences


def compare_zero_noise_reference(
    evaluator_summary: Mapping[str, Any],
    reference_summary: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    if reference_summary.get("status") != "complete":
        raise ValueError("historical clean reference summary is incomplete")
    if reference_summary.get("seed") != 2026 or reference_summary.get(
        "episodes_requested"
    ) != 100:
        raise ValueError("historical clean reference protocol mismatch")
    if reference_summary.get("checkpoint_sha256") != manifest["checkpoint_sha256"]:
        raise ValueError("historical clean reference checkpoint mismatch")
    differences: dict[str, float] = {}
    for metric in METRICS:
        actual = float(evaluator_summary["metrics"][metric])
        expected = float(reference_summary["metrics"][metric])
        difference = abs(actual - expected)
        differences[metric] = difference
        if difference > 1e-6:
            raise ValueError(
                f"zero-noise gate failed for {metric}: {actual} != {expected}"
            )
    return {
        "status": "passed",
        "aggregate_tolerance": 1e-6,
        "aggregate_absolute_differences": differences,
        "historical_episode_level_available": False,
        "historical_episode_level_note": (
            "The frozen first-stage evaluator recorded aggregate metrics only. "
            "The new clean run is the episode-level reference for paired noisy analyses."
        ),
        "reference_summary_sha256": canonical_json_sha256(reference_summary),
    }


def finalize(
    run_root: Path,
    *,
    expected_episodes: int,
    reference_summary_path: Path | None = None,
) -> dict[str, Any]:
    manifest_path = run_root / "condition_manifest.json"
    evaluator_summary_path = run_root / "summary.json"
    manifest = load_json(manifest_path)
    evaluator_summary = load_json(evaluator_summary_path)
    if int(manifest["episodes"]) != expected_episodes:
        raise ValueError("condition manifest episode count mismatch")
    records = validate_episode_records(
        load_episode_shards(run_root / "episode_shards"),
        manifest,
        expected_episodes,
    )
    metrics = aggregate_episode_metrics(records)
    evaluator_differences = compare_evaluator_summary(
        evaluator_summary, manifest, metrics
    )

    episodes_path = run_root / "episodes.jsonl"
    with episodes_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            handle.write("\n")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "status": "complete",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "run": manifest,
        "episodes": expected_episodes,
        "episode_set_sha256": canonical_json_sha256(
            [[row["scene_id"], row["episode_id"]] for row in records]
        ),
        "episodes_jsonl_sha256": sha256_file(episodes_path),
        "metrics": metrics,
        "evaluator_rounding_absolute_differences": evaluator_differences,
    }
    if reference_summary_path is not None:
        payload["zero_noise_gate"] = compare_zero_noise_reference(
            evaluator_summary,
            load_json(reference_summary_path),
            manifest,
        )
    output = run_root / "robustness_summary.json"
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--expected-episodes", type=int, required=True)
    parser.add_argument("--reference-summary", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    payload = finalize(
        args.run_root,
        expected_episodes=args.expected_episodes,
        reference_summary_path=args.reference_summary,
    )
    print(json.dumps(payload["metrics"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
