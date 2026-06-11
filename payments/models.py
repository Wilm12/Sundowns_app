"""Payment models representing membership payments and validation rules."""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from points.services import award_points
from points.rules import PointEvent


class Payment(models.Model):
    """Represents a payment toward a user's membership."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    membership = models.ForeignKey(
        'membership.Membership',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=100, unique=True, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validate payment amount and ensure the payment belongs to the membership user."""

        if not self.membership_id:
            return

        expected = self.membership.expected_price()
        if self.amount != expected:
            raise ValidationError({
                'amount': f'Amount must be {expected} for {self.membership.tier} membership.'
            })

        if self.user_id and self.membership.user_id != self.user_id:
            raise ValidationError({
                'user': 'Payment user must match the membership user.'
            })

    def save(self, *args, **kwargs):
        """Ensure the payment is valid before saving and activate membership on success.
        
        Points are awarded only when status transitions to 'successful' (not on re-saves).
        """

        self.full_clean()
        
        # Capture old status before save (if this is an update)
        old_status = None
        if self.pk:
            old_payment = Payment.objects.get(pk=self.pk)
            old_status = old_payment.status
        
        # Save the payment
        super().save(*args, **kwargs)

        # Activate membership when status is successful
        if self.status == 'successful':
            self.membership.status = 'active'
            self.membership.save()
        
        # Award points only on status transition: anything → successful
        if old_status != 'successful' and self.status == 'successful':
            award_points(
                user=self.user,
                event=PointEvent.MEMBERSHIP_PAYMENT,
                description="Membership payment successful",
                reference_id=self.reference
            )

    def __str__(self):
        return f"{self.user} - {self.membership} - {self.amount} - {self.status}"