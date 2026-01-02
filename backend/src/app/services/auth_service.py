"""
Authentication service for user management and magic links.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User, SubscriptionTier
from app.utils.auth import create_access_token, create_magic_link_token, verify_magic_link_token
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self):
        """Initialize auth service."""
        self.email_service = EmailService()

    async def request_magic_link(
        self, db: Session, email: str, frontend_url: str = "http://localhost:3000"
    ) -> bool:
        """
        Request magic link for email authentication.

        Args:
            db: Database session
            email: User email address
            frontend_url: Frontend URL for magic link

        Returns:
            True if magic link was sent, False otherwise
        """
        # Normalize email
        email = email.lower().strip()

        # Get or create user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                subscription_tier=SubscriptionTier.FREE,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {email}")

        # Generate magic link token
        magic_link_token = create_magic_link_token(email)

        # Send email
        success = await self.email_service.send_magic_link(
            email, magic_link_token, frontend_url
        )

        if success:
            logger.info(f"Magic link sent to {email}")
        else:
            logger.warning(f"Failed to send magic link to {email}")

        return success

    def verify_magic_link(self, db: Session, token: str) -> Optional[dict]:
        """
        Verify magic link token and create access token.

        Args:
            db: Database session
            token: Magic link token

        Returns:
            Dictionary with access_token and user info, or None if invalid
        """
        # Verify token
        email = verify_magic_link_token(token)
        if not email:
            logger.warning("Invalid magic link token")
            return None

        # Get user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"User not found for email: {email}")
            return None

        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "subscription_tier": user.subscription_tier.value,
            },
        }

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    def is_paid_user(self, db: Session, user_id: int) -> bool:
        """
        Check if user has paid subscription.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            True if user has paid subscription, False otherwise
        """
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False

        # Check subscription tier
        if user.subscription_tier == SubscriptionTier.PAID:
            return True

        # Check active subscription
        from app.models.subscription import Subscription, SubscriptionStatus

        active_subscription = (
            db.query(Subscription)
            .filter(Subscription.user_id == user_id)
            .filter(Subscription.status == SubscriptionStatus.ACTIVE)
            .first()
        )

        return active_subscription is not None

