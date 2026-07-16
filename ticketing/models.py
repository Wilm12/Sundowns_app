
from django.db import models
from django.conf import settings
import uuid
import logging

from points.rules import PointEvent
from points.services import award_points
from engagement.events import EngagementEvent
from engagement.envelope import EngagementEventEnvelope
from engagement.dispatcher import publish

logger = logging.getLogger(__name__)

User = settings.AUTH_USER_MODEL

class Ticket(models.Model):
    """Represents a booked or verified match ticket."""
    STATUS_CHOICES = (
        ('booked', 'Booked'),
        ('used', 'Used'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    match = models.ForeignKey('matches.Match', on_delete=models.CASCADE, related_name='tickets')
    qr_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='booked')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Award ticket booking points when a ticket becomes booked."""
        is_create = self.pk is None
        old_status = None

        if not is_create:
            old_status = Ticket.objects.filter(pk=self.pk).values_list('status', flat=True).first()

        super().save(*args, **kwargs)

        if self.status == 'booked' and (is_create or old_status != 'booked'):
            award_points(
                user=self.user,
                event=PointEvent.TICKET_BOOKING,
                description=f"Ticket booked for {self.match}",
                reference_id=f"ticket_booking:{self.pk}"
            )

            try:
                envelope = EngagementEventEnvelope(
                    event=EngagementEvent.TICKET_BOOKED,
                    user=self.user,
                    payload={
                        "ticket_id": self.id,
                        "match_id": self.match.id,
                        "match": self.match.opponent,
                        "qr_code": str(self.qr_code),
                    },
                )

                publish(envelope)

            except Exception:
                logger.exception(
                    "Failed to publish TICKET_BOOKED event "
                    "for ticket %s",
                    self.id,
                )

    def __str__(self):
        return f"Ticket {self.id}"
