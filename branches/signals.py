from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Branch, BranchPolicy


@receiver(post_save, sender=Branch)
def create_branch_policy(sender, instance, created, **kwargs):
    """Create a default policy for each new branch without duplicating one."""
    if created and not BranchPolicy.objects.filter(branch=instance).exists():
        BranchPolicy.objects.create(branch=instance)
