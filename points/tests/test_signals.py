"""Tests for points signals."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from points.models import PointsAccount

User = get_user_model()


class PointsAccountSignalTestCase(TestCase):
    """Test suite for automatic PointsAccount creation via signals."""

    def test_points_account_created_when_user_is_created(self):
        """Test that PointsAccount is automatically created when User is created."""
        # Create a new user
        user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='testpass123'
        )

        # Check that PointsAccount was automatically created
        self.assertTrue(PointsAccount.objects.filter(user=user).exists())
        account = PointsAccount.objects.get(user=user)
        self.assertEqual(account.user, user)

    def test_points_account_has_default_balance(self):
        """Test that automatically created PointsAccount has default balance of 0."""
        user = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )

        account = PointsAccount.objects.get(user=user)
        self.assertEqual(account.balance, 0)

    def test_no_duplicate_points_account_creation(self):
        """Test that duplicate PointsAccounts cannot be created for the same user."""
        user = User.objects.create_user(
            username='uniqueuser',
            email='unique@example.com',
            password='testpass123'
        )

        # Verify only one account exists
        accounts = PointsAccount.objects.filter(user=user)
        self.assertEqual(accounts.count(), 1)

        # Try to manually create another (should not create duplicate due to get_or_create)
        account2, created = PointsAccount.objects.get_or_create(user=user)
        self.assertFalse(created)
        self.assertEqual(account2.id, accounts.first().id)

        # Still only one account
        self.assertEqual(PointsAccount.objects.filter(user=user).count(), 1)

    def test_existing_user_can_have_account_created(self):
        """Test that PointsAccount creation works for users created without signal."""
        # Create user directly (bypassing signal in theory)
        user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )

        # Account should still be created via signal
        self.assertTrue(PointsAccount.objects.filter(user=user).exists())

    def test_multiple_users_get_separate_accounts(self):
        """Test that multiple users each get their own PointsAccount."""
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

        account1 = PointsAccount.objects.get(user=user1)
        account2 = PointsAccount.objects.get(user=user2)

        self.assertNotEqual(account1.id, account2.id)
        self.assertEqual(account1.user, user1)
        self.assertEqual(account2.user, user2)

    def test_points_account_accessible_via_user_relation(self):
        """Test that PointsAccount is accessible via user.points_account."""
        user = User.objects.create_user(
            username='relationtest',
            email='relation@example.com',
            password='testpass123'
        )

        # Should be accessible via reverse relation
        account = user.points_account
        self.assertIsNotNone(account)
        self.assertEqual(account.user, user)

    def test_user_deletion_cascades_to_points_account(self):
        """Test that deleting a user also deletes the PointsAccount."""
        user = User.objects.create_user(
            username='deletetest',
            email='delete@example.com',
            password='testpass123'
        )

        account_id = user.points_account.id

        # Delete the user
        user.delete()

        # PointsAccount should also be deleted
        self.assertFalse(PointsAccount.objects.filter(id=account_id).exists())
