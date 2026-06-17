# Salsa20

Salsa20 differential-linear cryptanalysis project for the 4-round Salsa20 part
of the CTF task.

## Scope

- Implement and analyze only 4-round Salsa20.
- Do not implement ChaCha or Forro in this repository.
- Treat key recovery as a reduced-subkey candidate-ranking experiment unless a
  stronger result is actually implemented and verified.

## Repository Structure

```text
data/
  raw/
  generated/
src/
  salsa20_4round.py
  masks.py
  differential_linear_distinguisher.py
  key_recovery.py
  complexity_measurement.py
  utils.py
scripts/
  run_distinguisher.py
  run_key_recovery.py
  run_complexity.py
  create_submission_salsa20.py
tests/
  test_salsa20.py
results/
  distinguisher/
  key_recovery/
  complexity/
  plots/
reports/
  salsa20_4round_report.md
  final_salsa20_ctf_report.md
references/
  notes_on_methodology.md
```

## Implementation Plan

1. Implement the 4-round Salsa20 core. **Phase 1 implemented.**
2. Verify state layout, quarter-round, row-round, column-round, and
   double-round behavior.
3. Construct practical differential-linear distinguishers. **Phase 2 implemented.**
4. Experimentally verify distinguisher bias and correlation. **Phase 2 implemented.**
5. Extend the distinguisher into a reduced-subkey candidate-ranking demo.
6. Measure data complexity and time complexity.
7. Generate CSV and JSON result artifacts.
8. Prepare the final report and Salsa20-only submission package.

Detailed planning notes are in `references/notes_on_methodology.md`.

## Phase 1 Status

Implemented:

- 32-bit word normalization and modular addition.
- `rotl32`.
- Salsa20 `quarterround`, `rowround`, `columnround`, and `doubleround`.
- `salsa20_core(state, rounds=4, feedforward=False)`.
- `salsa20_hash(state, rounds=4, feedforward=True)`.
- Unit tests for round behavior, fixed-input reproducibility, feed-forward
  behavior, and 32-bit output bounds.

Run tests with:

```bash
python3 -m unittest discover -s tests
```

Phase 2 implements differential-linear distinguisher search and experimental
bias/correlation verification.

## Phase 2 Status

Implemented:

- Generic bit-mask helpers for input XOR differences and output linear masks.
- Deterministic search over single-bit and selected low-weight masks.
- Verification of the best search candidate with a larger independent sample.
- CSV and JSON output generation under `results/distinguisher/`.

Run the distinguisher pipeline with:

```bash
python3 scripts/run_distinguisher.py
```

## Continuing on Another Machine

```bash
git clone <repo-url>
cd Salsa20
python3 scripts/verify_environment.py
codex
```

Then read:

```bash
docs/handover.md
docs/codex_prompts.md
```
