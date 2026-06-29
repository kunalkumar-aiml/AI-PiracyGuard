"""JWT authentication middleware for AI-PiracyGuard API.

Provides decorators for route protection with role-based access control.

Usage:
    from piracyguard.api.middleware.auth import token_required, role_required

    @app.route("/admin-only")
    @token_required
    @role_required("admin")
    def admin_endpoint():
        ...
"""

import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, Dict, Optional

import jwt
from flask import g, request, current_app

from piracyguard.exceptions import (
    TokenExpiredError,
    TokenInvalidError,
    TokenMissingError,
    InsufficientPermissionsError,
)
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)

# Configuration constants
_JWT_ALGORITHM: str = "HS256"
_ACCESS_TOKEN_EXPIRES_MINUTES: int = 120
_REFRESH_TOKEN_EXPIRES_DAYS: int = 30


def _get_secret_key() -> str:
    """Helper to dynamically fetch the secret key from Flask current_app config or env."""
    try:
        return current_app.config["SECRET_KEY"]
    except RuntimeError:
        # Fallback if accessed outside of application context
        return os.environ.get("SECRET_KEY", "change-me-in-production")


def create_access_token(
    user_id: int,
    username: str,
    role: str,
    expires_minutes: Optional[int] = None,
) -> str:
    """Create a JWT access token.

    Args:
        user_id: User's database ID.
        username: User's username.
        role: User's role (admin, analyst, viewer).
        expires_minutes: Override default expiration.

    Returns:
        Encoded JWT token string.
    """
    exp_minutes = expires_minutes or _ACCESS_TOKEN_EXPIRES_MINUTES
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=exp_minutes),
    }
    token = jwt.encode(payload, _get_secret_key(), algorithm=_JWT_ALGORITHM)
    return token


def create_refresh_token(
    user_id: int,
    expires_days: Optional[int] = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        user_id: User's database ID.
        expires_days: Override default expiration.

    Returns:
        Encoded JWT refresh token string.
    """
    exp_days = expires_days or _REFRESH_TOKEN_EXPIRES_DAYS
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=exp_days),
    }
    token = jwt.encode(payload, _get_secret_key(), algorithm=_JWT_ALGORITHM)
    return token


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string.

    Returns:
        Decoded token payload.

    Raises:
        TokenExpiredError: If the token has expired.
        TokenInvalidError: If the token is malformed or tampered with.
    """
    try:
        secret = _get_secret_key()
        payload = jwt.decode(token, secret, algorithms=[_JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as e:
        logger.warning(f"Expired signature: {e}")
        raise TokenExpiredError()
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {type(e).__name__}: {e}")
        raise TokenInvalidError()


def token_required(f: Callable) -> Callable:
    """Decorator to require a valid JWT access token.

    Extracts the token from the Authorization header (Bearer scheme).
    Sets `g.current_user` with the decoded token payload.

    Usage:
        @app.route("/protected")
        @token_required
        def protected_route():
            user = g.current_user
            return jsonify({"user": user["username"]})
    """

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            raise TokenMissingError()

        # Support both "Bearer <token>" and raw "<token>" formats
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        elif len(parts) == 1:
            token = parts[0]
        else:
            raise TokenInvalidError()

        payload = decode_token(token)

        # Ensure it's an access token (not a refresh token)
        if payload.get("type") != "access":
            raise TokenInvalidError()

        # Store user info in Flask's g context
        g.current_user = {
            "id": int(payload.get("sub")) if payload.get("sub") is not None else None,
            "username": payload.get("username"),
            "role": payload.get("role"),
        }

        logger.debug(
            "Authenticated request",
            extra={
                "user": payload.get("username"),
                "request_id": request.headers.get("X-Request-ID"),
            },
        )

        return f(*args, **kwargs)

    return decorated


def role_required(*allowed_roles: str) -> Callable:
    """Decorator to require specific user roles.

    Must be used AFTER @token_required.

    Args:
        *allowed_roles: One or more role strings that are permitted.

    Usage:
        @app.route("/admin")
        @token_required
        @role_required("admin")
        def admin_only():
            ...

        @app.route("/analysts")
        @token_required
        @role_required("admin", "analyst")
        def analyst_route():
            ...
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            current_user = getattr(g, "current_user", None)
            if current_user is None:
                raise TokenMissingError()

            user_role = current_user.get("role", "")
            if user_role not in allowed_roles:
                logger.warning(
                    "Insufficient permissions",
                    extra={
                        "user": current_user.get("username"),
                        "required_roles": list(allowed_roles),
                        "user_role": user_role,
                    },
                )
                raise InsufficientPermissionsError(
                    required_role=", ".join(allowed_roles)
                )

            return f(*args, **kwargs)

        return decorated

    return decorator
