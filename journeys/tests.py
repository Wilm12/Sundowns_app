from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from branches.models import Branch, BranchPolicy, BranchStatus
from matches.models import Match
from supporters.models import EligibilityReason, StudentVerification, StudentVerificationStatus, SupporterEligibility

from engagement.events import EngagementEvent

from .models import Journey, JourneyStatus
from .services.book_journey import BookJourneyService, InvalidJourneyTransition
from .services.open_journey import IneligibleSupporter, InvalidBranch, JourneyAlreadyExists, OpenJourneyService


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

    def _create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-pass-123",
        )
