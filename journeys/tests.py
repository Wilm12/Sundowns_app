import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from branches.models import Branch, BranchPolicy, BranchRole, BranchStatus
from matches.models import Match
from supporters.models import EligibilityReason, StudentVerification, StudentVerificationStatus, SupporterEligibility

from engagement.events import EngagementEvent
from branches.services.branch_admin_dashboard import BranchAdminDashboardService
from .models import Journey, JourneyStatus
from .services.allocate_ticket import AllocateTicketService, InvalidJourneyState, JourneyAlreadyHasTicket
from .services.book_journey import BookJourneyService, InvalidJourneyTransition
from .services.collect_ticket import (
    CollectTicketService,
    InvalidCollectionCode,
    InvalidJourneyState as CollectionInvalidJourneyState,
    TicketAlreadyCollected,
)
from branches.services.authorization import BranchAdminRequired
from .services.open_journey import IneligibleSupporter, InvalidBranch, JourneyAlreadyExists, OpenJourneyService
from .services.record_attendance import (
    AttendanceAlreadyRecorded,
    InvalidJourneyState as AttendanceInvalidJourneyState,
    RecordAttendanceService,
)


class JourneyServiceTests(TestCase):
    def test_eligible_supporter_can_open_a_journey(self):
        supporter = self._create_user(username="journey-supporter")
        branch = Branch.objects.create(name="Journey Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Pirates")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)

        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)

        self.assertEqual(journey.status, JourneyStatus.OPEN)
        self.assertEqual(journey.supporter, supporter)
        self.assertEqual(journey.branch, branch)
        self.assertEqual(journey.match, match)

    def test_ineligible_supporter_cannot_open_a_journey(self):
        supporter = self._create_user(username="ineligible-journey-user")
        branch = Branch.objects.create(name="Ineligible Journey Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="Durban", opponent="Arrows")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=False, reason=EligibilityReason.VERIFICATION_PENDING)

        with self.assertRaises(IneligibleSupporter):
            OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)

    def test_duplicate_active_journey_is_prevented(self):
        supporter = self._create_user(username="duplicate-journey-user")
        branch = Branch.objects.create(name="Duplicate Journey Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="Cape Town", opponent="Cape Town City")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)

        with self.assertRaises(JourneyAlreadyExists):
            OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)

    def test_open_journey_can_be_booked(self):
        supporter = self._create_user(username="bookable-journey-user")
        branch = Branch.objects.create(name="Bookable Journey Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="Mbombela", opponent="Royal AM")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)

        booked_journey = BookJourneyService.book_journey(journey)

        self.assertEqual(booked_journey.status, JourneyStatus.BOOKED)

    def test_invalid_transition_is_rejected(self):
        supporter = self._create_user(username="invalid-transition-user")
        branch = Branch.objects.create(name="Invalid Transition Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="Pretoria", opponent="Stellenbosch")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)
        journey.status = JourneyStatus.CANCELLED
        journey.save(update_fields=["status", "updated_at"])

        with self.assertRaises(InvalidJourneyTransition):
            BookJourneyService.book_journey(journey)

    @patch("journeys.services.open_journey.publish")
    def test_journey_opened_event_is_published(self, mock_publish):
        supporter = self._create_user(username="opened-event-user")
        branch = Branch.objects.create(name="Opened Event Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="Johannesburg", opponent="Mamelodi Sundowns")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)

        OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)

        self.assertEqual(mock_publish.call_count, 1)
        envelope = mock_publish.call_args.args[0]
        self.assertEqual(envelope.event, EngagementEvent.JOURNEY_OPENED)
        self.assertEqual(envelope.payload["supporter_id"], supporter.pk)

    @patch("journeys.services.book_journey.publish")
    def test_journey_booked_event_is_published(self, mock_publish):
        supporter = self._create_user(username="booked-event-user")
        branch = Branch.objects.create(name="Booked Event Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="Bloemfontein", opponent="Kaizer Chiefs")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)

        BookJourneyService.book_journey(journey)

        self.assertEqual(mock_publish.call_count, 1)
        envelope = mock_publish.call_args.args[0]
        self.assertEqual(envelope.event, EngagementEvent.JOURNEY_BOOKED)
        self.assertEqual(envelope.payload["supporter_id"], supporter.pk)

    def test_booked_journey_can_receive_a_ticket(self):
        supporter = self._create_user(username="ticketed-journey-user")
        branch = Branch.objects.create(name="Ticket Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="Gqeberha", opponent="Orlando Pirates")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)
        BookJourneyService.book_journey(journey)

        updated_journey = AllocateTicketService.allocate(journey)

        self.assertEqual(updated_journey.status, JourneyStatus.TICKET_READY)
        self.assertIsNotNone(updated_journey.ticket)
        self.assertIsNotNone(updated_journey.collection_code)
        self.assertIsNotNone(updated_journey.ticket_allocated_at)

    def test_open_journey_cannot_receive_a_ticket(self):
        supporter = self._create_user(username="open-ticket-journey-user")
        branch = Branch.objects.create(name="Open Ticket Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="Kimberley", opponent="Golden Arrows")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)

        with self.assertRaises(InvalidJourneyState):
            AllocateTicketService.allocate(journey)

    def test_duplicate_ticket_allocation_is_prevented(self):
        supporter = self._create_user(username="duplicate-ticket-journey-user")
        branch = Branch.objects.create(name="Duplicate Ticket Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="Ladysmith", opponent="Maritzburg")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)
        BookJourneyService.book_journey(journey)
        AllocateTicketService.allocate(journey)

        with self.assertRaises(InvalidJourneyState):
            AllocateTicketService.allocate(journey)

    def test_collection_code_is_generated(self):
        supporter = self._create_user(username="collection-code-user")
        branch = Branch.objects.create(name="Collection Code Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="Polokwane", opponent="Sekhukhune")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)
        BookJourneyService.book_journey(journey)

        updated_journey = AllocateTicketService.allocate(journey)

        self.assertIsNotNone(updated_journey.collection_code)
        self.assertRegex(updated_journey.collection_code, r"^\d{4}$")

    @patch("journeys.services.allocate_ticket.publish")
    def test_ticket_allocated_event_is_published(self, mock_publish):
        supporter = self._create_user(username="ticket-event-user")
        branch = Branch.objects.create(name="Ticket Event Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="George", opponent="Stellenbosch")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)
        BookJourneyService.book_journey(journey)

        AllocateTicketService.allocate(journey)

        self.assertEqual(mock_publish.call_count, 1)
        envelope = mock_publish.call_args.args[0]
        self.assertEqual(envelope.event, EngagementEvent.TICKET_ALLOCATED)
        self.assertEqual(envelope.payload["supporter_id"], supporter.pk)

    @patch("journeys.services.collect_ticket.publish")
    def test_gate_redemption_succeeds_for_authorized_branch_admin(self, mock_publish):
        supporter = self._create_user(username="collector-supporter")
        collector = self._create_user(username="ticket-branch-admin")
        branch = Branch.objects.create(name="Collection Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        BranchRole.objects.create(branch=branch, user=collector, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        match = Match.objects.create(date=timezone.now(), location="Durban", opponent="AmaZulu")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)
        BookJourneyService.book_journey(journey)
        AllocateTicketService.allocate(journey)

        redeemed_journey = CollectTicketService.collect(str(journey.collection_code), collector)

        self.assertEqual(redeemed_journey.status, JourneyStatus.MATCH_ATTENDED)
        self.assertIsNotNone(redeemed_journey.attended_at)
        self.assertEqual(redeemed_journey.attended_by, collector)
        self.assertEqual(mock_publish.call_count, 1)
        envelope = mock_publish.call_args.args[0]
        self.assertEqual(envelope.event, EngagementEvent.ATTENDANCE_RECORDED)
        self.assertEqual(envelope.payload["attended_by"], collector.pk)

    def test_duplicate_ticket_collection_is_rejected(self):
        supporter = self._create_user(username="duplicate-collector-supporter")
        collector = self._create_user(username="duplicate-collector")
        branch = Branch.objects.create(name="Duplicate Collection Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        BranchRole.objects.create(branch=branch, user=collector, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        match = Match.objects.create(date=timezone.now(), location="Cape Town", opponent="Cape Town City")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)
        BookJourneyService.book_journey(journey)
        AllocateTicketService.allocate(journey)
        CollectTicketService.collect(str(journey.collection_code), collector)

        with self.assertRaises(TicketAlreadyCollected):
            CollectTicketService.collect(str(journey.collection_code), collector)

    def test_invalid_collection_code_is_rejected(self):
        collector = self._create_user(username="invalid-code-collector")
        branch = Branch.objects.create(name="Invalid Code Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        BranchRole.objects.create(branch=branch, user=collector, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        with self.assertRaises(InvalidCollectionCode):
            CollectTicketService.collect("not-a-real-code", collector)

    def test_non_branch_admin_cannot_collect_ticket(self):
        supporter = self._create_user(username="unauthorized-supporter")
        collector = self._create_user(username="unauthorized-collector")
        branch = Branch.objects.create(name="Unauthorized Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="Mafikeng", opponent="Platinum Stars")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)
        BookJourneyService.book_journey(journey)
        AllocateTicketService.allocate(journey)

        with self.assertRaises(BranchAdminRequired):
            CollectTicketService.collect(str(journey.collection_code), collector)

    def test_dashboard_pending_and_attended_metrics_update_after_redemption(self):
        branch = Branch.objects.create(name="Redemption Metrics Branch", status=BranchStatus.ACTIVE)
        admin = self._create_user(username="redemption-admin")
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        supporter = self._create_user(username="redemption-supporter")
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)
        supporter.branch = branch
        supporter.save(update_fields=["branch"])

        SupporterEligibility.objects.create(
            supporter=supporter,
            is_eligible=True,
            reason=EligibilityReason.VERIFIED,
        )

        match = Match.objects.create(date=timezone.now(), location="Johannesburg", opponent="Kaizer Chiefs")
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)
        BookJourneyService.book_journey(journey)
        AllocateTicketService.allocate(journey)

        dashboard_before = BranchAdminDashboardService.get_dashboard(admin, branch=branch)
        self.assertEqual(dashboard_before["journey_metrics"]["pending_count"], 1)
        self.assertEqual(dashboard_before["journey_metrics"]["attended_count"], 0)

        CollectTicketService.collect(str(journey.collection_code), admin, branch=branch, match=match)

        dashboard_after = BranchAdminDashboardService.get_dashboard(admin, branch=branch)
        self.assertEqual(dashboard_after["journey_metrics"]["pending_count"], 0)
        self.assertEqual(dashboard_after["journey_metrics"]["attended_count"], 1)

    @patch("journeys.services.record_attendance.publish")
    def test_collected_journey_can_record_attendance(self, mock_publish):
        supporter = self._create_user(username="attendance-supporter")
        recorder = self._create_user(username="attendance-recorder")
        branch = Branch.objects.create(name="Attendance Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        BranchRole.objects.create(branch=branch, user=recorder, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        match = Match.objects.create(date=timezone.now(), location="Pretoria", opponent="Mamelodi Sundowns")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)
        BookJourneyService.book_journey(journey)
        AllocateTicketService.allocate(journey)
        journey.status = JourneyStatus.TICKET_COLLECTED
        journey.save(update_fields=["status", "updated_at"])

        updated_journey = RecordAttendanceService.record(journey, recorder)

        self.assertEqual(updated_journey.status, JourneyStatus.MATCH_ATTENDED)
        self.assertIsNotNone(updated_journey.attended_at)
        self.assertEqual(updated_journey.attended_by, recorder)
        self.assertEqual(mock_publish.call_count, 1)

    def test_ticket_ready_journey_cannot_record_attendance(self):
        supporter = self._create_user(username="attendance-ready-supporter")
        recorder = self._create_user(username="attendance-ready-recorder")
        branch = Branch.objects.create(name="Attendance Ready Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        BranchRole.objects.create(branch=branch, user=recorder, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        match = Match.objects.create(date=timezone.now(), location="Bloemfontein", opponent="Free State Stars")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)
        BookJourneyService.book_journey(journey)
        AllocateTicketService.allocate(journey)

        with self.assertRaises(AttendanceInvalidJourneyState):
            RecordAttendanceService.record(journey, recorder)

    def test_duplicate_attendance_is_rejected(self):
        supporter = self._create_user(username="duplicate-attendance-supporter")
        recorder = self._create_user(username="duplicate-attendance-recorder")
        branch = Branch.objects.create(name="Duplicate Attendance Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        BranchRole.objects.create(branch=branch, user=recorder, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        match = Match.objects.create(date=timezone.now(), location="Cape Town", opponent="Ajax Cape Town")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)
        BookJourneyService.book_journey(journey)
        AllocateTicketService.allocate(journey)
        journey.status = JourneyStatus.TICKET_COLLECTED
        journey.save(update_fields=["status", "updated_at"])
        RecordAttendanceService.record(journey, recorder)

        with self.assertRaises(AttendanceAlreadyRecorded):
            RecordAttendanceService.record(journey, recorder)

    def test_unauthorized_recorder_cannot_record_attendance(self):
        supporter = self._create_user(username="unauthorized-attendance-supporter")
        recorder = self._create_user(username="unauthorized-attendance-recorder")
        branch = Branch.objects.create(name="Unauthorized Attendance Branch", status=BranchStatus.ACTIVE)
        BranchPolicy.objects.get(branch=branch)
        match = Match.objects.create(date=timezone.now(), location="Mthatha", opponent="Chippa United")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        journey = OpenJourneyService.open_journey(supporter=supporter, branch=branch, match=match)
        BookJourneyService.book_journey(journey)
        AllocateTicketService.allocate(journey)
        journey.status = JourneyStatus.TICKET_COLLECTED
        journey.save(update_fields=["status", "updated_at"])

        with self.assertRaises(BranchAdminRequired):
            RecordAttendanceService.record(journey, recorder)

    def _create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-pass-123",
        )
