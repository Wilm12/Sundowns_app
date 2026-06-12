from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from points.models import PointsTransaction

User = get_user_model()


class PointsDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='pointsuser',
            email='pointsuser@example.com',
            password='testpass123',
        )

        self.account = self.user.points_account

    def test_anonymous_users_are_redirected_to_login(self):
        response = self.client.get(reverse('points_dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/api/auth/login-page/', response['Location'])

    def test_logged_in_user_sees_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('points_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Points')
        self.assertContains(response, 'Current Balance')

    def test_current_balance_is_displayed(self):
        PointsTransaction.objects.create(
            account=self.account,
            transaction_type='membership_payment',
            points=50,
            description='Membership payment',
            reference_id='mem_test',
            created_at=timezone.now() - timedelta(minutes=5),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('points_dashboard'))

        self.assertContains(response, '50')
        self.assertContains(response, 'Membership payment')

    def test_transactions_are_displayed_in_newest_first_order(self):
        older = PointsTransaction.objects.create(
            account=self.account,
            transaction_type='ticket_booking',
            points=10,
            description='Ticket booked',
            reference_id='ticket_test',
            created_at=timezone.now() - timedelta(minutes=10),
        )
        newer = PointsTransaction.objects.create(
            account=self.account,
            transaction_type='transport_booking',
            points=5,
            description='Transport booked',
            reference_id='transport_test',
            created_at=timezone.now(),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('points_dashboard'))

        content = response.content.decode()
        self.assertLess(content.index('Transport booked'), content.index('Ticket booked'))
        self.assertContains(response, 'Transport booked')
        self.assertContains(response, 'Ticket booked')
