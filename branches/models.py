from django.conf import settings
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


class BranchPolicy(models.Model):
    branch = models.OneToOneField(
        Branch,
        on_delete=models.CASCADE,
        related_name="branch_policy",
    )
    student_verification_required = models.BooleanField(default=True)
    booking_deadline_hours = models.PositiveIntegerField(default=24)
    maximum_bus_capacity = models.PositiveIntegerField(default=100)
    attendance_threshold = models.PositiveIntegerField(default=70)
    allow_guest_supporters = models.BooleanField(default=False)
    announcement_requires_approval = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['branch'], name='unique_branch_policy_per_branch')
        ]

    def __str__(self):
        return f"Policy for {self.branch.name}"


class BranchRole(models.Model):
    class Role(models.TextChoices):
        MEMBER = "MEMBER", "Member"
        BRANCH_ADMIN = "BRANCH_ADMIN", "Branch Admin"

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="branch_roles",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="branch_roles",
    )
    role = models.CharField(max_length=30, choices=Role.choices)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_branch_roles",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'user', 'role'],
                condition=models.Q(is_active=True),
                name='unique_active_branch_role_per_user_per_branch',
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.role} ({self.branch})"