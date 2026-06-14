from django.test import TestCase
from django.contrib.auth import get_user_model

from points import tiers
from points.services import award_points
from points.rules import PointEvent

User = get_user_model()


class TierHelperTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tieruser', email='tier@example.com', password='pw')

    def test_get_tier_from_points(self):
        self.assertEqual(tiers.get_tier_from_points(50), 'bronze')
        self.assertEqual(tiers.get_tier_from_points(150), 'silver')
        self.assertEqual(tiers.get_tier_from_points(750), 'gold')
        self.assertEqual(tiers.get_tier_from_points(1500), 'platinum')

    def test_points_until_next_tier(self):
        self.assertEqual(tiers.points_until_next_tier(50), 50)
        self.assertEqual(tiers.points_until_next_tier(750), 250)
        self.assertEqual(tiers.points_until_next_tier(1200), 0)

    def test_get_user_tier_with_account(self):
        # award some points via existing service
        award_points(self.user, event=PointEvent.MEMBERSHIP_PAYMENT, description='test', reference_id='t1')
        self.user.refresh_from_db()
        self.assertEqual(tiers.get_user_tier(self.user), 'bronze' if self.user.points_account.balance < 100 else 'silver')
