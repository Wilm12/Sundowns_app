"""Points system models for tracking user points and transactions."""

from django.db import models
from django.conf import settings
from django.db.models import Sum


class PointsAccount(models.Model):
    """Represents a user's points account, tied to the user (not membership).

    Points belong to the supporter/user and persist across membership lifecycle changes
    (expiry, renewal, upgrades, downgrades, etc.). This ensures continuity of rewards
    and incentives regardless of membership status.

    Attributes:
        user: OneToOne link to User. Points are user-specific.
        current_balance: Current points balance (informational, defaults to 0).
        created_at: Timestamp when account was created.
        updated_at: Timestamp when account was last updated.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='points_account'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return string representation of the points account."""
        return f"PointsAccount({self.user.username}, balance={self.balance})"

    @property
    def balance(self):
        """Calculate the actual balance by summing all transactions.

        The ledger (PointsTransaction records) is the single source of truth.

        Returns:
            int: Sum of all transaction points. Returns 0 if no transactions exist.
        """
        total = self.transactions.aggregate(total=Sum('points'))['total']
        return total if total is not None else 0

    class Meta:
        verbose_name = "Points Account"
        verbose_name_plural = "Points Accounts"


class PointsTransaction(models.Model):
    """Records a points transaction for a user's account.

    Transactions are immutable records of all points movements. The calculated balance
    is derived by summing all transactions, ensuring auditability and accuracy.

    Attributes:
        account: ForeignKey to PointsAccount.
        transaction_type: Type of transaction (membership_payment, ticket_booking, etc).
        points: Points amount (positive or negative).
        description: Human-readable description of the transaction.
        reference_id: Optional external reference (e.g., payment_id, booking_id).
        created_at: Timestamp when transaction was recorded.
    """

    class TransactionType(models.TextChoices):
        """Transaction type choices using Django TextChoices."""
        MEMBERSHIP_PAYMENT = 'membership_payment', 'Membership Payment'
        TICKET_BOOKING = 'ticket_booking', 'Ticket Booking'
        TRANSPORT_BOOKING = 'transport_booking', 'Transport Booking'
        REWARD_REDEMPTION = 'reward_redemption', 'Reward Redemption'
        MANUAL_ADJUSTMENT = 'manual_adjustment', 'Manual Adjustment'

    account = models.ForeignKey(
        PointsAccount,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        max_length=30,
        choices=TransactionType.choices,
        default=TransactionType.MANUAL_ADJUSTMENT
    )
    points = models.IntegerField(help_text="Positive or negative integer")
    description = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return string representation of the transaction."""
        return f"Transaction({self.account.user.username}, {self.get_transaction_type_display()}, {self.points}pts)"

    class Meta:
        verbose_name = "Points Transaction"
        verbose_name_plural = "Points Transactions"
        ordering = ['-created_at']
