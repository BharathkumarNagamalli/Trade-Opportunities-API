"""
models.py — Pydantic request / response schemas
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Request bodies ────────────────────────────────────────────────────────────

class TokenRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_\-\.]+$",
        examples=["bunny_dev"],
    )

    @field_validator("username")
    @classmethod
    def no_whitespace(cls, v: str) -> str:
        if " " in v:
            raise ValueError("Username must not contain spaces.")
        return v.lower()


# ── Response bodies ───────────────────────────────────────────────────────────

class GuestTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(3600, description="Token TTL in seconds")
    session_id: str


class AnalysisResponse(BaseModel):
    sector: str
    report: str = Field(..., description="Full markdown analysis report")
    sources_count: int = Field(..., description="Number of news articles collected")
    processing_time_seconds: float
    session_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SessionInfo(BaseModel):
    session_id: str
    username: str
    requests_made: int
    sectors_queried: List[str]
    created_at: datetime
    last_active: datetime
    rate_limit_remaining: int


class ErrorResponse(BaseModel):
    error: str
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
