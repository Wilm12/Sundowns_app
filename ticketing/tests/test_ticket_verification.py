from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from branches.models import Branch
from users.models import User
from membership.models import Membership
from matches.models import Match
from ticketing.models import Ticket


class TicketVerificationTests(APITestCase):
    def test_admin_can_verify_ticket_qr(self):
        branch = Branch.objects.create(
            name="Johannesburg Branch",
            location="Johannesburg",
        )

        admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="StrongPass123!",
            role="admin",
            branch=branch,
        )

        member = User.objects.create_user(
            username="memberuser",
            email="member@example.com",
            password="StrongPass123!",
            role="member",
            branch=branch,
        )

        Membership.objects.create(
            user=member,
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
            user=member,
            match=match,
            status="booked",
        )

        self.client.force_authenticate(user=admin_user)

        url = reverse("ticket_verify")

        response = self.client.post(
            url,
            {
                "qr_code": str(ticket.qr_code),
            },
            format="json",
        )

        ticket.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ticket.status, "used")

    def test_member_cannot_verify_ticket_qr(self):
        branch = Branch.objects.create(
            name="Pretoria Branch",
            location="Pretoria",
        )

        member = User.objects.create_user(
            username="memberuser2",
            email="member2@example.com",
            password="StrongPass123!",
            role="member",
            branch=branch,
        )

        Membership.objects.create(
            user=member,
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
            user=member,
            match=match,
            status="booked",
        )

        self.client.force_authenticate(user=member)

        url = reverse("ticket_verify")

        response = self.client.post(
            url,
            {
                "qr_code": str(ticket.qr_code),
            },
            format="json",
        )

        ticket.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ticket.status, "booked")
