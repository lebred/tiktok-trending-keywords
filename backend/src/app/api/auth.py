"""
Authentication API endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService
from app.utils.auth import get_user_id_from_token
from app.api.schemas import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    frontend_url: str = "http://localhost:3000"


class VerifyRequest(BaseModel):
    """Verify magic link request schema."""
    token: str


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    email: str
    subscription_tier: str


class LoginResponse(BaseModel):
    """Login response schema."""
    message: str
    email: str


class VerifyResponse(BaseModel):
    """Verify response schema."""
    access_token: str
    token_type: str
    user: UserResponse


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Dependency to get current authenticated user.

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session

    Returns:
        User model instance

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    user_id = get_user_id_from_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
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


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Request magic link for email authentication.

    Sends a magic link to the provided email address.
    """
    auth_service = AuthService()

    success = await auth_service.request_magic_link(
        db, request.email, request.frontend_url
    )

    if not success:
        # Don't reveal if email exists or not for security
        logger.warning(f"Failed to send magic link to {request.email}")

    # Always return success message (security best practice)
    return LoginResponse(
        message="If an account exists, a magic link has been sent to your email.",
        email=request.email,
    )


@router.post("/verify", response_model=VerifyResponse)
async def verify(
    request: VerifyRequest,
    db: Session = Depends(get_db),
):
    """
    Verify magic link token and return access token.

    Validates the magic link token and returns a JWT access token.
    """
    auth_service = AuthService()
    result = auth_service.verify_magic_link(db, request.token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link token",
        )

    return VerifyResponse(
        access_token=result["access_token"],
        token_type=result["token_type"],
        user=UserResponse(
            id=result["user"]["id"],
            email=result["user"]["email"],
            subscription_tier=result["user"]["subscription_tier"],
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user=Depends(get_current_user),
):
    """
    Get current user information.

    Requires authentication.
    """
    return UserResponse(
        id=user.id,
        email=user.email,
        subscription_tier=user.subscription_tier.value,
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint.

    Note: With JWT tokens, logout is handled client-side by removing the token.
    This endpoint exists for API consistency.
    """
    return {"message": "Logged out successfully"}

