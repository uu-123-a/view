"""Small security helpers without external services."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from flask import Flask, jsonify, request


class LoginRateLimiter:
    def __init__(self, limit: int = 10, window_seconds: int = 300) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.attempts: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self.lock:
            bucket = self.attempts[key]
            while bucket and now - bucket[0] > self.window_seconds:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return False
            bucket.append(now)
            return True


login_limiter = LoginRateLimiter()


def register_security(app: Flask) -> None:
    @app.before_request
    def protect_login_routes():
        if request.method == "POST" and request.path in {"/api/auth/login", "/api/admin/auth/login"}:
            key = f"{request.remote_addr or 'unknown'}:{request.path}"
            if not login_limiter.allow(key):
                return jsonify({"error": "登录尝试过于频繁，请五分钟后再试。"}), 429
        return None

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(self), microphone=(self), geolocation=()")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self' ws: wss:; style-src 'self' 'unsafe-inline'; script-src 'self'")
        return response
