from django.utils import timezone

from ..models import StudentVerification, Supporter, SupporterStatus


class RejectStudentVerificationService:
    """Application service for rejecting student verification."""

    @staticmethod
    def reject(supporter, verified_by=None, evidence_reference=""):
        verification = StudentVerification.objects.filter(supporter=supporter).order_by("-created_at").first()
        if verification is None:
            verification = StudentVerification.objects.create(
                supporter=supporter,
                verification_status=StudentVerification.VerificationStatus.REJECTED,
                verified_by=verified_by,
                evidence_reference=evidence_reference,
            )
        else:
            verification.verification_status = StudentVerification.VerificationStatus.REJECTED
            verification.verified_by = verified_by
            verification.evidence_reference = evidence_reference
            verification.verified_at = timezone.now()
            verification.save()

        supporter.status = SupporterStatus.PENDING_VERIFICATION
        supporter.save(update_fields=["status"])
        return verification
