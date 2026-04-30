from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Payment(models.Model):
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
        self.full_clean()
        super().save(*args, **kwargs)

        if self.status == 'successful':
            self.membership.status = 'active'
            self.membership.save()

    def __str__(self):
        return f"{self.user} - {self.membership} - {self.amount} - {self.status}"