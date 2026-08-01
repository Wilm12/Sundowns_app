from django.utils import timezone

from ..models import StudentVerification


class RenewVerificationService:
    """Application service for renewing verification for a new academic period."""

    @staticmethod
    def renew(supporter, verified_by=None, evidence_reference="", expires_at=None):
        verification = StudentVerification.objects.filter(supporter=supporter).order_by("-created_at").first()
        if verification is None:
            verification = StudentVerification.objects.create(
                supporter=supporter,
                verification_status=StudentVerification.VerificationStatus.APPROVED,
                verified_by=verified_by,
                evidence_reference=evidence_reference,
            )
        else:
            verification.verification_status = StudentVerification.VerificationStatus.APPROVED
            verification.verified_by = verified_by
            verification.evidence_reference = evidence_reference
            verification.verified_at = timezone.now()
            verification.expires_at = expires_at
            verification.save()

        return verification
