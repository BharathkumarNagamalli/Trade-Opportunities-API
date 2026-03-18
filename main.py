"""
Trade Opportunities API
=======================
FastAPI service that analyzes market data and provides trade opportunity
insights for specific sectors in India.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth import create_guest_token, verify_token
from data_collector import DataCollector
from ai_analyzer import AIAnalyzer
from rate_limiter import RateLimiter
from models import (
    AnalysisResponse,
    ErrorResponse,
    GuestTokenResponse,
    SessionInfo,
    TokenRequest,
)
from session_manager import SessionManager

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("trade_api")

# ── Singletons (shared across requests) ──────────────────────────────────────
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
session_manager = SessionManager()
data_collector = DataCollector()
ai_analyzer = AIAnalyzer()

# ── App lifecycle ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Trade Opportunities API starting up…")
    yield
    logger.info("Trade Opportunities API shutting down…")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Trade Opportunities API",
    description=(
        "Analyzes market data and provides trade opportunity insights "
        "for specific sectors in India using AI-powered analysis."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Security ──────────────────────────────────────────────────────────────────
bearer_scheme = HTTPBearer()

ALLOWED_SECTORS = {
    "pharmaceuticals", "technology", "agriculture", "automotive",
    "textiles", "chemicals", "electronics", "energy", "manufacturing",
    "finance", "healthcare", "retail", "infrastructure", "defence",
    "aerospace", "food", "education", "logistics", "telecom", "tourism",
}


# ── Dependency: token validation ──────────────────────────────────────────────
async def get_current_session(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Call POST /token to get a new one.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    session_id: str = payload.get("session_id", "")
    session_manager.touch(session_id)
    return session_id


# ── Dependency: rate limiting ─────────────────────────────────────────────────
async def enforce_rate_limit(
    request: Request,
    session_id: str = Depends(get_current_session),
):
    client_key = session_id or request.client.host
    if not rate_limiter.is_allowed(client_key):
        remaining_seconds = rate_limiter.retry_after(client_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {remaining_seconds}s.",
            headers={"Retry-After": str(remaining_seconds)},
        )
    return session_id


# ── Exception handlers ────────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            status_code=exc.status_code,
        ).model_dump(mode="json"),
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post(
    "/token",
    response_model=GuestTokenResponse,
    summary="Obtain a guest bearer token",
    tags=["Authentication"],
)
async def get_token(body: TokenRequest):
    """
    Generate a guest JWT token.  
    Pass any username in the body — no password required for this guest flow.
    The token expires in **60 minutes**.
    """
    session_id = session_manager.create(body.username)
    token = create_guest_token(subject=body.username, session_id=session_id)
    logger.info("Token issued for user=%s session=%s", body.username, session_id)
    return GuestTokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=3600,
        session_id=session_id,
    )


@app.get(
    "/analyze/{sector}",
    response_model=AnalysisResponse,
    summary="Analyze trade opportunities for an Indian sector",
    tags=["Analysis"],
    responses={
        200: {"description": "Structured markdown analysis report"},
        400: {"model": ErrorResponse, "description": "Invalid sector name"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        503: {"model": ErrorResponse, "description": "External service error"},
    },
)
async def analyze_sector(
    sector: str,
    session_id: str = Depends(enforce_rate_limit),
):
    """
    Returns an AI-generated markdown report of current trade opportunities
    for the requested **sector** in India.

    **Supported sectors** (case-insensitive):  
    pharmaceuticals · technology · agriculture · automotive · textiles ·
    chemicals · electronics · energy · manufacturing · finance · healthcare ·
    retail · infrastructure · defence · aerospace · food · education ·
    logistics · telecom · tourism

    The pipeline:
    1. Validates and normalises the sector name.
    2. Scrapes current news/market data via DuckDuckGo.
    3. Sends collected context to Google Gemini for structured analysis.
    4. Returns the markdown report together with metadata.
    """
    sector_clean = sector.strip().lower().replace("-", " ").replace("_", " ")

    if sector_clean not in ALLOWED_SECTORS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Sector '{sector}' is not supported. "
                f"Valid sectors: {sorted(ALLOWED_SECTORS)}"
            ),
        )

    logger.info("Analysis request | sector=%s session=%s", sector_clean, session_id)
    t0 = time.perf_counter()

    # 1. Collect market data
    try:
        raw_data = await data_collector.fetch(sector_clean)
    except Exception as exc:
        logger.error("Data collection failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to collect market data. Please try again shortly.",
        )

    # 2. AI analysis
    try:
        report_markdown = await ai_analyzer.analyze(sector_clean, raw_data)
    except Exception as exc:
        logger.error("AI analysis failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analysis service unavailable. Please try again shortly.",
        )

    elapsed = round(time.perf_counter() - t0, 2)
    session_manager.record_request(session_id, sector_clean)
    logger.info("Analysis complete | sector=%s elapsed=%.2fs", sector_clean, elapsed)

    return AnalysisResponse(
        sector=sector_clean,
        report=report_markdown,
        sources_count=len(raw_data.get("articles", [])),
        processing_time_seconds=elapsed,
        session_id=session_id,
    )


@app.get(
    "/session",
    response_model=SessionInfo,
    summary="View current session usage statistics",
    tags=["Session"],
)
async def get_session_info(session_id: str = Depends(get_current_session)):
    """Returns usage stats and request history for the current session."""
    info = session_manager.get(session_id)
    if not info:
        raise HTTPException(status_code=404, detail="Session not found.")
    remaining = rate_limiter.remaining(session_id)
    return SessionInfo(
        session_id=session_id,
        username=info["username"],
        requests_made=info["requests_made"],
        sectors_queried=info["sectors_queried"],
        created_at=info["created_at"],
        last_active=info["last_active"],
        rate_limit_remaining=remaining,
    )


@app.get("/health", tags=["Health"], summary="Health check")
async def health():
    return {"status": "ok", "service": "Trade Opportunities API", "version": "1.0.0"}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
