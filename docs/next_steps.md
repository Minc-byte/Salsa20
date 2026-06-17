# Next Steps

## Phase 2: Differential-Linear Distinguisher Search

- Implement mask helpers for input XOR differences and output linear masks.
- Search single-bit and selected low-weight masks.
- Run 4-round Salsa20 core without feed-forward for candidate pairs.
- Estimate probability, bias, correlation, standard error, and confidence
  intervals.
- Save CSV and JSON results.
- Verify the best candidate with a larger independent sample count.

## Phase 3: Key-Recovery Extension

- Build only a reduced-subkey candidate-ranking experiment.
- Define the guessed subkey bits explicitly.
- Score candidates using the verified distinguisher statistic.
- Report true reduced-subkey rank, candidate-space size, sample count, and
  runtime.
- Do not claim full key recovery.

## Phase 4: Complexity Measurement

- Measure distinguisher success versus sample count.
- Measure reduced-subkey ranking runtime versus candidate count and data count.
- Save CSV and JSON summaries.
- Generate plots only after result schemas are stable.

## Phase 5: Final Report

- Document implementation, tests, distinguisher method, verified results,
  reduced-subkey ranking, complexity, and limitations.
- Include exact commands needed to reproduce results.
- Keep claims aligned with implemented experiments.

## Phase 6: Submission Package

- Package only Salsa20 files, result artifacts, and reports.
- Exclude unrelated algorithms.
- Include a manifest of files and reproduction commands.
