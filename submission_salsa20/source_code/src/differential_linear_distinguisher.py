"""Differential-linear distinguisher search for 4-round Salsa20."""

from __future__ import annotations

import argparse
import heapq
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
    refined_candidate_input_differences,
    refined_candidate_output_masks,
    validate_mask,
)
from src.salsa20_4round import STATE_WORDS, salsa20_core
from src.utils import write_csv, write_json

RESULTS_DIR = Path("results/distinguisher")
SEARCH_CSV = RESULTS_DIR / "salsa20_search_results.csv"
SEARCH_JSON = RESULTS_DIR / "salsa20_search_results.json"
VERIFY_CSV = RESULTS_DIR / "salsa20_verified_distinguisher.csv"
VERIFY_JSON = RESULTS_DIR / "salsa20_verified_distinguisher.json"
REFINED_SEARCH_CSV = RESULTS_DIR / "salsa20_refined_search_results.csv"
REFINED_VERIFY_CSV = RESULTS_DIR / "salsa20_refined_verified_distinguisher.csv"
REFINED_VERIFY_JSON = RESULTS_DIR / "salsa20_refined_verified_distinguisher.json"


def _random_state(rng: random.Random) -> list[int]:
    return [rng.getrandbits(32) for _ in range(STATE_WORDS)]


def _output_difference(left: list[int], right: list[int]) -> list[int]:
    return [(left_word ^ right_word) & 0xFFFFFFFF for left_word, right_word in zip(left, right)]


def _state_to_int(state: list[int]) -> int:
    value = 0
    for word_index, word in enumerate(state):
        value |= (word & 0xFFFFFFFF) << (32 * word_index)
    return value


def _mask_to_int(mask: Mask) -> int:
    value = 0
    for word_index, bit_index in mask:
        value |= 1 << (32 * word_index + bit_index)
    return value


def _derived_seed(seed: int, input_difference: Mask, output_mask: Mask) -> int:
    material = f"{seed}|{mask_to_string(input_difference)}|{mask_to_string(output_mask)}".encode(
        "utf-8"
    )
    digest = hashlib.blake2b(material, digest_size=8).digest()
    return int.from_bytes(digest, "little")


def _search_seed(seed: int, input_difference: Mask) -> int:
    material = f"{seed}|refined|{mask_to_string(input_difference)}".encode("utf-8")
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


def _save_csv_results(results: list[dict[str, Any]], csv_path: Path) -> None:
    write_csv(csv_path, _csv_rows(results))


def confidence_interval_excludes_half(result: dict[str, Any]) -> bool:
    """Return whether the approximate 95 percent CI excludes probability 0.5."""
    return float(result["approx_95ci_high"]) < 0.5 or float(result["approx_95ci_low"]) > 0.5


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


def search_refined_distinguishers(
    samples: int,
    seed: int,
    max_input_masks: int | None = None,
    max_output_masks: int | None = None,
    top_results: int = 100,
    rounds: int = 4,
) -> list[dict[str, Any]]:
    """Search a broader low-weight mask set using batched output-mask scoring."""
    if samples <= 0:
        raise ValueError("samples must be positive.")
    if top_results <= 0:
        raise ValueError("top_results must be positive.")

    input_masks = refined_candidate_input_differences()
    output_masks = refined_candidate_output_masks()
    if max_input_masks is not None:
        input_masks = input_masks[:max_input_masks]
    if max_output_masks is not None:
        output_masks = output_masks[:max_output_masks]

    encoded_output_masks = [
        (mask_to_string(mask), [list(bit) for bit in mask], _mask_to_int(mask))
        for mask in output_masks
    ]

    heap: list[tuple[float, str, str, dict[str, Any]]] = []
    sequence = 0
    for input_difference in input_masks:
        delta = validate_mask(input_difference)
        input_string = mask_to_string(delta)
        rng = random.Random(_search_seed(seed, delta))
        matches = [0] * len(encoded_output_masks)

        for _ in range(samples):
            state = _random_state(rng)
            paired_state = apply_xor_difference(state, delta)
            left = salsa20_core(state, rounds=rounds, feedforward=False)
            right = salsa20_core(paired_state, rounds=rounds, feedforward=False)
            difference_bits = _state_to_int(_output_difference(left, right))

            for mask_index, (_, _, output_mask_int) in enumerate(encoded_output_masks):
                if ((difference_bits & output_mask_int).bit_count() & 1) == 0:
                    matches[mask_index] += 1

        for mask_index, match_count in enumerate(matches):
            output_string, output_bits, _ = encoded_output_masks[mask_index]
            stats = _statistics(samples, match_count)
            result = {
                "input_difference": input_string,
                "output_mask": output_string,
                "input_difference_bits": [list(bit) for bit in delta],
                "output_mask_bits": output_bits,
                "abs_correlation": abs(float(stats["correlation"])),
                "seed": seed,
                "rounds": rounds,
                "feedforward": False,
                **stats,
            }
            ranking_key = (
                float(result["abs_correlation"]),
                -sequence,
                input_string,
                output_string,
            )
            sequence += 1
            if len(heap) < top_results:
                heapq.heappush(heap, (*ranking_key, result))
            elif ranking_key > heap[0][:4]:
                heapq.heapreplace(heap, (*ranking_key, result))

    results = [item[4] for item in heap]
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


def refined_search_mode(
    samples: int,
    seed: int,
    output_dir: Path = RESULTS_DIR,
    max_input_masks: int | None = None,
    max_output_masks: int | None = None,
    top_results: int = 100,
) -> list[dict[str, Any]]:
    """Run refined search mode and save the top ranked candidates."""
    results = search_refined_distinguishers(
        samples=samples,
        seed=seed,
        max_input_masks=max_input_masks,
        max_output_masks=max_output_masks,
        top_results=top_results,
    )
    _save_csv_results(results, output_dir / REFINED_SEARCH_CSV.name)
    return results


def refined_verify_mode(
    candidate: dict[str, Any],
    samples: int,
    seed: int,
    output_dir: Path = RESULTS_DIR,
) -> dict[str, Any]:
    """Re-run a refined candidate and save refined verification outputs."""
    result = run_distinguisher_experiment(
        input_difference=[tuple(bit) for bit in candidate["input_difference_bits"]],
        output_mask=[tuple(bit) for bit in candidate["output_mask_bits"]],
        samples=samples,
        seed=seed,
        rounds=int(candidate.get("rounds", 4)),
        feedforward=False,
    )
    _save_csv_results([result], output_dir / REFINED_VERIFY_CSV.name)
    write_json(output_dir / REFINED_VERIFY_JSON.name, {"results": [result]})
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


def run_refined_search_and_verify(
    refined_search_samples: int,
    verify_samples: int,
    seed: int,
    output_dir: Path = RESULTS_DIR,
    max_input_masks: int | None = None,
    max_output_masks: int | None = None,
    top_results: int = 100,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run the expanded refined search, then verify its best candidate."""
    refined_results = refined_search_mode(
        samples=refined_search_samples,
        seed=seed,
        output_dir=output_dir,
        max_input_masks=max_input_masks,
        max_output_masks=max_output_masks,
        top_results=top_results,
    )
    if not refined_results:
        raise RuntimeError("No refined distinguisher candidates were evaluated.")

    verified = refined_verify_mode(
        candidate=refined_results[0],
        samples=verify_samples,
        seed=seed + 1,
        output_dir=output_dir,
    )
    return refined_results, verified


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="4-round Salsa20 differential-linear search")
    parser.add_argument("--mode", choices=["search", "verify", "refined", "all"], default="all")
    parser.add_argument("--search-samples", type=int, default=512)
    parser.add_argument("--refined-search-samples", type=int, default=256)
    parser.add_argument("--verify-samples", type=int, default=65536)
    parser.add_argument("--seed", type=int, default=20260617)
    parser.add_argument("--max-input-masks", type=int, default=16)
    parser.add_argument("--max-output-masks", type=int, default=16)
    parser.add_argument("--refined-top-results", type=int, default=100)
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
    elif args.mode == "refined":
        _, best = run_refined_search_and_verify(
            refined_search_samples=args.refined_search_samples,
            verify_samples=args.verify_samples,
            seed=args.seed,
            output_dir=args.output_dir,
            top_results=args.refined_top_results,
        )
    else:
        _, initial_best = run_search_and_verify(
            search_samples=args.search_samples,
            verify_samples=args.verify_samples,
            seed=args.seed,
            max_input_masks=args.max_input_masks,
            max_output_masks=args.max_output_masks,
            output_dir=args.output_dir,
        )
        best = initial_best
        if not confidence_interval_excludes_half(initial_best):
            _, best = run_refined_search_and_verify(
                refined_search_samples=args.refined_search_samples,
                verify_samples=args.verify_samples,
                seed=args.seed,
                output_dir=args.output_dir,
                top_results=args.refined_top_results,
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
