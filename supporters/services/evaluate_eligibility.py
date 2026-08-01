from ..models import Eligibility, Supporter


class EvaluateEligibilityService:
    """Application service for evaluating whether a supporter may participate."""

    @staticmethod
    def evaluate(supporter, is_eligible, reason=""):
        eligibility, _ = Eligibility.objects.get_or_create(supporter=supporter)
        eligibility.is_eligible = is_eligible
        eligibility.reason = reason
        eligibility.save(update_fields=["is_eligible", "reason", "evaluated_at"])
        return eligibility
