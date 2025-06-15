"""Billing and subscription management routes."""

import os
from datetime import datetime, timedelta
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from openhands.storage.data_models.subscription import (
    SUBSCRIPTION_LIMITS,
    SUBSCRIPTION_PRICING,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
    UsageMetrics,
)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

app = APIRouter(prefix='/api/billing')


def get_current_user() -> str:
    """Placeholder function for user authentication.

    This should be replaced with the actual user authentication implementation.
    """
    return 'placeholder_user_id'


class CreateCheckoutSessionRequest(BaseModel):
    """Request model for creating checkout session."""

    tier: SubscriptionTier
    success_url: str
    cancel_url: str


class CreateCheckoutSessionResponse(BaseModel):
    """Response model for checkout session."""

    checkout_url: str


class SubscriptionResponse(BaseModel):
    """Response model for subscription info."""

    subscription: Subscription
    usage_percentage: dict


class UsageResponse(BaseModel):
    """Response model for usage info."""

    current_usage: UsageMetrics
    limits: dict
    usage_percentage: dict


@app.post('/create-subscription-checkout', response_model=CreateCheckoutSessionResponse)
async def create_subscription_checkout(
    request: CreateCheckoutSessionRequest, user_id: str = Depends(get_current_user)
):
    """Create a Stripe checkout session for subscription."""
    try:
        # Get or create Stripe customer
        customer = await get_or_create_stripe_customer(user_id)

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'OpenHands {request.tier.value.title()} Plan',
                            'description': f'Monthly subscription to OpenHands {request.tier.value.title()} tier',
                        },
                        'unit_amount': SUBSCRIPTION_PRICING[request.tier],
                        'recurring': {
                            'interval': 'month',
                        },
                    },
                    'quantity': 1,
                }
            ],
            mode='subscription',
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                'user_id': user_id,
                'tier': request.tier.value,
            },
        )

        return CreateCheckoutSessionResponse(checkout_url=checkout_session.url)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/subscription', response_model=SubscriptionResponse)
async def get_subscription(user_id: str = Depends(get_current_user)):
    """Get current subscription information."""
    subscription = await get_user_subscription(user_id)
    if not subscription:
        # Create free tier subscription
        subscription = await create_free_subscription(user_id)

    usage_percentage = calculate_usage_percentage(subscription)

    return SubscriptionResponse(
        subscription=subscription, usage_percentage=usage_percentage
    )


@app.get('/usage', response_model=UsageResponse)
async def get_usage(user_id: str = Depends(get_current_user)):
    """Get current usage information."""
    subscription = await get_user_subscription(user_id)
    if not subscription:
        subscription = await create_free_subscription(user_id)

    usage_percentage = calculate_usage_percentage(subscription)

    return UsageResponse(
        current_usage=subscription.current_usage,
        limits=subscription.limits.dict(),
        usage_percentage=usage_percentage,
    )


@app.post('/cancel-subscription')
async def cancel_subscription(user_id: str = Depends(get_current_user)):
    """Cancel current subscription."""
    subscription = await get_user_subscription(user_id)
    if not subscription or not subscription.stripe_subscription_id:
        raise HTTPException(status_code=404, detail='No active subscription found')

    try:
        # Cancel in Stripe
        stripe.Subscription.modify(
            subscription.stripe_subscription_id, cancel_at_period_end=True
        )

        # Update local subscription
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.utcnow()
        await update_subscription(subscription)

        return {'message': 'Subscription cancelled successfully'}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post('/webhook')
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks."""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid payload')
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail='Invalid signature')

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        await handle_checkout_completed(event['data']['object'])
    elif event['type'] == 'invoice.payment_succeeded':
        await handle_payment_succeeded(event['data']['object'])
    elif event['type'] == 'invoice.payment_failed':
        await handle_payment_failed(event['data']['object'])
    elif event['type'] == 'customer.subscription.deleted':
        await handle_subscription_deleted(event['data']['object'])

    return {'status': 'success'}


# Helper functions
async def get_or_create_stripe_customer(user_id: str):
    """Get or create a Stripe customer for the user."""
    # Implementation would depend on your user storage system
    # This is a placeholder
    customers = stripe.Customer.list(metadata={'user_id': user_id})

    if customers.data:
        return customers.data[0]
    else:
        return stripe.Customer.create(metadata={'user_id': user_id})


async def get_user_subscription(user_id: str) -> Optional[Subscription]:
    """Get user's current subscription."""
    # Implementation would depend on your storage system
    # This is a placeholder
    pass


async def create_free_subscription(user_id: str) -> Subscription:
    """Create a free tier subscription for new user."""
    now = datetime.utcnow()
    subscription = Subscription(
        id=f'sub_{user_id}_{int(now.timestamp())}',
        user_id=user_id,
        tier=SubscriptionTier.FREE,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        limits=SUBSCRIPTION_LIMITS[SubscriptionTier.FREE],
        created_at=now,
        updated_at=now,
    )

    # Save to storage
    await save_subscription(subscription)
    return subscription


async def save_subscription(subscription: Subscription):
    """Save subscription to storage."""
    # Implementation would depend on your storage system
    pass


async def update_subscription(subscription: Subscription):
    """Update subscription in storage."""
    # Implementation would depend on your storage system
    pass


def calculate_usage_percentage(subscription: Subscription) -> dict:
    """Calculate usage percentage for each metric."""
    usage = subscription.current_usage
    limits = subscription.limits

    percentages = {}

    if limits.max_conversations_per_month:
        percentages['conversations'] = min(
            100, (usage.ai_conversations / limits.max_conversations_per_month) * 100
        )

    if limits.max_runtime_hours_per_month:
        percentages['runtime'] = min(
            100, (usage.runtime_hours / limits.max_runtime_hours_per_month) * 100
        )

    if limits.max_storage_gb:
        percentages['storage'] = min(
            100, (usage.storage_gb / limits.max_storage_gb) * 100
        )

    return percentages


async def handle_checkout_completed(session):
    """Handle successful checkout completion."""
    user_id = session['metadata']['user_id']
    tier = SubscriptionTier(session['metadata']['tier'])

    # Create or update subscription
    subscription = await get_user_subscription(user_id)
    if not subscription:
        subscription = await create_free_subscription(user_id)

    subscription.tier = tier
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.stripe_subscription_id = session['subscription']
    subscription.stripe_customer_id = session['customer']
    subscription.limits = SUBSCRIPTION_LIMITS[tier]
    subscription.amount = SUBSCRIPTION_PRICING[tier]
    subscription.updated_at = datetime.utcnow()

    await update_subscription(subscription)


async def handle_payment_succeeded(invoice):
    """Handle successful payment."""
    invoice['subscription']
    # Update subscription status and period
    pass


async def handle_payment_failed(invoice):
    """Handle failed payment."""
    invoice['subscription']
    # Update subscription status to past_due
    pass


async def handle_subscription_deleted(subscription):
    """Handle subscription deletion."""
    # Downgrade to free tier
    pass
