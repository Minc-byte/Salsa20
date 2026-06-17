# 4-Round Salsa20 Differential-Linear Cryptanalysis Report

## Scope

This report covers only 4-round Salsa20.

## Planned Structure

1. Implementation
2. Verification
3. Differential-linear distinguisher
4. Experimental bias and correlation results
5. Reduced-subkey candidate-ranking extension
6. Data and time complexity
7. Limitations
8. Reproducibility notes

## Current Status

Phase 1 implemented the 4-round Salsa20 core and unit tests. Phase 2 adds a
practical differential-linear distinguisher search and verification pipeline.

## Phase 2: Differential-Linear Distinguisher

### Objective

Find practical differential-linear distinguishers for 4-round Salsa20 by
searching small input XOR differences and low-weight output linear masks.

### Method

For each candidate pair `(Delta, Gamma)`:

1. Generate random 16-word Salsa20 states.
2. Apply the input XOR difference `Delta`.
3. Run both states through 4-round Salsa20 core mode.
4. Compute the output XOR difference.
5. Evaluate the parity selected by output mask `Gamma`.
6. Estimate probability, bias, correlation, standard error, and an approximate
   95 percent confidence interval.

The measured event is `linear_parity(F(X) xor F(X xor Delta), Gamma) == 0`.
The reported bias is `Pr[event] - 1/2`, and the reported correlation is
`2 * bias`.

### Core Mode Without Feed-Forward

The search uses `salsa20_core(..., feedforward=False)`. This isolates the
4-round transformation itself. The Salsa20 hash output adds the input state back
into the transformed state, and those final modular additions can change the
observed mask behavior. Any experiment using feed-forward should therefore be
reported separately.

### Search Strategy

The search uses:

- Deterministic single-bit input differences.
- Selected two-bit input differences.
- Deterministic single-bit output masks.
- Selected low-weight output masks.

Candidates are ranked by absolute observed correlation. The best search result
is then re-run in verification mode with a larger independent sample count.

### Output Files

Search outputs:

- `results/distinguisher/salsa20_search_results.csv`
- `results/distinguisher/salsa20_search_results.json`

Verification outputs:

- `results/distinguisher/salsa20_verified_distinguisher.csv`
- `results/distinguisher/salsa20_verified_distinguisher.json`

### Limitations

This phase only searches a compact practical mask set. A high-ranking candidate
from a small search can include sampling noise, which is why verification uses a
larger independent run. This phase does not claim full key recovery or stronger
results for 6, 7, or 8 rounds.
