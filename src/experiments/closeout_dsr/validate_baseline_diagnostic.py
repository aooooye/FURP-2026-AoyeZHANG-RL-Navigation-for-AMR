#!/usr/bin/env python3
"""Gate the frozen experiment using the transferred seed-100 checkpoint."""

import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
OLD_SUMMARY = (
    REPO_ROOT
    / "src"
    / "results"
    / "week03"
    / "remote_20260716T074249Z"
    / "week03_eval_habitat_test_seed2026_100ep_ckpt9_env2"
    / "summary.json"
)
NEW_SUMMARY = (
    REPO_ROOT
    / "src"
    / "results"
    / "closeout_dsr"
    / "closeout_diagnostic_oldbaseline_trainseed100_evalseed2026_100ep"
    / "summary.json"
)
OUTPUT = (
    REPO_ROOT
    / "src"
    / "results"
    / "closeout_dsr"
    / "baseline_diagnostic_gate.json"
)
REPRODUCTION_METRICS = ("success", "spl", "distance_to_goal", "reward")
TOLERANCES = {
    "success": 0.02,
    "spl": 0.02,
    "distance_to_goal": 0.02,
    "reward": 0.10,
}
DECOMPOSITION_TOLERANCE = 0.0002


def load(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "complete":
        raise ValueError(f"incomplete summary: {path}")
    return payload


def main() -> int:
    old = load(OLD_SUMMARY)
    new = load(NEW_SUMMARY)
    old_metrics = old["metrics"]
    new_metrics = new["metrics"]

    metric_differences = {
        name: float(new_metrics[name]) - float(old_metrics[name])
        for name in REPRODUCTION_METRICS
    }
    reproduction_passed = all(
        abs(value) <= TOLERANCES[name]
        for name, value in metric_differences.items()
    )

    premature_stop = float(new_metrics["premature_stop"])
    non_stop_failure = float(new_metrics["non_stop_failure"])
    failure_rate = 1.0 - float(new_metrics["success"])
    decomposition_error = abs(
        premature_stop + non_stop_failure - failure_rate
    )
    decomposition_passed = decomposition_error <= DECOMPOSITION_TOLERANCE
    mechanism_passed = premature_stop > non_stop_failure

    passed = (
        reproduction_passed
        and decomposition_passed
        and mechanism_passed
    )
    payload = {
        "status": "passed" if passed else "failed",
        "metric_tolerances": TOLERANCES,
        "metric_differences_new_minus_old": metric_differences,
        "reproduction_passed": reproduction_passed,
        "failure_rate": failure_rate,
        "premature_stop_rate": premature_stop,
        "non_stop_failure_rate": non_stop_failure,
        "failure_decomposition_error": decomposition_error,
        "failure_decomposition_tolerance": DECOMPOSITION_TOLERANCE,
        "failure_decomposition_passed": decomposition_passed,
        "mechanism_gate": "premature_stop_rate > non_stop_failure_rate",
        "mechanism_passed": mechanism_passed,
        "old_summary": str(OLD_SUMMARY.relative_to(REPO_ROOT)).replace("\\", "/"),
        "new_summary": str(NEW_SUMMARY.relative_to(REPO_ROOT)).replace("\\", "/"),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
