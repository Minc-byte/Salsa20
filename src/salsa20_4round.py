"""4-round Salsa20 core primitives.

The functions in this module implement the Salsa20 round structure over a
16-word state. Words are Python integers interpreted modulo 2**32.
"""

WORD_MASK = 0xFFFFFFFF
STATE_WORDS = 16
DEFAULT_ROUNDS = 4


def add32(left: int, right: int) -> int:
    """Add two words modulo 2**32."""
    return (left + right) & WORD_MASK


def word32(value: int) -> int:
    """Normalize ``value`` to a 32-bit word."""
    return value & WORD_MASK


def rotl32(value: int, shift: int) -> int:
    """Rotate a 32-bit word left by ``shift`` bits."""
    shift &= 31
    value &= WORD_MASK
    return ((value << shift) | (value >> (32 - shift))) & WORD_MASK


def _validate_state(state: list[int] | tuple[int, ...]) -> list[int]:
    if len(state) != STATE_WORDS:
        raise ValueError(f"Salsa20 state must contain {STATE_WORDS} words.")
    return [word32(word) for word in state]


def _validate_rounds(rounds: int) -> None:
    if rounds < 0 or rounds % 2 != 0:
        raise ValueError("Salsa20 rounds must be a non-negative even integer.")


def quarterround(y0: int, y1: int, y2: int, y3: int) -> tuple[int, int, int, int]:
    """Apply the Salsa20 quarterround to four 32-bit words."""
    z1 = word32(y1) ^ rotl32(add32(y0, y3), 7)
    z2 = word32(y2) ^ rotl32(add32(z1, y0), 9)
    z3 = word32(y3) ^ rotl32(add32(z2, z1), 13)
    z0 = word32(y0) ^ rotl32(add32(z3, z2), 18)
    return z0, z1, z2, z3


def rowround(state: list[int] | tuple[int, ...]) -> list[int]:
    """Apply the Salsa20 rowround to a 16-word state."""
    y = _validate_state(state)
    z = [0] * STATE_WORDS

    z[0], z[1], z[2], z[3] = quarterround(y[0], y[1], y[2], y[3])
    z[5], z[6], z[7], z[4] = quarterround(y[5], y[6], y[7], y[4])
    z[10], z[11], z[8], z[9] = quarterround(y[10], y[11], y[8], y[9])
    z[15], z[12], z[13], z[14] = quarterround(y[15], y[12], y[13], y[14])
    return z


def columnround(state: list[int] | tuple[int, ...]) -> list[int]:
    """Apply the Salsa20 columnround to a 16-word state."""
    x = _validate_state(state)
    y = [0] * STATE_WORDS

    y[0], y[4], y[8], y[12] = quarterround(x[0], x[4], x[8], x[12])
    y[5], y[9], y[13], y[1] = quarterround(x[5], x[9], x[13], x[1])
    y[10], y[14], y[2], y[6] = quarterround(x[10], x[14], x[2], x[6])
    y[15], y[3], y[7], y[11] = quarterround(x[15], x[3], x[7], x[11])
    return y


def doubleround(state: list[int] | tuple[int, ...]) -> list[int]:
    """Apply one Salsa20 doubleround: columnround followed by rowround."""
    return rowround(columnround(state))


def salsa20_core(
    state: list[int] | tuple[int, ...],
    rounds: int = DEFAULT_ROUNDS,
    feedforward: bool = False,
) -> list[int]:
    """Apply the Salsa20 round function to a 16-word state.

    ``feedforward=False`` returns the state after the requested rounds without
    adding the initial state. Differential-linear experiments usually use this
    core/permutation mode because it isolates the round transformation being
    analyzed. If feed-forward is used in an experiment, it should be documented
    because the final modular additions can change the measured masks and
    correlations.
    """
    _validate_rounds(rounds)
    initial = _validate_state(state)
    current = initial[:]

    for _ in range(rounds // 2):
        current = doubleround(current)

    if feedforward:
        return [add32(output, original) for output, original in zip(current, initial)]
    return current


def salsa20_hash(
    state: list[int] | tuple[int, ...],
    rounds: int = DEFAULT_ROUNDS,
    feedforward: bool = True,
) -> list[int]:
    """Apply the Salsa20 hash/core output form.

    Salsa20's hash output normally includes feed-forward: after the rounds, the
    original input state is added word-wise to the transformed state modulo
    2**32. This wrapper defaults to that standard output behavior, while
    ``salsa20_core`` defaults to the no-feed-forward mode used by the planned
    differential-linear experiments.
    """
    return salsa20_core(state, rounds=rounds, feedforward=feedforward)


def salsa20_core_4round(
    state: list[int] | tuple[int, ...],
    add_initial_state: bool = False,
) -> list[int]:
    """Compatibility wrapper for the 4-round Salsa20 core."""
    return salsa20_core(state, rounds=4, feedforward=add_initial_state)


# Backward-compatible aliases for the skeleton names.
quarter_round = quarterround
row_round = rowround
column_round = columnround
double_round = doubleround
