# Notes on Methodology

## Scope

This repository targets only the Salsa20 part of the CTF task. The concrete
target is 4-round Salsa20. ChaCha and Forro are intentionally out of scope.

The work will follow this sequence:

1. Implement the 4-round Salsa20 core.
2. Verify the state layout and round functions.
3. Build practical differential-linear distinguishers.
4. Experimentally verify bias and correlation.
5. Extend the distinguisher into a reduced-subkey candidate-ranking demo.
6. Measure data and time complexity.
7. Generate CSV and JSON result artifacts.
8. Prepare the final report and submission package.

## Implementation Plan

### 1. Salsa20 Core

- Represent the Salsa20 state as 16 little-endian 32-bit words.
- Implement `rotl32`, `quarter_round`, `row_round`, `column_round`, and
  `double_round` in `src/salsa20_4round.py`.
- Implement `salsa20_core_4round` as two double-rounds.
- Keep a switch for feed-forward addition, because cryptanalytic experiments
  may need either the raw permutation state or the standard core output.

### 2. Round Verification

- Add reference-vector tests for quarter-round, row-round, column-round, and
  double-round behavior.
- Verify the state index convention before any cryptanalytic experiment is
  trusted.
- Add tests for 32-bit modular addition, rotation masking, and input validation.

### 3. Differential-Linear Distinguisher

- Define input differences and output linear masks in `src/masks.py`.
- Start from simple one-bit and low-weight word differences.
- Estimate the differential-linear correlation by sampling pairs
  `(X, X + Delta)` and measuring parity agreement under the output mask.
- Rank candidates by absolute bias/correlation, stability across seeds, and
  required sample count.

### 4. Bias and Correlation Verification

- Implement repeatable experiments in
  `src/differential_linear_distinguisher.py`.
- Use deterministic seeding and independent repeated trials.
- Store raw and summarized outputs under `results/distinguisher/`.
- Report sample count, estimated bias, estimated correlation, confidence
  interval, seed, input difference, output mask, and elapsed time.

### 5. Reduced-Subkey Candidate Ranking

- Implement only a practical reduced-subkey ranking experiment unless the
  project later supports a stronger claim.
- Define the guessed subkey bits explicitly and document the reduced candidate
  space.
- Score each candidate by how well partially inverted observations preserve
  the selected distinguisher statistic.
- Report rank of the true reduced subkey, candidate-space size, data count, and
  runtime.

### 6. Complexity Measurement

- Measure empirical success versus sample count for the distinguisher.
- Measure candidate-ranking runtime versus candidate-space size and data count.
- Write JSON summaries and CSV tables under `results/complexity/`.
- Generate plots only after the CSV/JSON schemas are stable.

### 7. Results and Artifacts

- `results/distinguisher/`: distinguisher trials and aggregate summaries.
- `results/key_recovery/`: reduced-subkey ranking outputs.
- `results/complexity/`: timing and data-complexity measurements.
- `results/plots/`: generated figures for reports.
- `data/generated/`: generated experiment inputs if needed.
- `data/raw/`: immutable externally supplied data if any is used.

### 8. Reports and Submission

- Keep `reports/salsa20_4round_report.md` focused on implementation,
  distinguisher construction, reduced-subkey ranking, complexity, and results.
- Keep `reports/final_salsa20_ctf_report.md` as the final Salsa20-only CTF
  deliverable.
- `scripts/create_submission_salsa20.py` will package only the Salsa20 files,
  reports, and result artifacts.

## Claim Discipline

- Do not claim full 256-bit Salsa20 key recovery unless it is implemented and
  experimentally validated.
- Treat the key-recovery component as a reduced-subkey candidate-ranking demo
  until evidence supports a stronger statement.
- Every reported distinguisher should include enough metadata to reproduce it.
- Reports must describe only the cryptanalytic method, experiments, results,
  limitations, and reproducibility details.
