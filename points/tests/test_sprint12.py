from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from points.models import PointsTransaction
from points import tiers as tier_helpers
from rewards.models import Reward

User = get_user_model()


class Sprint12UITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='sprint12',
            email='s12@example.com',
            password='testpass123',
        )
        self.account = self.user.points_account

    def test_dashboard_shows_current_tier_and_progress(self):
        # give user 350 points (between silver(100) and gold(500))
        PointsTransaction.objects.create(
            account=self.account,
            transaction_type='membership_payment',
            points=350,
            description='Bulk points',
            reference_id='bulk1',
            created_at=timezone.now() - timedelta(minutes=5),
        )
        self.client.force_login(self.user)
        resp = self.client.get(reverse('points_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Silver')
        self.assertContains(resp, 'Progress:')
        self.assertContains(resp, 'points until Gold')

    def test_reward_detail_displays_locked_message_when_below_required_tier(self):
        # user has 50 points (bronze)
        PointsTransaction.objects.create(
            account=self.account,
            transaction_type='membership_payment',
            points=50,
            description='Initial',
            reference_id='init1',
            created_at=timezone.now() - timedelta(minutes=5),
        )
        reward = Reward.objects.create(
            name='Gold Only Reward',
            description='Exclusive',
            points_cost=1000,
            quantity_available=10,
            minimum_tier='gold',
        )
        self.client.force_login(self.user)
        resp = self.client.get(reverse('reward_detail_page', args=[reward.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '🔒')
        self.assertContains(resp, 'Requires Gold tier')

    def test_tiers_page_renders(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('tiers_page'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Loyalty Tiers')
        for tier in tier_helpers.TIER_ORDER:
            self.assertContains(resp, tier.capitalize())
