import tempfile
import unittest
from pathlib import Path

import aggregate_results
from protocol_guard import FORMAL_NOISE_SEEDS, METRICS, METHODS, NOISY_CONDITIONS, TRAINING_SEEDS, run_relative_path


class AggregateResultsTests(unittest.TestCase):
    def _synthetic_records(self):
        records = []
        for method in METHODS:
            for seed in TRAINING_SEEDS:
                records.append(
                    {
                        "phase": "zero_noise",
                        "condition": "clean",
                        "method": method,
                        "training_seed": seed,
                        "noise_seed": 0,
                        "metrics": {metric: 1.0 for metric in METRICS},
                    }
                )
        for condition in NOISY_CONDITIONS:
            for method in METHODS:
                for seed in TRAINING_SEEDS:
                    for noise_seed in FORMAL_NOISE_SEEDS:
                        degradation = -0.2 if method == "baseline" else -0.1
                        records.append(
                            {
                                "phase": "formal",
                                "condition": condition,
                                "method": method,
                                "training_seed": seed,
                                "noise_seed": noise_seed,
                                "metrics": {
                                    metric: 1.0 + degradation for metric in METRICS
                                },
                            }
                        )
        return records

    def test_paired_drop_and_hierarchical_summary(self):
        cells = aggregate_results.build_cells(self._synthetic_records())
        summaries = aggregate_results.summarize_cells(cells)
        self.assertEqual(len(cells), 27)
        combined = summaries["combined"]["success"]
        self.assertAlmostEqual(combined["mean_over_training_seeds"], 0.1)
        self.assertEqual(combined["positive_training_seed_count"], 3)
        self.assertIn("一致性", aggregate_results.success_interpretation(summaries))

    def test_formal_discovery_rejects_missing_and_extra_runs(self):
        with tempfile.TemporaryDirectory() as temporary:
            saved = aggregate_results.RESULTS_ROOT
            aggregate_results.RESULTS_ROOT = Path(temporary)
            try:
                with self.assertRaisesRegex(ValueError, "missing="):
                    aggregate_results.validate_exact_formal_matrix()
                for condition in NOISY_CONDITIONS:
                    for method in METHODS:
                        for seed in TRAINING_SEEDS:
                            for noise_seed in FORMAL_NOISE_SEEDS:
                                relative = run_relative_path(
                                    "formal", condition, method, seed, noise_seed
                                )
                                path = Path(temporary) / relative / "condition_manifest.json"
                                path.parent.mkdir(parents=True, exist_ok=True)
                                path.write_text("{}", encoding="utf-8")
                aggregate_results.validate_exact_formal_matrix()
                contaminant = (
                    Path(temporary)
                    / "formal"
                    / "combined"
                    / "smoke_contaminant"
                    / "condition_manifest.json"
                )
                contaminant.parent.mkdir(parents=True)
                contaminant.write_text("{}", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "extra="):
                    aggregate_results.validate_exact_formal_matrix()
            finally:
                aggregate_results.RESULTS_ROOT = saved


if __name__ == "__main__":
    unittest.main()
