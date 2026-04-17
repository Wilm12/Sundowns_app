

from django.db import models
from django.conf import settings
import uuid

User = settings.AUTH_USER_MODEL

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('booked', 'Booked'),
        ('used', 'Used'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    match = models.ForeignKey('matches.Match', on_delete=models.CASCADE, related_name='tickets')
    qr_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.id}"