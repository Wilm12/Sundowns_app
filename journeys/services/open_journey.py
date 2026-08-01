from datetime import datetime
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from engagement.dispatcher import publish
from engagement.envelope import EngagementEventEnvelope
from engagement.events import EngagementEvent

from branches.models import Branch, BranchPolicy, BranchStatus
from supporters.models import SupporterEligibility
from supporters.services.evaluate_eligibility import EvaluateEligibilityService

from ..events import JourneyOpened
from ..models import Journey, JourneyStatus


class JourneyAlreadyExists(Exception):
    """Raised when an active journey already exists for the same supporter/branch/match."""


class IneligibleSupporter(Exception):
    """Raised when a supporter is not currently eligible to start a journey."""


class InvalidBranch(Exception):
    """Raised when the branch is not operationally open for journey creation."""


class OpenJourneyService:
    """Open a new journey for an eligible supporter in an active branch."""

    @staticmethod
    def open_journey(supporter, branch, match):
        eligibility = SupporterEligibility.objects.filter(supporter=supporter).first()
        if not eligibility or not eligibility.is_eligible:
            raise IneligibleSupporter("Supporter is not currently eligible to start a journey.")

        if branch.status != BranchStatus.ACTIVE:
            raise InvalidBranch("Branch is not active.")

        policy = BranchPolicy.objects.filter(branch=branch).first()
        if policy is None:
            raise InvalidBranch("Branch policy is missing.")

        if Journey.objects.filter(
            supporter=supporter,
            branch=branch,
            match=match,
            status__in=[JourneyStatus.OPEN, JourneyStatus.BOOKED],
        ).exists():
            raise JourneyAlreadyExists("An active journey already exists for the same supporter/branch/match.")

        journey = Journey.objects.create(
            supporter=supporter,
            branch=branch,
            match=match,
            status=JourneyStatus.OPEN,
        )

        event = JourneyOpened(
            journey_id=journey.pk,
            supporter_id=supporter.pk,
            branch_id=branch.pk,
            match_id=match.pk,
            timestamp=timezone.now(),
            correlation_id=uuid4(),
        )
        envelope = EngagementEventEnvelope(
            event=EngagementEvent.JOURNEY_OPENED,
            user=supporter,
            payload={
                "journey_id": journey.pk,
                "supporter_id": supporter.pk,
                "branch_id": branch.pk,
                "match_id": match.pk,
                "timestamp": datetime.now(),
            },
            correlation_id=event.correlation_id,
        )
        publish(envelope)
        return journey
