from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from branches.models import Branch
from matches.models import Match
from transport.models import Transport


class Command(BaseCommand):
    help = "Seed initial branches, matches, and transport options"

    def handle(self, *args, **options):
        branches = [
            "Pretoria Central",
            "Mamelodi East",
            "Mamelodi West",
            "Soshanguve",
            "Tuks",
            "TUT",
            "Atteridgeville",
        ]

        branch_objects = {}

        for name in branches:
            branch, created = Branch.objects.get_or_create(name=name)
            branch_objects[name] = branch

            self.stdout.write(
                self.style.SUCCESS(f"{'Created' if created else 'Exists'} branch: {name}")
            )

        matches = [
            ("RB Leipzig", "Loftus Versfeld", 7),
            ("AS FAR Rabat", "Loftus Versfeld", 14),
            ("Orlando Pirates", "FNB Stadium", 21),
            ("Kaizer Chiefs", "Loftus Versfeld", 28),
        ]

        match_objects = {}

        for opponent, location, days_from_now in matches:
            match, created = Match.objects.get_or_create(
                opponent=opponent,
                defaults={
                    "location": location,
                    "date": timezone.now() + timedelta(days=days_from_now),
                },
            )
            match_objects[opponent] = match

            self.stdout.write(
                self.style.SUCCESS(f"{'Created' if created else 'Exists'} match: Sundowns vs {opponent}")
            )

        transport_setup = [
            ("Pretoria Central", "RB Leipzig", 20),
            ("Pretoria Central", "AS FAR Rabat", 20),
            ("Pretoria Central", "Orlando Pirates", 20),
            ("Pretoria Central", "Kaizer Chiefs", 20),
            ("Mamelodi East", "RB Leipzig", 15),
            ("Mamelodi West", "AS FAR Rabat", 15),
            ("Soshanguve", "Orlando Pirates", 15),
            ("Tuks", "RB Leipzig", 12),
            ("TUT", "AS FAR Rabat", 15),
            ("Atteridgeville", "Orlando Pirates", 15),
        ]

        for branch_name, opponent, capacity in transport_setup:
            transport, created = Transport.objects.get_or_create(
                branch=branch_objects[branch_name],
                match=match_objects[opponent],
                defaults={
                    "owner_id": 1,
                    "capacity": capacity,
                    "status": "active",
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"{'Created' if created else 'Exists'} transport: "
                    f"{branch_name} -> Sundowns vs {opponent}"
                )
            )

        self.stdout.write(self.style.SUCCESS("Initial seed data completed."))
