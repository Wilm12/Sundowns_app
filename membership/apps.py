"""Membership app configuration for the Sundowns project.

This module defines the Django application configuration for the membership
app, including startup signal registration.
"""

from django.apps import AppConfig


class MembershipConfig(AppConfig):
    """Membership application configuration.

    Registers the membership app and sets the default primary key field type for
    membership models. The ready hook imports signal handlers so they are
    registered when Django starts.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'membership'

    def ready(self):
        """Register membership signal handlers on app startup."""
        import membership.signals
