# Progress Log

## 1. Repository Skeleton Created

- Created the required Salsa20-only project structure.
- Added source, script, test, result, report, data, and reference directories.
- Added placeholder files and planning notes for later phases.

## 2. Phase 1 Salsa20 Core Implemented

- Implemented 32-bit word normalization and modular addition.
- Implemented `rotl32`.
- Implemented Salsa20 `quarterround`.
- Implemented Salsa20 `rowround`.
- Implemented Salsa20 `columnround`.
- Implemented Salsa20 `doubleround`.
- Implemented `salsa20_core(state, rounds=4, feedforward=False)`.
- Implemented `salsa20_hash(state, rounds=4, feedforward=True)`.

## 3. Tests Added

- Added rotation behavior tests.
- Added standard Salsa20 quarterround vector test.
- Added deterministic rowround and columnround tests.
- Added 4-round reproducibility test.
- Added feed-forward behavior test.
- Added 32-bit output bounds test.

## 4. Phase 1 Validation

Command:

```bash
python3 -m unittest discover -s tests
```

Result:

```text
Ran 7 tests
OK
```

Compile command:

```bash
python3 -m py_compile src/*.py scripts/*.py
```

Result:

```text
OK
```

## 5. Pending Phase 2

Phase 2 is differential-linear distinguisher search and verification for
4-round Salsa20. It should use the no-feed-forward core mode unless an
experiment explicitly documents otherwise.
