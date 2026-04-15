from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class PointsLedger(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('redeemed', 'Redeemed'),
        ('expired', 'Expired'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='points')
    points = models.IntegerField()
    reason = models.CharField(max_length=50)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.points}"