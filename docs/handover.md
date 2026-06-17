# Salsa20 CTF Handover

## Project Purpose

This repository is for the Salsa20 portion of the CTF task titled
Differential-Linear Cryptanalysis of ARX Stream Ciphers. The project is scoped
to a practical, reproducible analysis workflow for reduced-round Salsa20.

## CTF Requirements Addressed

- Implement the reduced-round Salsa20 target.
- Verify the Salsa20 round structure before cryptanalytic experiments.
- Build a differential-linear distinguisher for 4-round Salsa20.
- Extend the distinguisher into a documented reduced-subkey ranking experiment.
- Measure empirical data and time complexity.
- Produce result artifacts and final Salsa20-only reports.

## Current Scope

- 4-round Salsa20 only.
- Differential-linear cryptanalysis only.
- No ChaCha implementation.
- No Forro implementation.
- No full 6, 7, or 8-round Salsa20 key-recovery claims.
- No full 256-bit key-recovery claim unless it is actually implemented and
  experimentally validated.

## Completed Baseline

Phase 1 is the completed baseline for continuing from another machine:

- Repository skeleton created.
- `src/salsa20_4round.py` implemented.
- 32-bit word operations implemented.
- `rotl32` implemented.
- Salsa20 `quarterround`, `rowround`, `columnround`, and `doubleround`
  implemented.
- `salsa20_core(state, rounds=4, feedforward=False)` implemented.
- `salsa20_hash(state, rounds=4, feedforward=True)` implemented.
- Unit tests added for round behavior, reproducibility, feed-forward behavior,
  and 32-bit output bounds.

## What Remains

The next planned stage is Phase 2:

- Implement generic mask helpers.
- Implement practical differential-linear distinguisher search.
- Verify the best candidate with a larger independent sample count.
- Save CSV and JSON distinguisher outputs.
- Update the report with the Phase 2 method, output files, and limitations.

Later stages:

- Phase 3: reduced-subkey candidate-ranking extension.
- Phase 4: data and time complexity measurement.
- Phase 5: final report.
- Phase 6: submission package.

## Commands Already Validated

Phase 1 validation command:

```bash
python3 -m unittest discover -s tests
```

Phase 1 result:

```text
Ran 7 tests
OK
```

Compile validation command:

```bash
python3 -m py_compile src/*.py scripts/*.py
```

Environment verification command for handover:

```bash
python3 scripts/verify_environment.py
```

## Next Codex Prompt

Use the Phase 2 prompt from `docs/codex_prompts.md`. It is written to be
self-contained so the work can continue from a fresh clone without chat
history.

## Important Limitations and Forbidden Claims

- Do not use the discarded Salsa20 paper as a primary reference for this CTF
  implementation path.
- Do not implement ChaCha in this repository.
- Do not implement Forro in this repository.
- Do not claim full 256-bit Salsa20 key recovery unless it is actually
  implemented and experimentally validated.
- Do not claim full 6, 7, or 8-round Salsa20 key recovery.
- If key recovery is attempted, describe it as reduced-subkey candidate ranking
  until stronger evidence exists.

## Repository Structure

```text
data/
  raw/              External immutable input data, if any.
  generated/        Generated experiment inputs, if needed.
docs/
  handover.md       Machine-to-machine handover context.
  progress_log.md   Chronological project progress.
  next_steps.md     Planned project phases.
  codex_prompts.md  Self-contained continuation prompts.
src/
  salsa20_4round.py Core Salsa20 implementation.
  masks.py          Planned mask helpers for Phase 2.
  differential_linear_distinguisher.py
                    Planned Phase 2 distinguisher search.
  key_recovery.py   Planned Phase 3 reduced-subkey ranking.
  complexity_measurement.py
                    Planned Phase 4 complexity measurement.
  utils.py          Shared utility functions.
scripts/
  verify_environment.py
                    Handover environment verifier.
  run_distinguisher.py
                    Planned Phase 2 entry point.
  run_key_recovery.py
                    Planned Phase 3 entry point.
  run_complexity.py Planned Phase 4 entry point.
  create_submission_salsa20.py
                    Planned final packaging entry point.
tests/
  test_salsa20.py   Phase 1 Salsa20 core tests.
results/
  distinguisher/    Planned Phase 2 outputs.
  key_recovery/     Planned Phase 3 outputs.
  complexity/       Planned Phase 4 outputs.
  plots/            Planned report plots.
reports/
  salsa20_4round_report.md
                    Working technical report.
  final_salsa20_ctf_report.md
                    Final Salsa20-only CTF report.
references/
  notes_on_methodology.md
                    Methodology notes and claim discipline.
```
