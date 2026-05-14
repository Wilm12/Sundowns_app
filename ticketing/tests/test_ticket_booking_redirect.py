from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from branches.models import Branch
from users.models import User
from membership.models import Membership
from matches.models import Match


class TicketBookingRedirectTests(TestCase):
    def test_successful_ticket_booking_redirects_to_transport_prompt(self):
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

        self.client.login(username="testuser", password="StrongPass123!")

        url = reverse("book_ticket_page", args=[match.id])

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/transport-prompt/", response.url)