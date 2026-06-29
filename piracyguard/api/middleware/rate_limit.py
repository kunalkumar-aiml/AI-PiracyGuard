"""Rate limiting middleware for AI-PiracyGuard API.

Provides simple in-memory rate limiting. For production, integrate
with Redis-based rate limiting via Flask-Limiter.
"""

import time
from collections import defaultdict
from functools import wraps
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Tuple

from flask import request, jsonify, Response

from piracyguard.exceptions import RateLimitExceededError
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Thread-safe in-memory rate limiter using sliding window algorithm.

    For production deployments, replace with Redis-based implementation.
    """

    def __init__(self) -> None:
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def _get_client_key(self) -> str:
        """Get a unique key for the current client."""
        # Use IP address + endpoint as the rate limit key
        client_ip = request.remote_addr or "unknown"
        endpoint = request.endpoint or "unknown"
        return f"{client_ip}:{endpoint}"

    def _cleanup_old_entries(self, key: str, window_seconds: int) -> None:
        """Remove request timestamps older than the time window."""
        cutoff = time.time() - window_seconds
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > cutoff
        ]

    def check_rate_limit(
        self,
        max_requests: int = 100,
        window_seconds: int = 3600,
    ) -> Tuple[bool, int]:
        """Check if the current request is within rate limits.

        Args:
            max_requests: Maximum requests allowed in the window.
            window_seconds: Time window in seconds.

        Returns:
            Tuple of (is_allowed, remaining_requests).
        """
        key = self._get_client_key()

        with self._lock:
            self._cleanup_old_entries(key, window_seconds)
            current_count = len(self._requests[key])

            if current_count >= max_requests:
                return False, 0

            self._requests[key].append(time.time())
            return True, max_requests - current_count - 1


# Module-level singleton
_limiter = RateLimiter()


def rate_limit(
    max_requests: int = 100,
    window_seconds: int = 3600,
) -> Callable:
    """Decorator to apply rate limiting to a route.

    Args:
        max_requests: Maximum requests per window.
        window_seconds: Window duration in seconds.

    Usage:
        @app.route("/api/scan")
        @rate_limit(max_requests=10, window_seconds=60)
        def scan():
            ...
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            allowed, remaining = _limiter.check_rate_limit(
                max_requests=max_requests,
                window_seconds=window_seconds,
            )

            if not allowed:
                logger.warning(
                    "Rate limit exceeded",
                    extra={
                        "client_ip": request.remote_addr,
                        "endpoint": request.endpoint,
                    },
                )
                raise RateLimitExceededError(retry_after=window_seconds)

            response = f(*args, **kwargs)

            # Add rate limit headers if response is a tuple or Response
            if isinstance(response, tuple):
                resp_obj, status_code = response[0], response[1] if len(response) > 1 else 200
                if hasattr(resp_obj, "headers"):
                    resp_obj.headers["X-RateLimit-Limit"] = str(max_requests)
                    resp_obj.headers["X-RateLimit-Remaining"] = str(remaining)
                    resp_obj.headers["X-RateLimit-Window"] = str(window_seconds)
            elif hasattr(response, "headers"):
                response.headers["X-RateLimit-Limit"] = str(max_requests)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Window"] = str(window_seconds)

            return response

        return decorated

    return decorator
