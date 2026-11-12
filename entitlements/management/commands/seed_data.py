from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from entitlements.models import Benefit, Product, Subscription

# Stable machine-readable code -> human-readable display name.
BENEFITS = {
    "web_access": "Web access",
    "print_magazine": "Print magazine",
    "ad_free": "Ad-free",
}

# Each product is a superset of the previous one.
PRODUCTS = {
    "Digital": (Decimal("9.99"), ["web_access"]),
    "Print": (Decimal("19.99"), ["web_access", "print_magazine"]),
    "Premium": (Decimal("29.99"), ["web_access", "print_magazine", "ad_free"]),
}

# Demo users only hold subscriptions; they have no password, so they can't log in.
DEMO_USERNAMES = ["maia", "monty", "momo"]

# Dev-only admin account for /admin/ and the browsable API.
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# (username, product, state): one story per user.
SUBSCRIPTIONS = [
    ("maia", "Premium", "active"),   # active: all three benefits
    ("monty", "Digital", "expired"),  # renewal: Digital expired...
    ("monty", "Print", "active"),     # ...then upgraded to Print
    ("momo", "Digital", "revoked"),   # revoked: no benefits
]


class Command(BaseCommand):
    help = "Seed benefits, products, demo users and subscriptions. Safe to run more than once."

    @transaction.atomic
    def handle(self, *args, **options):
        for code, name in BENEFITS.items():
            _, created = Benefit.objects.update_or_create(
                code=code, defaults={"name": name}
            )
            self.report("Benefit", code, created)

        for name, (price, benefit_codes) in PRODUCTS.items():
            product, created = Product.objects.update_or_create(
                name=name, defaults={"price": price}
            )
            # set() replaces the product's benefits with exactly this list,
            # so running it again never adds duplicate links.
            product.benefits.set(Benefit.objects.filter(code__in=benefit_codes))
            self.report("Product", name, created)

        User = get_user_model()  # the project's custom entitlements.User
        for username in DEMO_USERNAMES:
            _, created = User.objects.get_or_create(username=username)
            self.report("User", username, created)

        admin_created = not User.objects.filter(username=ADMIN_USERNAME).exists()
        if admin_created:
            User.objects.create_superuser(ADMIN_USERNAME, password=ADMIN_PASSWORD)
        self.report("Admin", ADMIN_USERNAME, admin_created)

        now = timezone.now()
        for username, product_name, state in SUBSCRIPTIONS:
            user = User.objects.get(username=username)
            product = Product.objects.get(name=product_name)
            label = f"{username} {product_name} ({state})"

            # Only seed if this user has never had this product, so re-running
            # doesn't add duplicates or touch subscriptions made through the API.
            if Subscription.objects.filter(user=user, product=product).exists():
                self.report("Subscription", label, False)
                continue

            if state == "expired":
                expire_date = now - timedelta(days=1)
            else:
                expire_date = now + timedelta(days=365)
            revoked_at = now if state == "revoked" else None

            subscription = Subscription.objects.create(
                user=user, product=product, expire_date=expire_date, revoked_at=revoked_at
            )
            if state == "expired":
                # granted_date uses auto_now_add (always "now"), so backdate it
                # with update(), which skips that, so the expired one reads as a year ago.
                Subscription.objects.filter(id=subscription.id).update(
                    granted_date=now - timedelta(days=366)
                )
            self.report("Subscription", label, True)

    def report(self, kind, name, created):
        status = "created" if created else "already existed"
        self.stdout.write(f"{kind} {name}: {status}")
