from rest_framework.test import APITestCase

from entitlements.models import Benefit, Product, User


class ApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username="alice")
        # The API requires a logged-in user (IsAuthenticated in settings)
        self.client.force_authenticate(user=self.user)

        web = Benefit.objects.create(code="web_access", name="Web access")
        Benefit.objects.create(code="print_magazine", name="Print magazine")
        Benefit.objects.create(code="ad_free", name="Ad-free")

        self.digital = Product.objects.create(name="Digital", price="9.99")
        self.digital.benefits.set([web])

        self.payload = {"user_id": self.user.id, "product_id": self.digital.id}

    def test_grant_returns_201(self):
        response = self.client.post("/api/subscriptions/", self.payload)

        self.assertEqual(response.status_code, 201)

    def test_granting_same_product_again_returns_400(self):
        self.client.post("/api/subscriptions/", self.payload)

        response = self.client.post("/api/subscriptions/", self.payload)

        self.assertEqual(response.status_code, 400)

    def test_grant_with_unknown_product_returns_404(self):
        payload = {"user_id": self.user.id, "product_id": 9999}

        response = self.client.post("/api/subscriptions/", payload)

        self.assertEqual(response.status_code, 404)

    def test_revoke_after_grant_returns_200(self):
        self.client.post("/api/subscriptions/", self.payload)

        response = self.client.post("/api/subscriptions/revoke/", self.payload)

        self.assertEqual(response.status_code, 200)

    def test_entitlements_returns_benefit_codes_after_grant(self):
        self.client.post("/api/subscriptions/", self.payload)

        response = self.client.get(f"/api/users/{self.user.id}/entitlements/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([b["code"] for b in response.data], ["web_access"])

    def test_entitlements_for_unknown_user_returns_404(self):
        response = self.client.get("/api/users/9999/entitlements/")

        self.assertEqual(response.status_code, 404)
