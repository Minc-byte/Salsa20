"""Tests for Phase 4 complexity measurement utilities."""

import json
import tempfile
import unittest
from pathlib import Path

from src.complexity_measurement import (
    estimate_distinguisher_data_complexity,
    estimate_key_recovery_work,
    run_complexity_measurement,
)


class ComplexityMeasurementTests(unittest.TestCase):
    def test_c_inverse_square_sanity(self) -> None:
        self.assertAlmostEqual(estimate_distinguisher_data_complexity(0.5), 4.0)
        self.assertAlmostEqual(estimate_distinguisher_data_complexity(-0.25), 16.0)

    def test_candidate_count_is_two_to_bits(self) -> None:
        work = estimate_key_recovery_work(bits=8, samples=64)

        self.assertEqual(work["key_recovery_candidates"], 256)
        self.assertEqual(work["key_recovery_total_scoring_operations"], 256 * 64)

    def test_output_files_generated_in_smoke_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            summary = run_complexity_measurement(
                distinguisher_runtime_samples=8,
                key_recovery_bits=4,
                key_recovery_samples=4,
                seed=3333,
                output_dir=output_dir,
            )

            csv_path = output_dir / "salsa20_complexity_estimates.csv"
            json_path = output_dir / "salsa20_complexity_estimates.json"
            self.assertTrue(csv_path.exists())
            self.assertTrue(json_path.exists())

            payload = json.loads(json_path.read_text())
            self.assertEqual(payload["key_recovery_candidates"], 16)
            self.assertEqual(payload["key_recovery_total_scoring_operations"], 64)
            self.assertEqual(payload["distinguisher_correlation"], summary["distinguisher_correlation"])


if __name__ == "__main__":
    unittest.main()
