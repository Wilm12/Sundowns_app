from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Membership(models.Model):
    TIER_CHOICES = (
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('golden', 'Golden'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='membership')
    tier = models.CharField(max_length=10, choices=TIER_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    start_date = models.DateField()
    expiry_date = models.DateField()

    def __str__(self):
        return f"{self.user} - {self.tier}"