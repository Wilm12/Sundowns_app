from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from points.rules import PointEvent
from points.services import award_points
from rewards.models import Reward, RewardRedemption

User = get_user_model()


class RewardViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='rewardviewuser',
            email='rewardview@example.com',
            password='testpass123'
        )

    def test_reward_list_page_is_blocked_when_feature_is_frozen(self):
        self.client.login(username='rewardviewuser', password='testpass123')
        response = self.client.get(reverse('reward_list_page'))
        self.assertEqual(response.status_code, 403)

    def test_reward_detail_page_is_blocked_when_feature_is_frozen(self):
        reward = Reward.objects.create(
            name='VIP Access',
            description='Access to a VIP lounge.',
            points_cost=30,
            quantity_available=10,
            is_active=True,
        )
        self.client.login(username='rewardviewuser', password='testpass123')

        response = self.client.get(reverse('reward_detail_page', args=[reward.pk]))

        self.assertEqual(response.status_code, 403)

    def test_successful_redemption_route_is_blocked_when_feature_is_frozen(self):
        reward = Reward.objects.create(
            name='Signed Ball',
            description='A signed football.',
            points_cost=25,
            quantity_available=2,
            is_active=True,
        )
        award_points(
            self.user,
            event=PointEvent.MEMBERSHIP_PAYMENT,
            description='Award points for membership payment',
            reference_id='mem_200'
        )
        self.client.login(username='rewardviewuser', password='testpass123')

        response = self.client.post(reverse('redeem_reward', args=[reward.pk]), follow=True)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(RewardRedemption.objects.filter(user=self.user, reward=reward).exists())

    def test_insufficient_points_shows_error_message(self):
        reward = Reward.objects.create(
            name='Premium Jersey',
            description='A premium jersey.',
            points_cost=100,
            quantity_available=5,
            is_active=True,
        )
        award_points(
            self.user,
            event=PointEvent.MEMBERSHIP_PAYMENT,
            description='Award points for membership payment',
            reference_id='mem_201'
        )
        self.client.login(username='rewardviewuser', password='testpass123')

        response = self.client.post(reverse('redeem_reward', args=[reward.pk]), follow=True)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(RewardRedemption.objects.filter(user=self.user, reward=reward).exists())

    def test_inactive_reward_shows_error_message(self):
        reward = Reward.objects.create(
            name='Inactive Gift',
            description='Currently unavailable.',
            points_cost=10,
            quantity_available=5,
            is_active=False,
        )
        award_points(
            self.user,
            event=PointEvent.MEMBERSHIP_PAYMENT,
            description='Award points for membership payment',
            reference_id='mem_202'
        )
        self.client.login(username='rewardviewuser', password='testpass123')

        response = self.client.post(reverse('redeem_reward', args=[reward.pk]), follow=True)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(RewardRedemption.objects.filter(user=self.user, reward=reward).exists())

    def test_out_of_stock_reward_shows_error_message(self):
        reward = Reward.objects.create(
            name='Sold Out Gift',
            description='No stock available.',
            points_cost=10,
            quantity_available=0,
            is_active=True,
        )
        award_points(
            self.user,
            event=PointEvent.MEMBERSHIP_PAYMENT,
            description='Award points for membership payment',
            reference_id='mem_203'
        )
        self.client.login(username='rewardviewuser', password='testpass123')

        response = self.client.post(reverse('redeem_reward', args=[reward.pk]), follow=True)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(RewardRedemption.objects.filter(user=self.user, reward=reward).exists())

    def test_my_redemptions_page_is_blocked_when_feature_is_frozen(self):
        reward = Reward.objects.create(
            name='Collector Pin',
            description='A limited edition pin.',
            points_cost=10,
            quantity_available=5,
            is_active=True,
        )
        redemption = RewardRedemption.objects.create(
            user=self.user,
            reward=reward,
            points_spent=10,
            status=RewardRedemption.Status.PENDING,
        )
        self.client.login(username='rewardviewuser', password='testpass123')

        response = self.client.get(reverse('my_redemptions_page'))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(RewardRedemption.objects.filter(pk=redemption.pk, user=self.user).exists())
