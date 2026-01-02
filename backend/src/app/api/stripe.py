"""
Stripe API endpoints for subscription management.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import stripe

from app.database import get_db
from app.models.user import User, SubscriptionTier
from app.models.subscription import Subscription, SubscriptionStatus
from app.api.dependencies import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stripe", tags=["stripe"])

# Initialize Stripe
if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


class CreateCheckoutRequest(BaseModel):
    """Create checkout session request."""

    success_url: str
    cancel_url: str


class CreateCheckoutResponse(BaseModel):
    """Create checkout session response."""

    checkout_url: str
    session_id: str


@router.post("/create-checkout", response_model=CreateCheckoutResponse)
async def create_checkout(
    request: CreateCheckoutRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create Stripe checkout session for subscription.

    Requires authentication.
    """
    if not settings.stripe_secret_key or not settings.stripe_price_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe not configured",
        )

    try:
        # Create or get Stripe customer
        customer_id = user.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={"user_id": str(user.id)},
            )
            customer_id = customer.id
            user.stripe_customer_id = customer_id
            db.commit()

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": settings.stripe_price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={"user_id": str(user.id)},
        )

        return CreateCheckoutResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id,
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe error: {str(e)}",
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Handle Stripe webhook events.

    Processes subscription events (created, updated, deleted, etc.)
    Note: This endpoint should be configured in Stripe dashboard with the webhook secret.
    """
    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook secret not configured",
        )

    # Get raw body for signature verification
    body = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            body, sig_header, settings.stripe_webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle event
    event_type = event["type"]
    data = event["data"]["object"]

    logger.info(f"Processing Stripe webhook event: {event_type}")

    try:
        if event_type == "checkout.session.completed":
            # Subscription created
            customer_id = data.get("customer")
            subscription_id = data.get("subscription")
            user_id = data.get("metadata", {}).get("user_id")

            if user_id and subscription_id:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if user:
                    # Update user subscription tier
                    user.subscription_tier = SubscriptionTier.PAID

                    # Get subscription details from Stripe
                    subscription = stripe.Subscription.retrieve(subscription_id)

                    # Create or update subscription record
                    db_subscription = (
                        db.query(Subscription)
                        .filter(Subscription.stripe_subscription_id == subscription_id)
                        .first()
                    )

                    if not db_subscription:
                        db_subscription = Subscription(
                            user_id=user.id,
                            stripe_subscription_id=subscription_id,
                            status=SubscriptionStatus.ACTIVE,
                            current_period_end=subscription.current_period_end,
                        )
                        db.add(db_subscription)
                    else:
                        db_subscription.status = SubscriptionStatus.ACTIVE
                        db_subscription.current_period_end = (
                            subscription.current_period_end
                        )

                    db.commit()
                    logger.info(f"Subscription activated for user {user_id}")

        elif event_type in [
            "customer.subscription.updated",
            "customer.subscription.deleted",
        ]:
            # Subscription updated or deleted
            subscription_id = data.get("id")
            status_str = data.get("status", "").upper()

            db_subscription = (
                db.query(Subscription)
                .filter(Subscription.stripe_subscription_id == subscription_id)
                .first()
            )

            if db_subscription:
                # Map Stripe status to our status
                status_map = {
                    "ACTIVE": SubscriptionStatus.ACTIVE,
                    "CANCELED": SubscriptionStatus.CANCELED,
                    "PAST_DUE": SubscriptionStatus.PAST_DUE,
                    "UNPAID": SubscriptionStatus.UNPAID,
                    "TRIALING": SubscriptionStatus.TRIALING,
                    "INCOMPLETE": SubscriptionStatus.INCOMPLETE,
                    "INCOMPLETE_EXPIRED": SubscriptionStatus.INCOMPLETE_EXPIRED,
                }

                db_subscription.status = status_map.get(
                    status_str, SubscriptionStatus.INCOMPLETE
                )
                db_subscription.current_period_end = data.get("current_period_end")

                # Update user tier if subscription is not active
                if db_subscription.status != SubscriptionStatus.ACTIVE:
                    user = (
                        db.query(User)
                        .filter(User.id == db_subscription.user_id)
                        .first()
                    )
                    if user:
                        user.subscription_tier = SubscriptionTier.FREE

                db.commit()
                logger.info(f"Subscription {subscription_id} updated to {status_str}")

    except Exception as e:
        logger.error(f"Error processing webhook event {event_type}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook",
        )

    return {"status": "success"}


@router.get("/subscription-status")
async def get_subscription_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current user's subscription status.

    Requires authentication.
    """
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )

    return {
        "subscription_tier": user.subscription_tier.value,
        "has_active_subscription": (
            subscription is not None
            and subscription.status == SubscriptionStatus.ACTIVE
        ),
        "subscription": (
            {
                "status": subscription.status.value if subscription else None,
                "current_period_end": (
                    subscription.current_period_end.isoformat()
                    if subscription and subscription.current_period_end
                    else None
                ),
            }
            if subscription
            else None
        ),
    }
