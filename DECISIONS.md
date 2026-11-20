# Architectural & Environment Decisions

## 1. Python Environment Setup (Pre-P0)
- **Date:** 2026-11-20
- **Requirement:** The project requires Python 3.12; system Python is 3.9.6.
- **Resolution Path:**
  1. Verified existing `python3.12` — not found in system PATH.
  2. Verified Homebrew `brew` — not installed on the system.
  3. Installed `uv` via the official installer (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
  4. Provisioned CPython 3.12.16 via `uv python install 3.12`.
  5. Created virtual environment at `.venv` using Python 3.12 (`uv venv --python 3.12 .venv`).
  6. Added `.venv/` to `.gitignore`.
- **Enforcement Rule:** Every subsequent `pip install`, `pytest`, and `uvicorn` execution throughout all build phases must strictly invoke `.venv/bin/python` and `.venv/bin/pip`.
