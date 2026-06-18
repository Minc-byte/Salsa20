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

### Refined Verification

The initial Phase 2 candidate was:

- `Delta = w04.b00`
- `Gamma = w08.b13+w12.b13`
- `samples = 8192`
- `probability = 0.5062255859375`
- `bias = 0.0062255859375`
- `correlation = 0.012451171875`
- approximate 95 percent CI: `[0.49539885269150336, 0.5170523191834967]`

Because this confidence interval included `0.5`, the candidate was not strong
enough for final reporting. Re-verifying the same candidate at `65536` samples
also remained inconclusive:

- `probability = 0.502899169921875`
- `bias = 0.002899169921875`
- `correlation = 0.00579833984375`
- approximate 95 percent CI: `[0.499071109274623, 0.5067272305691269]`

The refined search therefore expands the candidate set while staying within
4-round Salsa20 differential-linear analysis:

- more single-bit input differences over related row and column words
- all single-bit output masks
- same-bit two-word masks over Salsa20 row and column word groups
- selected low-weight row-pair masks using rotation-related bit offsets

The best refined verified distinguisher is:

- `Delta = w08.b26`
- `Gamma = w06.b00+w07.b09`
- `samples = 65536`
- `probability = 0.204254150390625`
- `bias = -0.295745849609375`
- `correlation = -0.59149169921875`
- approximate 95 percent CI: `[0.20116749075895551, 0.20734081002229449]`

This refined confidence interval excludes `0.5`. The inference is that this
candidate is a statistically strong 4-round Salsa20 differential-linear
distinguisher for the measured no-feed-forward core event. It is still only a
distinguisher and does not constitute key recovery.

## Linear Extension to Key Recovery

The CTF handover calls for extending the distinguisher into a key-recovery
style experiment. This phase addresses that requirement as a reduced-subkey
candidate-ranking demo only; it does not claim full 256-bit Salsa20 key
recovery.

The experiment uses the refined verified 4-round distinguisher:

- `Delta = w08.b26`
- `Gamma = w06.b00+w07.b09`

For each sample, a public 16-word Salsa20 state template is generated with the
selected reduced-subkey bit positions cleared. A fixed secret reduced subkey is
embedded into those positions, the paired state is created with `Delta`, and
both states are run through the 4-round core without feed-forward. The observed
bit is the `Gamma` parity of the output XOR difference.

Each candidate reduced subkey is embedded into the same public templates and
scored by agreement with the observed parity sequence. Candidates are ranked by
agreement count, equivalently by the candidate score correlation
`2 * agreement_probability - 1`.

Default setup:

- reduced key size: `8` bits
- candidate count: `256`
- subkey positions: word `1`, bits `0` through `7`
- samples: `64`
- seed: `20260619`
- secret reduced subkey: `0xfd`

Result:

- recovered best candidate: `0xfd`
- correct reduced-subkey rank: `1`
- top score: `64/64`
- top score correlation: `1.0`

This demonstrates a practical reduced-subkey candidate-ranking extension of the
verified differential-linear distinguisher. The setup is intentionally reduced
and controlled: it ranks a small embedded subkey space from generated
observations and should not be described as recovery of the full Salsa20 key.

## Data and Time Complexity

The refined distinguisher has measured verification correlation
`-0.59149169921875`. Using the standard rough estimate
`N ~= correlation^-2`, the estimated data complexity is:

- estimated distinguisher data complexity: `2.858266317136788` pairs
- ceiling estimate: `3` pairs
- verification samples used for the refined result: `65536`

The local runtime measurement for the refined distinguisher used `4096`
sample pairs:

- measured probability: `0.21435546875`
- measured correlation: `-0.5712890625`
- wall-clock runtime: `0.3784792999995261` seconds

The reduced-subkey key-ranking experiment uses the Phase 3 default setup:

- reduced key bits: `8`
- candidates: `256`
- samples per candidate: `64`
- total scoring operations: `16384`
- wall-clock runtime: `1.539827655999943` seconds
- correct reduced-subkey rank: `1`

Inference: the verified 4-round distinguisher has a large empirical correlation,
so the heuristic pair complexity is very small for distinguishing in this
reduced-round no-feed-forward setting. The key-ranking workload scales as
`2^bits * samples` for this demo and remains practical for the default 8-bit
candidate space. These figures are measurements for this Python implementation
and reduced setup; they are not evidence of full 256-bit Salsa20 key recovery.

### Output Files

Search outputs:

- `results/distinguisher/salsa20_search_results.csv`
- `results/distinguisher/salsa20_search_results.json`

Verification outputs:

- `results/distinguisher/salsa20_verified_distinguisher.csv`
- `results/distinguisher/salsa20_verified_distinguisher.json`

Refined outputs:

- `results/distinguisher/salsa20_refined_search_results.csv`
- `results/distinguisher/salsa20_refined_verified_distinguisher.csv`
- `results/distinguisher/salsa20_refined_verified_distinguisher.json`

Key-ranking outputs:

- `results/key_recovery/salsa20_key_recovery_rankings.csv`
- `results/key_recovery/salsa20_key_recovery_summary.json`

Complexity outputs:

- `results/complexity/salsa20_complexity_estimates.csv`
- `results/complexity/salsa20_complexity_estimates.json`

### Limitations

This phase only searches a compact practical mask set. A high-ranking candidate
from a small search can include sampling noise, which is why verification uses a
larger independent run. This phase does not claim full key recovery or stronger
results for 6, 7, or 8 rounds. The refined result is reported only for the
4-round Salsa20 core without feed-forward; feed-forward behavior and full
Salsa20 output distinguishers require separate experiments. The key-ranking
extension is a reduced-subkey candidate-ranking demo over a small embedded
candidate space, not recovery of a full Salsa20 key. Complexity estimates use
the rough `N ~= c^-2` heuristic and local wall-clock measurements, so they
should be treated as experiment-scale guidance rather than portable optimized
implementation benchmarks.
