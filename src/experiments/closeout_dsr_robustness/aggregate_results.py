#!/usr/bin/env python3
"""Strict aggregation for the frozen 54-run noisy robustness matrix."""

from __future__ import annotations

import csv
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from protocol_guard import (
    FORMAL_NOISE_SEEDS,
    METRICS,
    METHODS,
    NOISY_CONDITIONS,
    RESULTS_ROOT,
    TRAINING_SEEDS,
    build_run_manifest,
    load_json,
    run_relative_path,
    verify_passed_run,
)


def spec_key(
    phase: str,
    condition: str,
    method: str,
    training_seed: int,
    noise_seed: int,
) -> tuple[str, str, str, int, int]:
    return phase, condition, method, training_seed, noise_seed


def expected_specs() -> list[tuple[str, str, str, int, int]]:
    clean = [
        spec_key("zero_noise", "clean", method, seed, 0)
        for method in METHODS
        for seed in TRAINING_SEEDS
    ]
    formal = [
        spec_key("formal", condition, method, seed, noise_seed)
        for condition in NOISY_CONDITIONS
        for method in METHODS
        for seed in TRAINING_SEEDS
        for noise_seed in FORMAL_NOISE_SEEDS
    ]
    return clean + formal


def root_for(spec: tuple[str, str, str, int, int]) -> Path:
    phase, condition, method, seed, noise_seed = spec
    return RESULTS_ROOT / run_relative_path(
        phase, condition, method, seed, noise_seed
    )


def discover_formal_manifests() -> set[Path]:
    root = RESULTS_ROOT / "formal"
    if not root.exists():
        return set()
    return {
        path.parent.relative_to(RESULTS_ROOT)
        for path in root.rglob("condition_manifest.json")
    }


def validate_exact_formal_matrix() -> None:
    expected = {
        run_relative_path("formal", condition, method, seed, noise_seed)
        for condition in NOISY_CONDITIONS
        for method in METHODS
        for seed in TRAINING_SEEDS
        for noise_seed in FORMAL_NOISE_SEEDS
    }
    discovered = discover_formal_manifests()
    missing = sorted(str(path) for path in expected - discovered)
    extra = sorted(str(path) for path in discovered - expected)
    if missing or extra:
        raise ValueError(
            f"formal matrix is not exact; missing={missing}, extra={extra}"
        )


def load_record(spec: tuple[str, str, str, int, int]) -> dict[str, Any]:
    phase, condition, method, seed, noise_seed = spec
    expected = build_run_manifest(
        phase=phase,
        condition=condition,
        method=method,
        training_seed=seed,
        noise_seed=noise_seed,
    )
    root = root_for(spec)
    verify_passed_run(root, expected)
    summary = load_json(root / "robustness_summary.json")
    if phase == "zero_noise" and summary.get("zero_noise_gate", {}).get(
        "status"
    ) != "passed":
        raise ValueError(f"zero-noise gate is absent or failed: {root}")
    metrics = summary.get("metrics", {})
    if tuple(metrics.keys()) != tuple(sorted(METRICS)):
        # JSON is written with sorted keys; exact membership is what matters.
        if set(metrics) != set(METRICS):
            raise ValueError(f"metric schema mismatch: {root}")
    return {
        "phase": phase,
        "condition": condition,
        "method": method,
        "training_seed": seed,
        "noise_seed": noise_seed,
        "episodes": int(summary["episodes"]),
        "episode_set_sha256": summary["episode_set_sha256"],
        "run_identity_sha256": expected["run_identity_sha256"],
        "checkpoint_sha256": expected["checkpoint_sha256"],
        "source": str(root.relative_to(RESULTS_ROOT.parent.parent.parent)).replace(
            "\\", "/"
        ),
        "metrics": {name: float(metrics[name]) for name in METRICS},
    }


def validate_episode_sets(records: Iterable[Mapping[str, Any]]) -> str:
    hashes = {str(record["episode_set_sha256"]) for record in records}
    if len(hashes) != 1:
        raise ValueError(f"evaluation episode sets differ across runs: {sorted(hashes)}")
    return next(iter(hashes))


def build_cells(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = {
        (
            record["phase"],
            record["condition"],
            record["method"],
            record["training_seed"],
            record["noise_seed"],
        ): record
        for record in records
    }
    cells: list[dict[str, Any]] = []
    for condition in NOISY_CONDITIONS:
        for seed in TRAINING_SEEDS:
            for noise_seed in FORMAL_NOISE_SEEDS:
                methods: dict[str, Any] = {}
                for method in METHODS:
                    clean = index[("zero_noise", "clean", method, seed, 0)]
                    noisy = index[("formal", condition, method, seed, noise_seed)]
                    methods[method] = {
                        "clean": clean["metrics"],
                        "noisy": noisy["metrics"],
                        "drop_noisy_minus_clean": {
                            metric: noisy["metrics"][metric]
                            - clean["metrics"][metric]
                            for metric in METRICS
                        },
                    }
                cells.append(
                    {
                        "condition": condition,
                        "training_seed": seed,
                        "noise_seed": noise_seed,
                        "methods": methods,
                        "robustness_advantage_dsr_drop_minus_baseline_drop": {
                            metric: methods["dsr"]["drop_noisy_minus_clean"][metric]
                            - methods["baseline"]["drop_noisy_minus_clean"][metric]
                            for metric in METRICS
                        },
                    }
                )
    return cells


def summarize_cells(cells: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for condition in NOISY_CONDITIONS:
        condition_cells = [cell for cell in cells if cell["condition"] == condition]
        metric_summaries: dict[str, Any] = {}
        for metric in METRICS:
            seed_rows = []
            for seed in TRAINING_SEEDS:
                values = [
                    float(
                        cell[
                            "robustness_advantage_dsr_drop_minus_baseline_drop"
                        ][metric]
                    )
                    for cell in condition_cells
                    if cell["training_seed"] == seed
                ]
                if len(values) != len(FORMAL_NOISE_SEEDS):
                    raise ValueError(
                        f"noise-seed cell count mismatch for {condition}/{metric}/{seed}"
                    )
                seed_rows.append(
                    {
                        "training_seed": seed,
                        "noise_seed_values": values,
                        "mean_over_noise_seeds": statistics.fmean(values),
                    }
                )
            seed_means = [row["mean_over_noise_seeds"] for row in seed_rows]
            metric_summaries[metric] = {
                "training_seed_rows": seed_rows,
                "mean_over_training_seeds": statistics.fmean(seed_means),
                "sample_std_over_training_seeds": statistics.stdev(seed_means),
                "positive_training_seed_count": sum(value > 0.0 for value in seed_means),
            }
        output[condition] = metric_summaries
    return output


def success_interpretation(summary: Mapping[str, Any]) -> str:
    combined = summary["combined"]["success"]
    mean = float(combined["mean_over_training_seeds"])
    positive_count = int(combined["positive_training_seed_count"])
    if mean > 0.0 and positive_count >= 2:
        return "DSR呈一致性较好的鲁棒优势。"
    if mean > 0.0:
        return "结果混合：存在平均优势，但缺乏跨训练种子一致性。"
    return "未观察到DSR鲁棒优势。"


def write_comparison_csv(path: Path, cells: Iterable[Mapping[str, Any]]) -> None:
    fields = [
        "condition",
        "training_seed",
        "noise_seed",
        "metric",
        "baseline_clean",
        "baseline_noisy",
        "baseline_drop",
        "dsr_clean",
        "dsr_noisy",
        "dsr_drop",
        "robustness_advantage",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for cell in cells:
            for metric in METRICS:
                baseline = cell["methods"]["baseline"]
                dsr = cell["methods"]["dsr"]
                writer.writerow(
                    {
                        "condition": cell["condition"],
                        "training_seed": cell["training_seed"],
                        "noise_seed": cell["noise_seed"],
                        "metric": metric,
                        "baseline_clean": baseline["clean"][metric],
                        "baseline_noisy": baseline["noisy"][metric],
                        "baseline_drop": baseline["drop_noisy_minus_clean"][metric],
                        "dsr_clean": dsr["clean"][metric],
                        "dsr_noisy": dsr["noisy"][metric],
                        "dsr_drop": dsr["drop_noisy_minus_clean"][metric],
                        "robustness_advantage": cell[
                            "robustness_advantage_dsr_drop_minus_baseline_drop"
                        ][metric],
                    }
                )


def write_status_csv(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    fields = [
        "phase",
        "condition",
        "method",
        "training_seed",
        "noise_seed",
        "episodes",
        "checkpoint_sha256",
        "run_identity_sha256",
        "source",
        "status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    **{field: record.get(field) for field in fields},
                    "status": "passed",
                }
            )


def conclusion_markdown(payload: Mapping[str, Any]) -> str:
    summaries = payload["condition_summaries"]
    lines = [
        "# DSR controlled test-time robustness result",
        "",
        f"**Primary interpretation:** {payload['primary_interpretation']}",
        "",
        "| Noise condition | Success robustness advantage | Seed-direction consistency | SPL robustness advantage |",
        "|---|---:|---:|---:|",
    ]
    for condition in NOISY_CONDITIONS:
        success = summaries[condition]["success"]
        spl = summaries[condition]["spl"]
        lines.append(
            "| {condition} | {success:+.4f} | {count}/3 | {spl:+.4f} |".format(
                condition=condition,
                success=success["mean_over_training_seeds"],
                count=success["positive_training_seed_count"],
                spl=spl["mean_over_training_seeds"],
            )
        )
    lines.extend(
        [
            "",
            "Robustness advantage is `(DSR noisy - DSR clean) - "
            "(Baseline noisy - Baseline clean)`; positive values are favorable "
            "for Success and SPL.",
            "",
            "This is descriptive evidence from two Habitat test scenes. No "
            "statistical-significance, Gibson/HM3D, real-robot, or Sim2Real claim is made.",
            "",
        ]
    )
    return "\n".join(lines)


def aggregate() -> dict[str, Any]:
    validate_exact_formal_matrix()
    records = [load_record(spec) for spec in expected_specs()]
    if len(records) != 60:
        raise ValueError(f"expected 60 clean/formal records, got {len(records)}")
    episode_set_sha256 = validate_episode_sets(records)
    cells = build_cells(records)
    if len(cells) != 27:
        raise ValueError(f"expected 27 paired noisy cells, got {len(cells)}")
    summaries = summarize_cells(cells)
    payload = {
        "schema_version": 1,
        "status": "complete",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": {
            "zero_noise_runs": 6,
            "formal_noisy_runs": 54,
            "episodes_total": 6000,
            "training_seeds": list(TRAINING_SEEDS),
            "noise_seeds": list(FORMAL_NOISE_SEEDS),
            "conditions": list(NOISY_CONDITIONS),
            "episode_set_sha256": episode_set_sha256,
            "statistics": (
                "mean over three noise seeds within each training seed, then "
                "mean and sample SD over three training seeds"
            ),
        },
        "records": records,
        "paired_cells": cells,
        "condition_summaries": summaries,
        "primary_interpretation": success_interpretation(summaries),
        "claim_boundary": (
            "Controlled test-time robustness on two Habitat test scenes; "
            "descriptive only, without significance or deployment claims."
        ),
    }
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    (RESULTS_ROOT / "comparison.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_comparison_csv(RESULTS_ROOT / "comparison.csv", cells)
    write_status_csv(RESULTS_ROOT / "run_status.csv", records)
    (RESULTS_ROOT / "conclusion.md").write_text(
        conclusion_markdown(payload), encoding="utf-8"
    )
    return payload


def main() -> int:
    payload = aggregate()
    print(payload["primary_interpretation"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
