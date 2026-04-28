from django.db import models
from django.conf import settings


class Membership(models.Model):
    TIER_CHOICES = (
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('golden', 'Golden'),
    )

    TIER_PRICES = {
        "basic": 100,
        "premium": 200,
        "golden": 300,
    }

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='basic')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def expected_price(self):
        return self.TIER_PRICES[self.tier]

    def __str__(self):
        return f"{self.user} - {self.tier} - {self.status}"
