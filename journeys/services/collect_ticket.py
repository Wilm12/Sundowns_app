from datetime import datetime
from uuid import uuid4

from django.utils import timezone

from engagement.dispatcher import publish
from engagement.envelope import EngagementEventEnvelope
from engagement.events import EngagementEvent

from branches.services.authorization import BranchAdminRequired, is_branch_admin
from supporters.models import StudentVerification, StudentVerificationStatus

from ..events import AttendanceRecorded
from ..models import Journey, JourneyStatus


class InvalidCollectionCode(Exception):
    """Raised when a collection code does not resolve to a journey."""


class TicketAlreadyCollected(Exception):
    """Raised when a ticket has already been collected."""


class InvalidJourneyState(Exception):
    """Raised when a journey is not in a state that can be redeemed."""


class VerificationRequired(Exception):
    """Raised when the supporter has not completed active verification."""


class CollectTicketService:
    """Redeem a ticket at the gate using a four-digit numeric code."""

    @staticmethod
    def collect(collection_code, collector, branch=None, match=None):
        code = str(collection_code).strip() if collection_code is not None else ""
        if not code.isdigit() or len(code) != 4:
            raise InvalidCollectionCode("Collection code must be a 4-digit numeric code.")

        journeys = Journey.objects.filter(collection_code=code)
        if branch is not None:
            journeys = journeys.filter(branch=branch)
        if match is not None:
            journeys = journeys.filter(match=match)

        try:
            journey = journeys.get()
        except Journey.DoesNotExist:
            raise InvalidCollectionCode("Collection code does not match an existing journey.")

        if journey.status == JourneyStatus.MATCH_ATTENDED:
            raise TicketAlreadyCollected("Ticket has already been redeemed.")

        active_verification = (
            StudentVerification.objects.filter(
                user=journey.supporter,
                status__in=[
                    StudentVerificationStatus.VERIFIED,
                    StudentVerificationStatus.APPROVED,
                ],
                expires_at__gt=timezone.now(),
            ).exists()
        )
        if not active_verification:
            raise VerificationRequired("Supporter verification is required before gate entry.")

        if journey.status not in [JourneyStatus.BOOKED, JourneyStatus.TICKET_READY]:
            raise InvalidJourneyState("Only BOOKED or TICKET_READY journeys may be redeemed at the gate.")

        if not is_branch_admin(collector, journey.branch):
            raise BranchAdminRequired("Only branch admins can redeem tickets for this branch.")

        journey.attended_at = timezone.now()
        journey.attended_by = collector
        journey.status = JourneyStatus.MATCH_ATTENDED
        journey.save(update_fields=["attended_at", "attended_by", "status", "updated_at"])

        event = AttendanceRecorded(
            journey_id=journey.pk,
            supporter_id=journey.supporter_id,
            branch_id=journey.branch_id,
            match_id=journey.match_id,
            attended_by=collector.pk,
            attended_at=journey.attended_at,
            correlation_id=uuid4(),
        )
        envelope = EngagementEventEnvelope(
            event=EngagementEvent.ATTENDANCE_RECORDED,
            user=journey.supporter,
            payload={
                "journey_id": journey.pk,
                "supporter_id": journey.supporter_id,
                "branch_id": journey.branch_id,
                "match_id": journey.match_id,
                "attended_by": collector.pk,
                "attended_at": datetime.now(),
            },
            correlation_id=event.correlation_id,
        )
        publish(envelope)
        return journey
