"""
session_manager.py — In-memory session tracking
"""

import uuid
from datetime import datetime, timezone
from threading import Lock
from typing import Optional


class SessionManager:
    """
    Lightweight in-memory session store.
    Stores metadata per session_id including request count and queried sectors.
    """

    def __init__(self):
        self._sessions: dict[str, dict] = {}
        self._lock = Lock()

    def create(self, username: str) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        with self._lock:
            self._sessions[session_id] = {
                "username": username,
                "requests_made": 0,
                "sectors_queried": [],
                "created_at": now,
                "last_active": now,
            }
        return session_id

    def touch(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["last_active"] = datetime.now(tz=timezone.utc)

    def record_request(self, session_id: str, sector: str) -> None:
        with self._lock:
            if session_id in self._sessions:
                s = self._sessions[session_id]
                s["requests_made"] += 1
                if sector not in s["sectors_queried"]:
                    s["sectors_queried"].append(sector)
                s["last_active"] = datetime.now(tz=timezone.utc)

    def get(self, session_id: str) -> Optional[dict]:
        with self._lock:
            return self._sessions.get(session_id)
