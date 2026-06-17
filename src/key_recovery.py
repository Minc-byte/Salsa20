"""Planned reduced-subkey candidate-ranking extension.

This project will not claim full 256-bit key recovery unless such a result is
actually implemented and experimentally supported.
"""


def rank_reduced_subkey_candidates(
    observations: list[dict],
    candidate_space: range,
    seed: int,
) -> list[dict]:
    """Rank a reduced subkey candidate space using distinguisher statistics."""
    raise NotImplementedError("Planned for the key-recovery demo step.")
