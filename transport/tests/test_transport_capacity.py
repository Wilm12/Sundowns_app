from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from branches.models import Branch
from users.models import User
from membership.models import Membership
from matches.models import Match
from ticketing.models import Ticket
from transport.models import Transport, TransportBooking


class TransportCapacityTests(TestCase):
    def test_user_cannot_book_transport_when_full(self):
        branch = Branch.objects.create(
            name="Johannesburg Branch",
            location="Johannesburg",
        )

        user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPass123!",
            branch=branch,
        )

        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="StrongPass123!",
            branch=branch,
        )

        Membership.objects.create(
            user=user,
            tier="basic",
            status="active",
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=30),
        )

        Membership.objects.create(
            user=other_user,
            tier="basic",
            status="active",
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=30),
        )

        match = Match.objects.create(
            opponent="Kaizer Chiefs",
            location="FNB Stadium",
            date=timezone.now(),
        )

        transport = Transport.objects.create(
            branch=branch,
            match=match,
            owner_id=1,
            capacity=1,
            status="active",
        )

        other_ticket = Ticket.objects.create(
            user=other_user,
            match=match,
            status="booked",
        )

        TransportBooking.objects.create(
            ticket=other_ticket,
            transport=transport,
            status="booked",
        )

        user_ticket = Ticket.objects.create(
            user=user,
            match=match,
            status="booked",
        )

        self.client.login(
            username="testuser",
            password="StrongPass123!"
        )

        url = reverse(
            "book_transport_page",
            args=[transport.id, user_ticket.id]
        )

        response = self.client.get(url)

        booking_exists = TransportBooking.objects.filter(
            ticket=user_ticket,
            transport=transport,
        ).exists()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(booking_exists)
        self.assertEqual(transport.available_seats(), 0)
