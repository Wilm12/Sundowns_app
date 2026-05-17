"""Matches app configuration for the Sundowns project.

This module defines the Django application configuration for the matches app
and its default model settings.
"""

from django.apps import AppConfig


class MatchesConfig(AppConfig):
    """Matches application configuration.

    Registers the matches app and sets a consistent default primary key field
    type for match-related models.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'matches'
