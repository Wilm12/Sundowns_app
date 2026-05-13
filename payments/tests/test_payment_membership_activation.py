from django.test import TestCase
from django.utils import timezone

from branches.models import Branch
from users.models import User
from membership.models import Membership
from payments.models import Payment


class PaymentMembershipActivationTests(TestCase):
    def test_successful_payment_activates_membership(self):
        branch = Branch.objects.create(
            name="Johannesburg Branch",
            location="Johannesburg"
        )

        user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPass123!",
            branch=branch,
        )

        membership = Membership.objects.create(
            user=user,
            tier="basic",
            status="inactive",
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date(),
        )

        Payment.objects.create(
            user=user,
            membership=membership,
            amount=membership.expected_price(),
            status="successful",
        )

        membership.refresh_from_db()

        self.assertEqual(membership.status, "active")