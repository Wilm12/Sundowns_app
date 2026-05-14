from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from branches.models import Branch
from users.models import User
from membership.models import Membership
from matches.models import Match
from ticketing.models import Ticket


class TicketBookingTests(TestCase):
    def test_user_cannot_book_same_match_twice(self):
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

        match = Match.objects.create(
            opponent="Kaizer Chiefs",
            location="FNB Stadium",
            date=timezone.now(),
        )

        Ticket.objects.create(
            user=user,
            match=match,
            status="booked",
        )

        self.client.login(
            username="testuser",
            password="StrongPass123!"
        )

        url = reverse("book_ticket_page", args=[match.id])

        response = self.client.get(url)

        tickets_count = Ticket.objects.filter(
            user=user,
            match=match
        ).count()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(tickets_count, 1)
