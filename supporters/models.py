from django.conf import settings
from django.db import models


class StudentVerificationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    VERIFIED = "VERIFIED", "Verified"
    REJECTED = "REJECTED", "Rejected"
    EXPIRED = "EXPIRED", "Expired"


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
