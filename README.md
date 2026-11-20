# BidParakh: GeM Bid Evaluator

> Officer-side GeM bid evaluation: AI reads, code decides.

BidParakh helps government procurement officers evaluate technical bids submitted on the GeM portal. It resolves corrigenda criteria, extracts null-and-void lists, validates evidence quotes against PDF text layers, and executes deterministic rule evaluations.

## Development Setup

```bash
# 1. Environment and dependencies
.venv/bin/pip install -r requirements.txt

# 2. Run unit tests
.venv/bin/python -m pytest tests/unit -q

# 3. Run application server
.venv/bin/uvicorn app.main:app --port 8080 --reload
```
