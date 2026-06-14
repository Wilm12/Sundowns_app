from django.test import TestCase
from django.contrib.auth import get_user_model

from points.rules import PointEvent
from points.services import award_points
from points.tiers import TIER_THRESHOLDS
from points.models import PointsTransaction
from rewards.models import Reward, RewardRedemption
from rewards.services import redeem_reward

User = get_user_model()


class RewardTierEligibilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tieruser2', email='tier2@example.com', password='pw')

    def test_redemption_denied_for_insufficient_tier(self):
        # create a gold-only reward
        reward = Reward.objects.create(
            name='Gold Gift',
            description='Gold only',
            points_cost=10,
            quantity_available=5,
            is_active=True,
            minimum_tier='gold',
        )

        # user has no points -> bronze
        with self.assertRaises(ValueError):
            redeem_reward(self.user, reward)

    def test_redemption_allowed_for_higher_tier(self):
        reward = Reward.objects.create(
            name='Silver Gift',
            description='Silver and above',
            points_cost=10,
            quantity_available=5,
            is_active=True,
            minimum_tier='silver',
        )
        silver_points = TIER_THRESHOLDS['silver']
        account = self.user.points_account
        PointsTransaction.objects.create(
            account=account,
            transaction_type=PointsTransaction.TransactionType.MEMBERSHIP_PAYMENT,
            points=silver_points,
            description='test award',
            reference_id='silver_threshold',
        )

        redemption = redeem_reward(self.user, reward)
        self.assertEqual(redemption.points_spent, reward.points_cost)
