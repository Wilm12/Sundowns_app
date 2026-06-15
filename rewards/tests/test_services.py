from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.models import Sum

from points.rules import PointEvent
from points.services import award_points
from points.models import PointsTransaction
from rewards.models import Reward, RewardRedemption
from rewards.services import redeem_reward

User = get_user_model()


class RewardRedemptionServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='serviceuser',
            email='service@example.com',
            password='testpass123'
        )

    def test_successful_redemption_creates_redemption_and_transaction(self):
        reward = Reward.objects.create(
            name='Signed Poster',
            description='Redeem for a signed poster.',
            points_cost=20,
            quantity_available=5,
            is_active=True,
        )

        award_points(
            self.user,
            event=PointEvent.MEMBERSHIP_PAYMENT,
            description='Award points for membership payment',
            reference_id='mem_100'
        )

        redemption = redeem_reward(self.user, reward)

        reward.refresh_from_db()
        self.assertEqual(redemption.status, RewardRedemption.Status.PENDING)
        self.assertEqual(redemption.points_spent, 20)
        self.assertEqual(reward.quantity_available, 4)

        transaction = PointsTransaction.objects.get(reference_id=f'reward_redemption:{redemption.pk}')
        self.assertEqual(transaction.points, -20)
        self.assertEqual(transaction.transaction_type, 'reward_redemption')
        self.assertEqual(transaction.description, 'reward redemption')
        self.assertEqual(self.user.points_account.balance, 30)
        # ensure notification was created for redemption
        from notifications.models import Notification
        notif = Notification.objects.filter(user=self.user, notification_type=Notification.NotificationType.REWARD_REDEEMED)
        self.assertTrue(notif.exists())

    def test_insufficient_balance_raises_error(self):
        reward = Reward.objects.create(
            name='Matchday Ticket',
            description='Redeem for a matchday ticket.',
            points_cost=50,
            quantity_available=5,
            is_active=True,
        )

        award_points(
            self.user,
            event=PointEvent.TRANSPORT_BOOKING,
            description='Award points for transport booking',
            reference_id='transport_100'
        )

        with self.assertRaises(ValueError):
            redeem_reward(self.user, reward)

        self.assertEqual(RewardRedemption.objects.count(), 0)
        self.assertEqual(PointsTransaction.objects.filter(reference_id__startswith='reward_redemption').count(), 0)

    def test_inactive_reward_raises_error(self):
        reward = Reward.objects.create(
            name='Closed Event',
            description='Inactive reward.',
            points_cost=10,
            quantity_available=5,
            is_active=False,
        )

        award_points(
            self.user,
            event=PointEvent.MEMBERSHIP_PAYMENT,
            description='Award points for membership payment',
            reference_id='mem_101'
        )

        with self.assertRaises(ValueError):
            redeem_reward(self.user, reward)

        self.assertEqual(RewardRedemption.objects.count(), 0)

    def test_out_of_stock_reward_raises_error(self):
        reward = Reward.objects.create(
            name='Sold Out Voucher',
            description='No available stock.',
            points_cost=10,
            quantity_available=0,
            is_active=True,
        )

        award_points(
            self.user,
            event=PointEvent.MEMBERSHIP_PAYMENT,
            description='Award points for membership payment',
            reference_id='mem_102'
        )

        with self.assertRaises(ValueError):
            redeem_reward(self.user, reward)

        self.assertEqual(RewardRedemption.objects.count(), 0)

    def test_balance_decreases_correctly_through_ledger(self):
        reward = Reward.objects.create(
            name='Exclusive Pin',
            description='Redeem for an exclusive pin.',
            points_cost=15,
            quantity_available=3,
            is_active=True,
        )

        award_points(
            self.user,
            event=PointEvent.TICKET_BOOKING,
            description='Award points for ticket booking',
            reference_id='ticket_100'
        )
        award_points(
            self.user,
            event=PointEvent.TRANSPORT_BOOKING,
            description='Award points for transport booking',
            reference_id='transport_101'
        )

        redemption = redeem_reward(self.user, reward)

        self.user.points_account.refresh_from_db()
        expected_balance = 10 + 5 - 15
        self.assertEqual(self.user.points_account.balance, expected_balance)

        total_points = self.user.points_account.transactions.aggregate(total=Sum('points'))['total']
        self.assertEqual(total_points, expected_balance)
        self.assertEqual(redemption.points_spent, 15)
