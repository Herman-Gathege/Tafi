"""Passwords, opaque tokens and the session cookie's JWT."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error

from app.core.config import get_settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a password with argon2."""
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Return True when the password matches the stored hash."""
    try:
        return _hasher.verify(password_hash, password)
    except (Argon2Error, ValueError):
        return False


def generate_token() -> str:
    """A high-entropy token for an invite or password reset link."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Store tokens hashed: they are random, so a plain digest is enough."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session_token(user_id: uuid.UUID, *, now: datetime | None = None) -> str:
    """Sign a short-lived session JWT for a user."""
    settings = get_settings()
    issued = now or datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(issued.timestamp()),
        "exp": int((issued + timedelta(hours=settings.session_ttl_hours)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_session_token(token: str) -> uuid.UUID:
    """Return the user id from a session JWT, or raise jwt.InvalidTokenError."""
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    return uuid.UUID(str(payload["sub"]))
