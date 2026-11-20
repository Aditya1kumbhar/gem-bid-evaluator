# BidParakh: GeM Bid Evaluator

> Officer-side GeM bid evaluation: AI reads, code decides.

BidParakh helps government procurement officers evaluate technical bids submitted on the GeM portal. It resolves corrigenda criteria, extracts null-and-void lists, validates evidence quotes against PDF text layers, and executes deterministic rule evaluations.

---

## Development Setup

```bash
# 1. Environment and dependencies
.venv/bin/pip install -r requirements.txt

# 2. Run unit tests
.venv/bin/python -m pytest tests/unit -q

# 3. Run application server
.venv/bin/uvicorn app.main:app --port 8080 --reload
```

---

## End-to-End Demo Sequence (cURL)

> **Important Ordering Rule:** Tender upload order matters! Always upload the **main bid PDF first**, followed by **corrigenda in date order**. This guarantees that the resolver's newest-wins rule applies correctly and supersedes older criteria.

### 1. Upload Tender Documents (Main Bid first, then Corrigendum)
```bash
# Response returns tender_id (e.g. "a1b2c3d4...")
TENDER_ID=$(curl -s -X POST http://localhost:8080/tenders \
  -F "files=@fixtures/GEM-2026-B-7945477-main-bid.pdf" \
  -F "files=@fixtures/GEM-2026-B-7945477-C5-corrigendum.pdf" \
  | jq -r .tender_id)

echo "Created Tender ID: $TENDER_ID"
```

### 2. Add Bidder Submission Packs
```bash
# Add Bidder 1 (Pass pack)
curl -s -X POST "http://localhost:8080/tenders/$TENDER_ID/bidders" \
  -F "name=Alpha Solutions Pvt Ltd" \
  -F "files=@fixtures/GEM-2026-B-7945477-C5-corrigendum.pdf"

# Add Bidder 2 (Fail pack)
curl -s -X POST "http://localhost:8080/tenders/$TENDER_ID/bidders" \
  -F "name=Beta Technologies" \
  -F "files=@fixtures/GEM-2026-B-7945477-C5-corrigendum.pdf"

# Add Bidder 3 (Review pack)
curl -s -X POST "http://localhost:8080/tenders/$TENDER_ID/bidders" \
  -F "name=Gamma Infotech" \
  -F "files=@fixtures/GEM-2026-B-7945477-C5-corrigendum.pdf"
```

### 3. Run Evaluation Pipeline
```bash
# Runs extraction, quote verification, rules engine, and caches result to disk
curl -s -X POST "http://localhost:8080/tenders/$TENDER_ID/evaluate" | jq .
```

### 4. Download Verdict Matrix (CSV)
```bash
curl -s "http://localhost:8080/tenders/$TENDER_ID/matrix.csv" -o matrix.csv
cat matrix.csv
```

### 5. View Procurement Officer Report (HTML)
Open in your browser:
```bash
open "http://localhost:8080/tenders/$TENDER_ID/report"
```
Or retrieve raw HTML via curl:
```bash
curl -s "http://localhost:8080/tenders/$TENDER_ID/report"
```

---

## Preflight Verification

Verify verdict stability across multiple runs:

```bash
# Generate synthetic bidder fixture PDFs (if not already present)
.venv/bin/python scripts/make_fixtures.py

# Run preflight against local server or deployed URL
.venv/bin/python scripts/preflight.py --base-url http://localhost:8080 --runs 10
```

---

## Cloud Run Deployment

Deploy to Google Cloud Run (region `asia-south1`):

```bash
gcloud run deploy gem-bid-evaluator \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 3 \
  --memory 1Gi \
  --timeout 300 \
  --set-env-vars GEMINI_MODEL=gemini-3.8-flash,GEMINI_FALLBACK_MODEL=gemini-3.5-flash-lite,GEMINI_API_KEY=<paste key at deploy time, never commit it>
```

> **Deployment Notes:**
> - The `gemini_api_key.txt` file is for local development only. On Cloud Run the key is supplied via the `GEMINI_API_KEY` environment variable. The file is excluded by `.dockerignore` so it is never baked into the container image.
> - Keep `--min-instances 1` during live judging to eliminate cold starts. After judging, redeploy with `--min-instances 0` to stop idle billing.

