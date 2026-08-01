from django.conf import settings
from django.db import models


class SupporterStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    PENDING_VERIFICATION = "PENDING_VERIFICATION", "Pending Verification"
    VERIFIED = "VERIFIED", "Verified"
    INACTIVE = "INACTIVE", "Inactive"
    SUSPENDED = "SUSPENDED", "Suspended"


class Supporter(models.Model):
    """Aggregate root for supporter identity and operational profile."""

    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    student_number = models.CharField(max_length=50, blank=True)
    university = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=25,
        choices=SupporterStatus.choices,
        default=SupporterStatus.PENDING_VERIFICATION,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Supporter"
        verbose_name_plural = "Supporters"

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class StudentVerification(models.Model):
    """Reusable student-verification record for a supporter."""

    class VerificationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        EXPIRED = "EXPIRED", "Expired"

    supporter = models.ForeignKey(
        Supporter,
        on_delete=models.CASCADE,
        related_name="verifications",
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_supporters",
    )
    evidence_reference = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["supporter"],
                condition=models.Q(verification_status__in=["APPROVED", "PENDING"]),
                name="unique_active_verification_per_supporter",
            )
        ]

    def __str__(self):
        return f"Verification for {self.supporter}"


class Eligibility(models.Model):
    """Derived eligibility state for a supporter."""

    supporter = models.OneToOneField(
        Supporter,
        on_delete=models.CASCADE,
        related_name="eligibility",
    )
    is_eligible = models.BooleanField(default=False)
    reason = models.CharField(max_length=255, blank=True)
    evaluated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Eligibility for {self.supporter}"
