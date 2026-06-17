"""Differential-linear distinguisher search for 4-round Salsa20."""

from __future__ import annotations

import argparse
import hashlib
import math
import random
from pathlib import Path
from typing import Any

from src.masks import (
    Mask,
    apply_xor_difference,
    candidate_input_differences,
    candidate_output_masks,
    linear_parity,
    mask_to_string,
    random_single_bit_masks,
    validate_mask,
)
from src.salsa20_4round import STATE_WORDS, salsa20_core
from src.utils import write_csv, write_json

RESULTS_DIR = Path("results/distinguisher")
SEARCH_CSV = RESULTS_DIR / "salsa20_search_results.csv"
SEARCH_JSON = RESULTS_DIR / "salsa20_search_results.json"
VERIFY_CSV = RESULTS_DIR / "salsa20_verified_distinguisher.csv"
VERIFY_JSON = RESULTS_DIR / "salsa20_verified_distinguisher.json"


def _random_state(rng: random.Random) -> list[int]:
    return [rng.getrandbits(32) for _ in range(STATE_WORDS)]


def _output_difference(left: list[int], right: list[int]) -> list[int]:
    return [(left_word ^ right_word) & 0xFFFFFFFF for left_word, right_word in zip(left, right)]


def _derived_seed(seed: int, input_difference: Mask, output_mask: Mask) -> int:
    material = f"{seed}|{mask_to_string(input_difference)}|{mask_to_string(output_mask)}".encode(
        "utf-8"
    )
    digest = hashlib.blake2b(material, digest_size=8).digest()
    return int.from_bytes(digest, "little")


def _statistics(samples: int, matches: int) -> dict[str, float | int]:
    probability = matches / samples
    bias = probability - 0.5
    correlation = 2.0 * bias
    standard_error = math.sqrt(probability * (1.0 - probability) / samples)
    ci_delta = 1.96 * standard_error

    return {
        "samples": samples,
        "matches": matches,
        "probability": probability,
        "bias": bias,
        "correlation": correlation,
        "standard_error": standard_error,
        "approx_95ci_low": max(0.0, probability - ci_delta),
        "approx_95ci_high": min(1.0, probability + ci_delta),
    }


def _csv_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rank, result in enumerate(results, start=1):
        rows.append(
            {
                "rank": rank,
                "input_difference": result["input_difference"],
                "output_mask": result["output_mask"],
                "samples": result["samples"],
                "matches": result["matches"],
                "probability": result["probability"],
                "bias": result["bias"],
                "correlation": result["correlation"],
                "abs_correlation": result["abs_correlation"],
                "standard_error": result["standard_error"],
                "approx_95ci_low": result["approx_95ci_low"],
                "approx_95ci_high": result["approx_95ci_high"],
                "seed": result["seed"],
                "rounds": result["rounds"],
                "feedforward": result["feedforward"],
            }
        )
    return rows


def _save_results(results: list[dict[str, Any]], csv_path: Path, json_path: Path) -> None:
    write_csv(csv_path, _csv_rows(results))
    write_json(json_path, {"results": results})


def _candidate_masks(max_masks: int, seed: int, role: str) -> list[Mask]:
    if max_masks <= 0:
        raise ValueError("max_masks must be positive.")

    if role == "input":
        base = candidate_input_differences()
    elif role == "output":
        base = candidate_output_masks()
    else:
        raise ValueError(f"Unknown mask role: {role}.")

    rng = random.Random(seed + (17 if role == "input" else 31))
    singles = random_single_bit_masks(count=max_masks, rng=rng)

    candidates: list[Mask] = []
    seen: set[str] = set()
    for mask in [*base, *singles]:
        normalized = validate_mask(mask)
        key = mask_to_string(normalized)
        if key not in seen:
            seen.add(key)
            candidates.append(normalized)
        if len(candidates) >= max_masks:
            break

    return candidates


def run_distinguisher_experiment(
    input_difference: Mask,
    output_mask: Mask,
    samples: int,
    seed: int,
    rounds: int = 4,
    feedforward: bool = False,
) -> dict[str, Any]:
    """Estimate a differential-linear statistic for one candidate pair."""
    if samples <= 0:
        raise ValueError("samples must be positive.")

    delta = validate_mask(input_difference)
    gamma = validate_mask(output_mask)
    rng = random.Random(_derived_seed(seed, delta, gamma))

    matches = 0
    for _ in range(samples):
        state = _random_state(rng)
        paired_state = apply_xor_difference(state, delta)
        left = salsa20_core(state, rounds=rounds, feedforward=feedforward)
        right = salsa20_core(paired_state, rounds=rounds, feedforward=feedforward)
        difference = _output_difference(left, right)
        matches += 1 if linear_parity(difference, gamma) == 0 else 0

    stats = _statistics(samples, matches)
    input_string = mask_to_string(delta)
    output_string = mask_to_string(gamma)
    return {
        "input_difference": input_string,
        "output_mask": output_string,
        "input_difference_bits": [list(bit) for bit in delta],
        "output_mask_bits": [list(bit) for bit in gamma],
        "abs_correlation": abs(float(stats["correlation"])),
        "seed": seed,
        "rounds": rounds,
        "feedforward": feedforward,
        **stats,
    }


def search_practical_distinguishers(
    samples: int,
    seed: int,
    max_input_masks: int = 16,
    max_output_masks: int = 16,
    rounds: int = 4,
) -> list[dict[str, Any]]:
    """Search and rank practical 4-round Salsa20 distinguisher candidates."""
    input_masks = _candidate_masks(max_input_masks, seed, "input")
    output_masks = _candidate_masks(max_output_masks, seed, "output")

    results: list[dict[str, Any]] = []
    for input_difference in input_masks:
        for output_mask in output_masks:
            results.append(
                run_distinguisher_experiment(
                    input_difference=input_difference,
                    output_mask=output_mask,
                    samples=samples,
                    seed=seed,
                    rounds=rounds,
                    feedforward=False,
                )
            )

    results.sort(
        key=lambda item: (
            -float(item["abs_correlation"]),
            item["input_difference"],
            item["output_mask"],
        )
    )
    return results


def search_mode(
    samples: int,
    seed: int,
    max_input_masks: int,
    max_output_masks: int,
    output_dir: Path = RESULTS_DIR,
) -> list[dict[str, Any]]:
    """Run search mode and save ranked candidates."""
    results = search_practical_distinguishers(
        samples=samples,
        seed=seed,
        max_input_masks=max_input_masks,
        max_output_masks=max_output_masks,
    )
    _save_results(
        results,
        output_dir / SEARCH_CSV.name,
        output_dir / SEARCH_JSON.name,
    )
    return results


def verify_mode(
    candidate: dict[str, Any],
    samples: int,
    seed: int,
    output_dir: Path = RESULTS_DIR,
) -> dict[str, Any]:
    """Re-run a candidate with a larger sample count and save the result."""
    result = run_distinguisher_experiment(
        input_difference=[tuple(bit) for bit in candidate["input_difference_bits"]],
        output_mask=[tuple(bit) for bit in candidate["output_mask_bits"]],
        samples=samples,
        seed=seed,
        rounds=int(candidate.get("rounds", 4)),
        feedforward=False,
    )
    _save_results([result], output_dir / VERIFY_CSV.name, output_dir / VERIFY_JSON.name)
    return result


def run_search_and_verify(
    search_samples: int,
    verify_samples: int,
    seed: int,
    max_input_masks: int,
    max_output_masks: int,
    output_dir: Path = RESULTS_DIR,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run search mode, then verify the best candidate."""
    search_results = search_mode(
        samples=search_samples,
        seed=seed,
        max_input_masks=max_input_masks,
        max_output_masks=max_output_masks,
        output_dir=output_dir,
    )
    if not search_results:
        raise RuntimeError("No distinguisher candidates were evaluated.")

    verified = verify_mode(
        candidate=search_results[0],
        samples=verify_samples,
        seed=seed + 1,
        output_dir=output_dir,
    )
    return search_results, verified


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="4-round Salsa20 differential-linear search")
    parser.add_argument("--mode", choices=["search", "verify", "all"], default="all")
    parser.add_argument("--search-samples", type=int, default=512)
    parser.add_argument("--verify-samples", type=int, default=8192)
    parser.add_argument("--seed", type=int, default=20260617)
    parser.add_argument("--max-input-masks", type=int, default=16)
    parser.add_argument("--max-output-masks", type=int, default=16)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.mode == "search":
        results = search_mode(
            samples=args.search_samples,
            seed=args.seed,
            max_input_masks=args.max_input_masks,
            max_output_masks=args.max_output_masks,
            output_dir=args.output_dir,
        )
        best = results[0]
    elif args.mode == "verify":
        search_results = search_mode(
            samples=args.search_samples,
            seed=args.seed,
            max_input_masks=args.max_input_masks,
            max_output_masks=args.max_output_masks,
            output_dir=args.output_dir,
        )
        best = verify_mode(
            candidate=search_results[0],
            samples=args.verify_samples,
            seed=args.seed + 1,
            output_dir=args.output_dir,
        )
    else:
        _, best = run_search_and_verify(
            search_samples=args.search_samples,
            verify_samples=args.verify_samples,
            seed=args.seed,
            max_input_masks=args.max_input_masks,
            max_output_masks=args.max_output_masks,
            output_dir=args.output_dir,
        )

    print(
        "Best distinguisher: "
        f"Delta={best['input_difference']} "
        f"Gamma={best['output_mask']} "
        f"samples={best['samples']} "
        f"bias={best['bias']:.6f} "
        f"correlation={best['correlation']:.6f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
