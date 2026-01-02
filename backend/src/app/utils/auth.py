"""
Authentication utilities for JWT token generation and validation.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

logger = logging.getLogger(__name__)

# Password hashing context (for future use if needed)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Dictionary with user data (e.g., {"sub": user_id, "email": email})
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    return encoded_jwt


def create_magic_link_token(email: str, expires_minutes: int = 15) -> str:
    """
    Create magic link token for email authentication.

    Args:
        email: User email address
        expires_minutes: Token expiration time in minutes (default: 15)

    Returns:
        Encoded JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    
    to_encode = {
        "email": email,
        "type": "magic_link",
        "exp": expire,
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


def verify_magic_link_token(token: str) -> Optional[str]:
    """
    Verify magic link token and return email.

    Args:
        token: Magic link token

    Returns:
        Email address if token is valid, None otherwise
    """
    payload = verify_token(token)
    
    if not payload:
        return None
    
    if payload.get("type") != "magic_link":
        logger.warning("Token is not a magic link token")
        return None
    
    email = payload.get("email")
    if not email:
        return None
    
    return email


def get_user_id_from_token(token: str) -> Optional[int]:
    """
    Extract user ID from access token.

    Args:
        token: JWT access token

    Returns:
        User ID or None if invalid
    """
    payload = verify_token(token)
    
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if user_id:
        try:
            return int(user_id)
        except (ValueError, TypeError):
            return None
    
    return None

