"""Create the Salsa20-only CTF submission folder and ZIP archive."""

from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_DIR = REPO_ROOT / "submission_salsa20"
ZIP_PATH = REPO_ROOT / "submission_salsa20.zip"


PACKAGE_README = """# Salsa20-Only CTF Submission

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
"""


REQUIRED_REPORTS = [
    "reports/final_salsa20_ctf_report.md",
    "reports/final_salsa20_ctf_report.docx",
    "reports/final_salsa20_ctf_report.pdf",
]

REQUIRED_RESULTS = [
    "results/distinguisher/salsa20_search_results.csv",
    "results/distinguisher/salsa20_search_results.json",
    "results/distinguisher/salsa20_verified_distinguisher.csv",
    "results/distinguisher/salsa20_verified_distinguisher.json",
    "results/distinguisher/salsa20_refined_search_results.csv",
    "results/distinguisher/salsa20_refined_verified_distinguisher.csv",
    "results/distinguisher/salsa20_refined_verified_distinguisher.json",
    "results/key_recovery/salsa20_key_recovery_rankings.csv",
    "results/key_recovery/salsa20_key_recovery_summary.json",
    "results/complexity/salsa20_complexity_estimates.csv",
    "results/complexity/salsa20_complexity_estimates.json",
]

REQUIRED_PACKAGE_PATHS = [
    "README.md",
    "submission_manifest.md",
    "source_code/src/salsa20_4round.py",
    "source_code/src/masks.py",
    "source_code/src/differential_linear_distinguisher.py",
    "source_code/src/key_recovery.py",
    "source_code/src/complexity_measurement.py",
    "source_code/scripts/run_distinguisher.py",
    "source_code/scripts/run_key_recovery.py",
    "source_code/scripts/run_complexity.py",
    "source_code/scripts/create_submission_salsa20.py",
    "source_code/tests/test_salsa20.py",
    "source_code/tests/test_masks_and_distinguisher.py",
    "source_code/tests/test_key_recovery.py",
    "source_code/tests/test_complexity_measurement.py",
    "reports/final_salsa20_ctf_report.md",
    "reports/final_salsa20_ctf_report.docx",
    "reports/final_salsa20_ctf_report.pdf",
    "results/distinguisher/salsa20_refined_verified_distinguisher.json",
    "results/key_recovery/salsa20_key_recovery_summary.json",
    "results/complexity/salsa20_complexity_estimates.json",
    "references/notes_on_methodology.md",
]


def _ignore_generated(directory: str, names: list[str]) -> set[str]:
    del directory
    return {
        name
        for name in names
        if name == "__pycache__"
        or name.endswith(".pyc")
        or name == ".pytest_cache"
        or name == "verify_environment.py"
    }


def _copy_tree(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, ignore=_ignore_generated)


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _verify_sources_exist() -> None:
    required = [
        "submission_manifest.md",
        "src",
        "scripts",
        "tests",
        "references/notes_on_methodology.md",
        *REQUIRED_REPORTS,
        *REQUIRED_RESULTS,
    ]
    missing = [path for path in required if not (REPO_ROOT / path).exists()]
    if missing:
        raise FileNotFoundError("Missing required files before packaging: " + ", ".join(missing))


def _verify_package() -> None:
    missing = [path for path in REQUIRED_PACKAGE_PATHS if not (SUBMISSION_DIR / path).exists()]
    if missing:
        raise FileNotFoundError("Missing required files in package: " + ", ".join(missing))


def create_submission_package() -> Path:
    """Recreate submission_salsa20/ and submission_salsa20.zip."""
    _verify_sources_exist()

    if SUBMISSION_DIR.exists():
        shutil.rmtree(SUBMISSION_DIR)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    (SUBMISSION_DIR / "source_code").mkdir(parents=True)
    (SUBMISSION_DIR / "reports").mkdir()
    (SUBMISSION_DIR / "results").mkdir()
    (SUBMISSION_DIR / "references").mkdir()

    (SUBMISSION_DIR / "README.md").write_text(PACKAGE_README, encoding="utf-8")
    _copy_file(REPO_ROOT / "submission_manifest.md", SUBMISSION_DIR / "submission_manifest.md")

    _copy_tree(REPO_ROOT / "src", SUBMISSION_DIR / "source_code" / "src")
    _copy_tree(REPO_ROOT / "scripts", SUBMISSION_DIR / "source_code" / "scripts")
    _copy_tree(REPO_ROOT / "tests", SUBMISSION_DIR / "source_code" / "tests")

    for report in REQUIRED_REPORTS:
        _copy_file(REPO_ROOT / report, SUBMISSION_DIR / report)

    for result in REQUIRED_RESULTS:
        _copy_file(REPO_ROOT / result, SUBMISSION_DIR / result)

    _copy_file(
        REPO_ROOT / "references" / "notes_on_methodology.md",
        SUBMISSION_DIR / "references" / "notes_on_methodology.md",
    )

    _verify_package()
    archive_base = ZIP_PATH.with_suffix("")
    shutil.make_archive(str(archive_base), "zip", root_dir=REPO_ROOT, base_dir=SUBMISSION_DIR.name)
    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"ZIP archive was not created: {ZIP_PATH}")
    return ZIP_PATH


def main() -> int:
    zip_path = create_submission_package()
    print(f"Created {SUBMISSION_DIR.relative_to(REPO_ROOT)}")
    print(f"Created {zip_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
