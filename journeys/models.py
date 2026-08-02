from django.conf import settings
from django.db import models

from branches.models import Branch
from matches.models import Match
from ticketing.models import Ticket


class JourneyStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    BOOKED = "BOOKED", "Booked"
    CANCELLED = "CANCELLED", "Cancelled"
    COMPLETED = "COMPLETED", "Completed"
    TICKET_READY = "TICKET_READY", "Ticket Ready"
    TICKET_COLLECTED = "TICKET_COLLECTED", "Ticket Collected"
    MATCH_ATTENDED = "MATCH_ATTENDED", "Match Attended"


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
        max_length=20,
        choices=JourneyStatus.choices,
        default=JourneyStatus.OPEN,
    )
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="journey",
    )
    ticket_allocated_at = models.DateTimeField(null=True, blank=True)
    collection_code = models.CharField(max_length=4, null=True, blank=True, unique=True)
    ticket_collected_at = models.DateTimeField(null=True, blank=True)
    ticket_collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collected_journeys",
    )
    attended_at = models.DateTimeField(null=True, blank=True)
    attended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_attendance",
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
