from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from entitlements.models import Benefit, Product

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

DEMO_USERNAMES = ["alice", "bob", "carol"]
DEMO_PASSWORD = "password123"


class Command(BaseCommand):
    help = "Seed benefits, products and demo users. Safe to run more than once."

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
            user, created = User.objects.get_or_create(username=username)
            if created:
                # Only set the password on creation, so re-running doesn't
                # overwrite a password that was changed later.
                user.set_password(DEMO_PASSWORD)
                user.save()
            self.report("User", username, created)

    def report(self, kind, name, created):
        status = "created" if created else "already existed"
        self.stdout.write(f"{kind} {name}: {status}")
