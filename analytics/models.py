from django.db import models
from branches.models import Branch
from matches.models import Match


class BranchMatchSnapshot(models.Model):
    """Historical snapshot of branch-match analytics at a specific point in time.
    
    This model stores a snapshot of journey statuses, verifications, and transport
    bookings for a given branch and match on a specific date. It allows us to
    track progress over time without reprocessing the entire journey ledger.
    
    Journeys remain the source of truth; snapshots are derived data.
    """
    snapshot_date = models.DateField()

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="match_snapshots"
    )

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name="branch_snapshots"
    )

    # Journey status counts
    booked = models.PositiveIntegerField(default=0)
    ticket_ready = models.PositiveIntegerField(default=0)
    collected = models.PositiveIntegerField(default=0)
    attended = models.PositiveIntegerField(default=0)

    # Verification status
    verification_completed = models.PositiveIntegerField(default=0)

    # Transport metrics
    transport_booked = models.PositiveIntegerField(default=0)
    transport_capacity = models.PositiveIntegerField(default=0)

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("snapshot_date", "branch", "match")
        ordering = ["-snapshot_date", "branch__name"]

    def __str__(self):
        return f"{self.branch.name} - {self.match.opponent} ({self.snapshot_date})"
