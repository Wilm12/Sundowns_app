from django.db import models
from django.core.exceptions import ValidationError

class Payment(models.Model):
    STATUS_CHOICES = (
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    )

    membership = models.ForeignKey(
        'membership.Membership',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    payment_date = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not self.membership_id:
            return

        expected = self.membership.expected_price()
        if self.amount != expected:
            raise ValidationError({
                'amount': f'Amount must be {expected} for {self.membership.tier} membership.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.membership} - {self.amount}"