from django.test import TestCase
from django.contrib.auth import get_user_model

from notifications.models import Notification
from notifications.services import create_notification
from points.services import award_points
from rewards.services import redeem_reward
from rewards.models import Reward

User = get_user_model()


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='notifyuser',
            email='notify@example.com',
            password='password123'
        )

    def test_create_notification(self):
        notification = create_notification(
            self.user,
            title='Points earned',
            message='You earned 100 points.',
            notification_type=Notification.NotificationType.POINTS_EARNED,
        )

        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Points earned')
        self.assertEqual(notification.notification_type, 'points_earned')
        self.assertFalse(notification.is_read)

    def test_points_integration_creates_notification(self):
        award_points(
            self.user,
            event='membership_payment',
            description='Monthly membership bonus',
            reference_id='notify-points-1',
        )

        notification = Notification.objects.filter(
            user=self.user,
            notification_type=Notification.NotificationType.POINTS_EARNED,
        ).first()

        self.assertIsNotNone(notification)
        self.assertIn('earned', notification.message.lower())

    def test_tier_upgrade_integration_creates_notification(self):
        award_points(self.user, event='membership_payment', description='Baseline', reference_id='tier-1')
        award_points(self.user, event='membership_payment', description='Tier upgrade', reference_id='tier-2')

        tier_notification = Notification.objects.filter(
            user=self.user,
            notification_type=Notification.NotificationType.TIER_UPGRADE,
        ).first()

        self.assertIsNotNone(tier_notification)
        self.assertIn('upgraded', tier_notification.message.lower())

    def test_reward_integration_creates_notification(self):
        award_points(self.user, event='membership_payment', description='Points to redeem', reference_id='reward-points')

        reward = Reward.objects.create(
            name='Exclusive Poster',
            description='Redeem for a poster',
            points_cost=50,
            quantity_available=5,
            is_active=True,
        )
        redemption = redeem_reward(self.user, reward)

        notification = Notification.objects.filter(
            user=self.user,
            notification_type=Notification.NotificationType.REWARD_REDEEMED,
        ).first()

        self.assertIsNotNone(notification)
        self.assertIn(str(reward.name), notification.message)
        self.assertEqual(redemption.user, self.user)
        self.assertEqual(redemption.reward, reward)
