"""Data and time complexity measurements for the Salsa20 CTF experiments."""

from __future__ import annotations

import argparse
import math
import time
from pathlib import Path
from typing import Any

from src.differential_linear_distinguisher import run_distinguisher_experiment
from src.key_recovery import (
    DEFAULT_REDUCED_KEY_BITS,
    DEFAULT_SAMPLES as DEFAULT_KEY_RECOVERY_SAMPLES,
    DEFAULT_SEED as DEFAULT_KEY_RECOVERY_SEED,
    DELTA_MASK,
    GAMMA_MASK,
    run_reduced_subkey_experiment,
)
from src.masks import mask_to_string, validate_mask
from src.utils import write_csv, write_json

RESULTS_DIR = Path("results/complexity")
ESTIMATES_CSV = RESULTS_DIR / "salsa20_complexity_estimates.csv"
ESTIMATES_JSON = RESULTS_DIR / "salsa20_complexity_estimates.json"
REFINED_CORRELATION = -0.59149169921875
REFINED_VERIFY_SAMPLES = 65536
DEFAULT_DISTINGUISHER_RUNTIME_SAMPLES = 4096


def estimate_distinguisher_data_complexity(correlation: float) -> float:
    """Estimate pair count for a distinguisher using the rule N ~= c^-2."""
    if correlation == 0.0:
        return math.inf
    return 1.0 / (correlation * correlation)


def estimate_key_recovery_work(bits: int, samples: int, candidates: int | None = None) -> dict[str, int]:
    """Estimate reduced-subkey scoring work."""
    if bits <= 0:
        raise ValueError("bits must be positive.")
    if samples <= 0:
        raise ValueError("samples must be positive.")

    candidate_count = candidates if candidates is not None else 1 << bits
    if candidate_count <= 0:
        raise ValueError("candidates must be positive.")

    return {
        "key_recovery_reduced_key_bits": bits,
        "key_recovery_candidates": candidate_count,
        "key_recovery_samples_per_candidate": samples,
        "key_recovery_total_scoring_operations": candidate_count * samples,
    }


def measure_runtime_for_distinguisher(
    samples: int = DEFAULT_DISTINGUISHER_RUNTIME_SAMPLES,
    seed: int = 20260618,
) -> dict[str, Any]:
    """Measure wall-clock runtime for one refined distinguisher verification run."""
    if samples <= 0:
        raise ValueError("samples must be positive.")

    started = time.perf_counter()
    result = run_distinguisher_experiment(
        input_difference=DELTA_MASK,
        output_mask=GAMMA_MASK,
        samples=samples,
        seed=seed,
        rounds=4,
        feedforward=False,
    )
    elapsed = time.perf_counter() - started

    return {
        "distinguisher_runtime_samples": samples,
        "distinguisher_wall_clock_seconds": elapsed,
        "distinguisher_runtime_probability": result["probability"],
        "distinguisher_runtime_correlation": result["correlation"],
    }


def measure_runtime_for_key_recovery(
    bits: int = DEFAULT_REDUCED_KEY_BITS,
    samples: int = DEFAULT_KEY_RECOVERY_SAMPLES,
    seed: int = DEFAULT_KEY_RECOVERY_SEED,
) -> dict[str, Any]:
    """Measure wall-clock runtime for the reduced-subkey ranking experiment."""
    if samples <= 0:
        raise ValueError("samples must be positive.")

    started = time.perf_counter()
    _, summary = run_reduced_subkey_experiment(
        reduced_key_bits=bits,
        samples=samples,
        seed=seed,
    )
    elapsed = time.perf_counter() - started

    return {
        "key_recovery_wall_clock_seconds": elapsed,
        "key_recovery_secret_subkey": summary["secret_subkey"],
        "key_recovery_secret_subkey_hex": summary["secret_subkey_hex"],
        "key_recovery_best_candidate": summary["best_candidate"],
        "key_recovery_best_candidate_hex": summary["best_candidate_hex"],
        "key_recovery_correct_rank": summary["correct_rank"],
        "key_recovery_top_score": summary["top_score"],
        "key_recovery_top_score_correlation": summary["top_score_correlation"],
    }


def build_complexity_summary(
    correlation: float = REFINED_CORRELATION,
    verification_samples: int = REFINED_VERIFY_SAMPLES,
    distinguisher_runtime_samples: int = DEFAULT_DISTINGUISHER_RUNTIME_SAMPLES,
    key_recovery_bits: int = DEFAULT_REDUCED_KEY_BITS,
    key_recovery_samples: int = DEFAULT_KEY_RECOVERY_SAMPLES,
    seed: int = DEFAULT_KEY_RECOVERY_SEED,
) -> dict[str, Any]:
    """Build a combined complexity summary dictionary."""
    data_complexity = estimate_distinguisher_data_complexity(correlation)
    key_work = estimate_key_recovery_work(bits=key_recovery_bits, samples=key_recovery_samples)
    distinguisher_runtime = measure_runtime_for_distinguisher(
        samples=distinguisher_runtime_samples,
        seed=20260618,
    )
    key_recovery_runtime = measure_runtime_for_key_recovery(
        bits=key_recovery_bits,
        samples=key_recovery_samples,
        seed=seed,
    )

    return {
        "experiment": "4-round Salsa20 complexity estimates",
        "rounds": 4,
        "feedforward": False,
        "delta": mask_to_string(validate_mask(DELTA_MASK)),
        "gamma": mask_to_string(validate_mask(GAMMA_MASK)),
        "distinguisher_correlation": correlation,
        "distinguisher_estimated_data_complexity_pairs": data_complexity,
        "distinguisher_estimated_data_complexity_pairs_ceiling": math.ceil(data_complexity),
        "distinguisher_verification_samples_used": verification_samples,
        **distinguisher_runtime,
        **key_work,
        **key_recovery_runtime,
        "limitations": [
            "Data complexity uses the rough N ~= c^-2 distinguisher heuristic.",
            "Runtime measurements are wall-clock measurements on this local Python implementation.",
            "Key recovery is reduced-subkey candidate ranking only.",
            "No full 256-bit Salsa20 key recovery is claimed.",
        ],
    }


def write_complexity_outputs(summary: dict[str, Any], output_dir: Path = RESULTS_DIR) -> None:
    """Write complexity estimates to CSV and JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    row = {key: value for key, value in summary.items() if key != "limitations"}
    row["limitations"] = " | ".join(summary["limitations"])
    write_csv(output_dir / ESTIMATES_CSV.name, [row])
    write_json(output_dir / ESTIMATES_JSON.name, summary)


def run_complexity_measurement(
    correlation: float = REFINED_CORRELATION,
    verification_samples: int = REFINED_VERIFY_SAMPLES,
    distinguisher_runtime_samples: int = DEFAULT_DISTINGUISHER_RUNTIME_SAMPLES,
    key_recovery_bits: int = DEFAULT_REDUCED_KEY_BITS,
    key_recovery_samples: int = DEFAULT_KEY_RECOVERY_SAMPLES,
    seed: int = DEFAULT_KEY_RECOVERY_SEED,
    output_dir: Path = RESULTS_DIR,
) -> dict[str, Any]:
    """Run all Phase 4 complexity measurements and save outputs."""
    summary = build_complexity_summary(
        correlation=correlation,
        verification_samples=verification_samples,
        distinguisher_runtime_samples=distinguisher_runtime_samples,
        key_recovery_bits=key_recovery_bits,
        key_recovery_samples=key_recovery_samples,
        seed=seed,
    )
    write_complexity_outputs(summary, output_dir=output_dir)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Measure 4-round Salsa20 experiment complexity")
    parser.add_argument("--distinguisher-runtime-samples", type=int, default=DEFAULT_DISTINGUISHER_RUNTIME_SAMPLES)
    parser.add_argument("--key-bits", type=int, choices=[4, 8, 12], default=DEFAULT_REDUCED_KEY_BITS)
    parser.add_argument("--key-samples", type=int, default=DEFAULT_KEY_RECOVERY_SAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_KEY_RECOVERY_SEED)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    summary = run_complexity_measurement(
        distinguisher_runtime_samples=args.distinguisher_runtime_samples,
        key_recovery_bits=args.key_bits,
        key_recovery_samples=args.key_samples,
        seed=args.seed,
        output_dir=args.output_dir,
    )

    print(
        "Distinguisher data complexity: "
        f"{summary['distinguisher_estimated_data_complexity_pairs']:.3f} pairs "
        f"(ceil {summary['distinguisher_estimated_data_complexity_pairs_ceiling']})"
    )
    print(
        "Distinguisher runtime: "
        f"{summary['distinguisher_wall_clock_seconds']:.6f}s for "
        f"{summary['distinguisher_runtime_samples']} samples"
    )
    print(
        "Key recovery work: "
        f"{summary['key_recovery_total_scoring_operations']} scoring operations "
        f"({summary['key_recovery_candidates']} candidates x "
        f"{summary['key_recovery_samples_per_candidate']} samples)"
    )
    print(
        "Key recovery runtime: "
        f"{summary['key_recovery_wall_clock_seconds']:.6f}s, "
        f"correct rank {summary['key_recovery_correct_rank']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
