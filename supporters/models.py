from django.conf import settings
from django.db import models


class StudentVerificationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    VERIFIED = "VERIFIED", "Verified"
    REJECTED = "REJECTED", "Rejected"
    EXPIRED = "EXPIRED", "Expired"


class EligibilityReason(models.TextChoices):
    VERIFIED = "VERIFIED", "Verified"
    VERIFICATION_EXPIRED = "VERIFICATION_EXPIRED", "Verification Expired"
    VERIFICATION_REJECTED = "VERIFICATION_REJECTED", "Verification Rejected"
    VERIFICATION_PENDING = "VERIFICATION_PENDING", "Verification Pending"
    SUPPORTER_SUSPENDED = "SUPPORTER_SUSPENDED", "Supporter Suspended"
    BRANCH_INACTIVE = "BRANCH_INACTIVE", "Branch Inactive"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE", "Manual Override"
    UNKNOWN = "UNKNOWN", "Unknown"


class SupporterEligibility(models.Model):
    """Authoritative eligibility decision for a supporter."""

    supporter = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="supporter_eligibility",
    )
    is_eligible = models.BooleanField(default=False)
    reason = models.CharField(
        max_length=30,
        choices=EligibilityReason.choices,
        default=EligibilityReason.UNKNOWN,
    )
    evaluated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Supporter Eligibility"
        verbose_name_plural = "Supporter Eligibility"

    def __str__(self):
        return f"{self.supporter} - eligible={self.is_eligible}"


class StudentVerification(models.Model):
    """Persistent verification record for a supporter identity."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_verifications",
    )
    student_number = models.CharField(max_length=50)
    university = models.CharField(max_length=150)
    status = models.CharField(
        max_length=20,
        choices=StudentVerificationStatus.choices,
        default=StudentVerificationStatus.PENDING,
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_students",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student Verification"
        verbose_name_plural = "Student Verifications"

    def __str__(self):
        return f"{self.user} - {self.student_number}"
