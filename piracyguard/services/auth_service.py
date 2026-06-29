"""Authentication and user management services.

Handles password hashing, user registration, role checks, and JWT generation.
"""

import hashlib
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from piracyguard.config import settings
from piracyguard.database.models import User, UserRole, AuditLog, AuditAction
from piracyguard.exceptions import AuthenticationError
from piracyguard.api.middleware.auth import create_access_token, create_refresh_token
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


class AuthService:
    """Authentication service for validating credentials and managing sessions."""

    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> str:
        """Hash a password using secure PBKDF2-HMAC-SHA256.

        Args:
            password: Plaintext password.
            salt: Optional salt. If None, generates a new random salt.

        Returns:
            String containing salt and hash in format: pbkdf2_sha256$iterations$salt_hex$hash_hex
        """
        iterations = 100000
        if salt is None:
            salt = os.urandom(16)
        
        pw_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )
        
        return f"pbkdf2_sha256${iterations}${salt.hex()}${pw_hash.hex()}"

    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a stored PBKDF2 hash.

        Args:
            password: Plaintext password.
            hashed_password: Stored hash string.

        Returns:
            True if match, False otherwise.
        """
        if not hashed_password or "$" not in hashed_password:
            return False

        try:
            algorithm, iterations, salt_hex, hash_hex = hashed_password.split("$")
            if algorithm != "pbkdf2_sha256":
                return False
            
            salt = bytes.fromhex(salt_hex)
            test_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                int(iterations)
            )
            return test_hash.hex() == hash_hex
        except (ValueError, TypeError):
            return False

    def authenticate_user(
        self,
        db: Session,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate user credentials and generate access/refresh tokens.

        Args:
            db: Database session.
            username: Target username.
            password: Target password.
            ip_address: Client IP address (for auditing).
            user_agent: Client User Agent (for auditing).

        Returns:
            Dict containing access_token, refresh_token, and user details.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        logger.info("Attempting user authentication", extra={"username": username})

        # Query user
        user = db.query(User).filter(User.username == username, User.is_active == True).first()

        # Handle fallback admin credentials (defined in config/env)
        # If user table is empty and we query 'admin', we can seed the admin user or authenticate directly
        is_fallback_match = False
        if username == settings.ADMIN_USERNAME:
            if settings.ADMIN_PASSWORD_HASH:
                # If pre-hashed admin password exists in env
                is_fallback_match = self.verify_password(password, settings.ADMIN_PASSWORD_HASH)
            else:
                # If plaintext admin password in env/settings (default admin)
                # To be secure, settings default could be 'admin' but overridden in .env
                # Let's check environment variable directly
                env_admin_pass = os.environ.get("ADMIN_PASSWORD", "admin")
                is_fallback_match = (password == env_admin_pass)

            # Auto-seed admin user if they don't exist in DB yet
            if is_fallback_match and not user:
                logger.info("Seeding admin user into database from environment config")
                user = User(
                    username=username,
                    password_hash=self.hash_password(password),
                    role=UserRole.ADMIN,
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)

        if not user or (not is_fallback_match and not self.verify_password(password, user.password_hash)):
            logger.warning("Failed login attempt", extra={"username": username})
            raise AuthenticationError("Invalid username or password.")

        # Update last login timestamp
        user.last_login = datetime.now(timezone.utc)
        db.commit()

        # Generate tokens
        access_token = create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role.value
        )
        refresh_token = create_refresh_token(user_id=user.id)

        # Log audit trail
        audit = AuditLog(
            action=AuditAction.LOGIN,
            user_id=user.id,
            resource_type="User",
            resource_id=str(user.uuid),
            ip_address=ip_address,
            user_agent=user_agent,
            details={"username": user.username}
        )
        db.add(audit)
        db.commit()

        logger.info("User authenticated successfully", extra={"username": username, "role": user.role.value})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "uuid": user.uuid,
                "username": user.username,
                "role": user.role.value
            }
        }
