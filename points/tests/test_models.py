"""Tests for points models."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from points.models import PointsAccount, PointsTransaction

User = get_user_model()


class PointsAccountTestCase(TestCase):
    """Test suite for PointsAccount model."""

    def setUp(self):
        """Set up test user and account."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # PointsAccount is automatically created by signal when user is created
        self.account = self.user.points_account

    def test_points_account_creation(self):
        """Test that a PointsAccount can be created."""
        self.assertIsNotNone(self.account.id)
        self.assertEqual(self.account.user, self.user)

    def test_points_account_balance_defaults_to_zero(self):
        """Test that current_balance defaults to 0."""
        self.assertEqual(self.account.balance, 0)

    def test_points_account_balance_with_no_transactions(self):
        """Test that balance is 0 when no transactions exist."""
        self.assertEqual(self.account.balance, 0)

    def test_points_account_str_representation(self):
        """Test string representation of PointsAccount."""
        expected = f"PointsAccount({self.user.username}, balance=0)"
        self.assertEqual(str(self.account), expected)

    def test_points_account_timestamps(self):
        """Test that created_at and updated_at are set."""
        self.assertIsNotNone(self.account.created_at)
        self.assertIsNotNone(self.account.updated_at)

    def test_points_account_one_to_one_relationship(self):
        """Test that PointsAccount has OneToOne relationship with User."""
        # Should be able to access account via user
        self.assertEqual(self.user.points_account, self.account)


class PointsTransactionTestCase(TestCase):
    """Test suite for PointsTransaction model."""

    def setUp(self):
        """Set up test user, account, and transaction."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # PointsAccount is automatically created by signal when user is created
        self.account = self.user.points_account

    def test_points_transaction_creation_membership_payment(self):
        """Test creating a membership_payment transaction."""
        transaction = PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.MEMBERSHIP_PAYMENT,
            points=100,
            description='Monthly membership payment',
            reference_id='pay_123'
        )
        self.assertIsNotNone(transaction.id)
        self.assertEqual(transaction.points, 100)
        self.assertEqual(transaction.transaction_type, 'membership_payment')

    def test_points_transaction_creation_ticket_booking(self):
        """Test creating a ticket_booking transaction."""
        transaction = PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.TICKET_BOOKING,
            points=50,
            description='Ticket booking for match',
            reference_id='ticket_456'
        )
        self.assertEqual(transaction.transaction_type, 'ticket_booking')
        self.assertEqual(transaction.points, 50)

    def test_points_transaction_creation_transport_booking(self):
        """Test creating a transport_booking transaction."""
        transaction = PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.TRANSPORT_BOOKING,
            points=25,
            description='Transport booking',
            reference_id='transport_789'
        )
        self.assertEqual(transaction.transaction_type, 'transport_booking')

    def test_points_transaction_creation_reward_redemption(self):
        """Test creating a reward_redemption transaction (negative points)."""
        transaction = PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.REWARD_REDEMPTION,
            points=-50,
            description='Redeemed discount voucher',
            reference_id='reward_101'
        )
        self.assertEqual(transaction.transaction_type, 'reward_redemption')
        self.assertEqual(transaction.points, -50)

    def test_points_transaction_creation_manual_adjustment(self):
        """Test creating a manual_adjustment transaction."""
        transaction = PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.MANUAL_ADJUSTMENT,
            points=10,
            description='Admin adjustment for data correction',
            reference_id='adj_202'
        )
        self.assertEqual(transaction.transaction_type, 'manual_adjustment')

    def test_points_transaction_reference_id_optional(self):
        """Test that reference_id is optional."""
        transaction = PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.MANUAL_ADJUSTMENT,
            points=5,
            description='Test without reference'
        )
        self.assertIsNone(transaction.reference_id)

    def test_points_transaction_str_representation(self):
        """Test string representation of PointsTransaction."""
        transaction = PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.MEMBERSHIP_PAYMENT,
            points=100,
            description='Monthly membership'
        )
        self.assertIn('testuser', str(transaction))
        self.assertIn('100', str(transaction))

    def test_points_transaction_timestamps(self):
        """Test that created_at is set."""
        transaction = PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.MANUAL_ADJUSTMENT,
            points=10,
            description='Test transaction'
        )
        self.assertIsNotNone(transaction.created_at)

    def test_balance_with_multiple_transactions(self):
        """Test that balance correctly sums transactions."""
        # Add various transactions
        PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.MEMBERSHIP_PAYMENT,
            points=100,
            description='Payment 1'
        )
        PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.TICKET_BOOKING,
            points=50,
            description='Booking 1'
        )
        PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.REWARD_REDEMPTION,
            points=-30,
            description='Redemption 1'
        )

        # Refresh account from database
        self.account.refresh_from_db()

        # Check balance
        expected_balance = 100 + 50 - 30
        self.assertEqual(self.account.balance, expected_balance)

    def test_balance_with_negative_transactions(self):
        """Test balance with all negative transactions."""
        PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.REWARD_REDEMPTION,
            points=-20,
            description='Redemption'
        )
        PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.MANUAL_ADJUSTMENT,
            points=-5,
            description='Adjustment'
        )

        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, -25)

    def test_transaction_ordering(self):
        """Test that transactions are ordered by created_at descending."""
        import time
        
        transaction1 = PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.MANUAL_ADJUSTMENT,
            points=10,
            description='First'
        )
        time.sleep(0.01)  # Small delay to ensure different timestamps
        transaction2 = PointsTransaction.objects.create(
            account=self.account,
            transaction_type=PointsTransaction.TransactionType.MANUAL_ADJUSTMENT,
            points=20,
            description='Second'
        )

        transactions = list(PointsTransaction.objects.filter(account=self.account))
        # Most recent should be first
        self.assertEqual(transactions[0].id, transaction2.id)
        self.assertEqual(transactions[1].id, transaction1.id)
