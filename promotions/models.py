"""Promotion models for offers, redemption, and tracking."""

from django.db import models
from django.conf import settings
from django.utils import timezone

from points.rules import PointEvent

User = settings.AUTH_USER_MODEL


class Promotion(models.Model):
    """Represents a time-bound promotion that can modify points awarded for an event."""

    # legacy/title kept for compatibility with earlier migrations/apps
    title = models.CharField(max_length=255, null=True, blank=True)
    # human-friendly name (preferred)
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    # event_type must match PointEvent values
    EVENT_CHOICES = tuple((e.value, e.value) for e in PointEvent)
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES, null=True, blank=True)

    multiplier = models.PositiveIntegerField(default=1)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # legacy fields preserved
    target_tier = models.CharField(max_length=10, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.name or self.title or f"Promotion {self.pk}"


class PromotionRedemption(models.Model):
    """Tracks when users redeem a promotion and its outcome."""
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