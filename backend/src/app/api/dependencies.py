"""
API dependencies for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.auth import get_user_id_from_token

security = HTTPBearer(auto_error=False)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Optional dependency to get current user if authenticated.

    Returns None if not authenticated (for public endpoints with optional auth).
    """
    if not credentials:
        return None

    token = credentials.credentials
    user_id = get_user_id_from_token(token)

    if not user_id:
        return None

    auth_service = AuthService()
    return auth_service.get_user_by_id(db, user_id)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Required dependency to get current authenticated user.

    Raises HTTPException if not authenticated.
    """
    token = credentials.credentials
    user_id = get_user_id_from_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = AuthService()
    user = auth_service.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_paid_user(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to ensure user has paid subscription.

    Raises HTTPException if user is not a paid subscriber.
    """
    auth_service = AuthService()
    
    if not auth_service.is_paid_user(db, user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Paid subscription required",
        )

    return user

