from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from points.rules import PointEvent
from promotions.services import get_points_multiplier
from promotions.models import Promotion


class PromotionServiceTestCase(TestCase):
    def test_no_promotion_returns_one(self):
        m = get_points_multiplier(PointEvent.TICKET_BOOKING)
        self.assertEqual(m, 1)

    def test_double_points_promotion(self):
        now = timezone.now()
        Promotion.objects.create(
            name='Double Tickets',
            event_type=PointEvent.TICKET_BOOKING.value,
            multiplier=2,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
            is_active=True,
        )

        m = get_points_multiplier(PointEvent.TICKET_BOOKING)
        self.assertEqual(m, 2)

    def test_triple_points_promotion(self):
        now = timezone.now()
        Promotion.objects.create(
            name='Triple Membership',
            event_type=PointEvent.MEMBERSHIP_PAYMENT.value,
            multiplier=3,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1),
            is_active=True,
        )

        m = get_points_multiplier(PointEvent.MEMBERSHIP_PAYMENT)
        self.assertEqual(m, 3)

    def test_expired_promotion_returns_one(self):
        now = timezone.now()
        Promotion.objects.create(
            name='Expired Promo',
            event_type=PointEvent.TRANSPORT_BOOKING.value,
            multiplier=5,
            start_date=now - timedelta(days=3),
            end_date=now - timedelta(days=1),
            is_active=True,
        )

        m = get_points_multiplier(PointEvent.TRANSPORT_BOOKING)
        self.assertEqual(m, 1)

    def test_inactive_promotion_ignored(self):
        now = timezone.now()
        Promotion.objects.create(
            name='Inactive Promo',
            event_type=PointEvent.TICKET_BOOKING.value,
            multiplier=4,
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
            is_active=False,
        )

        m = get_points_multiplier(PointEvent.TICKET_BOOKING)
        self.assertEqual(m, 1)
