"""Authentication endpoints blueprint for AI-PiracyGuard API.

Handles user registration, login verification, and token exchange.
"""

from flask import Blueprint, request, jsonify, g

from piracyguard.database.session import session_scope
from piracyguard.services.auth_service import AuthService
from piracyguard.exceptions import ValidationError
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)

auth_bp = Blueprint("auth", __name__)
auth_service = AuthService()


@auth_bp.route("/login", methods=["POST"])
def login() -> tuple:
    """Authenticate credentials and return JWT tokens.

    Endpoint: POST /api/v1/auth/login
    Request payload: { "username": "admin", "password": "..." }
    """
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        raise ValidationError("Username and password are required fields.")

    username = data["username"]
    password = data["password"]

    client_ip = request.remote_addr
    user_agent = request.headers.get("User-Agent")

    with session_scope() as db:
        res = auth_service.authenticate_user(
            db,
            username=username,
            password=password,
            ip_address=client_ip,
            user_agent=user_agent
        )

    return jsonify(res), 200
