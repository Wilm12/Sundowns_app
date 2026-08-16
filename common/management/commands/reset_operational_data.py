from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from analytics.models import BranchMatchSnapshot
from branches.models import Branch, BranchPolicy, BranchRole, CommitteeActivity, CommitteePosition, MatchAllocation
from communications.models import CommunicationLog
from journeys.models import Journey
from matches.models import Match
from membership.models import Membership
from notifications.models import Notification
from payments.models import Payment
from points.models import PointsAccount, PointsTransaction
from promotions.models import Promotion, PromotionRedemption
from rewards.models import PointsLedger, RewardRedemption
from supporters.models import StudentVerification, SupporterEligibility
from ticketing.models import Ticket
from transport.models import Transport, TransportBooking, TransportSettlement
from users.models import User


class Command(BaseCommand):
    help = (
        "Reset the operational database to a clean starting state. "
        "This is intentionally destructive and requires --confirm."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Required confirmation flag before destructive cleanup runs.",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError(
                "This command is destructive. Re-run with --confirm to reset operational data."
            )

        with transaction.atomic():
            before = {
                "branches": Branch.objects.count(),
                "users": User.objects.count(),
                "matches": Match.objects.count(),
                "journeys": Journey.objects.count(),
                "tickets": Ticket.objects.count(),
                "transport": Transport.objects.count(),
                "transport_bookings": TransportBooking.objects.count(),
                "analytics_snapshots": BranchMatchSnapshot.objects.count(),
                "committee_positions": CommitteePosition.objects.count(),
            }

            self.stdout.write(self.style.WARNING("Preparing destructive operational reset."))
            self.stdout.write(
                self.style.WARNING(
                    "This will remove all operational data, keep only the Tuks branch, "
                    "clear all users, and leave zero matches."
                )
            )

            self.stdout.write(self.style.WARNING(f"Before counts: {before}"))

            BranchMatchSnapshot.objects.all().delete()
            TransportBooking.objects.all().delete()
            TransportSettlement.objects.all().delete()
            Ticket.objects.all().delete()
            Journey.objects.all().delete()
            MatchAllocation.objects.all().delete()
            CommitteeActivity.objects.all().delete()
            CommitteePosition.objects.all().delete()
            BranchRole.objects.all().delete()
            BranchPolicy.objects.all().delete()
            Notification.objects.all().delete()
            CommunicationLog.objects.all().delete()
            PromotionRedemption.objects.all().delete()
            Promotion.objects.all().delete()
            RewardRedemption.objects.all().delete()
            PointsLedger.objects.all().delete()
            PointsTransaction.objects.all().delete()
            PointsAccount.objects.all().delete()
            SupporterEligibility.objects.all().delete()
            StudentVerification.objects.all().delete()
            Membership.objects.all().delete()
            Payment.objects.all().delete()
            Transport.objects.all().delete()
            Match.objects.all().delete()
            User.objects.all().delete()

            other_branches = Branch.objects.exclude(name="Tuks")
            deleted_branches_count, _ = other_branches.delete()
            tuks_branch, created = Branch.objects.get_or_create(name="Tuks")

            final = {
                "branches": Branch.objects.count(),
                "users": User.objects.count(),
                "matches": Match.objects.count(),
                "journeys": Journey.objects.count(),
                "tickets": Ticket.objects.count(),
                "transport": Transport.objects.count(),
                "transport_bookings": TransportBooking.objects.count(),
                "analytics_snapshots": BranchMatchSnapshot.objects.count(),
                "committee_positions": CommitteePosition.objects.count(),
            }

            self.stdout.write(self.style.SUCCESS(f"Deleted non-Tuks branches: {deleted_branches_count}"))
            self.stdout.write(self.style.SUCCESS(f"Created Tuks branch: {created}"))
            self.stdout.write(self.style.SUCCESS(f"After counts: {final}"))

            if Branch.objects.count() != 1 or not Branch.objects.filter(name="Tuks").exists():
                raise CommandError("Reset completed but the database does not contain exactly one Tuks branch.")
            if User.objects.count() != 0:
                raise CommandError("Reset completed but user records still remain.")
            if Match.objects.count() != 0:
                raise CommandError("Reset completed but match records still remain.")

            self.stdout.write(
                self.style.SUCCESS(
                    "Operational reset complete. The database now contains only the Tuks branch, no users, and no matches."
                )
            )
