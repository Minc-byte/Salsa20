"""Tests for the Phase 3 reduced-subkey ranking experiment."""

import json
import tempfile
import unittest
from pathlib import Path

from src.key_recovery import run_reduced_subkey_experiment


class ReducedSubkeyRankingTests(unittest.TestCase):
    def test_deterministic_ranking_under_fixed_seed(self) -> None:
        with tempfile.TemporaryDirectory() as first_tmpdir:
            first_rankings, first_summary = run_reduced_subkey_experiment(
                reduced_key_bits=4,
                samples=8,
                seed=1234,
                output_dir=Path(first_tmpdir),
            )
        with tempfile.TemporaryDirectory() as second_tmpdir:
            second_rankings, second_summary = run_reduced_subkey_experiment(
                reduced_key_bits=4,
                samples=8,
                seed=1234,
                output_dir=Path(second_tmpdir),
            )

        self.assertEqual(first_rankings, second_rankings)
        self.assertEqual(first_summary, second_summary)

    def test_output_files_generated_in_smoke_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            rankings, summary = run_reduced_subkey_experiment(
                reduced_key_bits=4,
                samples=8,
                seed=2222,
                output_dir=output_dir,
            )

            rankings_path = output_dir / "salsa20_key_recovery_rankings.csv"
            summary_path = output_dir / "salsa20_key_recovery_summary.json"
            self.assertTrue(rankings_path.exists())
            self.assertTrue(summary_path.exists())

            payload = json.loads(summary_path.read_text())
            self.assertEqual(payload["secret_subkey"], summary["secret_subkey"])
            self.assertEqual(payload["correct_rank"], summary["correct_rank"])
            self.assertEqual(len(rankings), 16)

    def test_default_setting_ranks_correct_key_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _, summary = run_reduced_subkey_experiment(
                reduced_key_bits=8,
                samples=64,
                seed=20260619,
                output_dir=Path(tmpdir),
            )

            self.assertEqual(summary["correct_rank"], 1)
            self.assertEqual(summary["secret_subkey"], summary["best_candidate"])
            self.assertEqual(summary["top_score"], summary["samples"])


if __name__ == "__main__":
    unittest.main()
