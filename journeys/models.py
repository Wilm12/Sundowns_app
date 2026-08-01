from django.conf import settings
from django.db import models

from branches.models import Branch
from matches.models import Match


class JourneyStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    BOOKED = "BOOKED", "Booked"
    CANCELLED = "CANCELLED", "Cancelled"
    COMPLETED = "COMPLETED", "Completed"


class Journey(models.Model):
    supporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="journeys",
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="journeys",
    )
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="journeys",
    )
    status = models.CharField(
        max_length=10,
        choices=JourneyStatus.choices,
        default=JourneyStatus.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["supporter", "branch", "match"],
                condition=models.Q(status__in=[JourneyStatus.OPEN, JourneyStatus.BOOKED]),
                name="unique_active_journey_per_supporter_branch_match",
            )
        ]

    def __str__(self):
        return f"{self.supporter} -> {self.branch} @ {self.match}"
