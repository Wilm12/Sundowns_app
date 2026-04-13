from django.db import models
from membership.models import Membership


class Payment(models.Model):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')

    def __str__(self):
        return f"Payment {self.id} - {self.membership.user.username} - {self.amount}"

