#!/usr/bin/env python3
"""Parse one Habitat evaluator log into reviewable JSON and Markdown."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
AVERAGE_METRIC = re.compile(
    rf"Average episode\s+([^:\r\n]+):\s*({FLOAT})(?:\s|$)", re.IGNORECASE
)
REQUIRED_METRICS = ("reward", "success", "spl", "distance_to_goal")


def normalize_metric_name(name: str) -> str:
    return re.sub(r"\s+", "_", name.strip().lower())


def parse_metric_occurrences(text: str) -> dict[str, list[float]]:
    occurrences: dict[str, list[float]] = {}
    for match in AVERAGE_METRIC.finditer(text):
        name = normalize_metric_name(match.group(1))
        occurrences.setdefault(name, []).append(float(match.group(2)))
    return occurrences


def final_metrics(occurrences: dict[str, list[float]]) -> dict[str, float]:
    return {name: values[-1] for name, values in sorted(occurrences.items())}


def missing_required(metrics: dict[str, float]) -> list[str]:
    return [name for name in REQUIRED_METRICS if name not in metrics]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def optional_metric_status(metrics: Iterable[str]) -> dict[str, str]:
    names = tuple(metrics)
    return {
        "collision": "available"
        if any("collision" in name for name in names)
        else "unavailable",
        "path_length_or_efficiency": "available"
        if any("path" in name and name != "spl" for name in names)
        else "unavailable",
    }


def markdown_summary(payload: dict[str, object]) -> str:
    metrics = payload["metrics"]
    assert isinstance(metrics, dict)
    rows = ["| Metric | Mean |", "|---|---:|"]
    rows.extend(f"| `{name}` | {value:.6g} |" for name, value in metrics.items())
    return "\n".join(
        [
            "# Weeks 3 & 4 Fixed Evaluation Summary",
            "",
            f"- Status: **{payload['status']}**",
            f"- Profile: `{payload['profile']}`",
            f"- Config: `{payload['config']}`",
            f"- Seed: `{payload['seed']}`",
            f"- Split: `{payload['split']}`",
            f"- Episodes requested: `{payload['episodes_requested']}`",
            f"- Checkpoint: `{payload['checkpoint']}`",
            "",
            *rows,
            "",
            "Optional metric availability is recorded in `summary.json`. Missing metrics are not estimated.",
            "",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--split", required=True)
    parser.add_argument("--episodes", type=int, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.log.is_file():
        raise SystemExit(f"Evaluation log does not exist: {args.log}")
    if not args.checkpoint.is_file():
        raise SystemExit(f"Checkpoint does not exist: {args.checkpoint}")

    occurrences = parse_metric_occurrences(args.log.read_text(encoding="utf-8", errors="replace"))
    metrics = final_metrics(occurrences)
    missing = missing_required(metrics)
    if missing:
        raise SystemExit(
            "Evaluation log is missing required aggregate metrics: " + ", ".join(missing)
        )

    payload: dict[str, object] = {
        "schema_version": 1,
        "status": "complete",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "profile": args.profile,
        "config": args.config,
        "seed": args.seed,
        "split": args.split,
        "episodes_requested": args.episodes,
        "checkpoint": str(args.checkpoint.resolve()),
        "checkpoint_sha256": sha256(args.checkpoint),
        "source_log": str(args.log.resolve()),
        "metrics": metrics,
        "metric_occurrence_counts": {
            name: len(values) for name, values in sorted(occurrences.items())
        },
        "optional_metric_status": optional_metric_status(metrics),
        "claim_boundary": (
            "Metrics are parsed from a separate fixed evaluation. They are not "
            "rolling training-window diagnostics."
        ),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(markdown_summary(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
