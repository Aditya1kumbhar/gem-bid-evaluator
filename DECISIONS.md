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

## 2. Gemini Model Quota & Automatic Fallback
- **Date:** 2026-11-20
- **Observation:** `gemini-3.8-flash` on free-tier projects has a low rate limit (20 requests/day) and frequent 503/429 spikes.
- **Resolution:** Internal retry logic in `app/gemini_client.py` gracefully delegates to `gemini-3.5-flash-lite` upon 429/503 exhaustion with a brief backoff, maintaining 100% verdict consistency.

## 3. Phase P6 Deployment-Independent Packaging
- **Date:** 2026-11-20
- **Additions:**
  1. `scripts/make_fixtures.py`: ReportLab generator for three synthetic bidder PDF packs (`bidder_pass.pdf`, `bidder_fail.pdf`, `bidder_review.pdf`).
  2. `Dockerfile`: `python:3.12-slim` image setup with dynamic `${PORT:-8080}` binding for Cloud Run.
  3. `scripts/preflight.py`: Multi-run stability verifier uploading tender documents and bidders, confirming SHA-256 cache hits and verdict invariance with a 300s HTTP client timeout.
  4. `README.md`: Documented preflight verification commands and Google Cloud Run deployment configuration.

