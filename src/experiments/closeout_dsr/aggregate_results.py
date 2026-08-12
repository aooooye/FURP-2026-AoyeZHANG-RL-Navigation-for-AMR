#!/usr/bin/env python3
"""Aggregate the frozen three-seed baseline versus DSR comparison."""

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
RESULTS_ROOT = REPO_ROOT / "src" / "results" / "closeout_dsr"
SEEDS = (100, 200, 300)
METRICS = (
    "success",
    "spl",
    "distance_to_goal",
    "reward",
    "stop_called",
    "premature_stop",
    "non_stop_failure",
)


def summary_path(condition: str, seed: int) -> Path:
    return (
        RESULTS_ROOT
        / (
            f"closeout_eval_{condition}_trainseed{seed}_"
            "evalseed2026_100ep"
        )
        / "summary.json"
    )


def load_record(condition: str, seed: int) -> Dict[str, object]:
    path = summary_path(condition, seed)
    if not path.is_file():
        raise FileNotFoundError(f"missing frozen evaluation summary: {path}")
    evaluation_status = path.parent / "run_status.txt"
    if not evaluation_status.is_file() or "status=passed" not in (
        evaluation_status.read_text(encoding="utf-8").splitlines()
    ):
        raise ValueError(f"evaluation run did not pass: {path.parent}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "complete":
        raise ValueError(f"incomplete evaluation summary: {path}")
    if payload.get("seed") != 2026 or payload.get("episodes_requested") != 100:
        raise ValueError(f"evaluation protocol mismatch: {path}")

    train_root = (
        RESULTS_ROOT
        / f"closeout_{condition}_trainseed{seed}_1m_env5"
    )
    training_status = train_root / "run_status.txt"
    if not training_status.is_file() or "status=passed" not in (
        training_status.read_text(encoding="utf-8").splitlines()
    ):
        raise ValueError(f"fresh training run did not pass: {train_root}")
    final_checkpoint_pointer = train_root / "final_checkpoint_path.txt"
    if not final_checkpoint_pointer.is_file():
        raise FileNotFoundError(
            "missing fresh-training checkpoint pointer: "
            f"{final_checkpoint_pointer}"
        )
    expected_checkpoint = Path(
        final_checkpoint_pointer.read_text(encoding="utf-8").strip()
    ).resolve()
    evaluated_checkpoint = Path(str(payload.get("checkpoint", ""))).resolve()
    if evaluated_checkpoint != expected_checkpoint:
        raise ValueError(
            "evaluation checkpoint is not the corresponding fresh same-server "
            f"training output: {path}"
        )

    metrics = payload.get("metrics", {})
    missing = [name for name in METRICS if name not in metrics]
    if missing:
        raise ValueError(f"missing metrics {missing}: {path}")
    return {
        "condition": condition,
        "training_seed": seed,
        "evaluation_seed": 2026,
        "episodes": 100,
        "source": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "metrics": {name: float(metrics[name]) for name in METRICS},
    }


def summarize(records: List[Dict[str, object]]) -> Dict[str, object]:
    output: Dict[str, object] = {}
    for name in METRICS:
        values = [float(record["metrics"][name]) for record in records]
        output[name] = {
            "mean": statistics.mean(values),
            "sample_std": statistics.stdev(values),
            "values": values,
        }
    return output


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def make_markdown(payload: Dict[str, object]) -> str:
    records = payload["records"]
    summaries = payload["condition_summaries"]
    delta = payload["delta_dsr_minus_baseline"]
    lines = [
        "# Frozen baseline versus DSR results",
        "",
        "All policies use standard Habitat 0.3.3 reward and dynamics plus numeric "
        "terminal STOP diagnostics during evaluation. Training seed varies; evaluation "
        "seed is fixed at 2026 for 100 episodes.",
        "",
        "| Condition | Train seed | Success | SPL | Final distance | Premature STOP | Non-STOP failure |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for record in records:
        metrics = record["metrics"]
        lines.append(
            "| {condition} | {seed} | {success} | {spl} | {distance:.4f} m | {premature} | {non_stop} |".format(
                condition=record["condition"],
                seed=record["training_seed"],
                success=pct(metrics["success"]),
                spl=pct(metrics["spl"]),
                distance=metrics["distance_to_goal"],
                premature=pct(metrics["premature_stop"]),
                non_stop=pct(metrics["non_stop_failure"]),
            )
        )
    lines.extend(
        [
            "",
            "| Condition | Mean Success | Mean SPL | Mean final distance | Mean premature STOP | Success SD | SPL SD |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for condition in ("baseline", "dsr"):
        stats = summaries[condition]
        lines.append(
            "| {condition} | {success} | {spl} | {distance:.4f} m | {premature} | {success_sd} | {spl_sd} |".format(
                condition=condition,
                success=pct(stats["success"]["mean"]),
                spl=pct(stats["spl"]["mean"]),
                distance=stats["distance_to_goal"]["mean"],
                premature=pct(stats["premature_stop"]["mean"]),
                success_sd=pct(stats["success"]["sample_std"]),
                spl_sd=pct(stats["spl"]["sample_std"]),
            )
        )
    lines.extend(
        [
            "",
            "## Directional differences",
            "",
            f"- Success: {100.0 * delta['success']:+.2f} percentage points.",
            f"- SPL: {100.0 * delta['spl']:+.2f} percentage points.",
            f"- Final distance: {delta['distance_to_goal']:+.4f} m (negative is better).",
            f"- Premature STOP rate: {100.0 * delta['premature_stop']:+.2f} percentage points (negative is better).",
            f"- Non-STOP failure rate: {100.0 * delta['non_stop_failure']:+.2f} percentage points (negative is better).",
            f"- Standard evaluation reward: {delta['reward']:+.4f}.",
            "",
            "These are two-scene fallback results, not a Gibson/HM3D benchmark or a "
            "claim of statistical significance. A null or negative result remains the final result; "
            "the protocol does not permit switching methods after inspection.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    records = [
        load_record(condition, seed)
        for condition in ("baseline", "dsr")
        for seed in SEEDS
    ]
    grouped = {
        condition: [
            record for record in records if record["condition"] == condition
        ]
        for condition in ("baseline", "dsr")
    }
    summaries = {
        condition: summarize(grouped[condition])
        for condition in ("baseline", "dsr")
    }
    delta = {
        name: summaries["dsr"][name]["mean"]
        - summaries["baseline"][name]["mean"]
        for name in METRICS
    }
    payload = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": {
            "profile": "habitat_test",
            "training_seeds": list(SEEDS),
            "evaluation_seed": 2026,
            "episodes_per_policy": 100,
            "evaluation_environment": (
                "standard Habitat 0.3.3 reward/dynamics plus numeric STOP diagnostics"
            ),
        },
        "records": records,
        "condition_summaries": summaries,
        "delta_dsr_minus_baseline": delta,
        "claim_boundary": (
            "Two-scene Habitat test-scenes fallback; controlled project ablation, "
            "not a Gibson/HM3D benchmark or statistical significance claim."
        ),
    }
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    (RESULTS_ROOT / "comparison.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (RESULTS_ROOT / "comparison.md").write_text(
        make_markdown(payload), encoding="utf-8"
    )
    print(RESULTS_ROOT / "comparison.md")


if __name__ == "__main__":
    main()
