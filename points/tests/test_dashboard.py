from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from points.models import PointsTransaction
from points import tiers as tier_helpers
from promotions.models import Promotion

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
        self.assertContains(response, 'Current Points')

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

    def test_active_promotions_are_shown_to_supporters(self):
        Promotion.objects.create(
            name='Double Ticket Points',
            event_type='ticket_booking',
            multiplier=2,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
            is_active=True,
        )
        Promotion.objects.create(
            name='Expired Promotion',
            event_type='membership_payment',
            multiplier=3,
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() - timedelta(days=1),
            is_active=True,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('points_dashboard'))

        self.assertContains(response, 'Active Promotions')
        self.assertContains(response, 'Double Ticket Points')
        self.assertContains(response, 'Multiplier: 2x points')
        self.assertNotContains(response, 'Expired Promotion')

    def test_earning_guide_is_visible_on_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('points_dashboard'))

        self.assertContains(response, 'How To Earn Points')
        self.assertContains(response, 'Membership Payment')
        self.assertContains(response, 'Transport Booking')

    def test_tiers_page_is_available(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('tiers_page'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Loyalty Tiers')
        for tier in tier_helpers.TIER_ORDER:
            self.assertContains(response, tier.capitalize())

    def test_next_tier_progress_is_calculated_correctly(self):
        PointsTransaction.objects.create(
            account=self.account,
            transaction_type='membership_payment',
            points=150,
            description='Membership payment',
            reference_id='mem_test',
            created_at=timezone.now() - timedelta(minutes=5),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('points_dashboard'))

        threshold = tier_helpers.TIER_THRESHOLDS['gold']
        self.assertContains(response, f'{threshold - 150} points until Gold')

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
