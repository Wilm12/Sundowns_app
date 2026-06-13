from django.test import TestCase
from django.contrib.auth import get_user_model

from rewards.models import Reward, RewardRedemption

User = get_user_model()


class RewardModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='rewarduser',
            email='reward@example.com',
            password='testpass123'
        )

    def test_reward_can_be_created(self):
        reward = Reward.objects.create(
            name='Team Scarf',
            description='Redeem for a team scarf.',
            points_cost=100,
            quantity_available=5,
            is_active=True,
        )

        self.assertEqual(reward.name, 'Team Scarf')
        self.assertTrue(reward.is_active)
        self.assertEqual(reward.quantity_available, 5)
        self.assertEqual(str(reward), 'Team Scarf')

    def test_reward_redemption_defaults_to_pending(self):
        reward = Reward.objects.create(
            name='VIP Pass',
            description='Redeem for VIP pass.',
            points_cost=150,
            quantity_available=2,
            is_active=True,
        )

        redemption = RewardRedemption.objects.create(
            user=self.user,
            reward=reward,
            points_spent=150,
        )

        self.assertEqual(redemption.status, RewardRedemption.Status.PENDING)
        self.assertIn('VIP Pass', str(redemption))
