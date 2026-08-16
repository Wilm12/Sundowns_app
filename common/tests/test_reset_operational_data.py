from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from analytics.models import BranchMatchSnapshot
from branches.models import Branch, BranchRole, CommitteePosition, MatchAllocation
from journeys.models import Journey, JourneyStatus
from matches.models import Match
from supporters.models import EligibilityReason, StudentVerification, StudentVerificationStatus, SupporterEligibility
from ticketing.models import Ticket
from transport.models import Transport, TransportBooking
from users.models import User


class ResetOperationalDataCommandTests(TestCase):
    def test_reset_operational_data_keeps_only_tuks_and_clears_operational_records(self):
        old_branch = Branch.objects.create(name="Pretoria Central")
        tuks = Branch.objects.create(name="Tuks")
        other_branch = Branch.objects.create(name="Cape Town")

        supporter = User.objects.create_user(username="supporter-for-reset", email="supporter@example.com", password="Password123!")
        supporter.branch = tuks
        supporter.save(update_fields=["branch"])

        admin = User.objects.create_user(username="admin-for-reset", email="admin@example.com", password="Password123!")
        admin.branch = tuks
        admin.save(update_fields=["branch"])

        branch_admin_role = BranchRole.objects.create(
            branch=tuks,
            user=admin,
            role=BranchRole.Role.BRANCH_ADMIN,
            is_active=True,
        )
        CommitteePosition.objects.create(
            branch=tuks,
            branch_role=branch_admin_role,
            position=CommitteePosition.Position.CHAIRPERSON,
            created_by=admin,
        )

        match = Match.objects.create(
            opponent="Kaizer Chiefs",
            location="Loftus",
            date=timezone.now() + timezone.timedelta(days=7),
        )

        MatchAllocation.objects.create(branch=tuks, match=match, allocated_tickets=20)
        journey = Journey.objects.create(supporter=supporter, branch=tuks, match=match, status=JourneyStatus.BOOKED)
        ticket = Ticket.objects.create(user=supporter, match=match)
        journey.ticket = ticket
        journey.save(update_fields=["ticket"])

        transport = Transport.objects.create(branch=tuks, match=match, owner_id=1, capacity=12)
        TransportBooking.objects.create(ticket=ticket, transport=transport)

        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        StudentVerification.objects.create(
            user=supporter,
            student_number="S12345",
            university="Tuks",
            status=StudentVerificationStatus.VERIFIED,
        )
        BranchMatchSnapshot.objects.create(
            branch=tuks,
            match=match,
            snapshot_date=timezone.now().date(),
            booked=1,
            ticket_ready=1,
            collected=1,
            attended=1,
            verification_completed=1,
            transport_booked=1,
            transport_capacity=12,
        )

        self.assertEqual(Branch.objects.count(), 3)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Match.objects.count(), 1)

        out = StringIO()
        call_command("reset_operational_data", "--confirm", stdout=out)

        self.assertEqual(Branch.objects.count(), 1)
        self.assertEqual(list(Branch.objects.values_list("name", flat=True)), ["Tuks"])
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Match.objects.count(), 0)
        self.assertEqual(Journey.objects.count(), 0)
        self.assertEqual(Ticket.objects.count(), 0)
        self.assertEqual(Transport.objects.count(), 0)
        self.assertEqual(TransportBooking.objects.count(), 0)
        self.assertEqual(BranchMatchSnapshot.objects.count(), 0)
        self.assertEqual(CommitteePosition.objects.count(), 0)
        self.assertIn("Tuks", out.getvalue())
        self.assertIn("'users': 0", out.getvalue())
        self.assertIn("'matches': 0", out.getvalue())
