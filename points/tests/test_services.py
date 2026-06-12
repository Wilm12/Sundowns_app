"""Tests for the points service layer."""

from django.test import TestCase
from django.contrib.auth import get_user_model

from points.rules import PointEvent
from points.services import award_points

User = get_user_model()


class PointsServiceTestCase(TestCase):
    """Test suite for point awarding service behavior."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='serviceuser',
            email='service@example.com',
            password='testpass123'
        )

    def test_membership_payment_awards_correct_points(self):
        transaction = award_points(
            self.user,
            event=PointEvent.MEMBERSHIP_PAYMENT,
            description='Award points for membership payment',
            reference_id='mem_001'
        )

        self.assertEqual(transaction.points, 50)
        self.assertEqual(transaction.transaction_type, 'membership_payment')
        self.assertEqual(self.user.points_account.balance, 50)

    def test_ticket_booking_awards_correct_points(self):
        transaction = award_points(
            self.user,
            event=PointEvent.TICKET_BOOKING,
            description='Award points for ticket booking',
            reference_id='ticket_001'
        )

        self.assertEqual(transaction.points, 10)
        self.assertEqual(transaction.transaction_type, 'ticket_booking')
        self.assertEqual(self.user.points_account.balance, 10)

    def test_transport_booking_awards_correct_points(self):
        transaction = award_points(
            self.user,
            event=PointEvent.TRANSPORT_BOOKING,
            description='Award points for transport booking',
            reference_id='transport_001'
        )

        self.assertEqual(transaction.points, 5)
        self.assertEqual(transaction.transaction_type, 'transport_booking')
        self.assertEqual(self.user.points_account.balance, 5)

    def test_award_points_is_idempotent_for_same_reference(self):
        transaction_one = award_points(
            self.user,
            event=PointEvent.TRANSPORT_BOOKING,
            description='Award points for transport booking',
            reference_id='transport_002'
        )

        transaction_two = award_points(
            self.user,
            event=PointEvent.TRANSPORT_BOOKING,
            description='Award points for transport booking',
            reference_id='transport_002'
        )

        self.assertEqual(transaction_one.pk, transaction_two.pk)
        self.user.points_account.refresh_from_db()
        self.assertEqual(self.user.points_account.balance, 5)

    def test_balance_updates_correctly_through_transactions(self):
        award_points(
            self.user,
            event=PointEvent.MEMBERSHIP_PAYMENT,
            description='Membership payment',
            reference_id='mem_002'
        )
        award_points(
            self.user,
            event=PointEvent.TICKET_BOOKING,
            description='Ticket booking',
            reference_id='ticket_002'
        )

        self.user.points_account.refresh_from_db()
        self.assertEqual(self.user.points_account.balance, 60)

    def test_multiple_transactions_accumulate_balance(self):
        award_points(
            self.user,
            event=PointEvent.MEMBERSHIP_PAYMENT,
            description='Membership payment',
            reference_id='mem_003'
        )
        award_points(
            self.user,
            event=PointEvent.TICKET_BOOKING,
            description='Ticket booking',
            reference_id='ticket_003'
        )
        award_points(
            self.user,
            event=PointEvent.TRANSPORT_BOOKING,
            description='Transport booking',
            reference_id='transport_003'
        )

        self.user.points_account.refresh_from_db()
        self.assertEqual(self.user.points_account.balance, 65)

    def test_invalid_event_raises_exception(self):
        with self.assertRaises(ValueError):
            award_points(
                self.user,
                event='invalid_event',
                description='Invalid event',
                reference_id='bad_001'
            )

    def test_award_points_requires_keyword_arguments(self):
        with self.assertRaises(TypeError):
            award_points(self.user, PointEvent.MEMBERSHIP_PAYMENT, 'desc')
