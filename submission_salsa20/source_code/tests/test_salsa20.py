"""Tests for the 4-round Salsa20 implementation."""

import unittest

from src.salsa20_4round import (
    WORD_MASK,
    columnround,
    doubleround,
    quarterround,
    rotl32,
    rowround,
    salsa20_core,
    salsa20_hash,
)


class Salsa20CoreTests(unittest.TestCase):
    def test_rotl32_known_behavior(self) -> None:
        self.assertEqual(rotl32(0x00000001, 1), 0x00000002)
        self.assertEqual(rotl32(0x80000000, 1), 0x00000001)
        self.assertEqual(rotl32(0x12345678, 8), 0x34567812)
        self.assertEqual(rotl32(0x12345678, 0), 0x12345678)
        self.assertEqual(rotl32(0x12345678, 32), 0x12345678)

    def test_quarterround_standard_vector(self) -> None:
        self.assertEqual(
            quarterround(0x11111111, 0x01020304, 0x9B8D6F43, 0x01234567),
            (0x4C321B5F, 0x1B293F0D, 0xEF2D531B, 0xD366442D),
        )

    def test_rowround_deterministic_behavior(self) -> None:
        state = [
            0x00000001,
            0x00000000,
            0x00000000,
            0x00000000,
            0x00000001,
            0x00000000,
            0x00000000,
            0x00000000,
            0x00000001,
            0x00000000,
            0x00000000,
            0x00000000,
            0x00000001,
            0x00000000,
            0x00000000,
            0x00000000,
        ]
        expected = [
            0x08008145,
            0x00000080,
            0x00010200,
            0x20500000,
            0x20100001,
            0x00048044,
            0x00000080,
            0x00010000,
            0x00000001,
            0x00002000,
            0x80040000,
            0x00000000,
            0x00000001,
            0x00000200,
            0x00402000,
            0x88000100,
        ]
        self.assertEqual(rowround(state), expected)

    def test_columnround_deterministic_behavior(self) -> None:
        state = [
            0x00000001,
            0x00000000,
            0x00000000,
            0x00000000,
            0x00000001,
            0x00000000,
            0x00000000,
            0x00000000,
            0x00000001,
            0x00000000,
            0x00000000,
            0x00000000,
            0x00000001,
            0x00000000,
            0x00000000,
            0x00000000,
        ]
        expected = [
            0x10090288,
            0x00000000,
            0x00000000,
            0x00000000,
            0x00000101,
            0x00000000,
            0x00000000,
            0x00000000,
            0x00020401,
            0x00000000,
            0x00000000,
            0x00000000,
            0x40A04001,
            0x00000000,
            0x00000000,
            0x00000000,
        ]
        self.assertEqual(columnround(state), expected)

    def test_four_round_reproducibility_under_fixed_input(self) -> None:
        state = [(0x9E3779B9 * i + 0x12345678) & WORD_MASK for i in range(16)]
        first = salsa20_core(state, rounds=4, feedforward=False)
        second = salsa20_core(state, rounds=4, feedforward=False)

        self.assertEqual(first, second)
        self.assertEqual(first, doubleround(doubleround(state)))
        self.assertEqual(len(first), 16)

    def test_feedforward_changes_output_compared_to_core_mode(self) -> None:
        state = [(0x01020304 * (i + 1)) & WORD_MASK for i in range(16)]

        core_output = salsa20_core(state, rounds=4, feedforward=False)
        hash_output = salsa20_hash(state, rounds=4, feedforward=True)

        self.assertNotEqual(core_output, hash_output)
        self.assertEqual(
            hash_output,
            [(core_output[i] + state[i]) & WORD_MASK for i in range(16)],
        )

    def test_outputs_remain_32_bit_words(self) -> None:
        state = [
            0xFFFFFFFF,
            0x100000000,
            0x123456789,
            0xABCDEF01,
            0x00000000,
            0x7FFFFFFF,
            0x80000000,
            0xDEADBEEF,
            0xCAFEBABE,
            0x13579BDF,
            0x2468ACE0,
            0x0F0F0F0F,
            0xF0F0F0F0,
            0xAAAAAAAA,
            0x55555555,
            0x31415926,
        ]
        outputs = [
            *quarterround(*state[:4]),
            *rowround(state),
            *columnround(state),
            *salsa20_core(state, rounds=4, feedforward=False),
            *salsa20_hash(state, rounds=4, feedforward=True),
        ]

        self.assertTrue(all(0 <= word <= WORD_MASK for word in outputs))


if __name__ == "__main__":
    unittest.main()
