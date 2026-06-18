# Salsa20-Only CTF Submission Manifest

## Scope

This submission covers 4-round Salsa20 only. It provides a tested
implementation, differential-linear distinguisher, refined experimental
verification, reduced-subkey candidate-ranking extension, and data/time
complexity measurements. It does not claim full 256-bit Salsa20 key recovery.

## CTF Requirement Mapping

| Requirement | Location | Status |
|---|---|---|
| 4-round Salsa20 implementation | `source_code/src/salsa20_4round.py` | Included |
| Differential-linear distinguisher | `source_code/src/differential_linear_distinguisher.py`, `source_code/src/masks.py` | Included |
| Experimental verification | `results/distinguisher/` | Included |
| Linear extension to key recovery | `source_code/src/key_recovery.py`, `results/key_recovery/` | Included as reduced-subkey ranking |
| Data complexity | `source_code/src/complexity_measurement.py`, `results/complexity/` | Included |
| Time complexity | `source_code/src/complexity_measurement.py`, `results/complexity/` | Included |
| Source code | `source_code/src/`, `source_code/scripts/`, `source_code/tests/` | Included |
| Experimental results | `results/` | Included |
| Report | `reports/final_salsa20_ctf_report.md`, `.docx`, `.pdf` | Included |

## Main Results

| Item | Value |
|---|---:|
| Refined input difference | `w08.b26` |
| Refined output mask | `w06.b00+w07.b09` |
| Refined probability | `0.204254150390625` |
| Refined bias | `-0.295745849609375` |
| Refined correlation | `-0.59149169921875` |
| Refined 95 percent CI | `[0.20116749075895551, 0.20734081002229449]` |
| Reduced secret subkey | `0xfd` |
| Reduced recovered candidate | `0xfd` |
| Correct reduced-subkey rank | `1` |
| Key-ranking score | `64/64` |
| Estimated data complexity | `2.858266317136788` pairs |
| Distinguisher runtime | `0.3784792999995261` seconds for `4096` samples |
| Key-ranking work | `16384` scoring operations |
| Key-ranking runtime | `1.539827655999943` seconds |

## Package Structure

```text
submission_salsa20/
  README.md
  submission_manifest.md
  source_code/
    src/
    scripts/
    tests/
  reports/
    final_salsa20_ctf_report.md
    final_salsa20_ctf_report.docx
    final_salsa20_ctf_report.pdf
  results/
    distinguisher/
    key_recovery/
    complexity/
  references/
    notes_on_methodology.md
```

## Reproduction Commands

```bash
python3 -m unittest discover -s tests
python3 scripts/run_distinguisher.py --verify-samples 65536
python3 scripts/run_key_recovery.py
python3 scripts/run_complexity.py
python3 -m py_compile src/*.py scripts/*.py
```

## Limitation

The key-ranking experiment is a reduced-subkey candidate-ranking demonstration.
It is not full 256-bit Salsa20 key recovery.
