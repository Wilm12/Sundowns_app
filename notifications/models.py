from django.db import models
from django.conf import settings


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        POINTS_EARNED = 'points_earned', 'Points Earned'
        TIER_UPGRADE = 'tier_upgrade', 'Tier Upgrade'
        REWARD_REDEEMED = 'reward_redeemed', 'Reward Redeemed'
        PROMOTION = 'promotion', 'Promotion'
        SYSTEM = 'system', 'System'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=120)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"Notification({self.user}, {self.notification_type}, read={self.is_read})"
