"""Transport domain models for vehicle options, bookings, and settlements."""

from django.db import models


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
