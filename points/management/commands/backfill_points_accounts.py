"""Management command to backfill PointsAccounts for users without them."""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from points.models import PointsAccount

User = get_user_model()


class Command(BaseCommand):
    """Backfill PointsAccounts for all users that don't have one yet."""

    help = "Create PointsAccounts for users who don't have one"

    def handle(self, *args, **options):
        """Execute the backfill operation."""
        created_count = 0
        skipped_count = 0

        # Iterate through all users
        for user in User.objects.all():
            # Check if user already has a PointsAccount
            account, created = PointsAccount.objects.get_or_create(user=user)

            if created:
                created_count += 1
            else:
                skipped_count += 1

        # Print summary
        total_users = User.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_count} PointsAccounts"
            )
        )
        self.stdout.write(
            f"Skipped {skipped_count} existing PointsAccounts"
        )
        self.stdout.write(
            f"Total users processed: {total_users}"
        )
