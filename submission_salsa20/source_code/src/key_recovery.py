"""Reduced-subkey candidate ranking for 4-round Salsa20.

This module implements a practical CTF-style key-ranking demo, not full
Salsa20 key recovery. A small reduced subkey is embedded into selected bits of
the 16-word Salsa20 input state, observations are generated with the verified
differential-linear masks, and each candidate is scored by agreement with the
observed parity sequence.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Any

from src.masks import Mask, apply_xor_difference, linear_parity, mask_to_string, validate_mask
from src.salsa20_4round import STATE_WORDS, salsa20_core
from src.utils import write_csv, write_json

DELTA_MASK: Mask = [(8, 26)]
GAMMA_MASK: Mask = [(6, 0), (7, 9)]
DEFAULT_REDUCED_KEY_BITS = 8
DEFAULT_SAMPLES = 64
DEFAULT_SEED = 20260619
RESULTS_DIR = Path("results/key_recovery")
RANKINGS_CSV = RESULTS_DIR / "salsa20_key_recovery_rankings.csv"
SUMMARY_JSON = RESULTS_DIR / "salsa20_key_recovery_summary.json"

# These are explicit reduced "subkey" positions inside the Salsa20 input state.
# They are selected from standard Salsa20 key-word slots rather than claiming a
# full 256-bit layout recovery.
REDUCED_SUBKEY_POSITIONS: tuple[tuple[int, int], ...] = tuple((1, bit) for bit in range(12))


def _validate_reduced_bits(reduced_key_bits: int) -> None:
    if reduced_key_bits not in (4, 8, 12):
        raise ValueError("reduced_key_bits must be one of 4, 8, or 12.")


def _random_state_template(rng: random.Random, key_positions: list[tuple[int, int]]) -> list[int]:
    state = [rng.getrandbits(32) for _ in range(STATE_WORDS)]
    for word_index, bit_index in key_positions:
        state[word_index] &= ~(1 << bit_index) & 0xFFFFFFFF
    return state


def _embed_reduced_subkey(
    state_template: list[int],
    candidate: int,
    key_positions: list[tuple[int, int]],
) -> list[int]:
    state = state_template[:]
    for bit_number, (word_index, bit_index) in enumerate(key_positions):
        if (candidate >> bit_number) & 1:
            state[word_index] |= 1 << bit_index
        else:
            state[word_index] &= ~(1 << bit_index) & 0xFFFFFFFF
    return state


def _gamma_parity_event(state: list[int]) -> int:
    paired_state = apply_xor_difference(state, DELTA_MASK)
    left = salsa20_core(state, rounds=4, feedforward=False)
    right = salsa20_core(paired_state, rounds=4, feedforward=False)
    difference = [(left_word ^ right_word) & 0xFFFFFFFF for left_word, right_word in zip(left, right)]
    return linear_parity(difference, GAMMA_MASK)


def generate_secret_subkey(reduced_key_bits: int = DEFAULT_REDUCED_KEY_BITS, seed: int = DEFAULT_SEED) -> int:
    """Generate the fixed reproducible secret reduced subkey."""
    _validate_reduced_bits(reduced_key_bits)
    return random.Random(seed + reduced_key_bits).randrange(1 << reduced_key_bits)


def generate_observations(
    secret_subkey: int,
    samples: int = DEFAULT_SAMPLES,
    reduced_key_bits: int = DEFAULT_REDUCED_KEY_BITS,
    seed: int = DEFAULT_SEED,
) -> list[dict[str, Any]]:
    """Generate public templates and observed Gamma parity bits for a secret."""
    _validate_reduced_bits(reduced_key_bits)
    if samples <= 0:
        raise ValueError("samples must be positive.")
    if not 0 <= secret_subkey < (1 << reduced_key_bits):
        raise ValueError("secret_subkey is outside the reduced candidate space.")

    rng = random.Random(seed)
    key_positions = list(REDUCED_SUBKEY_POSITIONS[:reduced_key_bits])
    observations: list[dict[str, Any]] = []
    for sample_index in range(samples):
        template = _random_state_template(rng, key_positions)
        secret_state = _embed_reduced_subkey(template, secret_subkey, key_positions)
        observations.append(
            {
                "sample_index": sample_index,
                "state_template": template,
                "observed_parity": _gamma_parity_event(secret_state),
            }
        )
    return observations


def rank_reduced_subkey_candidates(
    observations: list[dict[str, Any]],
    candidate_space: range,
    seed: int = DEFAULT_SEED,
    reduced_key_bits: int = DEFAULT_REDUCED_KEY_BITS,
    secret_subkey: int | None = None,
) -> list[dict[str, Any]]:
    """Rank reduced-subkey candidates by parity-sequence agreement."""
    del seed
    _validate_reduced_bits(reduced_key_bits)
    samples = len(observations)
    if samples == 0:
        raise ValueError("observations must not be empty.")

    key_positions = list(REDUCED_SUBKEY_POSITIONS[:reduced_key_bits])
    rankings: list[dict[str, Any]] = []
    for candidate in candidate_space:
        if not 0 <= candidate < (1 << reduced_key_bits):
            raise ValueError("candidate outside the reduced candidate space.")

        agreements = 0
        for observation in observations:
            candidate_state = _embed_reduced_subkey(
                observation["state_template"],
                candidate,
                key_positions,
            )
            predicted_parity = _gamma_parity_event(candidate_state)
            if predicted_parity == observation["observed_parity"]:
                agreements += 1

        agreement_probability = agreements / samples
        score_correlation = 2.0 * agreement_probability - 1.0
        rankings.append(
            {
                "candidate": candidate,
                "candidate_hex": f"0x{candidate:0{max(1, (reduced_key_bits + 3) // 4)}x}",
                "samples": samples,
                "agreements": agreements,
                "agreement_probability": agreement_probability,
                "score_correlation": score_correlation,
                "abs_score_correlation": abs(score_correlation),
                "is_correct": secret_subkey is not None and candidate == secret_subkey,
            }
        )

    rankings.sort(
        key=lambda item: (
            -int(item["agreements"]),
            int(item["candidate"]),
        )
    )
    for rank, item in enumerate(rankings, start=1):
        item["rank"] = rank
    return rankings


def run_reduced_subkey_experiment(
    reduced_key_bits: int = DEFAULT_REDUCED_KEY_BITS,
    samples: int = DEFAULT_SAMPLES,
    seed: int = DEFAULT_SEED,
    output_dir: Path = RESULTS_DIR,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run the reduced-subkey ranking experiment and save outputs."""
    _validate_reduced_bits(reduced_key_bits)
    secret_subkey = generate_secret_subkey(reduced_key_bits=reduced_key_bits, seed=seed)
    observations = generate_observations(
        secret_subkey=secret_subkey,
        samples=samples,
        reduced_key_bits=reduced_key_bits,
        seed=seed,
    )
    rankings = rank_reduced_subkey_candidates(
        observations=observations,
        candidate_space=range(1 << reduced_key_bits),
        seed=seed,
        reduced_key_bits=reduced_key_bits,
        secret_subkey=secret_subkey,
    )
    correct_entry = next(item for item in rankings if item["candidate"] == secret_subkey)
    best_entry = rankings[0]
    summary = {
        "experiment": "4-round Salsa20 reduced-subkey candidate ranking",
        "rounds": 4,
        "feedforward": False,
        "delta": mask_to_string(validate_mask(DELTA_MASK)),
        "gamma": mask_to_string(validate_mask(GAMMA_MASK)),
        "reduced_key_bits": reduced_key_bits,
        "candidate_count": 1 << reduced_key_bits,
        "samples": samples,
        "seed": seed,
        "secret_subkey": secret_subkey,
        "secret_subkey_hex": f"0x{secret_subkey:0{max(1, (reduced_key_bits + 3) // 4)}x}",
        "best_candidate": best_entry["candidate"],
        "best_candidate_hex": best_entry["candidate_hex"],
        "top_score": best_entry["agreements"],
        "top_agreement_probability": best_entry["agreement_probability"],
        "top_score_correlation": best_entry["score_correlation"],
        "correct_rank": correct_entry["rank"],
        "correct_score": correct_entry["agreements"],
        "correct_agreement_probability": correct_entry["agreement_probability"],
        "subkey_positions": [list(position) for position in REDUCED_SUBKEY_POSITIONS[:reduced_key_bits]],
        "top_candidates": rankings[: min(10, len(rankings))],
        "limitations": [
            "Reduced-subkey candidate ranking only.",
            "Does not claim full 256-bit Salsa20 key recovery.",
            "Uses the 4-round Salsa20 core without feed-forward.",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / RANKINGS_CSV.name, rankings)
    write_json(output_dir / SUMMARY_JSON.name, summary)
    return rankings, summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="4-round Salsa20 reduced-subkey ranking demo")
    parser.add_argument("--bits", type=int, choices=[4, 8, 12], default=DEFAULT_REDUCED_KEY_BITS)
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    _, summary = run_reduced_subkey_experiment(
        reduced_key_bits=args.bits,
        samples=args.samples,
        seed=args.seed,
        output_dir=args.output_dir,
    )

    print(f"Secret subkey: {summary['secret_subkey_hex']} ({summary['secret_subkey']})")
    print(f"Recovered best candidate: {summary['best_candidate_hex']} ({summary['best_candidate']})")
    print(f"Correct rank: {summary['correct_rank']}")
    print(f"Top score: {summary['top_score']}/{summary['samples']}")
    print(f"Samples: {summary['samples']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
