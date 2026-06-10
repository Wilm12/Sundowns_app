"""Points app configuration for the Sundowns project.

This module defines the Django application configuration for the points
app, including startup signal registration for automatic PointsAccount creation.
"""

from django.apps import AppConfig


class PointsConfig(AppConfig):
    """Points application configuration.

    Registers the points app and sets the default primary key field type.
    The ready hook imports signal handlers so they are registered when Django starts.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'points'

    def ready(self):
        """Import signal handlers when the app is ready."""
        import points.signals
