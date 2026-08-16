from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import User
from membership.models import Membership


class MembershipPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tieruser',
            email='tieruser@example.com',
            password='StrongPass123!',
            role='member',
        )
        self.client.force_login(self.user)

    def test_membership_page_renders_tier_cards(self):
        response = self.client.get(reverse('membership_page'))

        self.assertEqual(response.status_code, 403)

    def test_user_can_select_premium_tier(self):
        response = self.client.post(reverse('membership_page'), {'tier': 'premium'})

        self.assertEqual(response.status_code, 403)

        membership = Membership.objects.filter(user=self.user).order_by('-created_at').first()
        self.assertIsNotNone(membership)
        self.assertEqual(membership.tier, 'basic')

    def test_user_can_select_golden_tier(self):
        response = self.client.post(reverse('membership_page'), {'tier': 'golden'})

        self.assertEqual(response.status_code, 403)

        membership = Membership.objects.filter(user=self.user).order_by('-created_at').first()
        self.assertIsNotNone(membership)
        self.assertEqual(membership.tier, 'basic')

    def test_current_tier_button_is_marked_current(self):
        Membership.objects.create(
            user=self.user,
            tier='premium',
            status='active',
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timezone.timedelta(days=30),
        )

        response = self.client.get(reverse('membership_page'))

        self.assertEqual(response.status_code, 403)

    def test_selecting_new_tier_sets_membership_pending(self):
        Membership.objects.create(
            user=self.user,
            tier='basic',
            status='active',
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timezone.timedelta(days=30),
        )

        response = self.client.post(reverse('membership_page'), {'tier': 'golden'})

        self.assertEqual(response.status_code, 403)

        membership = Membership.objects.filter(user=self.user).order_by('-created_at').first()
        self.assertEqual(membership.tier, 'basic')

    def test_payment_page_amount_reflects_selected_tier(self):
        response = self.client.post(reverse('membership_page'), {'tier': 'golden'})
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse('payment_page'))

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Membership.objects.filter(user=self.user, tier='golden').exists())
