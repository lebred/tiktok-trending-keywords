"""
Subscription model for Stripe subscription management.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enumeration."""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"


class Subscription(BaseModel):
    """Subscription model for tracking Stripe subscriptions."""
    
    __tablename__ = "subscriptions"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    stripe_subscription_id = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(
        SQLEnum(SubscriptionStatus),
        nullable=False,
        default=SubscriptionStatus.INCOMPLETE
    )
    current_period_end = Column(DateTime, nullable=True)
    
    # Relationship to user
    user = relationship("User", back_populates="subscriptions")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, status={self.status.value})>"

