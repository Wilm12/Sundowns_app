from django.test import TestCase
from django.utils import timezone

from branches.models import Branch
from users.models import User
from membership.models import Membership
from payments.models import Payment
from points.models import PointsTransaction


class PaymentMembershipActivationTests(TestCase):
    """Test suite for payment status transitions, membership activation, and points awarding."""

    def setUp(self):
        """Set up test fixtures."""
        self.branch = Branch.objects.create(
            name="Johannesburg Branch",
            location="Johannesburg"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="StrongPass123!",
            branch=self.branch,
        )
        self.membership = Membership.objects.create(
            user=self.user,
            tier="basic",
            status="inactive",
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date(),
        )

    def test_new_payment_successful_awards_points(self):
        """Test that a new payment created as successful immediately awards points."""
        payment = Payment.objects.create(
            user=self.user,
            membership=self.membership,
            amount=self.membership.expected_price(),
            status="successful",
        )

        # Verify membership activated
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.status, "active")

        # Verify points awarded
        transaction = PointsTransaction.objects.filter(
            account=self.user.points_account
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.points, 50)
        self.assertEqual(transaction.transaction_type, 'membership_payment')

    def test_pending_to_successful_awards_points(self):
        """Test that changing payment status from pending to successful awards points."""
        payment = Payment.objects.create(
            user=self.user,
            membership=self.membership,
            amount=self.membership.expected_price(),
            status="pending",
        )

        # Verify no points awarded yet
        self.assertEqual(PointsTransaction.objects.filter(
            account=self.user.points_account
        ).count(), 0)

        # Update to successful
        payment.status = "successful"
        payment.save()

        # Verify points now awarded
        transaction = PointsTransaction.objects.filter(
            account=self.user.points_account
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.points, 50)

    def test_successful_to_successful_no_duplicate_points(self):
        """Test that re-saving a successful payment does NOT award points again."""
        payment = Payment.objects.create(
            user=self.user,
            membership=self.membership,
            amount=self.membership.expected_price(),
            status="successful",
            reference="pay_dup_test"
        )

        # Verify one transaction created
        self.assertEqual(PointsTransaction.objects.filter(
            account=self.user.points_account
        ).count(), 1)

        initial_balance = self.user.points_account.balance
        self.assertEqual(initial_balance, 50)

        # Re-save the same successful payment (e.g., admin edit)
        payment.status = "successful"
        payment.save()

        # Verify still only one transaction (no duplicate)
        self.assertEqual(PointsTransaction.objects.filter(
            account=self.user.points_account
        ).count(), 1)

        # Balance should not increase
        self.user.points_account.refresh_from_db()
        self.assertEqual(self.user.points_account.balance, 50)

    def test_failed_to_successful_awards_points(self):
        """Test that changing payment from failed to successful awards points."""
        payment = Payment.objects.create(
            user=self.user,
            membership=self.membership,
            amount=self.membership.expected_price(),
            status="failed",
        )

        # Verify no points for failed payment
        self.assertEqual(PointsTransaction.objects.filter(
            account=self.user.points_account
        ).count(), 0)

        # Update to successful
        payment.status = "successful"
        payment.save()

        # Verify points awarded on transition
        transaction = PointsTransaction.objects.filter(
            account=self.user.points_account
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.points, 50)

    def test_editing_successful_payment_no_duplicate_award(self):
        """Test that editing fields on a successful payment doesn't duplicate points."""
        payment = Payment.objects.create(
            user=self.user,
            membership=self.membership,
            amount=self.membership.expected_price(),
            status="successful",
            reference="pay_edit_test"
        )

        initial_count = PointsTransaction.objects.filter(
            account=self.user.points_account
        ).count()
        self.assertEqual(initial_count, 1)

        # Edit and re-save without changing status
        payment.reference = "pay_edit_test_updated"
        payment.save()

        # Still only one transaction
        self.assertEqual(PointsTransaction.objects.filter(
            account=self.user.points_account
        ).count(), 1)

    def test_membership_activation_still_works(self):
        """Test that membership activation works correctly regardless of points."""
        payment = Payment.objects.create(
            user=self.user,
            membership=self.membership,
            amount=self.membership.expected_price(),
            status="successful",
        )

        self.membership.refresh_from_db()
        self.assertEqual(self.membership.status, "active")

    def test_reference_id_preserved_in_transaction(self):
        """Test that payment reference is preserved as transaction reference_id."""
        payment = Payment.objects.create(
            user=self.user,
            membership=self.membership,
            amount=self.membership.expected_price(),
            status="successful",
            reference="pay_ref_12345"
        )

        transaction = PointsTransaction.objects.filter(
            account=self.user.points_account
        ).first()
        self.assertEqual(transaction.reference_id, "pay_ref_12345")

    def test_multiple_payments_accumulate_points(self):
        """Test that multiple successful payments accumulate points."""
        # Create first payment
        Payment.objects.create(
            user=self.user,
            membership=self.membership,
            amount=self.membership.expected_price(),
            status="successful",
        )

        self.user.points_account.refresh_from_db()
        self.assertEqual(self.user.points_account.balance, 50)

        # Create second membership and payment for same user
        membership2 = Membership.objects.create(
            user=self.user,
            tier="premium",
            status="inactive",
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date(),
        )

        Payment.objects.create(
            user=self.user,
            membership=membership2,
            amount=membership2.expected_price(),
            status="successful",
        )

        # Balance should accumulate (50 + 50)
        self.user.points_account.refresh_from_db()
        self.assertEqual(self.user.points_account.balance, 100)