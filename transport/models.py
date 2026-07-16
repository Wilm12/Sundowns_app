"""Transport domain models for vehicle options, bookings, and settlements."""

import logging
from django.db import models

from points.rules import PointEvent
from points.services import award_points
from engagement.events import EngagementEvent
from engagement.envelope import EngagementEventEnvelope
from engagement.dispatcher import publish

logger = logging.getLogger(__name__)


class Transport(models.Model):
    """Represents a transport option associated with a match and branch."""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        related_name='transport'
    )
    match = models.ForeignKey(
        'matches.Match',
        on_delete=models.CASCADE,
        related_name='transport_options',
        null=True,
        blank=True
    )
    owner_id = models.IntegerField()  # later FK to TaxiOwner
    capacity = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def available_seats(self):
        """Return the number of seats still available for this transport."""

        booked_count = self.bookings.filter(status='booked').count()
        return self.capacity - booked_count

    def __str__(self):
        return f"Transport {self.id}"


class TransportBooking(models.Model):
    """Represents a booking made by a ticket holder for a transport option."""
    STATUS_CHOICES = (
        ('booked', 'Booked'),
        ('boarded', 'Boarded'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )

    ticket = models.OneToOneField(
        'ticketing.Ticket',
        on_delete=models.CASCADE,
        related_name='transport_booking'
    )
    transport = models.ForeignKey(
        'transport.Transport',
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='booked')
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Award transport booking points only once when the booking becomes booked."""
        is_create = self.pk is None
        old_status = None

        if not is_create:
            old_status = TransportBooking.objects.filter(pk=self.pk).values_list('status', flat=True).first()

        super().save(*args, **kwargs)

        if self.status == 'booked' and (is_create or old_status != 'booked'):
            award_points(
                user=self.ticket.user,
                event=PointEvent.TRANSPORT_BOOKING,
                description=f"Transport booking for ticket {self.ticket.id}",
                reference_id=f"transport_booking:{self.pk}"
            )

            try:
                envelope = EngagementEventEnvelope(
                    event=EngagementEvent.TRANSPORT_BOOKED,
                    user=self.ticket.user,
                    payload={
                        "booking_id": self.id,
                        "transport_id": self.transport.id,
                        "match_id": self.transport.match.id if self.transport.match else None,
                        "branch": self.transport.branch.name,
                    },
                )

                publish(envelope)

            except Exception:
                logger.exception(
                    "Failed to publish TRANSPORT_BOOKED event "
                    "for booking %s",
                    self.id,
                )

    def __str__(self):
        return f"Booking {self.id}"


class TransportSettlement(models.Model):
    """Tracks settlement data owed to transport providers."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    )

    transport = models.ForeignKey(
        'transport.Transport',
        on_delete=models.CASCADE,
        related_name='settlements'
    )
    owner_id = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Settlement {self.id}"
