"""User model extending Django's AbstractUser with role and branch support."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Represents an authenticated user with role and branch metadata."""
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    branch_change_count = models.PositiveIntegerField(default=0)
    branch_change_window_start = models.DateField(null=True, blank=True)
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username