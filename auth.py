"""
auth.py — JWT guest-token creation and verification
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "trade-api-super-secret-change-in-prod-2024")
ALGORITHM: str = "HS256"
TOKEN_EXPIRE_MINUTES: int = 60


def create_guest_token(subject: str, session_id: str) -> str:
    """
    Create a signed JWT for the given username and session_id.
    Expires after TOKEN_EXPIRE_MINUTES.
    """
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": subject,
        "session_id": session_id,
        "iat": now,
        "exp": now + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
        "type": "guest",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT.
    Returns the payload dict on success, None on any failure.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
