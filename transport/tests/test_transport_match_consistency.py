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


class TransportMatchConsistencyTests(TestCase):
    def test_ticket_cannot_book_transport_for_different_match(self):
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

        Membership.objects.create(
            user=user,
            tier="basic",
            status="active",
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=30),
        )

        match_a = Match.objects.create(
            opponent="Kaizer Chiefs",
            location="FNB Stadium",
            date=timezone.now(),
        )

        match_b = Match.objects.create(
            opponent="Orlando Pirates",
            location="Loftus Versfeld",
            date=timezone.now() + timedelta(days=1),
        )

        ticket = Ticket.objects.create(
            user=user,
            match=match_a,
            status="booked",
        )

        transport = Transport.objects.create(
            branch=branch,
            match=match_b,
            owner_id=1,
            capacity=10,
            status="active",
        )

        self.client.login(
            username="testuser",
            password="StrongPass123!"
        )

        url = reverse(
            "book_transport_page",
            args=[transport.id, ticket.id]
        )

        response = self.client.get(url)

        booking_exists = TransportBooking.objects.filter(
            ticket=ticket,
            transport=transport,
        ).exists()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(booking_exists)
