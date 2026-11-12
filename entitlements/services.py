"""
Business logic for entitlements.

Keep views thin: views handle the HTTP request/response, and call functions
defined here to do the actual work.
"""
from datetime import timedelta
from django.utils import timezone
from .models import Subscription

YEARLY_SUBSCRIPTION_DAYS = 365

def active_subscriptions(user):
    return Subscription.objects.filter(
        user=user, revoked_at__isnull=True, expire_date__gt=timezone.now()
    )

#1. give user a product -> which means create a subscription for the relationship between user and product
def grant_product(user, product):
    """
    Grants a product to a user by creating a subscription.
    assumptions:
    1. Each subscription expires after a year (365 days) from the granted date.
    2. A user can have only one active subscription for a product at a time (only enforced in the service layer, not in the database).
    3. If a user's subscription is revoked or expired, they can be granted the product again in a new subscription entry. This means that we can audit the history of subscriptions for a user and product.
    """

    # Check if the user already has an active subscription for the product
    active_subscription = active_subscriptions(user).filter(product=product).exists()

    if active_subscription:
        raise ValueError(f"User {user.username} already has an active subscription for {product.name}.")

    # Create a new subscription (or it could mean that the user's subscription was revoked or expired, and we are granting it again)
    subscription = Subscription.objects.create(user=user, product=product, expire_date=timezone.now() + timedelta(days=YEARLY_SUBSCRIPTION_DAYS))
    return subscription

#2. revoke product from user
def revoke_product(user, product):
    """
    Revokes a product from a user by marking the subscription as revoked.
    """
    try:
        subscription = active_subscriptions(user).get(product=product)
        subscription.revoked_at = timezone.now()
        subscription.save()
        return subscription
    except Subscription.DoesNotExist: # Come back to make these errors more specific if time allows
        raise ValueError(f"User {user.username} does not have an active subscription for {product.name}.")

#3. get user entitlements -> get a user's benefits based on their active subscriptions
def get_user_entitlements(user):
    """
    Retrieves the benefits associated with a user's active subscriptions.
    note: this query is not optimized for performance, but it is simple and easy to understand. I would like to optimize it later if time allows.
    """
    subscriptions = active_subscriptions(user)

    benefits = set()
    for sub in subscriptions:
        product_benefits = sub.product.benefits.all()
        benefits.update(product_benefits)

    return list(benefits)
