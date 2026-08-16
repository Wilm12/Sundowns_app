"""Management command to generate analytics snapshots for matches."""

from django.core.management.base import BaseCommand
from matches.models import Match
from analytics.services.snapshot_service import AnalyticsSnapshotService


class Command(BaseCommand):
    help = "Generate analytics snapshots for matches"

    def add_arguments(self, parser):
        parser.add_argument(
            "--match-id",
            type=int,
            help="Generate snapshot for a single match"
        )

    def handle(self, *args, **options):
        """Generate snapshots for specified matches or all matches."""
        
        if options["match_id"]:
            matches = Match.objects.filter(id=options["match_id"])
        else:
            matches = Match.objects.all()

        total = 0

        for match in matches:
            snapshots = AnalyticsSnapshotService.generate_for_match(match)
            total += len(snapshots)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Generated {len(snapshots)} snapshots for {match.opponent}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"Total snapshots: {total}")
        )
