"""
User model for authentication and subscription management.
"""

from sqlalchemy import Column, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class SubscriptionTier(str, enum.Enum):
    """Subscription tier enumeration."""
    FREE = "free"
    PAID = "paid"


class User(BaseModel):
    """User model for authentication and subscription management."""
    
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    subscription_tier = Column(
        SQLEnum(SubscriptionTier),
        default=SubscriptionTier.FREE,
        nullable=False
    )
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    
    # Relationship to subscriptions
    subscriptions = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', tier={self.subscription_tier.value})>"

