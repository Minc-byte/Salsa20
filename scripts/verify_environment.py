"""Verify the Salsa20 CTF project environment."""

from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path


REQUIRED_FOLDERS = [
    "data/raw",
    "data/generated",
    "docs",
    "src",
    "scripts",
    "tests",
    "results/distinguisher",
    "results/key_recovery",
    "results/complexity",
    "results/plots",
    "reports",
    "references",
]

REQUIRED_FILES = [
    "README.md",
    "HANDOVER_CHECKLIST.md",
    "docs/handover.md",
    "docs/progress_log.md",
    "docs/next_steps.md",
    "docs/codex_prompts.md",
    "src/__init__.py",
    "src/salsa20_4round.py",
    "src/masks.py",
    "src/differential_linear_distinguisher.py",
    "src/key_recovery.py",
    "src/complexity_measurement.py",
    "src/utils.py",
    "scripts/verify_environment.py",
    "scripts/run_distinguisher.py",
    "scripts/run_key_recovery.py",
    "scripts/run_complexity.py",
    "scripts/create_submission_salsa20.py",
    "tests/test_salsa20.py",
    "reports/salsa20_4round_report.md",
    "reports/final_salsa20_ctf_report.md",
    "references/notes_on_methodology.md",
]


def check_paths(root: Path, paths: list[str], expect_dir: bool) -> tuple[bool, list[str]]:
    missing: list[str] = []
    for relative_path in paths:
        path = root / relative_path
        if expect_dir:
            exists = path.is_dir()
        else:
            exists = path.is_file()
        if not exists:
            missing.append(relative_path)
    return not missing, missing


def run_unittests(root: Path) -> tuple[bool, str]:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests"]
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    output = "\n".join(part for part in [completed.stdout, completed.stderr] if part)
    return completed.returncode == 0, output.strip()


def compile_python_files(root: Path) -> tuple[bool, list[str]]:
    failures: list[str] = []
    files = sorted((root / "src").glob("*.py")) + sorted((root / "scripts").glob("*.py"))
    for path in files:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            failures.append(f"{path.relative_to(root)}: {exc.msg}")
    return not failures, failures


def print_check(label: str, passed: bool, detail: str = "") -> None:
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {label}")
    if detail:
        print(detail)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    print(f"Python: {sys.version.split()[0]}")
    print(f"Repository: {root}")

    folders_ok, missing_folders = check_paths(root, REQUIRED_FOLDERS, expect_dir=True)
    print_check(
        "required folders exist",
        folders_ok,
        "\n".join(f"missing folder: {path}" for path in missing_folders),
    )

    files_ok, missing_files = check_paths(root, REQUIRED_FILES, expect_dir=False)
    print_check(
        "required files exist",
        files_ok,
        "\n".join(f"missing file: {path}" for path in missing_files),
    )

    tests_ok, unittest_output = run_unittests(root)
    print_check("unittest discovery", tests_ok, unittest_output)

    compile_ok, compile_failures = compile_python_files(root)
    print_check(
        "py_compile src/*.py scripts/*.py",
        compile_ok,
        "\n".join(compile_failures),
    )

    all_ok = folders_ok and files_ok and tests_ok and compile_ok
    print_check("overall environment", all_ok)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
