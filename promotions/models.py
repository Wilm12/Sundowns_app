from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Promotion(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    target_tier = models.CharField(max_length=10, null=True, blank=True)
    expiry_date = models.DateField()
    status = models.CharField(max_length=10)

    def __str__(self):
        return self.title


class PromotionRedemption(models.Model):
    STATUS_CHOICES = (
        ('redeemed', 'Redeemed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    )

    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='redemptions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promotion_redemptions')
    redeemed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.user} - {self.promotion}"