import json
import tempfile
import unittest
from pathlib import Path

import aggregate_results


class AggregateResultGuardTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temporary_directory.name) / "repo"
        self.results_root = (
            self.repo_root / "src" / "results" / "closeout_dsr"
        )
        self.saved_repo_root = aggregate_results.REPO_ROOT
        self.saved_results_root = aggregate_results.RESULTS_ROOT
        aggregate_results.REPO_ROOT = self.repo_root
        aggregate_results.RESULTS_ROOT = self.results_root

        self.train_root = (
            self.results_root / "closeout_baseline_trainseed100_1m_env5"
        )
        self.train_root.mkdir(parents=True)
        (self.train_root / "run_status.txt").write_text(
            "status=passed\n", encoding="utf-8"
        )
        self.checkpoint = self.train_root / "checkpoints" / "ckpt.9.pth"
        self.checkpoint.parent.mkdir()
        self.checkpoint.write_bytes(b"frozen checkpoint")
        (self.train_root / "final_checkpoint_path.txt").write_text(
            str(self.checkpoint.resolve()) + "\n", encoding="utf-8"
        )

        self.eval_summary = aggregate_results.summary_path("baseline", 100)
        self.eval_summary.parent.mkdir(parents=True)
        (self.eval_summary.parent / "run_status.txt").write_text(
            "status=passed\n", encoding="utf-8"
        )
        self.payload = {
            "status": "complete",
            "seed": 2026,
            "episodes_requested": 100,
            "checkpoint": str(self.checkpoint.resolve()),
            "metrics": {
                name: 0.5 for name in aggregate_results.METRICS
            },
        }
        self._write_summary()

    def tearDown(self):
        aggregate_results.REPO_ROOT = self.saved_repo_root
        aggregate_results.RESULTS_ROOT = self.saved_results_root
        self.temporary_directory.cleanup()

    def _write_summary(self):
        self.eval_summary.write_text(
            json.dumps(self.payload), encoding="utf-8"
        )

    def test_accepts_corresponding_fresh_checkpoint(self):
        record = aggregate_results.load_record("baseline", 100)
        self.assertEqual(record["training_seed"], 100)

    def test_rejects_old_or_mismatched_checkpoint(self):
        old_checkpoint = self.repo_root / "old" / "ckpt.9.pth"
        old_checkpoint.parent.mkdir()
        old_checkpoint.write_bytes(b"old checkpoint")
        self.payload["checkpoint"] = str(old_checkpoint.resolve())
        self._write_summary()
        with self.assertRaisesRegex(ValueError, "fresh same-server"):
            aggregate_results.load_record("baseline", 100)


if __name__ == "__main__":
    unittest.main()
