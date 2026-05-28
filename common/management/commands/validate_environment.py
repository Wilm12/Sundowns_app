from django.core.management.base import BaseCommand
from decouple import config


class Command(BaseCommand):
    help = "Validate required production environment variables"

    def handle(self, *args, **kwargs):
        required_vars = [
            "SECRET_KEY",
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD",
            "DB_HOST",
            "DB_PORT",
            "ALLOWED_HOSTS",
        ]

        missing = []

        for var in required_vars:
            value = config(var, default=None)

            if not value:
                missing.append(var)

        if missing:
            self.stdout.write(
                self.style.ERROR(
                    f"Missing environment variables: {', '.join(missing)}"
                )
            )
            raise SystemExit(1)

        self.stdout.write(
            self.style.SUCCESS(
                "Environment validation passed."
            )
        )
