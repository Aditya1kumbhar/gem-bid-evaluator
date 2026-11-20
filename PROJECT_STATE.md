# PROJECT_STATE: BidParakh (gem-bid-evaluator)

## Overview
Officer-side GeM bid evaluation backend: AI reads, code decides. Built for Startup Buildathon India 2026.

## Architecture & Layout
- `app/config.py`: Key loading hierarchy (`GEMINI_API_KEY` -> `GEMINI_API_KEY_FILE` -> `gemini_api_key.txt`).
- `app/schemas.py`: Single source of truth Pydantic v2 data models.
- `app/pdf_text.py`: `pypdf` per-page extraction and text normalisation.
- `app/numbers.py`: Indian money and count parser (`lakh`, `crore`, Indian comma patterns).
- `app/evidence_guard.py`: Strict & relaxed dual-pass quote verification against PDF text layers.
- `app/gemini_client.py`: Structured Gemini extraction with double extraction, dispute flagging, and fast fallback.
- `app/resolver.py`: Newest-wins criterion and void list resolution with `supersedes` tracking.
- `app/rules.py`: Pure deterministic rule engine (no network, no I/O, no AI).
- `app/speaking_order.py`: Strict template-based draft rejection lines for FAIL verdicts.
- `app/matrix.py`: Criteria-by-bidder verdict matrix, CSV download, and inline-styled HTML report table.
- `app/atc_flag.py`: ATC clause legality verification against Disclaimer items (FLAG / REVIEW / CLEAR).
- `app/jobs.py`: In-memory store and SHA-256 disk cache replay.
- `app/main.py`: FastAPI routes (`/health`, `/tenders`, `/tenders/{id}/bidders`, `/tenders/{id}/evaluate`, `/tenders/{id}/matrix.csv`, `/tenders/{id}/report`).
- `fixtures/`: Hero tender PDFs and synthetic bidder PDFs (`bidder_pass.pdf`, `bidder_fail.pdf`, `bidder_review.pdf`).
- `scripts/make_fixtures.py`: ReportLab synthetic fixture generator.
- `scripts/preflight.py`: Multi-run stability verifier.
- `Dockerfile`: Container configuration for Cloud Run (`PORT:-8080`).

## Status
- **Phases P0-P5:** Complete, tested, committed, and pushed to `origin/main`.
- **Phase P6 (Deployment-Independent Tasks):** Complete.
  - `scripts/make_fixtures.py` and 3 bidder PDFs generated.
  - `Dockerfile` created.
  - `scripts/preflight.py` created with 300s timeout.
  - `README.md` updated with preflight and Cloud Run deployment blocks.
  - All 26 unit tests pass.
- **Phase P6 (Deployment):** Paused awaiting user confirmation and GCP billing activation.
