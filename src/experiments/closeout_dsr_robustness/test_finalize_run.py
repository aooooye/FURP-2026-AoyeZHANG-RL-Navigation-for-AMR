import json
import tempfile
import unittest
from pathlib import Path

from finalize_run import (
    compare_evaluator_summary,
    finalize,
    validate_episode_records,
)
from protocol_guard import METRICS


class FinalizeRunTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name) / "run"
        (self.root / "episode_shards").mkdir(parents=True)
        self.manifest = {
            "phase": "smoke",
            "condition": "combined",
            "training_method": "baseline",
            "training_seed": 100,
            "noise_seed": 41001,
            "episodes": 2,
            "evaluation_seed": 2026,
            "checkpoint_sha256": "a" * 64,
            "protocol_sha256": "b" * 64,
            "checkpoint_manifest_sha256": "c" * 64,
            "noise_manifest_sha256": "d" * 64,
            "run_identity_sha256": "e" * 64,
        }
        self.records = [self._record("scene-a", "0", True), self._record("scene-b", "1", False)]
        self._write_inputs()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _record(self, scene, episode, success):
        return {
            "schema_version": 1,
            **{key: self.manifest[key] for key in (
                "phase", "condition", "training_seed", "noise_seed",
                "checkpoint_sha256", "protocol_sha256",
                "checkpoint_manifest_sha256", "noise_manifest_sha256",
                "run_identity_sha256",
            )},
            "training_method": self.manifest["training_method"],
            "scene_id": scene,
            "episode_id": episode,
            "steps": 10,
            "success": success,
            "spl": 0.8 if success else 0.0,
            "distance_to_goal": 0.1 if success else 0.3,
            "reward": 1.0 if success else 0.0,
            "stop_called": True,
            "premature_stop": not success,
            "non_stop_failure": False,
            "action_counts": {"stop": 1},
            "action_trace_sha256": "f" * 64,
            "localization_distance_bias_m": 0.01,
            "localization_bearing_bias_deg": 0.2,
        }

    def _write_inputs(self):
        (self.root / "condition_manifest.json").write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )
        (self.root / "episode_shards" / "episodes-1.jsonl").write_text(
            "\n".join(json.dumps(row) for row in self.records) + "\n",
            encoding="utf-8",
        )
        metrics = {
            metric: sum(float(row[metric]) for row in self.records) / 2
            for metric in METRICS
        }
        (self.root / "summary.json").write_text(
            json.dumps(
                {
                    "status": "complete",
                    "seed": 2026,
                    "episodes_requested": 2,
                    "checkpoint_sha256": "a" * 64,
                    "metrics": metrics,
                }
            ),
            encoding="utf-8",
        )

    def test_merges_and_validates_episode_evidence(self):
        payload = finalize(self.root, expected_episodes=2)
        self.assertEqual(payload["status"], "complete")
        self.assertEqual(payload["metrics"]["success"], 0.5)
        self.assertTrue((self.root / "episodes.jsonl").is_file())

    def test_rejects_duplicate_episode(self):
        self.records[1]["scene_id"] = self.records[0]["scene_id"]
        self.records[1]["episode_id"] = self.records[0]["episode_id"]
        with self.assertRaisesRegex(ValueError, "duplicate episode"):
            validate_episode_records(self.records, self.manifest, 2)

    def test_rejects_wrong_phase_or_smoke_metadata(self):
        self.records[0]["phase"] = "formal"
        with self.assertRaisesRegex(ValueError, "metadata mismatch"):
            validate_episode_records(self.records, self.manifest, 2)

    def test_rejects_diagnostic_partition_mismatch(self):
        self.records[1]["premature_stop"] = False
        with self.assertRaisesRegex(ValueError, "premature STOP"):
            validate_episode_records(self.records, self.manifest, 2)

    def test_reward_allows_independent_accumulation_beyond_print_rounding(self):
        metrics = {
            metric: sum(float(row[metric]) for row in self.records) / 2
            for metric in METRICS
        }
        evaluator = {
            "status": "complete",
            "seed": 2026,
            "episodes_requested": 2,
            "checkpoint_sha256": "a" * 64,
            "metrics": dict(metrics),
        }
        evaluator["metrics"]["reward"] -= 8.0e-5
        differences = compare_evaluator_summary(
            evaluator, self.manifest, metrics
        )
        self.assertAlmostEqual(differences["reward"], 8.0e-5)

    def test_non_reward_metric_keeps_strict_four_decimal_tolerance(self):
        metrics = {
            metric: sum(float(row[metric]) for row in self.records) / 2
            for metric in METRICS
        }
        evaluator = {
            "status": "complete",
            "seed": 2026,
            "episodes_requested": 2,
            "checkpoint_sha256": "a" * 64,
            "metrics": dict(metrics),
        }
        evaluator["metrics"]["spl"] -= 8.0e-5
        with self.assertRaisesRegex(ValueError, "spl"):
            compare_evaluator_summary(evaluator, self.manifest, metrics)


if __name__ == "__main__":
    unittest.main()
