from datetime import datetime
from uuid import uuid4

from django.utils import timezone

from engagement.dispatcher import publish
from engagement.envelope import EngagementEventEnvelope
from engagement.events import EngagementEvent

from ..events import StudentVerificationRequested
from ..models import StudentVerification, StudentVerificationStatus
from .evaluate_eligibility import EvaluateEligibilityService


class DuplicatePendingVerification(Exception):
    """Raised when a pending verification request already exists for the supporter."""


class RequestStudentVerificationService:
    """Create a pending verification request for a supporter."""

    @staticmethod
    def request(user, student_number, university, branch_id=None, requested_by=None):
        if StudentVerification.objects.filter(
            user=user,
            status=StudentVerificationStatus.PENDING,
        ).exists():
            raise DuplicatePendingVerification(
                f"A pending verification request already exists for {user}."
            )

        verification = StudentVerification.objects.create(
            user=user,
            student_number=student_number,
            university=university,
        )

        event = StudentVerificationRequested(
            supporter_id=user.pk,
            verification_id=verification.pk,
            branch_id=branch_id,
            acted_by=requested_by.pk if requested_by else None,
            timestamp=timezone.now(),
            correlation_id=uuid4(),
        )
        envelope = EngagementEventEnvelope(
            event=EngagementEvent.STUDENT_VERIFICATION_REQUESTED,
            user=user,
            payload={
                "verification_id": verification.pk,
                "supporter_id": user.pk,
                "branch_id": branch_id,
                "acted_by": requested_by.pk if requested_by else None,
                "timestamp": datetime.now(),
            },
            correlation_id=event.correlation_id,
        )
        publish(envelope)
        EvaluateEligibilityService.evaluate(user)
        return verification
