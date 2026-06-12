from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from branches.models import Branch
from matches.models import Match
from points.models import PointsTransaction
from ticketing.models import Ticket
from transport.models import Transport, TransportBooking
from users.models import User
from membership.models import Membership


class TransportBookingPointsTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Cape Town Branch",
            location="Cape Town",
        )

        self.user = User.objects.create_user(
            username="pointuser",
            email="pointuser@example.com",
            password="StrongPass123!",
            branch=self.branch,
        )

        Membership.objects.create(
            user=self.user,
            tier="basic",
            status="active",
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=30),
        )

        self.match = Match.objects.create(
            opponent="Golden Arrows",
            location="Cape Town Stadium",
            date=timezone.now(),
        )

        self.transport = Transport.objects.create(
            branch=self.branch,
            match=self.match,
            owner_id=1,
            capacity=10,
            status="active",
        )

        self.ticket = Ticket.objects.create(
            user=self.user,
            match=self.match,
            status="booked",
        )

    def test_transport_booking_save_awards_five_points(self):
        booking = TransportBooking.objects.create(
            ticket=self.ticket,
            transport=self.transport,
            status="booked",
        )

        self.assertEqual(self.user.points_account.balance, 15)
        self.assertEqual(
            PointsTransaction.objects.filter(
                account=self.user.points_account,
                transaction_type="transport_booking",
            ).count(),
            1
        )

        booking.status = "boarded"
        booking.save()

        self.assertEqual(
            PointsTransaction.objects.filter(
                account=self.user.points_account,
                transaction_type="transport_booking",
            ).count(),
            1
        )

    def test_transport_booking_status_transition_to_booked_awards_points(self):
        booking = TransportBooking.objects.create(
            ticket=self.ticket,
            transport=self.transport,
            status="cancelled",
        )

        self.assertEqual(self.user.points_account.balance, 10)

        booking.status = "booked"
        booking.save()

        self.assertEqual(self.user.points_account.balance, 15)
        transaction = PointsTransaction.objects.get(
            account=self.user.points_account,
            transaction_type="transport_booking",
        )
        self.assertEqual(transaction.reference_id, f"transport_booking:{booking.pk}")
