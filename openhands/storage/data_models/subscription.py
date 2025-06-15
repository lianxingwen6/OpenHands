"""Subscription data models for OpenHands SaaS."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SubscriptionTier(str, Enum):
    """Subscription tier enumeration."""

    FREE = 'free'
    PRO = 'pro'
    TEAM = 'team'
    ENTERPRISE = 'enterprise'


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""

    ACTIVE = 'active'
    INACTIVE = 'inactive'
    CANCELLED = 'cancelled'
    PAST_DUE = 'past_due'
    TRIALING = 'trialing'


class UsageMetrics(BaseModel):
    """Usage metrics for a subscription period."""

    ai_conversations: int = 0
    code_generations: int = 0
    runtime_hours: float = 0.0
    api_calls: int = 0
    storage_gb: float = 0.0

    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0

    # Feature usage
    code_reviews: int = 0
    document_generations: int = 0


class SubscriptionLimits(BaseModel):
    """Limits for each subscription tier."""

    max_conversations_per_month: Optional[int] = None
    max_projects: Optional[int] = None
    max_team_members: Optional[int] = None
    max_runtime_hours_per_month: Optional[float] = None
    max_api_calls_per_month: Optional[int] = None
    max_storage_gb: Optional[float] = None

    # Feature flags
    advanced_features: bool = False
    priority_support: bool = False
    api_access: bool = False
    team_collaboration: bool = False
    custom_runtime: bool = False


class Subscription(BaseModel):
    """Subscription model."""

    id: str
    user_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus

    # Stripe integration
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None

    # Billing
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime] = None

    # Usage tracking
    current_usage: UsageMetrics = UsageMetrics()
    limits: SubscriptionLimits = SubscriptionLimits()

    # Metadata
    created_at: datetime
    updated_at: datetime
    cancelled_at: Optional[datetime] = None

    # Billing amount in cents
    amount: int = 0
    currency: str = 'usd'


# Predefined subscription limits for each tier
SUBSCRIPTION_LIMITS = {
    SubscriptionTier.FREE: SubscriptionLimits(
        max_conversations_per_month=10,
        max_projects=1,
        max_team_members=1,
        max_runtime_hours_per_month=2.0,
        max_storage_gb=1.0,
        advanced_features=False,
        priority_support=False,
        api_access=False,
        team_collaboration=False,
        custom_runtime=False,
    ),
    SubscriptionTier.PRO: SubscriptionLimits(
        max_conversations_per_month=500,
        max_projects=5,
        max_team_members=1,
        max_runtime_hours_per_month=50.0,
        max_storage_gb=10.0,
        advanced_features=True,
        priority_support=True,
        api_access=False,
        team_collaboration=False,
        custom_runtime=True,
    ),
    SubscriptionTier.TEAM: SubscriptionLimits(
        max_conversations_per_month=None,  # Unlimited
        max_projects=None,  # Unlimited
        max_team_members=10,
        max_runtime_hours_per_month=200.0,
        max_storage_gb=100.0,
        advanced_features=True,
        priority_support=True,
        api_access=True,
        team_collaboration=True,
        custom_runtime=True,
    ),
    SubscriptionTier.ENTERPRISE: SubscriptionLimits(
        max_conversations_per_month=None,  # Unlimited
        max_projects=None,  # Unlimited
        max_team_members=None,  # Unlimited
        max_runtime_hours_per_month=None,  # Unlimited
        max_storage_gb=None,  # Unlimited
        advanced_features=True,
        priority_support=True,
        api_access=True,
        team_collaboration=True,
        custom_runtime=True,
    ),
}


# Pricing in cents
SUBSCRIPTION_PRICING = {
    SubscriptionTier.FREE: 0,
    SubscriptionTier.PRO: 2900,  # $29.00
    SubscriptionTier.TEAM: 9900,  # $99.00
    SubscriptionTier.ENTERPRISE: 0,  # Custom pricing
}
