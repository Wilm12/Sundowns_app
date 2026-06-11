"""Tests for the backfill_points_accounts management command."""

from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from branches.models import Branch
from points.models import PointsAccount
from points.signals import create_points_account

User = get_user_model()


class BackfillPointsAccountsCommandTestCase(TestCase):
    """Test suite for the backfill_points_accounts management command."""

    def create_user_without_points(self, **kwargs):
        post_save.disconnect(create_points_account, sender=User)
        try:
            return User.objects.create_user(**kwargs)
        finally:
            post_save.connect(create_points_account, sender=User)

    def test_backfill_empty_database(self):
        """Test backfill when database has users but no PointsAccounts."""
        branch = Branch.objects.create(
            name="Test Branch",
            location="Test Location"
        )

        # Create 5 users without PointsAccounts
        for i in range(5):
            self.create_user_without_points(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="testpass123",
                branch=branch
            )

        # Verify no PointsAccounts exist
        self.assertEqual(PointsAccount.objects.count(), 0)

        # Run the command
        out = StringIO()
        call_command('backfill_points_accounts', stdout=out)

        # Verify all accounts were created
        self.assertEqual(PointsAccount.objects.count(), 5)
        output = out.getvalue()
        self.assertIn("Created 5 PointsAccounts", output)
        self.assertIn("Skipped 0 existing PointsAccounts", output)
        self.assertIn("Total users processed: 5", output)

    def test_backfill_all_users_already_have_accounts(self):
        """Test backfill when all users already have PointsAccounts."""
        branch = Branch.objects.create(
            name="Test Branch",
            location="Test Location"
        )

        # Create users with existing PointsAccounts
        for i in range(3):
            user = self.create_user_without_points(
                username=f"existing_user{i}",
                email=f"existing{i}@example.com",
                password="testpass123",
                branch=branch
            )
            PointsAccount.objects.create(user=user)

        # Verify 3 accounts exist
        self.assertEqual(PointsAccount.objects.count(), 3)

        # Run the command
        out = StringIO()
        call_command('backfill_points_accounts', stdout=out)

        # Verify no new accounts created
        self.assertEqual(PointsAccount.objects.count(), 3)
        output = out.getvalue()
        self.assertIn("Created 0 PointsAccounts", output)
        self.assertIn("Skipped 3 existing PointsAccounts", output)
        self.assertIn("Total users processed: 3", output)

    def test_backfill_mixed_users(self):
        """Test backfill with mix of users with and without PointsAccounts."""
        branch = Branch.objects.create(
            name="Test Branch",
            location="Test Location"
        )

        # Create 3 users with PointsAccounts
        for i in range(3):
            user = self.create_user_without_points(
                username=f"with_account{i}",
                email=f"with{i}@example.com",
                password="testpass123",
                branch=branch
            )
            PointsAccount.objects.create(user=user)

        # Create 2 users without PointsAccounts
        for i in range(2):
            self.create_user_without_points(
                username=f"without_account{i}",
                email=f"without{i}@example.com",
                password="testpass123",
                branch=branch
            )

        # Verify state before backfill
        self.assertEqual(PointsAccount.objects.count(), 3)
        self.assertEqual(User.objects.count(), 5)

        # Run the command
        out = StringIO()
        call_command('backfill_points_accounts', stdout=out)

        # Verify correct counts
        self.assertEqual(PointsAccount.objects.count(), 5)
        output = out.getvalue()
        self.assertIn("Created 2 PointsAccounts", output)
        self.assertIn("Skipped 3 existing PointsAccounts", output)
        self.assertIn("Total users processed: 5", output)

    def test_backfill_idempotent(self):
        """Test that running backfill twice produces the same result."""
        branch = Branch.objects.create(
            name="Test Branch",
            location="Test Location"
        )

        # Create 4 users
        for i in range(4):
            self.create_user_without_points(
                username=f"idempotent_user{i}",
                email=f"idempotent{i}@example.com",
                password="testpass123",
                branch=branch
            )

        # Run the command first time
        out1 = StringIO()
        call_command('backfill_points_accounts', stdout=out1)
        first_count = PointsAccount.objects.count()

        # Run the command second time
        out2 = StringIO()
        call_command('backfill_points_accounts', stdout=out2)
        second_count = PointsAccount.objects.count()

        # Should be idempotent
        self.assertEqual(first_count, second_count)
        self.assertEqual(second_count, 4)

        # Second run should skip all
        output2 = out2.getvalue()
        self.assertIn("Created 0 PointsAccounts", output2)
        self.assertIn("Skipped 4 existing PointsAccounts", output2)

    def test_backfill_output_format(self):
        """Test that command output has correct format."""
        branch = Branch.objects.create(
            name="Test Branch",
            location="Test Location"
        )

        # Create 2 users
        for i in range(2):
            self.create_user_without_points(
                username=f"format_user{i}",
                email=f"format{i}@example.com",
                password="testpass123",
                branch=branch
            )

        # Run the command
        out = StringIO()
        call_command('backfill_points_accounts', stdout=out)

        output = out.getvalue()

        # Verify output contains all expected messages
        self.assertIn("Created 2 PointsAccounts", output)
        self.assertIn("Skipped 0 existing PointsAccounts", output)
        self.assertIn("Total users processed: 2", output)

    def test_backfill_creates_correct_account_properties(self):
        """Test that created PointsAccounts have correct properties."""
        branch = Branch.objects.create(
            name="Test Branch",
            location="Test Location"
        )

        user = self.create_user_without_points(
            username="properties_test",
            email="props@example.com",
            password="testpass123",
            branch=branch
        )

        # Run the command
        call_command('backfill_points_accounts', stdout=StringIO())

        # Verify account properties
        account = PointsAccount.objects.get(user=user)
        self.assertEqual(account.user, user)
        self.assertEqual(account.balance, 0)
        self.assertIsNotNone(account.created_at)
        self.assertIsNotNone(account.updated_at)
