from django.test import TestCase
from django.contrib.auth import get_user_model
from points.models import PointsTransaction
from rewards.models import Reward, RewardRedemption

from analytics.services import (
    get_analytics_loyalty_metrics,
    get_analytics_reward_metrics,
    get_analytics_membership_metrics,
)
from points.services import get_tier_distribution
from membership.models import Membership

User = get_user_model()


class AnalyticsServiceTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='supporter1',
            email='s1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='supporter2',
            email='s2@example.com',
            password='pass123'
        )
        self.user3 = User.objects.create_user(
            username='supporter3',
            email='s3@example.com',
            password='pass123'
        )

        PointsTransaction.objects.create(
            account=self.user1.points_account,
            transaction_type=PointsTransaction.TransactionType.MEMBERSHIP_PAYMENT,
            points=150,
            description='Award for signup'
        )
        PointsTransaction.objects.create(
            account=self.user1.points_account,
            transaction_type=PointsTransaction.TransactionType.REWARD_REDEMPTION,
            points=-50,
            description='Redemption'
        )
        PointsTransaction.objects.create(
            account=self.user2.points_account,
            transaction_type=PointsTransaction.TransactionType.MEMBERSHIP_PAYMENT,
            points=500,
            description='Award for loyalty'
        )
        PointsTransaction.objects.create(
            account=self.user3.points_account,
            transaction_type=PointsTransaction.TransactionType.MEMBERSHIP_PAYMENT,
            points=25,
            description='Award for action'
        )
        self.reward1 = Reward.objects.create(
            name='Free Match Ticket',
            description='Redeem for a free ticket',
            points_cost=200,
            quantity_available=10,
            is_active=True
        )
        self.reward2 = Reward.objects.create(
            name='Club Scarf',
            description='Redeem for a scarf',
            points_cost=100,
            quantity_available=3,
            is_active=True
        )
        RewardRedemption.objects.create(
            user=self.user1,
            reward=self.reward1,
            points_spent=200,
            status=RewardRedemption.Status.APPROVED
        )
        RewardRedemption.objects.create(
            user=self.user2,
            reward=self.reward1,
            points_spent=200,
            status=RewardRedemption.Status.COMPLETED
        )
        RewardRedemption.objects.create(
            user=self.user3,
            reward=self.reward2,
            points_spent=100,
            status=RewardRedemption.Status.APPROVED
        )

        Membership.objects.create(
            user=self.user1,
            tier='bronze',
            status='active'
        )
        Membership.objects.create(
            user=self.user2,
            tier='silver',
            status='expired'
        )
        Membership.objects.create(
            user=self.user3,
            tier='gold',
            status='active'
        )

    def test_tier_distribution_calculation(self):
        distribution = get_tier_distribution()

        self.assertEqual(distribution['bronze'], 1)
        self.assertEqual(distribution['silver'], 1)
        self.assertEqual(distribution['gold'], 1)
        self.assertEqual(distribution['platinum'], 0)

    def test_top_supporters_query(self):
        metrics = get_analytics_loyalty_metrics(limit=3)

        self.assertEqual(metrics['top_supporters'][0]['username'], 'supporter2')
        self.assertEqual(metrics['top_supporters'][0]['balance'], 500)
        self.assertEqual(metrics['top_supporters'][1]['username'], 'supporter1')
        self.assertEqual(metrics['top_supporters'][1]['balance'], 100)
        self.assertEqual(metrics['top_supporters'][2]['username'], 'supporter3')
        self.assertEqual(metrics['top_supporters'][2]['balance'], 25)

    def test_reward_analytics_counts(self):
        reward_metrics = get_analytics_reward_metrics()

        self.assertEqual(reward_metrics['total_rewards'], 2)
        self.assertEqual(reward_metrics['total_reward_redemptions'], 3)
        self.assertEqual(reward_metrics['most_redeemed_rewards'][0]['name'], 'Free Match Ticket')
        self.assertEqual(reward_metrics['most_redeemed_rewards'][0]['redemption_count'], 2)
        self.assertEqual(reward_metrics['least_redeemed_rewards'][0]['name'], 'Club Scarf')
        self.assertEqual(reward_metrics['least_redeemed_rewards'][0]['redemption_count'], 1)

    def test_membership_analytics_counts(self):
        membership_metrics = get_analytics_membership_metrics()

        self.assertEqual(membership_metrics['active_memberships'], 2)
        self.assertEqual(membership_metrics['expired_memberships'], 1)
