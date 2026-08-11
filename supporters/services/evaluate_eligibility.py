from uuid import uuid4

from django.utils import timezone

from engagement.dispatcher import publish
from engagement.envelope import EngagementEventEnvelope
from engagement.events import EngagementEvent

from ..events import EligibilityGranted, EligibilityRevoked
from ..models import (
    EligibilityReason,
    StudentVerification,
    StudentVerificationStatus,
    SupporterEligibility,
)


class EvaluateEligibilityService:
    """Application service for evaluating whether a supporter may participate."""

    @staticmethod
    def evaluate(user):
        verification = (
            StudentVerification.objects.filter(user=user)
            .order_by("-created_at")
            .first()
        )

        if verification and verification.status in {
            StudentVerificationStatus.APPROVED,
            StudentVerificationStatus.VERIFIED,
        }:
            if verification.expires_at is None or verification.expires_at > timezone.now():
                is_eligible = True
                reason = EligibilityReason.VERIFIED
            else:
                is_eligible = False
                reason = EligibilityReason.VERIFICATION_EXPIRED
        elif verification and verification.status == StudentVerificationStatus.REJECTED:
            is_eligible = False
            reason = EligibilityReason.VERIFICATION_REJECTED
        elif verification and verification.status == StudentVerificationStatus.PENDING:
            is_eligible = False
            reason = EligibilityReason.VERIFICATION_PENDING
        else:
            is_eligible = False
            reason = EligibilityReason.UNKNOWN

        eligibility, created = SupporterEligibility.objects.get_or_create(supporter=user)
        previous_eligible = eligibility.is_eligible
        previous_reason = eligibility.reason
        eligibility.is_eligible = is_eligible
        eligibility.reason = reason
        eligibility.evaluated_at = timezone.now()
        eligibility.expires_at = verification.expires_at if verification else None
        eligibility.save(update_fields=["is_eligible", "reason", "evaluated_at", "expires_at"])

        should_publish = created or previous_eligible != is_eligible or previous_reason != reason
        if should_publish and is_eligible:
            event = EligibilityGranted(
                supporter_id=user.pk,
                eligibility_id=eligibility.pk,
                reason=reason,
                evaluated_at=eligibility.evaluated_at,
                correlation_id=uuid4(),
            )
            envelope = EngagementEventEnvelope(
                event=EngagementEvent.ELIGIBILITY_GRANTED,
                user=user,
                payload={
                    "supporter_id": user.pk,
                    "eligibility_id": eligibility.pk,
                    "reason": reason,
                    "evaluated_at": eligibility.evaluated_at,
                },
                correlation_id=event.correlation_id,
            )
            publish(envelope)
        elif should_publish and not is_eligible:
            event = EligibilityRevoked(
                supporter_id=user.pk,
                eligibility_id=eligibility.pk,
                reason=reason,
                evaluated_at=eligibility.evaluated_at,
                correlation_id=uuid4(),
            )
            envelope = EngagementEventEnvelope(
                event=EngagementEvent.ELIGIBILITY_REVOKED,
                user=user,
                payload={
                    "supporter_id": user.pk,
                    "eligibility_id": eligibility.pk,
                    "reason": reason,
                    "evaluated_at": eligibility.evaluated_at,
                },
                correlation_id=event.correlation_id,
            )
            publish(envelope)

        return eligibility
