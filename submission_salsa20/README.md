# Salsa20-Only CTF Submission

This package contains the 4-round Salsa20 CTF solution artifacts:

- tested source code;
- differential-linear distinguisher experiments;
- refined verification results;
- reduced-subkey candidate-ranking results;
- data and time complexity measurements;
- final report in Markdown, DOCX, and PDF formats.

The key-ranking component is a reduced-subkey candidate-ranking demonstration.
It is not full 256-bit Salsa20 key recovery.

## Reproduction

From the package root, copy or inspect `source_code/`. In the original project
layout, the main reproduction commands are:

```bash
python3 -m unittest discover -s tests
python3 scripts/run_distinguisher.py --verify-samples 65536
python3 scripts/run_key_recovery.py
python3 scripts/run_complexity.py
python3 -m py_compile src/*.py scripts/*.py
```

## Main Report

See `reports/final_salsa20_ctf_report.pdf` for the reviewer-facing report.
