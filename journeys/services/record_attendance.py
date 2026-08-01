from datetime import datetime
from uuid import uuid4

from django.utils import timezone

from engagement.dispatcher import publish
from engagement.envelope import EngagementEventEnvelope
from engagement.events import EngagementEvent

from branches.models import BranchRole

from ..events import AttendanceRecorded
from ..models import Journey, JourneyStatus


class AttendanceAlreadyRecorded(Exception):
    """Raised when attendance has already been recorded for a journey."""


class RecorderNotAuthorized(Exception):
    """Raised when the recorder does not have an authorized role for the branch."""


class InvalidJourneyState(Exception):
    """Raised when the journey is not in a state that can record attendance."""


class RecordAttendanceService:
    """Record supporter attendance for a collected ticket journey."""

    @staticmethod
    def record(journey, recorder):
        if not isinstance(journey, Journey):
            raise InvalidJourneyState("Journey is invalid.")

        if journey.status == JourneyStatus.MATCH_ATTENDED:
            raise AttendanceAlreadyRecorded("Attendance has already been recorded for this journey.")

        if journey.status != JourneyStatus.TICKET_COLLECTED:
            raise InvalidJourneyState("Only TICKET_COLLECTED journeys may record attendance.")

        has_authorized_role = BranchRole.objects.filter(
            branch=journey.branch,
            user=recorder,
            role__in=[BranchRole.Role.BRANCH_ADMIN, BranchRole.Role.TICKET_DISTRIBUTOR],
            is_active=True,
        ).exists()
        if not has_authorized_role:
            raise RecorderNotAuthorized("Recorder is not authorized to record attendance for this branch.")

        journey.attended_at = timezone.now()
        journey.attended_by = recorder
        journey.status = JourneyStatus.MATCH_ATTENDED
        journey.save(update_fields=["attended_at", "attended_by", "status", "updated_at"])

        event = AttendanceRecorded(
            journey_id=journey.pk,
            supporter_id=journey.supporter_id,
            branch_id=journey.branch_id,
            match_id=journey.match_id,
            attended_by=recorder.pk,
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
                "attended_by": recorder.pk,
                "attended_at": datetime.now(),
            },
            correlation_id=event.correlation_id,
        )
        publish(envelope)
        return journey
