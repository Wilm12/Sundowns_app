from datetime import timedelta

from django.utils import timezone

from engagement.dispatcher import publish
from engagement.envelope import EngagementEventEnvelope
from engagement.events import EngagementEvent

from branches.services.authorization import BranchAdminRequired, is_branch_admin

from ..events import StudentVerified
from ..models import StudentVerification, StudentVerificationStatus
from .evaluate_eligibility import EvaluateEligibilityService


class ActiveVerificationExists(Exception):
    """Raised when another active verified record already exists for the user."""


class VerifyStudentService:
    """Application service for approving student verification."""

    @staticmethod
    def verify(verification, verifier):
        branch = getattr(verification.user, "branch", None)
        if not is_branch_admin(verifier, branch):
            raise BranchAdminRequired("Only branch admins can approve student verifications.")

        active_verification_exists = (
            StudentVerification.objects.filter(
                user=verification.user,
                status=StudentVerificationStatus.VERIFIED,
                expires_at__gt=timezone.now(),
            )
            .exclude(pk=verification.pk)
            .exists()
        )

        if active_verification_exists:
            raise ActiveVerificationExists(
                f"An active verified record already exists for {verification.user}."
            )

        verification.status = StudentVerificationStatus.APPROVED
        verification.verified_at = timezone.now()
        verification.expires_at = timezone.now() + timedelta(days=365)
        verification.verified_by = verifier
        verification.save()

        verification.user.is_active = True
        verification.user.save(update_fields=["is_active"])

        event = StudentVerified(
            supporter_id=verification.user_id,
            verification_id=verification.pk,
            verified_by=verifier.pk if verifier else None,
            expires_at=verification.expires_at,
        )
        envelope = EngagementEventEnvelope(
            event=EngagementEvent.STUDENT_VERIFIED,
            user=verification.user,
            payload={
                "verification_id": verification.pk,
                "supporter_id": verification.user_id,
                "acted_by": verifier.pk if verifier else None,
                "expires_at": verification.expires_at,
            },
        )
        publish(envelope)
        EvaluateEligibilityService.evaluate(verification.user)
        return verification
