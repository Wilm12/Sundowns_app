from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from branches.models import Branch
from users.models import User
from membership.models import Membership
from matches.models import Match
from ticketing.models import Ticket


class TransportPromptRedirectTests(TestCase):
    def test_transport_prompt_no_redirects_to_my_tickets(self):
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

        ticket = Ticket.objects.create(
            user=user,
            match=match,
            status="booked",
        )

        self.client.login(
            username="testuser",
            password="StrongPass123!"
        )

        url = reverse("transport_prompt_page", args=[ticket.id])

        response = self.client.post(url, {
            "transport_choice": "no"
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("my_tickets_page"))

    def test_transport_prompt_yes_redirects_to_transport(self):
        branch = Branch.objects.create(
            name="Pretoria Branch",
            location="Pretoria",
        )

        user = User.objects.create_user(
            username="testuser2",
            email="testuser2@example.com",
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
            opponent="Orlando Pirates",
            location="Loftus Versfeld",
            date=timezone.now(),
        )

        ticket = Ticket.objects.create(
            user=user,
            match=match,
            status="booked",
        )

        self.client.login(
            username="testuser2",
            password="StrongPass123!"
        )

        url = reverse("transport_prompt_page", args=[ticket.id])

        response = self.client.post(url, {
            "transport_choice": "yes"
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/transport/")