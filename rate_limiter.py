"""
rate_limiter.py — Sliding-window, in-memory rate limiter
"""

import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    """
    Sliding-window rate limiter.

    Tracks per-key request timestamps in a deque.
    Evicts timestamps older than `window_seconds` on every check.
    Thread-safe via a simple Lock.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def _evict_old(self, key: str) -> None:
        """Remove timestamps outside the current window (lock must be held)."""
        cutoff = time.monotonic() - self.window_seconds
        window = self._windows[key]
        while window and window[0] < cutoff:
            window.popleft()

    def is_allowed(self, key: str) -> bool:
        """Return True and record the request if within limit; False otherwise."""
        with self._lock:
            self._evict_old(key)
            window = self._windows[key]
            if len(window) < self.max_requests:
                window.append(time.monotonic())
                return True
            return False

    def remaining(self, key: str) -> int:
        """Return the number of remaining requests in the current window."""
        with self._lock:
            self._evict_old(key)
            return max(0, self.max_requests - len(self._windows[key]))

    def retry_after(self, key: str) -> int:
        """Return seconds until the oldest request leaves the window."""
        with self._lock:
            window = self._windows[key]
            if not window:
                return 0
            oldest = window[0]
            return max(0, int(self.window_seconds - (time.monotonic() - oldest)) + 1)
