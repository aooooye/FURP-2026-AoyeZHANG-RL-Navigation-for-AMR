import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from inspect_checkpoint import get_nested, integer_value
from summarize_eval import final_metrics, missing_required, parse_metric_occurrences


class SummarizeEvalTests(unittest.TestCase):
    def test_summary_cli_writes_json_and_markdown(self):
        script = Path(__file__).with_name("summarize_eval.py")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            log = root / "eval.log"
            checkpoint = root / "trusted_test_checkpoint.pth"
            output = root / "summary.json"
            markdown = root / "summary.md"
            log.write_text(
                "\n".join(
                    [
                        "Average episode reward: 4.5",
                        "Average episode success: 0.75",
                        "Average episode spl: 0.625",
                        "Average episode distance_to_goal: 0.8",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            checkpoint.write_bytes(b"test-only-checkpoint-placeholder")

            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--log",
                    str(log),
                    "--output",
                    str(output),
                    "--markdown-output",
                    str(markdown),
                    "--profile",
                    "gibson",
                    "--config",
                    "pointnav/ppo_pointnav",
                    "--seed",
                    "100",
                    "--split",
                    "val",
                    "--episodes",
                    "100",
                    "--checkpoint",
                    str(checkpoint),
                ],
                check=True,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("complete", payload["status"])
            self.assertEqual(0.75, payload["metrics"]["success"])
            self.assertIn("Fixed Evaluation Summary", markdown.read_text(encoding="utf-8"))

    def test_checkpoint_helpers_read_nested_step(self):
        checkpoint = {
            "extra_state": {"step": 5_000_128},
            "config": {"habitat_baselines": {"total_num_steps": 5_000_000}},
        }
        self.assertEqual(
            5_000_128, integer_value(get_nested(checkpoint, "extra_state", "step"))
        )
        self.assertEqual(
            5_000_000,
            integer_value(
                get_nested(
                    checkpoint, "config", "habitat_baselines", "total_num_steps"
                )
            ),
        )

    def test_parses_habitat_aggregate_metrics(self):
        text = """
        2026-07-16 INFO Average episode reward: 6.1250
        2026-07-16 INFO Average episode success: 0.8300
        2026-07-16 INFO Average episode spl: 0.7125
        2026-07-16 INFO Average episode distance_to_goal: 0.4200
        2026-07-16 INFO Average episode collisions.count: 1.2500
        """
        occurrences = parse_metric_occurrences(text)
        metrics = final_metrics(occurrences)
        self.assertEqual([], missing_required(metrics))
        self.assertAlmostEqual(0.83, metrics["success"])
        self.assertAlmostEqual(0.7125, metrics["spl"])
        self.assertAlmostEqual(1.25, metrics["collisions.count"])

    def test_uses_last_occurrence_and_detects_missing_metrics(self):
        text = """
        Average episode reward: 1.0
        Average episode reward: 2.0
        Average episode success: 0.5
        """
        metrics = final_metrics(parse_metric_occurrences(text))
        self.assertEqual(2.0, metrics["reward"])
        self.assertEqual(["spl", "distance_to_goal"], missing_required(metrics))


if __name__ == "__main__":
    unittest.main()
