from django.db import models


class BranchStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    SUSPENDED = "SUSPENDED", "Suspended"


class Branch(models.Model):
    name = models.CharField(max_length=255, unique=True)
    branch_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=BranchStatus.choices,
        default=BranchStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name