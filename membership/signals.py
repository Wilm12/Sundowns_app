from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Membership
from datetime import date, timedelta

User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=User)
def create_membership(sender, instance, created, **kwargs):
    if created:
        Membership.objects.create(
            user=instance,
            tier='basic',
            status='inactive',
            start_date=date.today(),
            expiry_date=date.today() + timedelta(days=30)
        )
