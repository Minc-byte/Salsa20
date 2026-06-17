# Handover Checklist

## Before Leaving Current Machine

```bash
git status
python3 scripts/verify_environment.py
git add .
git commit -m "Add Salsa20 handover documentation"
git push origin main
```

## On New Machine

```bash
git clone <repo-url>
cd Salsa20
python3 scripts/verify_environment.py
codex
```

Then start with the Phase 2 prompt from `docs/codex_prompts.md`.
