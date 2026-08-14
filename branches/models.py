from django.conf import settings
from django.db import models


class BranchCategory(models.TextChoices):
    COMMUNITY = "COMMUNITY", "Community"
    INSTITUTIONAL = "INSTITUTIONAL", "Institutional"


class BranchStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    SUSPENDED = "SUSPENDED", "Suspended"


class CommitteeAction(models.TextChoices):
    ADMIN_PROMOTED = "ADMIN_PROMOTED", "Admin Promoted"
    ADMIN_REMOVED = "ADMIN_REMOVED", "Admin Removed"
    SUPPORTER_VERIFIED = "SUPPORTER_VERIFIED", "Supporter Verified"
    TICKET_ALLOCATED = "TICKET_ALLOCATED", "Ticket Allocated"
    TICKET_COLLECTED = "TICKET_COLLECTED", "Ticket Collected"
    ATTENDANCE_RECORDED = "ATTENDANCE_RECORDED", "Attendance Recorded"


class Branch(models.Model):
    name = models.CharField(max_length=255, unique=True)
    branch_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(
        max_length=20,
        choices=BranchCategory.choices,
        default=BranchCategory.COMMUNITY,
    )
    institution = models.CharField(max_length=200, blank=True)
    university = models.CharField(max_length=255, blank=True, null=True)
    meeting_point = models.CharField(max_length=255, blank=True, null=True)
    ticket_collection_point = models.CharField(max_length=255, blank=True, null=True)
    social_media_links = models.JSONField(default=dict, blank=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=BranchStatus.choices,
        default=BranchStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    operational_match = models.ForeignKey(
        "matches.Match",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operational_branches",
    )

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


class CommitteePosition(models.Model):
    class Position(models.TextChoices):
        CHAIRPERSON = "CHAIRPERSON", "Chairperson"
        VICE_CHAIRPERSON = "VICE_CHAIRPERSON", "Vice Chairperson"
        SECRETARY = "SECRETARY", "Secretary"
        TREASURER = "TREASURER", "Treasurer"
        MEDIA_OFFICER = "MEDIA_OFFICER", "Media Officer"
        LOGISTICS_COORDINATOR = "LOGISTICS_COORDINATOR", "Logistics Coordinator"

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="committee_positions",
    )
    branch_role = models.OneToOneField(
        BranchRole,
        on_delete=models.CASCADE,
        related_name="committee_position",
    )
    position = models.CharField(max_length=40, choices=Position.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_committee_positions",
    )

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return f"{self.position} - {self.branch_role.user}"


class CommitteeActivity(models.Model):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="committee_activities",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="committee_activities_done",
    )
    action = models.CharField(max_length=40, choices=CommitteeAction.choices)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="committee_activities_targeted",
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.branch} - {self.action}"