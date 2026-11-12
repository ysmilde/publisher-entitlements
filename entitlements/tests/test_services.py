from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from entitlements.services import get_user_entitlements, grant_product, revoke_product
from django.contrib.auth import get_user_model
from entitlements.models import Benefit, Product, Subscription

User = get_user_model()


class ServicesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="alice")

        web = Benefit.objects.create(code="web_access", name="Web access")
        magazine = Benefit.objects.create(code="print_magazine", name="Print magazine")
        ad_free = Benefit.objects.create(code="ad_free", name="Ad-free")

        self.digital = Product.objects.create(name="Digital", price="9.99")
        self.digital.benefits.set([web])
        self.print = Product.objects.create(name="Print", price="19.99")
        self.print.benefits.set([web, magazine])
        self.premium = Product.objects.create(name="Premium", price="29.99")
        self.premium.benefits.set([web, magazine, ad_free])

    def create_active_subscription(self, product):
        return Subscription.objects.create(
            user=self.user, product=product, expire_date=timezone.now() + timedelta(days=30)
        )

    def create_expired_subscription(self, product):
        return Subscription.objects.create(
            user=self.user, product=product, expire_date=timezone.now() - timedelta(days=1)
        )

    # get_user_entitlements

    def test_no_subscriptions_returns_empty_list(self):
        self.assertEqual(get_user_entitlements(self.user), [])

    def test_active_subscription_returns_product_benefits(self):
        self.create_active_subscription(self.print)

        codes = sorted(b.code for b in get_user_entitlements(self.user))

        self.assertEqual(codes, ["print_magazine", "web_access"])

    def test_expired_subscription_grants_no_benefits(self):
        self.create_expired_subscription(self.premium)

        self.assertEqual(get_user_entitlements(self.user), [])

    def test_revoked_subscription_grants_no_benefits(self):
        subscription = self.create_active_subscription(self.premium)
        subscription.revoked_at = timezone.now()
        subscription.save()

        self.assertEqual(get_user_entitlements(self.user), [])

    def test_overlapping_products_return_no_duplicate_benefits(self):
        # Digital and Print both include web_access
        self.create_active_subscription(self.digital)
        self.create_active_subscription(self.print)

        codes = sorted(b.code for b in get_user_entitlements(self.user))

        self.assertEqual(codes, ["print_magazine", "web_access"])

    def test_revoking_one_product_keeps_benefits_from_the_other(self):
        self.create_active_subscription(self.digital)
        self.create_active_subscription(self.premium)

        revoke_product(self.user, self.premium)

        codes = sorted(b.code for b in get_user_entitlements(self.user))
        self.assertEqual(codes, ["web_access"])

    def test_other_users_subscription_does_not_grant_benefits(self):
        other = User.objects.create(username="bob")
        Subscription.objects.create(
            user=other, product=self.premium, expire_date=timezone.now() + timedelta(days=30)
        )

        self.assertEqual(get_user_entitlements(self.user), [])

    def test_revoking_one_users_subscription_leaves_other_users_alone(self):
        other = User.objects.create(username="bob")
        self.create_active_subscription(self.digital)
        Subscription.objects.create(
            user=other, product=self.digital, expire_date=timezone.now() + timedelta(days=30)
        )

        revoke_product(self.user, self.digital)

        self.assertEqual(len(get_user_entitlements(other)), 1)

    # grant_product

    def test_grant_creates_subscription_expiring_in_about_a_year(self):
        subscription = grant_product(self.user, self.digital)

        expected = timezone.now() + timedelta(days=365)
        self.assertAlmostEqual(subscription.expire_date, expected, delta=timedelta(minutes=1))
        self.assertIsNone(subscription.revoked_at)

    def test_grant_while_already_active_raises_value_error(self):
        self.create_active_subscription(self.digital)

        with self.assertRaises(ValueError):
            grant_product(self.user, self.digital)

    def test_grant_after_expiry_creates_new_row_and_keeps_old_one(self):
        old = self.create_expired_subscription(self.digital)
        old_expire_date = old.expire_date

        new = grant_product(self.user, self.digital)

        old.refresh_from_db()
        self.assertNotEqual(new.id, old.id)
        self.assertEqual(old.expire_date, old_expire_date)
        self.assertEqual(Subscription.objects.filter(user=self.user, product=self.digital).count(), 2)

    def test_grant_after_revoke_creates_new_row(self):
        old = grant_product(self.user, self.digital)
        revoke_product(self.user, self.digital)

        new = grant_product(self.user, self.digital)

        self.assertNotEqual(new.id, old.id)
        self.assertEqual(Subscription.objects.filter(user=self.user, product=self.digital).count(), 2)

    # revoke_product

    def test_revoke_sets_revoked_at_and_removes_benefits(self):
        subscription = self.create_active_subscription(self.digital)

        revoke_product(self.user, self.digital)

        subscription.refresh_from_db()
        self.assertIsNotNone(subscription.revoked_at)
        self.assertEqual(get_user_entitlements(self.user), [])

    def test_revoke_with_nothing_active_raises_value_error(self):
        with self.assertRaises(ValueError):
            revoke_product(self.user, self.digital)

    def test_revoking_twice_raises_value_error_on_second_call(self):
        self.create_active_subscription(self.digital)
        revoke_product(self.user, self.digital)

        with self.assertRaises(ValueError):
            revoke_product(self.user, self.digital)
