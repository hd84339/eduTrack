"""
Cryptographic security module for password hashing and JWT token processing.
Implements bcrypt adaptive password hashing (rounds >= 12) and RFC 7519 JWT utilities.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from uuid import UUID
import bcrypt
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings


class SecurityError(Exception):
    """Base exception for authentication and token errors."""
    pass


class TokenExpiredError(SecurityError):
    """Raised when a JWT has expired."""
    pass


class TokenInvalidError(SecurityError):
    """Raised when a JWT signature or structure is invalid."""
    pass


class TokenTypeMismatchError(SecurityError):
    """Raised when the token 'type' claim does not match the expected type."""
    pass


def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using adaptive bcrypt hashing with configured rounds (>= 12).
    Truncates beyond 72 bytes safely per bcrypt standard if needed.
    """
    password_bytes = plain_password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash in constant time.
    Fails safely on corrupted or malformed hashes.
    """
    try:
        password_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(
    subject: Union[str, UUID],
    extra_claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Issue an RFC 7519 JSON Web Token for user access.
    Default expiry is 30 minutes (1800s) as defined in API_DESIGN.md.
    """
    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: Union[str, UUID],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Issue a JSON Web Token for access token renewal.
    Default expiry is 7 days as configured.
    """
    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Decode, verify signature, and validate claims of a JWT.
    Enforces expiry check and optional token type check (e.g. 'access' vs 'refresh').
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "iat"]},
        )
    except ExpiredSignatureError as e:
        raise TokenExpiredError("Token has expired") from e
    except InvalidTokenError as e:
        raise TokenInvalidError("Invalid or malformed token") from e

    token_type = payload.get("type")
    if expected_type and token_type != expected_type:
        raise TokenTypeMismatchError(
            f"Invalid token type: expected '{expected_type}', got '{token_type}'"
        )

    return payload

