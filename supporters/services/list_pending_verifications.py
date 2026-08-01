from ..models import StudentVerification, StudentVerificationStatus


class ListPendingVerificationsService:
    """Return pending verification requests for a verifier queue."""

    @staticmethod
    def list():
        return StudentVerification.objects.filter(status=StudentVerificationStatus.PENDING).order_by("created_at")
