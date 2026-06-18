"""Mask helpers for Salsa20 differential-linear experiments.

A mask is represented as a list of ``(word_index, bit_index)`` pairs. Word
indices address the 16-word Salsa20 state; bit indices address bits inside a
32-bit word, with bit 0 as the least significant bit.
"""

from __future__ import annotations

import random
from collections.abc import Sequence

from src.salsa20_4round import STATE_WORDS, WORD_MASK, word32

Mask = list[tuple[int, int]]


def validate_mask(mask: Sequence[tuple[int, int]]) -> Mask:
    """Validate and normalize a mask."""
    normalized: Mask = []
    seen: set[tuple[int, int]] = set()

    for item in mask:
        if len(item) != 2:
            raise ValueError("Mask entries must be (word_index, bit_index) pairs.")
        word_index, bit_index = item
        if not isinstance(word_index, int) or not isinstance(bit_index, int):
            raise TypeError("Mask word and bit indices must be integers.")
        if not 0 <= word_index < STATE_WORDS:
            raise ValueError(f"Mask word index out of range: {word_index}.")
        if not 0 <= bit_index < 32:
            raise ValueError(f"Mask bit index out of range: {bit_index}.")
        pair = (word_index, bit_index)
        if pair in seen:
            raise ValueError(f"Duplicate mask entry: {pair}.")
        seen.add(pair)
        normalized.append(pair)

    return normalized


def apply_xor_difference(state: Sequence[int], mask: Sequence[tuple[int, int]]) -> list[int]:
    """Return ``state`` with the bit positions in ``mask`` flipped."""
    if len(state) != STATE_WORDS:
        raise ValueError(f"Salsa20 state must contain {STATE_WORDS} words.")

    output = [word32(word) for word in state]
    for word_index, bit_index in validate_mask(mask):
        output[word_index] ^= 1 << bit_index
        output[word_index] &= WORD_MASK
    return output


def linear_parity(state: Sequence[int], mask: Sequence[tuple[int, int]]) -> int:
    """Evaluate the parity selected by ``mask`` over a 16-word state."""
    if len(state) != STATE_WORDS:
        raise ValueError(f"Salsa20 state must contain {STATE_WORDS} words.")

    parity = 0
    for word_index, bit_index in validate_mask(mask):
        parity ^= (word32(state[word_index]) >> bit_index) & 1
    return parity


def mask_to_string(mask: Sequence[tuple[int, int]]) -> str:
    """Serialize a mask into a stable human-readable string."""
    normalized = validate_mask(mask)
    if not normalized:
        return "0"
    return "+".join(f"w{word_index:02d}.b{bit_index:02d}" for word_index, bit_index in normalized)


def random_single_bit_masks(
    count: int = 32,
    seed: int | None = None,
    rng: random.Random | None = None,
) -> list[Mask]:
    """Return deterministic random single-bit masks.

    If ``rng`` is supplied, it is used directly. Otherwise a local
    ``random.Random(seed)`` instance is used so calls can be reproducible
    without mutating the process-global RNG.
    """
    if count < 0:
        raise ValueError("count must be non-negative.")

    local_rng = rng if rng is not None else random.Random(seed)
    positions = [(word_index, bit_index) for word_index in range(STATE_WORDS) for bit_index in range(32)]
    local_rng.shuffle(positions)
    return [[position] for position in positions[: min(count, len(positions))]]


def word_bit_mask(word_index: int, bit_index: int) -> Mask:
    """Return a one-bit mask selecting one state word bit."""
    return validate_mask([(word_index, bit_index)])


def evaluate_linear_mask(state: Sequence[int], mask: Sequence[tuple[int, int]]) -> int:
    """Compatibility wrapper for linear parity evaluation."""
    return linear_parity(state, mask)


def candidate_input_differences() -> list[Mask]:
    """Return a compact deterministic set of simple input differences."""
    singles = [
        [(0, 0)],
        [(1, 0)],
        [(4, 0)],
        [(5, 7)],
        [(8, 9)],
        [(12, 13)],
        [(15, 18)],
    ]
    pairs = [
        [(0, 0), (1, 0)],
        [(0, 7), (4, 7)],
        [(5, 0), (10, 0)],
        [(8, 13), (12, 13)],
    ]
    return [validate_mask(mask) for mask in [*singles, *pairs]]


def candidate_output_masks() -> list[Mask]:
    """Return a compact deterministic set of simple output linear masks."""
    singles = [
        [(0, 0)],
        [(0, 7)],
        [(1, 0)],
        [(5, 9)],
        [(10, 13)],
        [(15, 18)],
    ]
    low_weight = [
        [(0, 0), (1, 0)],
        [(0, 7), (4, 7)],
        [(5, 9), (10, 9)],
        [(8, 13), (12, 13)],
    ]
    return [validate_mask(mask) for mask in [*singles, *low_weight]]


def refined_candidate_input_differences() -> list[Mask]:
    """Return an expanded deterministic set of single-bit input differences."""
    masks: list[Mask] = []

    for word_index in (0, 4, 5, 6, 7, 8, 12):
        for bit_index in range(32):
            masks.append([(word_index, bit_index)])

    for word_index in range(STATE_WORDS):
        for bit_index in (0, 1, 7, 8, 9, 12, 13, 14, 18):
            masks.append([(word_index, bit_index)])

    return _deduplicate_masks(masks)


def refined_candidate_output_masks() -> list[Mask]:
    """Return expanded low-weight output masks over related Salsa20 words."""
    masks: list[Mask] = []
    rows = [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (8, 9, 10, 11),
        (12, 13, 14, 15),
    ]
    columns = [
        (0, 4, 8, 12),
        (1, 5, 9, 13),
        (2, 6, 10, 14),
        (3, 7, 11, 15),
    ]

    for word_index in range(STATE_WORDS):
        for bit_index in range(32):
            masks.append([(word_index, bit_index)])

    for group in [*rows, *columns]:
        for left_position in range(len(group)):
            for right_position in range(left_position + 1, len(group)):
                left_word = group[left_position]
                right_word = group[right_position]
                for bit_index in range(32):
                    masks.append([(left_word, bit_index), (right_word, bit_index)])

    for group in rows:
        for left_position in range(len(group)):
            for right_position in range(left_position + 1, len(group)):
                left_word = group[left_position]
                right_word = group[right_position]
                for bit_index in range(32):
                    for offset in (7, 9, 13, 18):
                        masks.append(
                            [(left_word, bit_index), (right_word, (bit_index + offset) & 31)]
                        )

    return _deduplicate_masks(masks)


def _deduplicate_masks(masks: Sequence[Sequence[tuple[int, int]]]) -> list[Mask]:
    output: list[Mask] = []
    seen: set[str] = set()
    for mask in masks:
        normalized = validate_mask(mask)
        key = mask_to_string(normalized)
        if key not in seen:
            seen.add(key)
            output.append(normalized)
    return output
