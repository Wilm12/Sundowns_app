"""Reward models for point ledger entries and reward tracking."""

from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class PointsLedger(models.Model):
    """Represents a point transaction for a user."""
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


class Reward(models.Model):
    """A reward that supporters can redeem with points."""

    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255)
    points_cost = models.PositiveIntegerField()
    quantity_available = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Reward'
        verbose_name_plural = 'Rewards'


class RewardRedemption(models.Model):
    """Records the redemption of a reward by a user."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        FULFILLED = 'fulfilled', 'Fulfilled'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reward_redemptions')
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE, related_name='redemptions')
    points_spent = models.PositiveIntegerField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} redeemed {self.reward.name}"

    class Meta:
        verbose_name = 'Reward Redemption'
        verbose_name_plural = 'Reward Redemptions'
