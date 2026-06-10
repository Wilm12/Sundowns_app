"""Signal handlers for points account creation and lifecycle events."""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import PointsAccount

User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=User)
def create_points_account(sender, instance, created, **kwargs):
    """Automatically create a PointsAccount when a new user is created.

    Args:
        sender: The model class (User).
        instance: The user instance being saved.
        created: Boolean indicating if this is a new instance.
        **kwargs: Additional keyword arguments from the signal.

    Ensures:
        - PointsAccount is created only once per user.
        - No duplicate accounts can be created even if signal fires multiple times.
        - Initial balance is set to 0 by default.
    """
    if created:
        PointsAccount.objects.get_or_create(user=instance)
