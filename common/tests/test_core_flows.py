from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import User
from membership.models import Membership
from payments.models import Payment


class CoreFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPass123!",
            role="member",
        )

    def test_health_endpoint(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_login_returns_access_token(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "test@example.com",
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_successful_payment_activates_membership(self):
        membership = Membership.objects.create(
            user=self.user,
            tier="basic",
            status="pending",
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date(),
        )

        Payment.objects.create(
            user=self.user,
            membership=membership,
            amount="100.00",
            status="successful",
            reference="TEST-PAY-001",
        )

        membership.refresh_from_db()
        self.assertEqual(membership.status, "active")
