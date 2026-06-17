"""Tests for mask helpers and the Phase 2 distinguisher pipeline."""

import json
import tempfile
import unittest
from pathlib import Path

from src.differential_linear_distinguisher import run_search_and_verify, search_practical_distinguishers
from src.masks import apply_xor_difference, linear_parity, mask_to_string, validate_mask


class MaskHelperTests(unittest.TestCase):
    def test_mask_parity_correctness(self) -> None:
        state = [0] * 16
        state[0] = 0b1011
        state[3] = 0b1000

        self.assertEqual(linear_parity(state, [(0, 0)]), 1)
        self.assertEqual(linear_parity(state, [(0, 1)]), 1)
        self.assertEqual(linear_parity(state, [(0, 2)]), 0)
        self.assertEqual(linear_parity(state, [(0, 0), (0, 1)]), 0)
        self.assertEqual(linear_parity(state, [(0, 0), (3, 3)]), 0)

    def test_apply_difference_correctness(self) -> None:
        state = [0] * 16
        changed = apply_xor_difference(state, [(0, 0), (4, 7), (15, 31)])

        self.assertEqual(changed[0], 0x00000001)
        self.assertEqual(changed[4], 0x00000080)
        self.assertEqual(changed[15], 0x80000000)
        self.assertEqual(state, [0] * 16)

    def test_validate_mask_and_string(self) -> None:
        self.assertEqual(validate_mask([(1, 2), (3, 4)]), [(1, 2), (3, 4)])
        self.assertEqual(mask_to_string([(1, 2), (3, 4)]), "w01.b02+w03.b04")

        with self.assertRaises(ValueError):
            validate_mask([(16, 0)])
        with self.assertRaises(ValueError):
            validate_mask([(0, 32)])
        with self.assertRaises(ValueError):
            validate_mask([(0, 1), (0, 1)])


class DistinguisherPipelineTests(unittest.TestCase):
    def test_deterministic_search_under_fixed_seed(self) -> None:
        first = search_practical_distinguishers(
            samples=16,
            seed=12345,
            max_input_masks=4,
            max_output_masks=4,
        )
        second = search_practical_distinguishers(
            samples=16,
            seed=12345,
            max_input_masks=4,
            max_output_masks=4,
        )

        self.assertEqual(first, second)
        self.assertEqual(len(first), 16)
        self.assertGreaterEqual(first[0]["abs_correlation"], first[-1]["abs_correlation"])

    def test_result_files_generated_by_small_smoke_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            search_results, verified = run_search_and_verify(
                search_samples=8,
                verify_samples=16,
                seed=777,
                max_input_masks=3,
                max_output_masks=3,
                output_dir=output_dir,
            )

            expected_files = [
                output_dir / "salsa20_search_results.csv",
                output_dir / "salsa20_search_results.json",
                output_dir / "salsa20_verified_distinguisher.csv",
                output_dir / "salsa20_verified_distinguisher.json",
            ]
            for path in expected_files:
                self.assertTrue(path.exists(), f"missing output file: {path}")

            payload = json.loads((output_dir / "salsa20_verified_distinguisher.json").read_text())
            self.assertEqual(payload["results"][0], verified)
            self.assertEqual(search_results[0]["input_difference"], verified["input_difference"])
            self.assertIn("correlation", verified)


if __name__ == "__main__":
    unittest.main()
