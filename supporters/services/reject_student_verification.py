from datetime import datetime
from uuid import uuid4

from django.utils import timezone

from engagement.dispatcher import publish
from engagement.envelope import EngagementEventEnvelope
from engagement.events import EngagementEvent

from ..events import StudentVerificationRejected
from ..models import StudentVerification, StudentVerificationStatus
from .evaluate_eligibility import EvaluateEligibilityService


class VerificationAlreadyProcessed(Exception):
    """Raised when the verification is no longer pending and cannot be rejected."""


class RejectStudentVerificationService:
    """Reject a pending verification request."""

    @staticmethod
    def reject(verification, rejected_by=None):
        if verification.status != StudentVerificationStatus.PENDING:
            raise VerificationAlreadyProcessed(
                f"Verification {verification.pk} is already processed."
            )

        verification.status = StudentVerificationStatus.REJECTED
        verification.verified_by = rejected_by
        verification.verified_at = timezone.now()
        verification.save()

        event = StudentVerificationRejected(
            supporter_id=verification.user_id,
            verification_id=verification.pk,
            acted_by=rejected_by.pk if rejected_by else None,
            timestamp=timezone.now(),
            correlation_id=uuid4(),
        )
        envelope = EngagementEventEnvelope(
            event=EngagementEvent.STUDENT_VERIFICATION_REJECTED,
            user=verification.user,
            payload={
                "verification_id": verification.pk,
                "supporter_id": verification.user_id,
                "acted_by": rejected_by.pk if rejected_by else None,
                "timestamp": datetime.now(),
            },
            correlation_id=event.correlation_id,
        )
        publish(envelope)
        EvaluateEligibilityService.evaluate(verification.user)
        return verification
