from django.db import models

class Transport(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    branch = models.ForeignKey('branches.Branch', on_delete=models.CASCADE, related_name='transport')
    owner_id = models.IntegerField()  # can later be FK to TaxiOwner
    capacity = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return f"Transport {self.id}"

class TransportBooking(models.Model):
    STATUS_CHOICES = (
        ('booked', 'Booked'),
        ('boarded', 'Boarded'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )

    ticket = models.ForeignKey('ticketing.Ticket', on_delete=models.CASCADE, related_name='transport_bookings')
    transport = models.ForeignKey('transport.Transport', on_delete=models.CASCADE, related_name='bookings')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Booking {self.id}"

class TransportSettlement(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    )

    transport = models.ForeignKey('transport.Transport', on_delete=models.CASCADE, related_name='settlements')
    owner_id = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    payment_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Settlement {self.id}"