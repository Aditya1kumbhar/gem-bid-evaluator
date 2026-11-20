"""FastAPI main application module."""

from fastapi import FastAPI
from app.config import get_model, is_ai_configured

app = FastAPI(
    title="BidParakh",
    description="Officer-side GeM bid evaluation: AI reads, code decides.",
    version="1.0.0",
)


@app.get("/health")
def health() -> dict:
    """Return application health status and AI configuration."""
    return {
        "status": "ok",
        "ai_configured": is_ai_configured(),
        "model": get_model(),
    }
